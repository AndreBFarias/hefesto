"""Testes do mixin TriggersActionsMixin para handlers de preset IO.

FEAT-TRIGGER-PRESETS-IMPORT-EXPORT-01.

Cobertura:
  - Import válido atualiza ``draft.triggers.<side>`` sem chamar ``trigger_set``.
  - Import com arquivo malformado não altera draft nem widgets.
  - Import em ``left`` preserva ``right`` e vice-versa.
  - Export grava arquivo JSON com estado atual dos sliders.
  - Export cancelado (sem nome) não cria arquivo.
  - Round-trip via FileChooser mockado: export → import → draft idêntico.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any, ClassVar

import pytest

# Reusa stubs e fakes do test_triggers_actions (carrega instalação de gi).
# Isso garante que o módulo gi.repository.Gtk tenha as fakes necessárias antes
# do triggers_actions ser importado.
from tests.unit.test_triggers_actions import (
    _build_mixin,
    _FakeTriggersMixin,
)

# --- Stubs adicionais para FileChooserDialog e prompt_profile_name ---------


class _FakeFileFilter:
    def __init__(self) -> None:
        self.name = ""

    def set_name(self, n: str) -> None:
        self.name = n

    def add_pattern(self, _p: str) -> None:
        pass


class _FakeFileChooser:
    """FileChooser fake controlável por monkeypatch.

    Atributos de classe permitem injetar respostas/filename a partir do teste.
    """

    last_response: int = 0  # OK
    last_filename: str | None = None
    last_action: int = 0
    last_overwrite_confirm: bool = False
    instances: ClassVar[list[Any]] = []

    def __init__(self, **kwargs: Any) -> None:
        self.title = kwargs.get("title", "")
        self.parent = kwargs.get("parent")
        self.action = kwargs.get("action", 0)
        self._buttons: list[tuple[str, int]] = []
        self._default_response = 0
        self._current_name = ""
        self._filters: list[_FakeFileFilter] = []
        self._do_overwrite_confirmation = False
        _FakeFileChooser.instances.append(self)

    def add_button(self, label: str, response: int) -> None:
        self._buttons.append((label, response))

    def set_default_response(self, r: int) -> None:
        self._default_response = r

    def set_do_overwrite_confirmation(self, v: bool) -> None:
        self._do_overwrite_confirmation = bool(v)

    def set_current_name(self, n: str) -> None:
        self._current_name = n

    def add_filter(self, f: _FakeFileFilter) -> None:
        self._filters.append(f)

    def run(self) -> int:
        return _FakeFileChooser.last_response

    def get_filename(self) -> str | None:
        return _FakeFileChooser.last_filename

    def destroy(self) -> None:
        pass


def _install_filechooser_stubs(
    monkeypatch: pytest.MonkeyPatch, *, ok: bool, filename: str | None
) -> None:
    from gi.repository import Gtk

    # Constantes de Gtk.FileChooserAction e ResponseType — sobrescrever
    # sempre, porque outros suites podem ter instalado stubs incompletos
    # no mesmo gi.repository.Gtk (poluição entre testes na mesma sessão).
    Gtk.FileChooserAction = types.SimpleNamespace(OPEN=0, SAVE=1)  # type: ignore[attr-defined]
    Gtk.ResponseType = types.SimpleNamespace(  # type: ignore[attr-defined]
        OK=-5, CANCEL=-6, REJECT=-2,
    )

    Gtk.FileChooserDialog = _FakeFileChooser  # type: ignore[attr-defined]
    Gtk.FileFilter = _FakeFileFilter  # type: ignore[attr-defined]

    _FakeFileChooser.last_response = Gtk.ResponseType.OK if ok else Gtk.ResponseType.CANCEL
    _FakeFileChooser.last_filename = filename
    _FakeFileChooser.instances = []


def _install_prompt_stub(
    monkeypatch: pytest.MonkeyPatch, *, return_value: str | None
) -> dict[str, Any]:
    """Mocka ``hefesto.app.gui_dialogs.prompt_profile_name``.

    Retorna dict mutável com ``calls`` para asserts.
    """
    info: dict[str, Any] = {"calls": 0, "last_default": None}

    fake_module = sys.modules.get("hefesto.app.gui_dialogs")
    if fake_module is None:
        fake_module = types.ModuleType("hefesto.app.gui_dialogs")
        sys.modules["hefesto.app.gui_dialogs"] = fake_module

    def fake_prompt(parent: Any = None, default_name: str = "") -> str | None:
        info["calls"] += 1
        info["last_default"] = default_name
        return return_value

    fake_module.prompt_profile_name = fake_prompt  # type: ignore[attr-defined]
    return info


# --- Helper para anexar handlers novos ao mixin -----------------------


def _wire_preset_io(inst: _FakeTriggersMixin) -> None:
    """Anexa handlers de preset IO ao ``_FakeTriggersMixin`` instanciado.

    O ``_build_mixin`` original só anexa handlers da Wave V2.4; sprint nova
    adiciona métodos novos que precisam ser bindados manualmente.
    """
    from hefesto.app.actions import triggers_actions

    cls = triggers_actions.TriggersActionsMixin
    for name in (
        "on_trigger_left_preset_export",
        "on_trigger_right_preset_export",
        "on_trigger_left_preset_import",
        "on_trigger_right_preset_import",
        "_handle_preset_export",
        "_handle_preset_import",
        "_apply_imported_preset_to_editor",
        "_build_trigger_config_for_export",
        "_toast_preset_io",
    ):
        setattr(inst, name, cls.__dict__[name].__get__(inst, type(inst)))


# --- Testes -----------------------------------------------------------


def test_handle_preset_import_atualiza_draft_sem_chamar_ipc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Import válido popula draft do lado escolhido sem disparar ``trigger_set``."""
    mixin = _build_mixin(monkeypatch)
    _wire_preset_io(mixin)
    mixin.install_triggers_tab()

    # Cria preset em disco.
    preset_path = tmp_path / "rigid.json"
    preset_path.write_text(
        json.dumps({
            "schema_version": 1,
            "name": "Rigid teste",
            "exported_at": "2026-04-24T00:00:00+00:00",
            "trigger": {"mode": "Rigid", "params": [5, 200]},
        }),
        encoding="utf-8",
    )

    _install_filechooser_stubs(monkeypatch, ok=True, filename=str(preset_path))

    n_calls_antes = len(mixin._trigger_set_calls)  # type: ignore[attr-defined]
    mixin.on_trigger_left_preset_import(None)

    # IPC NÃO foi chamado.
    assert len(mixin._trigger_set_calls) == n_calls_antes  # type: ignore[attr-defined]
    # Draft refletindo preset.
    assert mixin.draft.triggers.left.mode == "Rigid"
    assert mixin.draft.triggers.left.params == (5, 200)


def test_handle_preset_import_arquivo_invalido_nao_altera_draft(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    mixin = _build_mixin(monkeypatch)
    _wire_preset_io(mixin)
    mixin.install_triggers_tab()

    # Estado inicial.
    assert mixin.draft.triggers.left.mode == "Off"

    bad_path = tmp_path / "ruim.json"
    bad_path.write_text("{nao_e_json", encoding="utf-8")

    _install_filechooser_stubs(monkeypatch, ok=True, filename=str(bad_path))

    mixin.on_trigger_left_preset_import(None)

    # Draft permanece em Off.
    assert mixin.draft.triggers.left.mode == "Off"
    assert mixin.draft.triggers.left.params == ()


def test_handle_preset_import_em_left_preserva_right(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    mixin = _build_mixin(monkeypatch)
    _wire_preset_io(mixin)
    mixin.install_triggers_tab()

    # Configura right num modo distinto antes do import em left.
    from hefesto.app.draft_config import (
        DraftConfig,
        TriggerDraft,
        TriggersDraft,
    )

    mixin.draft = DraftConfig(
        triggers=TriggersDraft(
            left=TriggerDraft(mode="Off", params=()),
            right=TriggerDraft(mode="Pulse", params=(1, 2, 3)),
        ),
    )

    preset_path = tmp_path / "p.json"
    preset_path.write_text(
        json.dumps({
            "schema_version": 1,
            "name": "Rigid",
            "exported_at": "2026-04-24T00:00:00+00:00",
            "trigger": {"mode": "Rigid", "params": [5, 200]},
        }),
        encoding="utf-8",
    )

    _install_filechooser_stubs(monkeypatch, ok=True, filename=str(preset_path))

    mixin.on_trigger_left_preset_import(None)

    assert mixin.draft.triggers.left.mode == "Rigid"
    # Right permanece intocado.
    assert mixin.draft.triggers.right.mode == "Pulse"
    assert mixin.draft.triggers.right.params == (1, 2, 3)


def test_handle_preset_import_cancelado_nao_altera_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mixin = _build_mixin(monkeypatch)
    _wire_preset_io(mixin)
    mixin.install_triggers_tab()

    _install_filechooser_stubs(monkeypatch, ok=False, filename=None)
    mixin.on_trigger_left_preset_import(None)

    assert mixin.draft.triggers.left.mode == "Off"


def test_handle_preset_export_grava_arquivo_com_estado_dos_sliders(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    mixin = _build_mixin(monkeypatch)
    _wire_preset_io(mixin)
    mixin.install_triggers_tab()

    # Configura estado: modo Rigid + sliders 5/200.
    combo = mixin._widgets["trigger_left_mode"]
    combo.set_active_id("Rigid")
    mixin.on_trigger_left_mode_changed(combo)
    widgets = mixin._trigger_param_widgets["left"]
    widgets["position"].set_value(5)
    widgets["force"].set_value(200)

    target = tmp_path / "rigid_export.json"
    _install_filechooser_stubs(monkeypatch, ok=True, filename=str(target))
    info = _install_prompt_stub(monkeypatch, return_value="Rigid exportado")

    mixin.on_trigger_left_preset_export(None)

    assert info["calls"] == 1
    assert target.exists()
    raw = json.loads(target.read_text(encoding="utf-8"))
    assert raw["name"] == "Rigid exportado"
    assert raw["trigger"]["mode"] == "Rigid"
    assert raw["trigger"]["params"] == [5, 200]


def test_handle_preset_export_cancelado_no_prompt_nao_cria_arquivo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    mixin = _build_mixin(monkeypatch)
    _wire_preset_io(mixin)
    mixin.install_triggers_tab()

    combo = mixin._widgets["trigger_left_mode"]
    combo.set_active_id("Rigid")
    mixin.on_trigger_left_mode_changed(combo)

    # Prompt retorna None (usuário cancelou nome).
    _install_prompt_stub(monkeypatch, return_value=None)
    target = tmp_path / "nada.json"
    _install_filechooser_stubs(monkeypatch, ok=True, filename=str(target))

    mixin.on_trigger_left_preset_export(None)

    assert not target.exists()


def test_round_trip_export_import_draft_identico(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Export do estado atual + import em outro mixin = draft idêntico."""
    mixin = _build_mixin(monkeypatch)
    _wire_preset_io(mixin)
    mixin.install_triggers_tab()

    # Configura Rigid 7/180 em left.
    combo = mixin._widgets["trigger_left_mode"]
    combo.set_active_id("Rigid")
    mixin.on_trigger_left_mode_changed(combo)
    widgets = mixin._trigger_param_widgets["left"]
    widgets["position"].set_value(7)
    widgets["force"].set_value(180)

    target = tmp_path / "rt.json"
    _install_filechooser_stubs(monkeypatch, ok=True, filename=str(target))
    _install_prompt_stub(monkeypatch, return_value="rt")

    mixin.on_trigger_left_preset_export(None)
    assert target.exists()

    # Novo mixin, import.
    mixin2 = _build_mixin(monkeypatch)
    _wire_preset_io(mixin2)
    mixin2.install_triggers_tab()

    _install_filechooser_stubs(monkeypatch, ok=True, filename=str(target))
    mixin2.on_trigger_right_preset_import(None)

    # right do mixin2 deve refletir o que estava em left do mixin.
    assert mixin2.draft.triggers.right.mode == "Rigid"
    assert mixin2.draft.triggers.right.params == (7, 180)


def test_handle_preset_import_modo_off_nao_quebra(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Import de preset com mode='Off' (sem params) é aceito sem erro."""
    mixin = _build_mixin(monkeypatch)
    _wire_preset_io(mixin)
    mixin.install_triggers_tab()

    target = tmp_path / "off.json"
    target.write_text(
        json.dumps({
            "schema_version": 1,
            "name": "Off",
            "exported_at": "2026-04-24T00:00:00+00:00",
            "trigger": {"mode": "Off", "params": []},
        }),
        encoding="utf-8",
    )

    _install_filechooser_stubs(monkeypatch, ok=True, filename=str(target))
    mixin.on_trigger_right_preset_import(None)

    assert mixin.draft.triggers.right.mode == "Off"
    assert mixin.draft.triggers.right.params == ()
