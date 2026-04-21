# FEAT-MOUSE-02 — Extensão do mapeamento Mouse: Circle=Enter, Square=Esc

**Tipo:** feat (pequeno).
**Wave:** V1.1 (Fase 2, paralelo).
**Estimativa:** 0.5 iteração.
**Dependências:** FEAT-MOUSE-01 já mergeada no `main`.

---

**Tracking:** issue [#87](https://github.com/AndreBFarias/hefesto/issues/87) — fechada por PR com `Closes #87` no body.

## Contexto

FEAT-MOUSE-01 estabeleceu o modo mouse com mapeamento:

- Cross (X) / L2 → `BTN_LEFT`
- Triangle (△) / R2 → `BTN_RIGHT`
- D-pad → `KEY_UP/DOWN/LEFT/RIGHT`
- Analógico esquerdo → `REL_X`/`REL_Y`
- Analógico direito → `REL_WHEEL`/`REL_HWHEEL`
- R3 → `BTN_MIDDLE`

Circle (○) e Square (□) ficaram sem função no modo mouse. O usuário quer:

- **Circle → `KEY_ENTER`** (confirmar / OK em diálogos, enviar em formulários).
- **Square → `KEY_ESC`** (cancelar / fechar menu / voltar).

Essa extensão torna o modo mouse um "navegador desktop completo" — abrir menus com Enter, fechar com Esc, sem precisar do teclado.

## Critérios de aceite

- [ ] `src/hefesto/integrations/uinput_mouse.py` — `UinputMouseDevice.__init__()` declara `KEY_ENTER` e `KEY_ESC` no conjunto de capabilities.
- [ ] `UinputMouseDevice.dispatch(state)` — edge-triggered: ao detectar `circle` transicionando `False → True`, emit `KEY_ENTER` press+release; análogo para `square` → `KEY_ESC`.
- [ ] Estado interno (`_prev_circle: bool`, `_prev_square: bool`) evita re-emissão enquanto botão está segurado. Hold não repete (consistente com L_BTN / R_BTN que também são edge-triggered).
- [ ] Atualizar a legenda "Mapeamento (fixo nesta versão):" na aba Mouse da GUI (`src/hefesto/gui/main.glade`) para incluir:
  - `Circle → Enter`
  - `Square → Esc`
- [ ] Testes em `tests/unit/test_uinput_mouse.py`:
  - `test_circle_edge_trigger_enter`: dispatch com `circle=True` em primeiro tick emite `KEY_ENTER`; segundo tick com `circle=True` NÃO re-emite.
  - `test_square_edge_trigger_esc`: análogo para `KEY_ESC`.
  - `test_release_allows_re_emit`: após release (`circle=False`), próxima pressão re-emite.
- [ ] Proof-of-work: `.venv/bin/pytest tests/unit -q` verde; captura da aba Mouse mostrando nova legenda atualizada.
- [ ] `./scripts/check_anonymity.sh` OK, `ruff` limpo.

## Arquivos tocados (previsão)

- `src/hefesto/integrations/uinput_mouse.py`
- `src/hefesto/gui/main.glade` (legenda da aba Mouse)
- `tests/unit/test_uinput_mouse.py`

## Fora de escopo

- Mapeamento customizável pelo usuário (fica para V2).
- Ações compostas (ex.: `Circle + Triangle` = `Alt+F4`).
- Outros botões do DualSense (`touchpad_press`, `options`, `create`) — V1.2 ou superior.

## Notas para o executor

- Seguir o mesmo padrão de edge-trigger já implementado para `cross`, `triangle`, `r3` em `UinputMouseDevice.dispatch`.
- Se `python-uinput` precisar de import adicional de `uinput.KEY_ENTER`/`uinput.KEY_ESC`, acrescentar no `__init__.py` da integração.
- Reaproveitar `_update_prev_button_state` helper se existir; senão adicionar estado `_prev_circle`/`_prev_square` ao lado dos outros.
