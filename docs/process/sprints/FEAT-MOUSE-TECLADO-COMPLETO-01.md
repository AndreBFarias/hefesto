# FEAT-MOUSE-TECLADO-COMPLETO-01 — Emulação completa de teclado + personalização de mapeamentos

**Tipo:** feat (grande — aditivo).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 2-3 iterações.
**Modelo sugerido:** opus.
**Dependências:** FEAT-MOUSE-02 (toggle de emulação mouse), INFRA-BUTTON-EVENTS-01 (BUTTON_DOWN/UP).

---

**Tracking:** label `type:feat`, `ui`, `hardware`, `kbd-emu`, `ai-task`, `status:ready`.

## Contexto

v2.1.0 já emula mouse via `UinputMouseDevice` quando toggle está ativo. Usuário quer expandir para emulação completa de teclado + permitir mapeamento configurável de cada botão do DualSense a qualquer tecla do teclado ou comando.

Lista de mudanças pedidas em 2026-04-23:

### Aba

- Renomear "Mouse" → "Mouse e Teclado" no notebook.

### Mapeamentos default novos (atuais em parênteses)

- **PS (solo)**: mantém "abre Steam" (FEAT-HOTKEY-STEAM-01 — já implementado).
- **Options (Start)**: tecla Super/Windows (`KEY_LEFTMETA`).
- **Share (Menos/Create)**: `KEY_SYSRQ` (PrintScreen).
- **Touchpad meio-clique**: `KEY_ENTER`.
- **Touchpad esquerda-clique**: `KEY_BACKSPACE`.
- **Touchpad direita-clique**: `KEY_DELETE`.
- **L3 (stick esquerdo click)**: abrir teclado virtual (`onboard --visible` ou `wvkbd-mobintl`).
- **R3 (stick direito click)**: fechar teclado virtual (`pkill -x onboard || pkill -x wvkbd-mobintl`).
- **R2 e L2**: **inverter** comportamento atual (hoje R2 mapeia a algo diferente de L2; trocar).
- **R1**: `Alt+Tab` (ciclo pra direita — `KEY_LEFTALT + KEY_TAB`).
- **L1**: `Alt+Shift+Tab` (ciclo pra esquerda — `KEY_LEFTALT + KEY_LEFTSHIFT + KEY_TAB`).
- Mantém mouse (analógico direito move cursor), scroll de linhas, zoom in/out.

### Personalização completa

- UI dedicada na aba "Mouse e Teclado" permite re-mapear **qualquer** botão do DualSense para **qualquer** tecla de teclado ou sequência (combo Alt+Tab, Ctrl+C, etc.).
- Tabela editável: coluna 1 = botão DualSense (dropdown fechado com nomes canônicos dos 17 botões); coluna 2 = tecla/combo destino (editor livre aceitando formato `KEY_X` ou `KEY_CTRL+KEY_C`); coluna 3 = descrição opcional.
- Botão "Adicionar mapping" cria linha nova; "Remover" apaga; "Restaurar defaults" restaura a lista default desta sprint.
- Mapeamentos persistem por perfil (campo novo `ProfileConfig.key_mappings: list[KeyMapping]` ou na raiz).

## Decisão

Implementação em 5 partes — avaliar quebra em sub-sprints se passar de 2 iterações:

1. **Rename da aba** — `main.glade` + keys de i18n se houver.
2. **KeyboardEmulator** novo em `src/hefesto/integrations/uinput_keyboard.py` análogo a `uinput_mouse.py`. Abre device virtual com `UI_SET_KEYBIT` para todas as teclas relevantes + `UI_SET_EVBIT EV_KEY`.
3. **Mapeamentos default** hardcoded em novo módulo `src/hefesto/core/keyboard_mappings.py` como `DEFAULT_BUTTON_BINDINGS: dict[str, KeySequence]`. `KeySequence` é dataclass `list[int]` com chaves `evdev.ecodes.KEY_*`.
4. **Persistência no perfil** — `ProfileConfig.key_bindings: dict[str, list[str]] | None = None`. JSON usa nomes `"KEY_LEFTALT"`; schema valida contra `evdev.ecodes`. Null = usar defaults. `_to_led_settings`-like mapper propaga para o `KeyboardEmulator` via `apply()` (armadilha A-06 — ter teste dedicado).
5. **UI de edição** em aba "Mouse e Teclado" — `GtkTreeView` com model `ListStore[str, str, str]`, colunas editáveis, botões de CRUD.
6. **L3/R3 abrem/fecham onboard** — handler específico que executa `subprocess.Popen(["onboard"])` com fallback para `wvkbd-mobintl` se onboard não instalado. Se nenhum dos dois, log warning + no-op (não falha).

## Critérios de aceite

- [ ] Aba renomeada para "Mouse e Teclado".
- [ ] Emulação de teclado funciona via FakeController: `HEFESTO_FAKE=1` + pressionar Options → `KEY_LEFTMETA` emitido no device virtual `/dev/input/event*`.
- [ ] Personalização via UI: alterar binding de Triangle para `KEY_C`, salvar perfil, recarregar perfil, confirmar que Triangle emite C.
- [ ] L3 abre onboard (se instalado) — se não instalado, warning no log mas sem crash.
- [ ] R3 fecha onboard.
- [ ] R1 emite Alt+Tab; janela foca próxima conforme WM.
- [ ] L1 emite Alt+Shift+Tab.
- [ ] R2/L2 trocam ordem: comportamento anterior de R2 agora é de L2 e vice-versa — validar em `docs/process/discoveries/` com diff dos bindings antes/depois.
- [ ] Touchpad: meio=Enter, esquerda=Backspace, direita=Delete.
- [ ] Mouse continua funcionando normalmente (analógico → REL_X/REL_Y, scroll, zoom).
- [ ] Testes: `tests/unit/test_keyboard_emulator.py`, `tests/unit/test_key_bindings_schema.py`, `tests/unit/test_profile_key_bindings.py` (armadilha A-06 — test `test_apply_propaga_key_bindings`).
- [ ] Smoke: `HEFESTO_FAKE=1 ... ./run.sh --smoke` sem traceback; log `keyboard.emulator.opened` e `key_binding.emit key=<nome>`.
- [ ] Screenshots: aba "Mouse e Teclado" com tabela de bindings visível.
- [ ] Permissões udev: `assets/72-ps5-controller-autosuspend.rules` pode precisar irmão para `/dev/uinput` (se não já existir).

## Arquivos tocados

- `src/hefesto/integrations/uinput_keyboard.py` (novo, ~150 linhas).
- `src/hefesto/core/keyboard_mappings.py` (novo — defaults).
- `src/hefesto/profiles/schema.py` (novo campo `key_bindings`).
- `src/hefesto/profiles/manager.py` (mapper propaga A-06).
- `src/hefesto/daemon/subsystems/keyboard.py` (novo subsystem se necessário, seguindo base.py; ver A-07).
- `src/hefesto/daemon/lifecycle.py` (wire-up do subsystem — A-07).
- `src/hefesto/gui/main.glade` (aba renomeada + tabela bindings).
- `src/hefesto/app/actions/mouse_actions.py` → rename para `input_actions.py` (ou novo arquivo).
- `assets/profiles_default/*.json` (8 perfis ganham `key_bindings: null` para usar defaults; 1 perfil exemplo com override).
- `tests/unit/test_keyboard_*.py`.

## Proof-of-work runtime

```bash
# Cenário 1: defaults funcionam
systemctl --user restart hefesto.service
sleep 2
hefesto profile switch fallback
# Pressionar Options (via FakeController input injection)
# Verificar no journal: "key_binding.emit key=KEY_LEFTMETA"

# Cenário 2: personalização persiste
# Via GUI, alterar Triangle → KEY_C, salvar como "meu_custom"
# systemctl restart
hefesto profile switch meu_custom
# Pressionar Triangle
# Verificar log: "key_binding.emit key=KEY_C"

.venv/bin/pytest tests/unit/test_keyboard_emulator.py tests/unit/test_key_bindings_schema.py tests/unit/test_profile_key_bindings.py -v
.venv/bin/pytest tests/unit -q
.venv/bin/ruff check src/ tests/
./scripts/check_anonymity.sh
python3 scripts/validar-acentuacao.py --all
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt
```

## Notas para o executor

- Armadilha A-06 é **certeira**: campo novo em `ProfileConfig` exige mapper propagando + teste integration. Não esquecer.
- Armadilha A-07: subsystem novo (keyboard.py) precisa wire-up em `Daemon` — método `_start_keyboard()`, zeragem no `_shutdown`, consumo no `_poll_loop` compartilhando `buttons_pressed` (A-09) com mouse e hotkey.
- Formato JSON das bindings: preferir strings `"KEY_LEFTALT+KEY_TAB"` — legíveis, diffable, facilmente editáveis à mão. Validar no loader via `evdev.ecodes.KEY_*` dict lookup.
- onboard/wvkbd-mobintl: detectar com `shutil.which` antes de tentar exec. Se nenhum, emitir log warning **uma vez** (não a cada press de L3). Guardar flag `_kbd_onscreen_available: bool`.
- Sprint **grande**. Se primeiro iteração passar de 2h ou 500 linhas de diff, quebrar em FEAT-KEYBOARD-EMULATOR-01 (infraestrutura) + FEAT-KEYBOARD-UI-01 (UI) + FEAT-KEYBOARD-DEFAULTS-01 (bindings novos).
- L3/R3 abrem/fecham onboard — essa é integração com ecosistema externo; se GNOME já tem atalho nativo para teclado virtual (`gsettings set org.gnome.desktop.a11y.applications screen-keyboard-enabled true`), preferir esse caminho em vez de Popen.

## Fora de escopo

- Suporte a macro/sequências temporais complexas (ex.: "hold Square 500ms → emit sequence").
- Suporte a chord MOD multi-layer (ex.: fn+Circle = outra cena).
- i18n de nomes de teclas na UI.
