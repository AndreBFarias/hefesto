# FEAT-MOUSE-01 — Aba Mouse: emular mouse+teclado via DualSense com uinput

**Tipo:** feat (maior).
**Wave:** fora de wave.
**Estimativa:** 1-2 iterações (mapeamento + aba GUI + polling).
**Dependências:** `python-uinput` já está em extras `[emulation]`; `uinput_gamepad.py` já existe.

---

## Contexto

Hefesto hoje emula Xbox360 via uinput (W6.3, PR #56). O pedido novo é emular **mouse+teclado** a partir do DualSense, via uma nova aba "Mouse" na GUI. Útil para navegar desktop, apresentações, emuladores retro, jogos que só aceitam mouse/teclado, etc.

Mapeamento canônico (decidido pelo usuário):

| DualSense | Saída emulada                          | evdev code           |
|---|---|---|
| **Cross** (X) ou **L2** | Botão esquerdo do mouse | `BTN_LEFT`           |
| **Triangle** (△) ou **R2** | Botão direito do mouse | `BTN_RIGHT`          |
| **D-pad up / down / left / right** | Setas de teclado | `KEY_UP`/`KEY_DOWN`/`KEY_LEFT`/`KEY_RIGHT` |
| **Analógico esquerdo** | Movimento do mouse (X, Y) | `REL_X` / `REL_Y`    |
| **Analógico direito** | Rolagem | `REL_WHEEL` (vertical), `REL_HWHEEL` (horizontal) |
| **R3** (clique no analógico direito) | Botão do meio (rodinha) | `BTN_MIDDLE`         |

## Arquitetura

### Novo módulo: `src/hefesto/integrations/uinput_mouse.py`

Classe `UinputMouseDevice` parecida com `uinput_gamepad.py` (já existente). Cria device virtual com `uinput.Device([...])` expondo BTN_LEFT, BTN_RIGHT, BTN_MIDDLE, REL_X, REL_Y, REL_WHEEL, REL_HWHEEL, KEY_UP/DOWN/LEFT/RIGHT.

Método `dispatch(state: ControllerState)` traduz o estado do controle em eventos. Políticas:

- **Analógico esquerdo → movimento**: aplicar **deadzone** (threshold ±20/128), escala configurável (default `mouse_speed=6`), emitir `REL_X` e `REL_Y` a cada tick enquanto stick não está em repouso. Fórmula: `dx = int((lx - 128) / 128 * speed)` (mesmo para dy).
- **Analógico direito → scroll**: deadzone maior (±40/128), escala separada (`scroll_speed=1`). Rate-limit: no máximo 1 evento de wheel a cada 50ms para evitar scroll violento.
- **Botões**: edge-triggered (press/release só no delta). Estado anterior guardado na instância.
- **D-pad**: edge-triggered (KEY_DOWN/KEY_UP via `uinput.emit_click`). D-pad e arrow keys têm mesma semântica e não se sobrepõem a outras ações do sistema.

### Nova aba GUI: Mouse

`main.glade`: novo `GtkNotebookPage` entre Rumble e Perfis (ou onde o executor escolher), id `tab_mouse`. Widgets:

- `GtkSwitch id="mouse_emulation_toggle"` — liga/desliga modo mouse (default OFF).
- `GtkScale id="mouse_speed_scale"` — speed do movimento (1-12, default 6).
- `GtkScale id="mouse_scroll_speed_scale"` — speed da rolagem (1-5, default 1).
- `GtkLabel` resumindo o mapeamento fixo (X/L2=esq, △/R2=dir, etc.) para o usuário entender sem abrir docs.
- Se `/dev/uinput` não está writable, mostrar aviso vermelho com link "rode ./scripts/install_udev.sh".

### Hook no daemon

Daemon hoje tem subsistemas em `lifecycle.py`. Adicionar:
- `DaemonConfig.mouse_emulation_enabled: bool = False` (default off).
- `_start_mouse_emulation()` análogo a `_start_udp()` etc.
- Subscribe do event bus em `EventTopic.STATE_UPDATE` → chama `UinputMouseDevice.dispatch(state)`.

Toggle do switch da GUI envia via IPC:
- Novo método JSON-RPC `mouse.emulation.set` `{ enabled: bool, speed: int, scroll_speed: int }`.
- Daemon responde e persiste em `daemon.toml` se for o caso.

## Critérios de aceite

- [ ] `src/hefesto/integrations/uinput_mouse.py` — novo, com `UinputMouseDevice` classe e `dispatch(state)`. Testes em `tests/unit/test_uinput_mouse.py` cobrem: (a) deadzone, (b) escala de velocidade, (c) edge-trigger de botões, (d) rate-limit do scroll, (e) D-pad → KEY_*.
- [ ] `src/hefesto/daemon/lifecycle.py` — `_start_mouse_emulation()` opt-in via `DaemonConfig.mouse_emulation_enabled`. Liga/desliga idempotente.
- [ ] `src/hefesto/daemon/ipc_server.py` — novo handler `mouse.emulation.set`. Atualizar docstring + lista de métodos.
- [ ] `src/hefesto/app/actions/mouse_actions.py` — novo mixin `MouseActionsMixin` com toggle, speeds, refresh de status, detecção de /dev/uinput writable.
- [ ] `src/hefesto/gui/main.glade` — aba nova `tab_mouse`, widgets descritos acima.
- [ ] `src/hefesto/app/app.py` — registrar `MouseActionsMixin`, signal handlers (`on_mouse_toggle_set`, `on_mouse_speed_changed`, `on_mouse_scroll_speed_changed`).
- [ ] Testes unitários: cobrir mapeamento (tabela do spec acima), rate-limit, deadzone.
- [ ] Proof-of-work visual: captura da aba Mouse com toggle OFF e ON, sliders visíveis, mapeamento legível. Descrição multimodal.
- [ ] Proof-of-work runtime: `HEFESTO_FAKE=1 ./run.sh --smoke` segue verde (mouse OFF default); teste manual adicional (instruções no PR) com toggle ON validando movimento via `evtest /dev/input/eventN` do device virtual.
- [ ] `./scripts/check_anonymity.sh`, ruff, 306+ tests.

## Arquivos tocados (previsão)

- `src/hefesto/integrations/uinput_mouse.py` (novo)
- `src/hefesto/daemon/lifecycle.py`
- `src/hefesto/daemon/ipc_server.py`
- `src/hefesto/app/actions/mouse_actions.py` (novo)
- `src/hefesto/app/actions/__init__.py` (expor o novo mixin)
- `src/hefesto/app/app.py`
- `src/hefesto/gui/main.glade`
- `src/hefesto/daemon/config.py` (se existir, adicionar flag)
- `tests/unit/test_uinput_mouse.py` (novo)

## Fora de escopo

- Macros customizadas / chord bindings.
- Mapeamento configurável pelo usuário (v1: fixo; feature futura).
- Suporte a touchpad do DualSense como mouse (separado).
- Integração com jogos específicos.

## Notas para o executor

- `python-uinput` requer `/dev/uinput` writable pelo usuário — já coberto por `assets/71-uinput.rules`.
- `UinputMouseDevice` deve ser opt-in via config para não criar device virtual acidentalmente.
- Deadzone padrão 20/128 (~16%) para stick analógico. Stick drift do DualSense é comum; valor menor causa jitter.
- Escala do scroll tem que ser pequena (`1`) — `REL_WHEEL` já é discreto, não precisa multiplicação.
- Rate-limit do scroll: use `time.monotonic()`, não `time.time()`, para imunidade a NTP jumps.
