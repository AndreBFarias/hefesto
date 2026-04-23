# FEAT-KEYBOARD-UI-01 — UI de edição de bindings + L3/R3 teclado virtual

**Tipo:** feat (grande — UI).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 2 iterações.
**Modelo sugerido:** opus.
**Dependências:** FEAT-KEYBOARD-EMULATOR-01 (merged), FEAT-KEYBOARD-PERSISTENCE-01.
**Sprint-mãe:** FEAT-MOUSE-TECLADO-COMPLETO-01 (dividida em 3 filhas).

---

**Tracking:** label `type:feat`, `ui`, `kbd-emu`, `ai-task`, `status:ready`.

## Contexto

Completa o trio da sprint-mãe: UI editável de key bindings na GUI, mais
handlers especiais para L3/R3 abrindo/fechando teclado virtual do sistema
(onboard/wvkbd-mobintl).

## Decisão

### 1. Rename da aba

- `src/hefesto/gui/main.glade`: tab "Mouse" → "Mouse e Teclado".
- `src/hefesto/app/actions/mouse_actions.py` **renomeado** para `input_actions.py`
  (classe `InputActionsMixin`) com aliases backcompat em `__init__.py`.
- Atualizar registro em `src/hefesto/app/app.py`.

### 2. TreeView de bindings

- Widget novo `key_bindings_treeview` em `main.glade` dentro da aba.
- Model `Gtk.ListStore[str, str, str]`: botão canônico, binding (formato
  `"KEY_LEFTALT+KEY_TAB"`), descrição.
- Colunas editáveis via `GtkCellRendererText` + `GtkCellRendererCombo` na
  coluna de botão (valores fixos: 17 botões canônicos).
- Botões: "Adicionar", "Remover", "Restaurar defaults".
- Handler grava no draft do perfil; "Salvar perfil" persiste via IPC
  `profile.save` (ou equivalente já existente).

### 3. L3/R3 handlers especiais

- `src/hefesto/daemon/subsystems/keyboard.py`: adicionar handler
  `_toggle_onscreen_keyboard(action: Literal["open", "close"])`.
- `shutil.which("onboard")` → `subprocess.Popen(["onboard", "--visible"])`.
- Senão `shutil.which("wvkbd-mobintl")` → `Popen(["wvkbd-mobintl"])`.
- Senão log warning **uma vez** (flag `_kbd_onscreen_available`).
- Fechar: `pkill -x onboard || pkill -x wvkbd-mobintl`.
- Bindings especiais L3/R3 viram tokens virtuais `"__OPEN_OSK__"` e
  `"__CLOSE_OSK__"` em `DEFAULT_BUTTON_BINDINGS` — `UinputKeyboardDevice`
  reconhece e delega para o handler em vez de emitir `KEY_*`.

### 4. Inversão R2/L2 + mapeamentos touchpad

- Ajustar `DEFAULT_BUTTON_BINDINGS` (ou `BUTTON_TO_UINPUT` no mouse se fizer
  sentido): o que hoje R2 faz, L2 passa a fazer, e vice-versa.
- Touchpad esquerda → KEY_BACKSPACE, meio → KEY_ENTER, direita → KEY_DELETE
  (depende do evdev_reader expor `touchpad_press` — **pré-requisito bloqueador**;
  se não estiver disponível, abrir sprint INFRA-EVDEV-TOUCHPAD-01 antes).

### 5. Validação visual

- Screenshot antes/depois da aba "Mouse e Teclado" com tabela de bindings
  populada e botões CRUD visíveis.
- sha256 + descrição multimodal (elementos, acentuação, contraste).

## Critérios de aceite

- [ ] Aba renomeada "Mouse e Teclado" no notebook.
- [ ] TreeView exibe 4+ linhas com bindings efetivos do perfil ativo.
- [ ] CRUD funciona: adicionar linha, remover, restaurar defaults.
- [ ] Alterar Triangle→KEY_C na UI + salvar + switch perfil = emite KEY_C.
- [ ] L3 abre onboard se instalado; sem onboard/wvkbd log warning **uma vez**.
- [ ] R3 fecha onboard.
- [ ] R1 emite Alt+Tab; L1 emite Alt+Shift+Tab.
- [ ] Inversão R2/L2 registrada em `docs/process/discoveries/`.
- [ ] Screenshots antes/depois em `/tmp/hefesto_gui_kbd_*.png` + sha256.
- [ ] Testes UI: `tests/unit/test_input_actions.py` cobrindo CRUD de rows.
- [ ] Smoke USB+BT verdes.

## Arquivos tocados

- `src/hefesto/gui/main.glade` — tab rename + TreeView + botões CRUD.
- `src/hefesto/app/actions/mouse_actions.py` → rename para `input_actions.py`.
- `src/hefesto/app/actions/__init__.py` — atualizar registro.
- `src/hefesto/app/app.py` — registrar mixin novo.
- `src/hefesto/daemon/subsystems/keyboard.py` — handler OSK + suporte a
  tokens virtuais.
- `src/hefesto/integrations/uinput_keyboard.py` — delegar tokens virtuais
  ao callback em vez de emitir.
- `src/hefesto/core/keyboard_mappings.py` — adicionar L3/R3 com tokens.
- `tests/unit/test_input_actions.py` (novo).
- `tests/unit/test_osk_handler.py` (novo).

## Proof-of-work runtime

```bash
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto

# Validação visual (CLI X11 pipeline):
/usr/bin/python3 -m hefesto.app.main &
sleep 3
WID=$(xdotool search --name "Hefesto v" | head -1)
TS=$(date +%Y%m%dT%H%M%S)
xdotool windowactivate "$WID" && sleep 0.4
# Clicar aba Mouse e Teclado via key_tab
import -window "$WID" "/tmp/hefesto_gui_kbd_${TS}.png"
sha256sum "/tmp/hefesto_gui_kbd_${TS}.png"
```

## Notas para o executor

- Rename de arquivo + rename de classe = cuidado com imports quebrados.
  Rodar `rg "MouseActionsMixin"` e `rg "mouse_actions"` antes de commitar.
- Tokens virtuais `__OPEN_OSK__` / `__CLOSE_OSK__` exigem que `parse_binding`
  e `format_binding` deixem passar `__*__` além de `KEY_*`. Ajustar regex.
- Onboard guard: detectar 1x no `start()` via `shutil.which`, guardar
  `_kbd_onscreen_available: bool | None` no device. `None` = ainda não
  verificou; `False` = log warning 1x e no-op perpétuo; `True` = funciona.
- GNOME nativo: `gsettings set org.gnome.desktop.a11y.applications screen-keyboard-enabled true`
  é alternativa se usuário não tem onboard/wvkbd. Opcional; não bloqueador.

## Fora de escopo

- Suporte a macros temporais (hold Square 500ms → sequência).
- Chord MOD multi-layer (fn+Circle).
- i18n dos nomes de teclas na UI.

# "O conhecimento fala, a sabedoria escuta." — Jimi Hendrix (apócrifo, mas pertinente)
