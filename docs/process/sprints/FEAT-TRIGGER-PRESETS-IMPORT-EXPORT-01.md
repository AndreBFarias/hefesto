# FEAT-TRIGGER-PRESETS-IMPORT-EXPORT-01 — Exportar/Importar preset de gatilho como JSON standalone

**Tipo:** feature (GUI + IO de arquivo + schema novo).
**Wave:** V2.5 — sprint #8 da ordem recomendada em `docs/process/SPRINT_ORDER.md:445`.
**Porte:** S.
**Estimativa:** 1 iteração.
**Dependências:** FEAT-PROFILE-STATE-01 (`DraftConfig` central), FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01 (MERGED 2026-04-24, baseline 1340 testes).

---

**Tracking:** label `type:feature`, `gui`, `triggers`, `profiles`, `ai-task`, `status:ready`.

## Objetivo

Adicionar 2 botões na aba **Gatilhos** da GUI GTK3 (um por coluna L2/R2 ou um par compartilhado) que permitem ao usuário **exportar** o estado atual do editor de gatilho selecionado para um arquivo `.json` standalone e **importar** um arquivo `.json` standalone repondo o estado do editor (sem commitar — usuário ainda precisa "Aplicar em L2/R2" para enviar via IPC e "Salvar perfil" no rodapé para persistir).

Uso esperado: um usuário cria um gatilho `MultiPositionFeedback` calibrado fino, exporta para `meu_gatilho_arco.json`, compartilha em fórum/Discord; outro usuário importa via GUI e tem o mesmo comportamento sem precisar redigitar 10 sliders.

## Contexto

Estado atual (2026-04-24, HEAD `main` pós FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01 merged), confirmado via leitura linha-a-linha:

- `src/hefesto/gui/main.glade:392-614` — aba Gatilhos é um `GtkBox` horizontal `tab_triggers_box` com 2 colunas (`GtkFrame` "L2 (gatilho esquerdo)" e "R2 (gatilho direito)"). Cada coluna tem layout vertical: `trigger_<side>_mode` (combo modo) → `trigger_<side>_preset_row` (linha de preset por posição, com `trigger_<side>_preset_combo`) → `trigger_<side>_desc` (label) → `GtkScrolledWindow` com `trigger_<side>_params_box` (sliders dinâmicos) → linha de 2 botões `trigger_<side>_apply` ("Aplicar em L2/R2") + `trigger_<side>_reset` ("Desligar (Off)"). A linha 617 fecha o `tab_triggers_box` e a tab tem label "Gatilhos" via `GtkLabel`. **Não existe rodapé extra** na aba — os 2 botões novos vão **dentro de cada coluna**, abaixo da linha apply/reset, ou em uma nova linha horizontal compartilhada entre as duas colunas. Decisão tomada na seção Escopo abaixo.
- `src/hefesto/app/actions/triggers_actions.py` (341L) — `TriggersActionsMixin` é o mixin canônico para handlers da aba. Usa `WidgetAccessMixin._get(...)`, mantém `self.draft` (instância imutável de `DraftConfig`) e `self._trigger_param_widgets[side][param_name]` (dict de `Gtk.Scale`). Já há padrão de `_collect_values(side)` (lê sliders → dict `{name: int}`) e `_apply_trigger(side)` (commita IPC + atualiza draft). Reusar esses helpers.
- `src/hefesto/profiles/schema.py:64-118` — `TriggerConfig(mode: str, params: list[int] | list[list[int]])` + `TriggersConfig(left: TriggerConfig, right: TriggerConfig)`. Validador `_validate_params` rejeita mistura `[[1,2], 3]`. Ambos com `model_config = ConfigDict(extra="forbid")`. Re-uso direto: o que importa para o preset standalone é **um único** `TriggerConfig` (lado único), não o par. Schema novo `TriggerPreset` será wrapper com metadados + um `TriggerConfig`.
- `src/hefesto/profiles/trigger_presets.py:1-125` — namespace **diferente** do que esta sprint adiciona. Esse arquivo expõe `FEEDBACK_POSITION_PRESETS` / `VIBRATION_POSITION_PRESETS` (presets internos hardcoded de 10 posições para o combo "Preset por posição"). **Não confundir**: a sprint nova é IO de arquivo do usuário, schema dedicado, módulo novo `trigger_preset_io.py`. Comentário explícito vai no docstring do módulo novo apontando essa diferença para evitar fusão errada na próxima refatoração.
- `src/hefesto/app/actions/footer_actions.py:170-256` — padrão canônico de `FileChooserDialog` no projeto: `Gtk.FileChooserDialog` + `Gtk.FileChooserAction.OPEN/SAVE`, filtro `*.json`, ler com `json.loads(Path(...).read_text("utf-8"))`, validar com `Profile.model_validate`, em erro chamar `self._footer_toast(f"Arquivo inválido: {exc}")` + `logger.warning(...)`. **Reusar exato esse padrão**, adaptando `Profile` → `TriggerPreset`.
- `src/hefesto/app/actions/firmware_actions.py:105-110` — também usa `FileChooserDialog`. Confirma que o padrão estabelecido no projeto é `FileChooserDialog`, **não** `FileChooserNative`. Sprint segue `FileChooserDialog` para consistência (mesmo que o prompt original tenha sugerido `Native`).
- `src/hefesto/app/draft_config.py:32-47` — `TriggerDraft(mode: str, params: tuple[int, ...])` (frozen) + `TriggersDraft(left, right)`. **Round-trip alvo**: editor → snapshot atual de sliders → exportar → reimportar → popular sliders idênticos. O draft do trigger no lado importado é atualizado via `self.draft.model_copy(update={"triggers": new_triggers})` no padrão já estabelecido em `_on_mode_changed` (linha 130) e `_apply_trigger` (linha 292-293).
- `src/hefesto/app/app.py:148-220` — `_signal_handlers()` registra **explicitamente** todos os handlers do builder (`on_trigger_left_*`, `on_firmware_*`, etc.). Armadilha A-7-ish recorrente: handler novo no glade sem entrada em `_signal_handlers()` → botão morto silenciosamente. Documentado em `BUG-FIRMWARE-SIGNAL-HANDLERS-01` (PR 77.1, MERGED). Spec exige adicionar handlers ao dict.
- `assets/profiles_default/fps.json` — referência do formato canônico de `triggers.left/right` em JSON: `{"mode": "Rigid", "params": [0, 255]}` para shape simples; presets multi-posição usam `params: [[…], …]` aninhado. O preset standalone exporta o **mesmo shape** dentro de um wrapper.
- `tests/unit/test_triggers_actions.py` (existente) — base para testes do mixin com mocks GTK; padrão `pytest` + `unittest.mock.MagicMock` para `Gtk.ComboBoxText`. Reusar como template dos novos casos.
- Baseline pytest 2026-04-24 HEAD `main`: **1340 testes coletados**.

L-21-3 aplicada: spec foi escrito **após** leitura completa de `main.glade` (linhas 390-620), `triggers_actions.py` (1-341), `schema.py` (1-220), `trigger_presets.py` (1-125), `draft_config.py` (1-200), `footer_actions.py` (170-260), `app.py` (130-220) e amostras `assets/profiles_default/*.json`.

Premissas do prompt original que **divergiram do código real**, ajustadas no spec:

- Prompt sugeriu `GtkFileChooserNative` — projeto usa **`FileChooserDialog`** em `footer_actions.py` e `firmware_actions.py`; sprint segue o padrão estabelecido.
- Prompt sugeriu `src/hefesto/app/actions/trigger_actions.py` (singular) — caminho real é `triggers_actions.py` (plural). Ajustado.
- Prompt sugeriu reusar `manager.py::load_profile/save_profile` — esses são para **perfil inteiro**; sprint cria funções **dedicadas** `export_trigger_preset`/`import_trigger_preset` no novo módulo `trigger_preset_io.py`. Justificativa: schema diferente (`TriggerPreset` é wrapper de um `TriggerConfig`, não Profile completo).
- Prompt sugeriu campo novo em `TriggersConfig` — **não é necessário**. Schema do preset standalone é arquivo separado; o `TriggersConfig` do `Profile` permanece intocado. Sprint **não dispara A-06** (não adiciona campo a `LedsConfig/TriggersConfig/RumbleConfig` consumido por mapper de perfil).

## Escopo

### Decisão 1 — Schema novo `TriggerPreset` com wrapper de metadados

Criar **novo arquivo** `src/hefesto/profiles/trigger_preset_schema.py` com:

```python
from __future__ import annotations
from datetime import UTC, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from hefesto.profiles.schema import TriggerConfig

SCHEMA_VERSION = 1


class TriggerPreset(BaseModel):
    """Preset standalone exportável de um único gatilho (L2 ou R2).

    Diferença vs. ``trigger_presets.py`` (sem 'io' no nome):
        - ``trigger_presets.py``: dicionários hardcoded de 10 intensidades por
          posição, internos ao app, não vão para arquivo do usuário.
        - Este módulo: wrapper JSON exportável/importável pelo usuário via GUI,
          carrega metadados (versão, timestamp, nome legível) + um TriggerConfig.

    Estrutura JSON canônica:
        {
          "schema_version": 1,
          "name": "Arco bow precisão",
          "exported_at": "2026-04-24T12:34:56+00:00",
          "trigger": {"mode": "MultiPositionFeedback", "params": [...]}
        }
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=SCHEMA_VERSION)
    name: str = Field(min_length=1, max_length=120)
    exported_at: str  # ISO8601 com offset, sem precisão sub-segundo
    trigger: TriggerConfig

    @field_validator("schema_version")
    @classmethod
    def _check_version(cls, value: int) -> int:
        if value != SCHEMA_VERSION:
            raise ValueError(
                f"schema_version não suportado: {value} (esperado {SCHEMA_VERSION})"
            )
        return value

    @field_validator("exported_at")
    @classmethod
    def _check_timestamp(cls, value: str) -> str:
        # Aceita ISO8601 com ou sem fração; rejeita string vazia.
        if not value:
            raise ValueError("exported_at vazio")
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"exported_at não é ISO8601: {value}") from exc
        return value


__all__ = ["SCHEMA_VERSION", "TriggerPreset"]
```

**Justificativa do wrapper (não exportar `TriggerConfig` puro):**

1. Versionamento explícito permite migração futura sem quebrar arquivos antigos.
2. Nome legível ajuda o usuário a identificar o arquivo (filename pode ter sido renomeado).
3. Timestamp dá pistas de origem e ordem cronológica em coleções de presets.
4. Espaço para crescer (campos opcionais no futuro: `author`, `description`, `tags`) sem quebrar contrato.

### Decisão 2 — Módulo IO `trigger_preset_io.py`

Criar **novo arquivo** `src/hefesto/profiles/trigger_preset_io.py`:

```python
from __future__ import annotations
import json
from datetime import UTC, datetime
from pathlib import Path

from hefesto.profiles.schema import TriggerConfig
from hefesto.profiles.trigger_preset_schema import SCHEMA_VERSION, TriggerPreset


def export_trigger_preset(
    path: Path,
    *,
    name: str,
    trigger: TriggerConfig,
) -> Path:
    """Serializa ``trigger`` como TriggerPreset JSON em ``path``.

    Atomic write via tempfile + rename, espelhando padrão de save_profile.
    Retorna o Path final (idêntico ao argumento, validado).
    """
    preset = TriggerPreset(
        schema_version=SCHEMA_VERSION,
        name=name,
        exported_at=datetime.now(UTC).isoformat(timespec="seconds"),
        trigger=trigger,
    )
    payload = preset.model_dump(mode="json")
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)

    path = Path(path)
    if path.suffix != ".json":
        path = path.with_suffix(".json")

    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(text + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def import_trigger_preset(path: Path) -> TriggerPreset:
    """Lê e valida JSON em ``path`` retornando TriggerPreset.

    Levanta:
        FileNotFoundError: arquivo inexistente.
        json.JSONDecodeError: JSON malformado.
        pydantic.ValidationError: schema/validação rejeitou.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return TriggerPreset.model_validate(raw)
```

Padrão de erro: **não engolir exceção dentro do módulo IO**. Quem chama (handler GTK) decide formato da mensagem ao usuário.

### Decisão 3 — Layout dos botões no glade

**Decisão escolhida: 1 botão de cada lado, dentro de cada coluna L2/R2.**

Razão:
- Mantém simetria visual (cada coluna é autônoma).
- Usuário sabe exatamente qual lado está sendo exportado (não precisa de combo extra "qual lado?").
- Implementação simples: handlers separados `on_trigger_left_preset_export`, `on_trigger_left_preset_import`, idem `right`.

Em cada coluna, **abaixo** da linha existente apply/reset (após `</packing></child>` da linha 498/606 no glade), adicionar nova `GtkBox` horizontal com 2 botões:

```xml
<child>
  <object class="GtkBox">
    <property name="orientation">horizontal</property>
    <property name="spacing">8</property>
    <property name="homogeneous">True</property>
    <property name="margin-top">4</property>
    <child>
      <object class="GtkButton" id="trigger_left_preset_export">
        <property name="label">Exportar preset...</property>
        <property name="tooltip-text">Salva o estado atual do editor L2 em arquivo JSON</property>
        <signal name="clicked" handler="on_trigger_left_preset_export"/>
      </object>
    </child>
    <child>
      <object class="GtkButton" id="trigger_left_preset_import">
        <property name="label">Importar preset...</property>
        <property name="tooltip-text">Carrega arquivo JSON e popula o editor L2 (não aplica)</property>
        <signal name="clicked" handler="on_trigger_left_preset_import"/>
      </object>
    </child>
  </object>
  <packing><property name="expand">False</property></packing>
</child>
```

Mesmo bloco espelhado para `right` (IDs `trigger_right_preset_export`, `trigger_right_preset_import`, handlers idem).

**Acentuação obrigatória**: labels e tooltips com `á/é/í/ó/ú/â/ê/ô/ã/õ/ç` corretos onde aplicável (ex. "Não aplica" deve ser "Não" — confirmar codificação UTF-8 ao salvar o glade).

### Decisão 4 — Handlers no `TriggersActionsMixin`

Adicionar em `src/hefesto/app/actions/triggers_actions.py`:

```python
def on_trigger_left_preset_export(self, _btn: Gtk.Button) -> None:
    self._handle_preset_export("left")

def on_trigger_right_preset_export(self, _btn: Gtk.Button) -> None:
    self._handle_preset_export("right")

def on_trigger_left_preset_import(self, _btn: Gtk.Button) -> None:
    self._handle_preset_import("left")

def on_trigger_right_preset_import(self, _btn: Gtk.Button) -> None:
    self._handle_preset_import("right")

def _handle_preset_export(self, side: str) -> None:
    """Coleta estado atual do editor (modo + params dos sliders), pede nome
    e caminho ao usuário, grava arquivo JSON. Não toca daemon nem perfil."""
    # 1. Coletar TriggerConfig do editor:
    #    - mode = combo trigger_<side>_mode.get_active_id()
    #    - params = self._collect_values(side) reformatado para list[int] ou
    #      list[list[int]] dependendo do modo (reusar lógica de _send_trigger_named).
    # 2. Pedir nome legível via gui_dialogs.prompt_profile_name(parent, default_name=f"trigger_{side}").
    # 3. Pedir caminho via Gtk.FileChooserDialog SAVE com filtro *.json.
    # 4. Chamar export_trigger_preset(path, name=nome, trigger=cfg).
    # 5. Toast de sucesso ou erro via self._toast_trigger(side, "export", ok).

def _handle_preset_import(self, side: str) -> None:
    """Pede arquivo, valida, popula widgets sem commitar IPC."""
    # 1. Gtk.FileChooserDialog OPEN com filtro *.json.
    # 2. import_trigger_preset(path) → TriggerPreset.
    # 3. Em erro de json/pydantic: self._toast_trigger(side, f"importar falhou: {exc}", False).
    #    Não alterar widgets nem draft.
    # 4. Em sucesso: setar combo trigger_<side>_mode.set_active_id(preset.trigger.mode);
    #    chamar self._rebuild_params(side, mode); restaurar valores nos sliders.
    #    Atualizar self.draft.triggers.<side> = TriggerDraft(mode, params=tuple(...)).
    # 5. NÃO chamar trigger_set (IPC) — usuário ainda precisa "Aplicar em L2/R2".
    # 6. Toast: "Preset importado em <SIDE>. Pressione 'Aplicar em <SIDE>' para enviar."
```

**Detalhe crítico** sobre `params` aninhados: modos `MultiPositionFeedback`/`MultiPositionVibration` têm `params: list[list[int]]`. Em `triggers_actions.py:269-271` o `_collect_values` retorna `dict[str, int]` (sliders flat). A **reconversão para shape canônico** é feita por `preset_to_factory_args` em `trigger_specs.py` — reusar essa função no export, e na importação, fazer o caminho inverso (preset.trigger.params → repopular sliders). Spec exige executor inspecionar `trigger_specs.py:preset_to_factory_args` e documentar a inversão no commit.

### Decisão 5 — Registro em `_signal_handlers`

Adicionar em `src/hefesto/app/app.py:148-220`, na seção "Triggers":

```python
"on_trigger_left_preset_export": self.on_trigger_left_preset_export,
"on_trigger_right_preset_export": self.on_trigger_right_preset_export,
"on_trigger_left_preset_import": self.on_trigger_left_preset_import,
"on_trigger_right_preset_import": self.on_trigger_right_preset_import,
```

**Armadilha herdada de `BUG-FIRMWARE-SIGNAL-HANDLERS-01`**: handler no glade sem entrada nesse dict = botão morto silencioso. Validação visual obrigatória clica nos botões para flagrar essa regressão.

### Restrições

- **NÃO tocar** `assets/profiles_default/*.json` — feature é GUI + IO standalone.
- **NÃO tocar** `src/hefesto/daemon/**` — sem alterações em IPC, schema do daemon, lifecycle.
- **NÃO criar** dependência nova em `pyproject.toml` — toda a feature usa stdlib + pydantic já presente.
- **NÃO importar** de `hefesto.daemon.*` em `trigger_preset_schema.py` ou `trigger_preset_io.py` (regra de camadas).
- **NÃO chamar** `trigger_set` (IPC) durante import — usuário aplica explicitamente. Invariante: import é não-destrutivo até "Aplicar em L2/R2" ser pressionado.
- **NÃO sobrescrever** outros campos do draft (LEDs, rumble, mouse, key_bindings) — só `triggers.<side>`.

## Arquivos tocados

**Criar:**
- `src/hefesto/profiles/trigger_preset_schema.py` (~50 linhas).
- `src/hefesto/profiles/trigger_preset_io.py` (~60 linhas).
- `tests/unit/test_trigger_preset_io.py` (~120 linhas, 5+ testes).
- `tests/unit/test_triggers_actions_preset_io.py` (~100 linhas, 4+ testes com mocks GTK).

**Modificar:**
- `src/hefesto/gui/main.glade` — 2 blocos `<child>` com par de botões (1 por coluna). +~30 linhas.
- `src/hefesto/app/actions/triggers_actions.py` — 4 handlers + 2 helpers privados (`_handle_preset_export`, `_handle_preset_import`). +~80 linhas.
- `src/hefesto/app/app.py:148-220` — 4 entradas no dict `_signal_handlers()`.

**Não tocar (invariante):**
- `assets/profiles_default/**`.
- `src/hefesto/daemon/**`.
- `src/hefesto/profiles/manager.py`, `loader.py`, `schema.py`, `trigger_presets.py`, `autoswitch.py`.
- `src/hefesto/core/**`.

## Critérios de aceite

1. `src/hefesto/gui/main.glade` ganha 4 GtkButton novos com IDs `trigger_left_preset_export`, `trigger_left_preset_import`, `trigger_right_preset_export`, `trigger_right_preset_import`. Labels PT-BR exatos: `"Exportar preset..."` e `"Importar preset..."` (com reticências triplas, tooltip explicando comportamento).
2. Handlers `on_trigger_<side>_preset_export` e `on_trigger_<side>_preset_import` **registrados em `_signal_handlers()` de `app.py`**. Validador roda smoke visual e clica nos 4 botões — nenhum gera "no handler defined" no journal/stderr.
3. `TriggerPreset.model_validate` aceita JSON válido (`schema_version=1`, `name` não-vazio, `exported_at` ISO8601 válido, `trigger` é `TriggerConfig` válido).
4. **Round-trip puro (sem GTK):** `cfg = TriggerConfig(mode="Rigid", params=[0, 255])` → `export_trigger_preset(p, name="x", trigger=cfg)` → `import_trigger_preset(p).trigger == cfg`. Idem para shape aninhado `mode="MultiPositionFeedback", params=[[0,1,2,...], ...]`.
5. **JSON malformado** (string `"{invalido"`) ao chamar `import_trigger_preset` levanta `json.JSONDecodeError`. Handler GUI captura e mostra toast `"Arquivo inválido: ..."` PT-BR. Nem widgets nem `self.draft` mudam.
6. **Schema rejeitado** (ex.: `schema_version=999`) ao chamar `import_trigger_preset` levanta `pydantic.ValidationError`. Handler GUI captura e mostra toast.
7. **Import bem-sucedido NÃO chama `trigger_set` (IPC).** Teste com mock de `trigger_set` confirma 0 invocações durante import. `self.draft.triggers.<side>` reflete o preset; `self.draft.triggers.<outro_lado>` permanece intacto.
8. **Export atomic write**: `export_trigger_preset` grava em `path.with_suffix(".json.tmp")` e faz `replace(path)`. Teste injeta exceção entre `write_text` e `replace`; arquivo final não é criado/sobrescrito.
9. Pytest sobe de **1340 → 1349** ou mais (≥9 novos testes). Suite completa passa: `1349 passed / 8 skipped` (skipped count herdado).
10. `ruff check src/ tests/` e `mypy src/hefesto` passam (mypy file count +1 ou +2 conforme arquivos novos com type hints completos).
11. **Acentuação periférica**: varredura `rg "funcao|validacao|configuracao|comunicacao|descricao|operacao|gravacao|exportacao|importacao|persiste"` nos arquivos tocados retorna zero. Especialmente `"importação"` e `"exportação"` com til.
12. **Validação visual obrigatória** (toca `main.glade`): validador-sprint auto-invoca skill `validacao-visual` e gera 2 PNGs (antes do fix sem botões + depois com botões na aba Gatilhos). Comando canônico do BRIEF (com `WID="Hefesto v"`) registrado no PR junto com sha256 dos PNGs.
13. **Sem emojis gráficos** nos labels/tooltips/toasts (Emoji_Presentation block proibido). Glifos Unicode de estado (●/○/▼) permitidos se já existirem na aba.

## Aritmética e baseline

- `triggers_actions.py` atual: 341 linhas. Crescimento estimado: +80L → ~421L. Sem violar nenhum teto (não há sprint de redução de tamanho ativa para esse arquivo).
- `main.glade` atual: 2300 linhas. +~30L → ~2330L. Sem teto.
- `app.py` atual: ~250L (seção `_signal_handlers`). +4L. Sem teto.
- Pytest baseline: **FAIL_BEFORE = 0** (1340 passed). Esperado **FAIL_AFTER = 0** (1349+ passed). Skipped permanece em 8.
- Mypy files: 113 atual → 114 ou 115 (+1 schema, +1 io). Erros: 0 → 0.

## Plano de implementação

1. **Criar schema** `src/hefesto/profiles/trigger_preset_schema.py` com `TriggerPreset` + constante `SCHEMA_VERSION`.
2. **Criar IO** `src/hefesto/profiles/trigger_preset_io.py` com `export_trigger_preset` + `import_trigger_preset`.
3. **Testes unit do IO** em `tests/unit/test_trigger_preset_io.py`:
   - `test_round_trip_simples` (mode=Rigid, params=[0,255]).
   - `test_round_trip_aninhado` (mode=MultiPositionFeedback, params=[[…],…]).
   - `test_export_normaliza_extensao` (path sem `.json` ganha sufixo).
   - `test_export_atomic_write` (tmpfile + replace).
   - `test_import_json_malformado_levanta_decodeerror`.
   - `test_import_schema_version_invalido_levanta_validation`.
   - `test_import_name_vazio_levanta_validation`.
   - `test_import_exported_at_invalido_levanta_validation`.
   - `test_import_trigger_extra_field_levanta_validation` (`extra="forbid"`).
4. **Glade**: adicionar 2 blocos de `GtkBox` (1 por coluna L2/R2), cada um com 2 botões. Confirmar UTF-8 BOM-less.
5. **Mixin**: adicionar 4 handlers públicos + 2 privados em `triggers_actions.py`. Reusar `_collect_values`, `preset_to_factory_args`, `_rebuild_params`. Para reconverter `dict[str,int]` em `list[int]` ou `list[list[int]]` no export, espelhar a lógica de `_send_trigger_named` (linhas 304-322).
6. **`app.py`**: adicionar 4 entradas no dict `_signal_handlers()`.
7. **Testes do mixin** em `tests/unit/test_triggers_actions_preset_io.py`:
   - `test_handle_preset_import_atualiza_draft_sem_chamar_ipc` (mock `trigger_set`).
   - `test_handle_preset_import_arquivo_invalido_nao_altera_draft`.
   - `test_handle_preset_import_outro_lado_intocado` (importa em `left` → `right` permanece).
   - `test_handle_preset_export_grava_arquivo_com_estado_dos_sliders` (mock chooser, mock filesystem).
8. **Lint + types**: `ruff check src/ tests/` e `mypy src/hefesto`.
9. **Smoke USB + BT** (2s cada) — proof-of-work runtime.
10. **Validação visual**: `.venv/bin/python -m hefesto.app.main`, navegar à aba Gatilhos, capturar PNG antes (sem botões — só se executor preservar baseline pré-mudança) e depois (com botões), sha256.
11. **Acentuação periférica**: `rg` nos arquivos tocados.

## Testes obrigatórios

### Unit IO (sem GTK)

```python
# tests/unit/test_trigger_preset_io.py
def test_round_trip_simples(tmp_path):
    cfg = TriggerConfig(mode="Rigid", params=[0, 255])
    p = export_trigger_preset(tmp_path / "rigid.json", name="Rigid teste", trigger=cfg)
    preset = import_trigger_preset(p)
    assert preset.trigger == cfg
    assert preset.name == "Rigid teste"
    assert preset.schema_version == 1
```

Repetir para shape aninhado, JSON malformado, schema_version errado, name vazio, exported_at inválido, extra field.

### Unit mixin (com mocks GTK)

Reusar fixtures de `tests/unit/test_triggers_actions.py`. Mockar `Gtk.FileChooserDialog.run/get_filename/destroy`, `gui_dialogs.prompt_profile_name`, e `trigger_set`. Asserts:
- `trigger_set.assert_not_called()` em import.
- `mixin.draft.triggers.left.mode == "Rigid"` após import válido em `left`.
- `mixin.draft.triggers.right == previous_right` (intocado).

## Proof-of-work esperado

Runtime real (comandos canônicos do BRIEF):

```bash
# Setup (idempotente)
bash scripts/dev-setup.sh

# Smoke USB
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke

# Smoke BT
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt

# Suite
.venv/bin/pytest tests/unit -v --no-header -q

# Lint + types
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto

# Anonimato
./scripts/check_anonymity.sh
```

Validação visual (skill `validacao-visual`, A-12 — usa `.venv/bin/python` com PyGObject; se ausente, fallback do BRIEF):

```bash
.venv/bin/python -m hefesto.app.main &
sleep 3
WID=$(xdotool search --name "Hefesto v" | head -1)
TS=$(date +%Y%m%dT%H%M%S)
xdotool windowactivate "$WID" && sleep 0.4
# Navegar à aba Gatilhos manualmente ou via xdotool key
import -window "$WID" "/tmp/hefesto_gui_triggers_preset_io_${TS}.png"
sha256sum "/tmp/hefesto_gui_triggers_preset_io_${TS}.png"
```

PR deve incluir:
- Diff completo (Edit-only, zero Write em arquivos pré-existentes).
- Output de pytest com contagem 1349+/8.
- Output de ruff + mypy zerados.
- 2 PNGs (antes/depois) + sha256.
- Descrição multimodal da validação visual: "Aba Gatilhos exibe duas colunas L2/R2 com 4 sliders de modo + linha de botões 'Aplicar / Desligar' + nova linha 'Exportar preset... / Importar preset...'. Acentuação correta. Contraste preservado."
- Hipótese verificada: `rg "TriggerPreset"` confirma instâncias só nos novos módulos + testes.

## Riscos e não-objetivos

**Riscos conhecidos:**
- `gi`/`Gtk` ausente no `.venv` (A-12 PARCIAL). Mitigação: validador roda smoke + testes; visual cai no fallback do BRIEF se PyGObject ausente.
- Modos com `params` aninhado podem ter conversão errada (sliders flat vs `list[list[int]]`). Mitigação: testes de round-trip explícitos para `MultiPositionFeedback` e `MultiPositionVibration`, espelhando `_send_trigger_named`.
- Usuário pode tentar importar arquivo `Profile.json` (perfil completo) confundindo com preset standalone. Mitigação: schema com `extra="forbid"` rejeita imediatamente; toast PT-BR cita `"name"`/`"trigger"` ausentes.

**Não-objetivos** (registrar como sprint nova se aparecerem):
- Compartilhar **pacote** com múltiplos presets (ex.: zip de 4 gatilhos). Próxima sprint se houver demanda.
- Importar **direto no perfil ativo** sem passar pelo editor. Quebra invariante "import é não-destrutivo".
- Auto-aplicar via IPC após import. Usuário deve apertar "Aplicar em L2/R2".
- I18N dos toasts/labels — virá em `FEAT-I18N-01` (item 7 da Wave V2.5).
- Browser/galeria de presets compartilhados (cloud) — fora do escopo do MVP.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-DualSense_Unix/VALIDATOR_BRIEF.md` (seções `[CORE] Contratos de runtime`, `[CORE] Capacidades visuais`, A-06, A-12).
- SPRINT_ORDER: `docs/process/SPRINT_ORDER.md:445` (item 8 Wave V2.5).
- Precedente histórico de FileChooser + validação pydantic: `BUG-FIRMWARE-SIGNAL-HANDLERS-01` (PR 77.1, 2026-04 MERGED) + `src/hefesto/app/actions/footer_actions.py:170-256`.
- Precedente histórico de schema standalone com wrapper de metadados: pydantic `Profile` em `src/hefesto/profiles/schema.py:187-220`.
- Lições aplicadas: L-21-3 (leitura código antes de spec), L-21-4 (proof-of-work runtime real), L-21-7 (aritmética explícita).
