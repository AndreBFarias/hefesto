# FEAT-KEYBOARD-EMULATOR-01 — Infraestrutura de emulação de teclado virtual

**Tipo:** feat (médio — aditivo infraestrutura).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Modelo sugerido:** opus.
**Dependências:** FEAT-MOUSE-01, FEAT-MOUSE-02 (merged).
**Sprint-mãe:** FEAT-MOUSE-TECLADO-COMPLETO-01 (dividida em 3 filhas).
**Status:** MERGED — 2026-04-23 (executado em `git commit` desta sessão).

---

**Tracking:** label `type:feat`, `hardware`, `kbd-emu`, `ai-task`.

## Contexto

A sprint-mãe `FEAT-MOUSE-TECLADO-COMPLETO-01` agrega 6 entregas: rename de
aba, device de teclado virtual, mapeamentos default, persistência por perfil,
UI editável e integração com onboard/wvkbd-mobintl. Análise de escopo no
executor-sprint identificou ~1200 linhas de diff estimadas e 3 domínios
independentes (infra / persistência / UI). Sprint quebrada em 3 filhas para
manter lotes <500 linhas e gates verdes por entrega.

Esta é a **filha 1**: entrega a infraestrutura — device, mapper de defaults
conservadores, subsystem, wire-up no Daemon. Sem UI, sem persistência no
perfil, sem onboard. Apenas "pressionar Options emite KEY_LEFTMETA via
uinput virtual" funcionando end-to-end pelo poll loop.

## Decisão

1. **`src/hefesto/core/keyboard_mappings.py`** (novo, 70L):
   - `DEFAULT_BUTTON_BINDINGS: dict[str, tuple[str, ...]]` hardcoded cobrindo
     `options`, `create` (Share), `l1`, `r1`. L3/R3 ficam para filha 3
     (dependem de onboard + UI permitir desligar conflito com R3=BTN_MIDDLE
     do mouse). Touchpad-press fica de fora (evdev_reader ainda não expõe
     keycode consistente).
   - `parse_binding(str) -> tuple[str, ...]` e `format_binding(tuple)`.

2. **`src/hefesto/integrations/uinput_keyboard.py`** (novo, 210L):
   - `UinputKeyboardDevice` análogo a `UinputMouseDevice`.
   - Device separado (`Hefesto Virtual Keyboard`) — evita colisão com o
     device do mouse que também expõe algumas teclas (`KEY_ENTER`/`KEY_ESC`).
   - Capabilities = superset (letras, modificadores, função, números, etc.)
     para que overrides futuros da filha 2/3 não exijam recriar o device.
   - `dispatch(buttons_pressed)` edge-triggered: press da sequência completa
     (modificadores+tecla) ao detectar False→True; release em ordem reversa
     ao detectar True→False.
   - `set_bindings(mapping)` para destravar a filha 2 sem tocar nesta classe.
   - `_release_all()` antes de `destroy()` evita ghost-keys.

3. **`src/hefesto/daemon/subsystems/keyboard.py`** (novo, 130L):
   - `start_keyboard_emulation`, `stop_keyboard_emulation`, `dispatch_keyboard`
     análogos ao módulo `mouse.py`.
   - `KeyboardSubsystem` com interface `Subsystem`.

4. **Wire-up no `Daemon` (armadilha A-07 — 4 pontos)**:
   - Slot `_keyboard_device: Any = None` no dataclass.
   - Método `_start_keyboard_emulation()` chamado em `run()` antes do
     `await self._stop_event.wait()`.
   - Método `_dispatch_keyboard_emulation(buttons_pressed)` chamado no
     `_poll_loop` reusando `buttons_pressed` de `_evdev_buttons_once()`
     (A-09 — snapshot único por tick preservado).
   - `shutdown` em `connection.py` chama `.stop()` no device antes de zerar
     o slot — evita ghost-keys após Ctrl+C.
   - `reload_config` reage a toggle `keyboard_emulation_enabled` (previne
     A-08 latente).

5. **Config**: `DaemonConfig.keyboard_emulation_enabled: bool = True`.
   Default True porque os bindings conservadores (Options/Share/Alt+Tab)
   são inofensivos e não colidem com o mouse. UI+perfil podem desligar.

## Critérios de aceite

- [x] `UinputKeyboardDevice.start()` cria device virtual ou retorna False sem
      exceção se uinput ausente.
- [x] `dispatch(frozenset({"options"}))` emite KEY_LEFTMETA press+release
      edge-triggered (hold não repete).
- [x] `dispatch(frozenset({"r1"}))` emite combo KEY_LEFTALT+KEY_TAB (press)
      seguido de release em ordem reversa ao soltar.
- [x] Botões usados pelo mouse (`cross`, `triangle`, `r3`, `dpad_*`,
      `circle`, `square`) NÃO produzem emit no teclado (test dedicado).
- [x] Wire-up A-07 coberto por `tests/unit/test_keyboard_wire_up.py`:
      slot existe, start chamado em run, dispatch chamado no poll_loop,
      stop chamado no shutdown.
- [x] `reload_config` liga/desliga device conforme toggle.
- [x] Smoke USB+BT mostram `keyboard_emulator_opened` e `keyboard_emulation_started`.
- [x] Suite unit: 1036 passed (+33 testes novos), 5 skipped — zero regressão.
- [x] Ruff clean, mypy zero erros, anonimato preservado, acentuação válida.

## Arquivos tocados

- `src/hefesto/core/keyboard_mappings.py` (+75L, novo).
- `src/hefesto/integrations/uinput_keyboard.py` (+210L, novo).
- `src/hefesto/daemon/subsystems/keyboard.py` (+130L, novo).
- `src/hefesto/daemon/lifecycle.py` (+40L): slot, 3 wrappers, config, reload.
- `src/hefesto/daemon/connection.py` (+5L): shutdown cleanup.
- `tests/unit/test_keyboard_mappings.py` (+85L, novo).
- `tests/unit/test_keyboard_emulator.py` (+225L, novo).
- `tests/unit/test_keyboard_wire_up.py` (+290L, novo).

Total: ~1060 linhas aditivas.

## Proof-of-work runtime

```bash
.venv/bin/pytest tests/unit -q --no-header
# 1036 passed, 5 skipped

.venv/bin/ruff check src/ tests/
# All checks passed!

.venv/bin/mypy src/hefesto
# Success: no issues found in 105 source files

./scripts/check_anonymity.sh
# OK: anonimato preservado.

HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
# poll.tick=54, battery.change.emitted=1, keyboard_emulator_opened, keyboard_emulation_started

HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt
# poll.tick=57, battery.change.emitted=1
```

## Notas

- Device virtual de teclado é **separado** do de mouse: é um novo `/dev/input/eventN`
  com nome "Hefesto Virtual Keyboard". Convenção 1 subsystem → 1 /dev/uinput próprio.
- `_release_all()` no `stop()` libera qualquer tecla ainda pressionada antes de
  destruir o device — evita tecla "colada" no sistema do usuário em caso de
  desligamento abrupto.
- `set_bindings(mapping)` já inclui guard de liberação: trocar mapping com botão
  pressionado libera as teclas do mapping antigo primeiro.
- L3/R3 ficaram de fora desta sprint: conflito com R3=BTN_MIDDLE do mouse exige
  que a UI (filha 3) permita ao usuário desativar o mouse antes de atribuir
  L3/R3 ao teclado. Decisão conservadora.

# "A forja não revela o ferreiro. Só a espada."
