"""Aba Triggers: dropdown de 19 presets + sliders dinâmicos + aplicar via IPC."""
# ruff: noqa: E402
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from hefesto.app.actions.base import WidgetAccessMixin
from hefesto.app.actions.trigger_specs import (
    PRESETS,
    TriggerParamSpec,
    get_spec,
    preset_to_factory_args,
)
from hefesto.app.ipc_bridge import trigger_set
from hefesto.profiles.schema import TriggerConfig
from hefesto.profiles.trigger_preset_io import (
    export_trigger_preset,
    import_trigger_preset,
)
from hefesto.profiles.trigger_presets import (
    FEEDBACK_POSITION_LABELS,
    VIBRATION_POSITION_LABELS,
    resolve_feedback_preset,
    resolve_vibration_preset,
)
from hefesto.utils.logging_config import get_logger

logger = get_logger(__name__)


class TriggersActionsMixin(WidgetAccessMixin):
    """Controla a aba Triggers (duas colunas L2/R2).

    Assume widgets no builder: trigger_<side>_mode, trigger_<side>_desc,
    trigger_<side>_params_box, trigger_<side>_apply, trigger_<side>_reset.
    """

    _trigger_param_widgets: dict[str, dict[str, Gtk.Scale]]
    # Guard para evitar loop widget->draft->refresh->widget.
    _guard_refresh: bool = False
    # Guard para evitar que a aplicação de preset dispare o handler de slider
    # e reverta o preset para "custom" imediatamente.
    _trigger_preset_applying: bool = False

    # Modos que ativam o dropdown de preset por posicao.
    _MODES_COM_PRESET = frozenset({"MultiPositionFeedback", "MultiPositionVibration"})

    def install_triggers_tab(self) -> None:
        self._trigger_param_widgets = {"left": {}, "right": {}}
        self._trigger_preset_applying = False
        for side in ("left", "right"):
            combo: Gtk.ComboBoxText = self._get(f"trigger_{side}_mode")
            combo.remove_all()
            for spec in PRESETS:
                combo.append(spec.name, spec.label)
            combo.set_active_id("Off")
            self._rebuild_params(side, "Off")
            self._populate_preset_combo(side, "MultiPositionFeedback")

    # --- draft integration ---

    def _refresh_triggers_from_draft(self) -> None:
        """Popula widgets da aba Triggers a partir de self.draft.triggers.

        Protegido por _guard_refresh para não disparar handlers de signal
        durante a atualização programatica dos combos.
        """
        if self._guard_refresh:
            return
        draft = getattr(self, "draft", None)
        if draft is None:
            return
        self._guard_refresh = True
        try:
            for side in ("left", "right"):
                trigger_draft = getattr(draft.triggers, side)
                combo: Gtk.ComboBoxText = self._get(f"trigger_{side}_mode")
                if combo is None:
                    continue
                combo.set_active_id(trigger_draft.mode)
                self._rebuild_params(side, trigger_draft.mode)
                # Restaura valores dos parametros
                widgets = self._trigger_param_widgets.get(side, {})
                for i, name in enumerate(widgets):
                    if i < len(trigger_draft.params):
                        widgets[name].set_value(trigger_draft.params[i])
        finally:
            self._guard_refresh = False

    # --- signals ---

    def on_trigger_left_mode_changed(self, combo: Gtk.ComboBoxText) -> None:
        self._on_mode_changed("left", combo)

    def on_trigger_right_mode_changed(self, combo: Gtk.ComboBoxText) -> None:
        self._on_mode_changed("right", combo)

    def on_trigger_left_preset_changed(self, combo: Gtk.ComboBoxText) -> None:
        self._on_preset_changed("left", combo)

    def on_trigger_right_preset_changed(self, combo: Gtk.ComboBoxText) -> None:
        self._on_preset_changed("right", combo)

    def on_trigger_left_apply(self, _btn: Gtk.Button) -> None:
        self._apply_trigger("left")

    def on_trigger_right_apply(self, _btn: Gtk.Button) -> None:
        self._apply_trigger("right")

    def on_trigger_left_reset(self, _btn: Gtk.Button) -> None:
        self._reset_trigger("left")

    def on_trigger_right_reset(self, _btn: Gtk.Button) -> None:
        self._reset_trigger("right")

    # --- preset IO (FEAT-TRIGGER-PRESETS-IMPORT-EXPORT-01) ---

    def on_trigger_left_preset_export(self, _btn: Gtk.Button) -> None:
        self._handle_preset_export("left")

    def on_trigger_right_preset_export(self, _btn: Gtk.Button) -> None:
        self._handle_preset_export("right")

    def on_trigger_left_preset_import(self, _btn: Gtk.Button) -> None:
        self._handle_preset_import("left")

    def on_trigger_right_preset_import(self, _btn: Gtk.Button) -> None:
        self._handle_preset_import("right")

    # --- helpers ---

    def _on_mode_changed(self, side: str, combo: Gtk.ComboBoxText) -> None:
        if self._guard_refresh:
            return
        preset_id = combo.get_active_id()
        if preset_id is None:
            return
        self._rebuild_params(side, preset_id)
        # Mostra/esconde a linha de preset conforme o modo selecionado.
        self._update_preset_row_visibility(side, preset_id)
        # Atualiza draft com novo modo (params zerados ate usuário ajustar sliders)
        draft = getattr(self, "draft", None)
        if draft is not None:
            from hefesto.app.draft_config import TriggerDraft

            new_trigger = TriggerDraft(mode=preset_id, params=())
            new_triggers = draft.triggers.model_copy(update={side: new_trigger})
            self.draft = draft.model_copy(update={"triggers": new_triggers})

    def _on_preset_changed(self, side: str, combo: Gtk.ComboBoxText) -> None:
        """Aplica o preset selecionado populando os sliders de posicao."""
        if self._guard_refresh or self._trigger_preset_applying:
            return
        preset_key = combo.get_active_id()
        if preset_key is None or preset_key == "custom":
            return

        # Determina qual dicionario de presets usar com base no modo atual.
        mode_combo: Gtk.ComboBoxText = self._get(f"trigger_{side}_mode")
        mode_id = mode_combo.get_active_id() if mode_combo else None

        if mode_id == "MultiPositionFeedback":
            valores = resolve_feedback_preset(preset_key)
        elif mode_id == "MultiPositionVibration":
            valores = resolve_vibration_preset(preset_key)
        else:
            return

        if valores is None:
            return

        # Popula os sliders de posicao com guard ativo.
        self._trigger_preset_applying = True
        try:
            widgets = self._trigger_param_widgets.get(side, {})
            for _idx, (nome, scale) in enumerate(widgets.items()):
                # Pula o slider de frequência em MultiPositionVibration (primeiro param).
                if mode_id == "MultiPositionVibration" and nome == "frequency":
                    continue
                # Mapeia nome "pos_N" para o indice N.
                if nome.startswith("pos_"):
                    try:
                        pos_idx = int(nome[4:])
                    except ValueError:
                        continue
                    if pos_idx < len(valores):
                        scale.set_value(valores[pos_idx])
                        scale.queue_draw()
        finally:
            self._trigger_preset_applying = False

    def _update_preset_row_visibility(self, side: str, mode_id: str) -> None:
        """Exibe ou oculta a linha de preset conforme o modo selecionado."""
        preset_row: Gtk.Box | None = self._get(f"trigger_{side}_preset_row")
        if preset_row is None:
            return
        deve_mostrar = mode_id in self._MODES_COM_PRESET
        preset_row.set_visible(deve_mostrar)
        if deve_mostrar:
            # Repopula o combo com os labels corretos para o modo atual.
            self._populate_preset_combo(side, mode_id)

    def _populate_preset_combo(self, side: str, mode_id: str) -> None:
        """Preenche o GtkComboBoxText de preset com as entradas do modo."""
        combo: Gtk.ComboBoxText | None = self._get(f"trigger_{side}_preset_combo")
        if combo is None:
            return
        combo.remove_all()
        if mode_id == "MultiPositionFeedback":
            labels = FEEDBACK_POSITION_LABELS
        elif mode_id == "MultiPositionVibration":
            labels = VIBRATION_POSITION_LABELS
        else:
            return
        for chave, label in labels.items():
            combo.append(chave, label)
        combo.set_active_id("custom")

    def _update_preset_to_custom(self, side: str) -> None:
        """Reverte o dropdown de preset para 'Personalizar' quando usuário move slider."""
        if self._trigger_preset_applying:
            return
        combo: Gtk.ComboBoxText | None = self._get(f"trigger_{side}_preset_combo")
        if combo is None or not combo.get_visible():
            return
        active = combo.get_active_id()
        if active != "custom":
            self._guard_refresh = True
            try:
                combo.set_active_id("custom")
            finally:
                self._guard_refresh = False

    def _rebuild_params(self, side: str, preset_id: str) -> None:
        spec = get_spec(preset_id)
        box: Gtk.Box = self._get(f"trigger_{side}_params_box")
        desc: Gtk.Label = self._get(f"trigger_{side}_desc")

        for child in box.get_children():
            box.remove(child)
        self._trigger_param_widgets[side] = {}

        if spec is None:
            desc.set_text("")
            return

        desc.set_markup(f"<i>{spec.description}</i>")

        for param in spec.params:
            row = self._build_param_row(param)
            box.pack_start(row, False, False, 0)
            self._trigger_param_widgets[side][param.name] = row.scale
            # Conecta sinal para reverter preset para "custom" ao mover slider.
            row.scale.connect(
                "value-changed",
                lambda _scale, _side=side: self._update_preset_to_custom(_side),
            )

        box.show_all()

    def _build_param_row(self, param: TriggerParamSpec) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.set_homogeneous(False)

        label = Gtk.Label(label=param.label)
        label.set_xalign(0)
        label.set_size_request(200, -1)
        row.pack_start(label, False, False, 0)

        adjust = Gtk.Adjustment(
            value=param.default,
            lower=param.min_value,
            upper=param.max_value,
            step_increment=1,
            page_increment=max(1, (param.max_value - param.min_value) // 10),
        )
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjust)
        scale.set_digits(0)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_hexpand(True)
        row.pack_start(scale, True, True, 0)

        row.scale = scale
        return row

    def _collect_values(self, side: str) -> dict[str, int]:
        widgets = self._trigger_param_widgets.get(side, {})
        return {name: int(scale.get_value()) for name, scale in widgets.items()}

    def _apply_trigger(self, side: str) -> None:
        combo: Gtk.ComboBoxText = self._get(f"trigger_{side}_mode")
        preset_id = combo.get_active_id()
        if preset_id is None:
            return
        spec = get_spec(preset_id)
        if spec is None:
            return

        values = self._collect_values(side)
        args = preset_to_factory_args(spec, values)

        # Persiste params posicionais no draft antes de enviar via IPC.
        draft = getattr(self, "draft", None)
        if draft is not None:
            from hefesto.app.draft_config import TriggerDraft

            params_list: list[int] = args if isinstance(args, list) else []
            new_trigger = TriggerDraft(mode=preset_id, params=tuple(params_list))
            new_triggers = draft.triggers.model_copy(update={side: new_trigger})
            self.draft = draft.model_copy(update={"triggers": new_triggers})

        if isinstance(args, dict):
            # Custom e MultiPosition_* usam dict; IPC espera posicional
            # no formato aceito por build_from_name nomeado.
            ok = self._send_trigger_named(side, preset_id, args)
        else:
            ok = trigger_set(side, preset_id, args)

        self._toast_trigger(side, preset_id, ok)

    def _send_trigger_named(
        self, side: str, preset_id: str, kwargs: dict[str, object]
    ) -> bool:
        """Formato alternativo pra presets com kwargs (custom, multi_pos)."""
        if preset_id == "Custom":
            mode_val = int(kwargs.get("mode", 0) or 0)  # type: ignore[call-overload]
            forces_obj = kwargs.get("forces", ())
            forces = list(forces_obj) if isinstance(forces_obj, (list, tuple)) else []
            return trigger_set(side, preset_id, [mode_val, *forces])
        if preset_id == "MultiPositionFeedback":
            strengths_obj = kwargs.get("strengths", [])
            strengths = list(strengths_obj) if isinstance(strengths_obj, (list, tuple)) else []
            return trigger_set(side, preset_id, strengths)
        if preset_id == "MultiPositionVibration":
            freq = int(kwargs.get("frequency", 0) or 0)  # type: ignore[call-overload]
            strengths_obj = kwargs.get("strengths", [])
            strengths = list(strengths_obj) if isinstance(strengths_obj, (list, tuple)) else []
            return trigger_set(side, preset_id, [freq, *strengths])
        return False

    def _reset_trigger(self, side: str) -> None:
        combo: Gtk.ComboBoxText = self._get(f"trigger_{side}_mode")
        combo.set_active_id("Off")
        self._rebuild_params(side, "Off")
        trigger_set(side, "Off", [])
        self._toast_trigger(side, "Off", True)

    def _toast_trigger(self, side: str, preset_id: str, ok: bool) -> None:
        bar: Any = self._get("status_bar")
        if bar is None:
            return
        ctx_id = bar.get_context_id("trigger")
        msg = (
            f"{side.upper()} -> {preset_id} aplicado"
            if ok
            else f"{side.upper()} -> {preset_id} falhou (daemon offline?)"
        )
        bar.push(ctx_id, msg)

    # --- preset IO helpers ---

    def _toast_preset_io(self, side: str, msg: str) -> None:
        """Empurra mensagem para a status_bar (canal dedicado a preset IO)."""
        bar: Any = self._get("status_bar")
        if bar is None:
            return
        ctx_id = bar.get_context_id("trigger_preset_io")
        bar.push(ctx_id, f"{side.upper()} -> {msg}")

    def _build_trigger_config_for_export(self, side: str) -> TriggerConfig | None:
        """Coleta o estado atual do editor (modo + sliders) como ``TriggerConfig``.

        Reusa ``preset_to_factory_args`` para reconverter ``dict[str, int]``
        em ``list[int]`` (modos simples) ou ``list[list[int]]`` (modos
        ``MultiPosition*``). Para ``Custom``, achata em ``[mode, *forces]``.
        Retorna ``None`` se modo é desconhecido ou ``Off`` (nada a exportar).
        """
        combo: Gtk.ComboBoxText | None = self._get(f"trigger_{side}_mode")
        if combo is None:
            return None
        preset_id = combo.get_active_id()
        if preset_id is None:
            return None
        spec = get_spec(preset_id)
        if spec is None:
            return None

        values = self._collect_values(side)
        args = preset_to_factory_args(spec, values)

        params: list[int] | list[list[int]]
        if isinstance(args, list):
            params = list(args)
        elif preset_id == "MultiPositionFeedback":
            strengths_obj = args.get("strengths", []) if isinstance(args, dict) else []
            strengths = (
                list(strengths_obj)
                if isinstance(strengths_obj, (list, tuple))
                else []
            )
            params = [list(strengths)]
        elif preset_id == "MultiPositionVibration":
            if isinstance(args, dict):
                freq = int(cast(Any, args.get("frequency", 0)) or 0)
                strengths_obj = args.get("strengths", [])
            else:
                freq = 0
                strengths_obj = []
            strengths = (
                list(strengths_obj)
                if isinstance(strengths_obj, (list, tuple))
                else []
            )
            params = [[freq], list(strengths)]
        elif preset_id == "Custom":
            if isinstance(args, dict):
                mode_val = int(cast(Any, args.get("mode", 0)) or 0)
                forces_obj = args.get("forces", ())
            else:
                mode_val = 0
                forces_obj = ()
            forces = (
                list(forces_obj)
                if isinstance(forces_obj, (list, tuple))
                else []
            )
            params = [mode_val, *forces]
        else:
            params = []

        return TriggerConfig(mode=preset_id, params=params)

    def _handle_preset_export(self, side: str) -> None:
        """Exporta o estado do editor ``side`` para arquivo JSON via FileChooser.

        Não toca o daemon nem o draft. Usuário escolhe nome legível
        (default ``trigger_<side>``) e caminho. Erros são reportados via
        toast PT-BR.
        """
        cfg = self._build_trigger_config_for_export(side)
        if cfg is None:
            self._toast_preset_io(side, "exportar: nenhum modo válido selecionado")
            return

        from hefesto.app import gui_dialogs

        window = self._get("main_window")
        nome = gui_dialogs.prompt_profile_name(
            parent=window, default_name=f"trigger_{side}"
        )
        if not nome:
            self._toast_preset_io(side, "exportar cancelado")
            return

        chooser = Gtk.FileChooserDialog(
            title="Exportar preset de gatilho",
            parent=window,
            action=Gtk.FileChooserAction.SAVE,
        )
        chooser.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        chooser.add_button("Salvar", Gtk.ResponseType.OK)
        chooser.set_default_response(Gtk.ResponseType.OK)
        chooser.set_do_overwrite_confirmation(True)
        chooser.set_current_name(f"{nome}.json")

        filtro = Gtk.FileFilter()
        filtro.set_name("Presets JSON (*.json)")
        filtro.add_pattern("*.json")
        chooser.add_filter(filtro)

        response = chooser.run()
        filename = chooser.get_filename()
        chooser.destroy()

        if response != Gtk.ResponseType.OK or not filename:
            self._toast_preset_io(side, "exportar cancelado")
            return

        try:
            final_path = export_trigger_preset(
                Path(filename), name=nome, trigger=cfg
            )
        except OSError as exc:
            self._toast_preset_io(side, f"falha ao gravar: {exc}")
            logger.warning(
                "trigger_preset_export_falhou",
                side=side,
                arquivo=filename,
                erro=str(exc),
            )
            return

        self._toast_preset_io(side, f"preset exportado em {final_path}")
        logger.info(
            "trigger_preset_export_ok",
            side=side,
            arquivo=str(final_path),
            nome=nome,
            modo=cfg.mode,
        )

    def _handle_preset_import(self, side: str) -> None:
        """Importa preset JSON e popula o editor de ``side`` sem aplicar via IPC.

        Usuário precisa pressionar "Aplicar em <SIDE>" para enviar o estado
        ao daemon. Outro lado (L2/R2) permanece intocado.
        """
        window = self._get("main_window")

        chooser = Gtk.FileChooserDialog(
            title="Importar preset de gatilho",
            parent=window,
            action=Gtk.FileChooserAction.OPEN,
        )
        chooser.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        chooser.add_button("Abrir", Gtk.ResponseType.OK)
        chooser.set_default_response(Gtk.ResponseType.OK)

        filtro = Gtk.FileFilter()
        filtro.set_name("Presets JSON (*.json)")
        filtro.add_pattern("*.json")
        chooser.add_filter(filtro)

        response = chooser.run()
        filename = chooser.get_filename()
        chooser.destroy()

        if response != Gtk.ResponseType.OK or not filename:
            self._toast_preset_io(side, "importar cancelado")
            return

        try:
            preset = import_trigger_preset(Path(filename))
        except FileNotFoundError as exc:
            self._toast_preset_io(side, f"arquivo não encontrado: {exc}")
            logger.warning(
                "trigger_preset_import_inexistente",
                side=side,
                arquivo=filename,
                erro=str(exc),
            )
            return
        except json.JSONDecodeError as exc:
            self._toast_preset_io(side, f"arquivo inválido: {exc}")
            logger.warning(
                "trigger_preset_import_json_invalido",
                side=side,
                arquivo=filename,
                erro=str(exc),
            )
            return
        except Exception as exc:
            # Validation error e demais — preservar comportamento "não altera widgets".
            self._toast_preset_io(side, f"arquivo inválido: {exc}")
            logger.warning(
                "trigger_preset_import_validacao_falhou",  # log key ASCII por convenção structlog
                side=side,
                arquivo=filename,
                erro=str(exc),
            )
            return

        # Popular widgets sem disparar IPC.
        self._apply_imported_preset_to_editor(side, preset.trigger)
        self._toast_preset_io(
            side,
            f"preset '{preset.name}' importado. Pressione 'Aplicar em "
            f"{side.upper()}' para enviar.",
        )
        logger.info(
            "trigger_preset_import_ok",
            side=side,
            arquivo=filename,
            nome=preset.name,
            modo=preset.trigger.mode,
        )

    def _apply_imported_preset_to_editor(
        self, side: str, trigger: TriggerConfig
    ) -> None:
        """Repopula combo de modo + sliders + draft a partir de ``TriggerConfig``.

        NÃO chama ``trigger_set`` (IPC). Usuário ainda precisa pressionar
        "Aplicar em L2/R2" para enviar ao daemon. Apenas o lado ``side`` é
        afetado; o outro permanece intocado em ``self.draft``.
        """
        from hefesto.app.draft_config import TriggerDraft

        combo: Gtk.ComboBoxText | None = self._get(f"trigger_{side}_mode")
        if combo is None:
            return

        # Reconstrói widgets dinâmicos do modo importado (com guard para não
        # disparar handlers de signal recursivamente).
        self._guard_refresh = True
        try:
            combo.set_active_id(trigger.mode)
            self._rebuild_params(side, trigger.mode)
            self._update_preset_row_visibility(side, trigger.mode)

            # Achatar params para a sequência ordenada de sliders.
            flat: list[int] = []
            if trigger.is_nested:
                for sub in trigger.params:
                    if isinstance(sub, list):
                        flat.extend(int(x) for x in sub)
            else:
                flat = [int(cast(Any, x)) for x in trigger.params]

            widgets = self._trigger_param_widgets.get(side, {})
            for idx, name in enumerate(widgets):
                if idx < len(flat):
                    widgets[name].set_value(flat[idx])
        finally:
            self._guard_refresh = False

        # Atualiza draft do lado importado preservando o outro.
        draft = getattr(self, "draft", None)
        if draft is not None:
            params_tuple: tuple[int, ...]
            if trigger.is_nested:
                acc: list[int] = []
                for sub in trigger.params:
                    if isinstance(sub, list):
                        acc.extend(int(x) for x in sub)
                params_tuple = tuple(acc)
            else:
                params_tuple = tuple(int(cast(Any, x)) for x in trigger.params)

            new_trigger = TriggerDraft(mode=trigger.mode, params=params_tuple)
            new_triggers = draft.triggers.model_copy(update={side: new_trigger})
            self.draft = draft.model_copy(update={"triggers": new_triggers})
