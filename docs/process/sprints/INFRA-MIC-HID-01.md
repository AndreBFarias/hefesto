# INFRA-MIC-HID-01 — Expor botão Mic do DualSense em ControllerState

**Tipo:** infra (pré-requisito de feat).
**Wave:** V1.1 (desbloqueio de FEAT-HOTKEY-MIC-01).
**Estimativa:** 0.5 iteração.
**Dependências:** **INFRA-BUTTON-EVENTS-01** (precisa de `ControllerState.buttons_pressed` já populado e publisher BUTTON_DOWN ativo no poll loop).
**Desbloqueia:** FEAT-HOTKEY-MIC-01 (#72).

---

**Tracking:** issue [#91](https://github.com/AndreBFarias/hefesto/issues/91) — fechada por PR com `Closes #91` no body. Criada com labels `status:ready ai-task type:infra P1-high`.

## Contexto

O botão dedicado de microfone do DualSense (ao lado do touchpad) **não está mapeado** em `EvdevReader.BUTTON_MAP` (`src/hefesto/core/evdev_reader.py:80-94`) porque o kernel Linux não expõe keycode evdev estável para ele — o controle reporta o estado pelo **HID-raw** no byte de miscelâneos do input report, bit 2.

Descoberta confirmada via grep em `.venv/lib/python3.10/site-packages/pydualsense/pydualsense.py:327`:
```python
self.state.micBtn = (misc2 & 0x04) != 0
```
A própria `pydualsense` já faz o parsing. Basta expor em `ControllerState` e no poll loop propagar o nome canônico `"mic_btn"` dentro de `buttons_pressed` quando `ds.state.micBtn` é `True`.

A sprint anterior (INFRA-BUTTON-EVENTS-01) já consolidou o campo `ControllerState.buttons_pressed: frozenset[str]` e o publisher de `EventTopic.BUTTON_DOWN`. Aqui adicionamos o elemento `"mic_btn"` a esse conjunto quando apropriado.

## Decisão

1. Em `PyDualSenseController.read_state()`, **após** construir o `buttons_pressed` a partir do `EvdevSnapshot`, consultar `ds.state.micBtn` (atributo bool parseado pela pydualsense a partir do HID-raw) e, se `True`, adicionar `"mic_btn"` ao conjunto antes de criar o `ControllerState`.
2. Em `FakeController` (tests/fixtures), permitir simular `mic_btn_pressed: bool` no replay — necessário para testar INFRA-BUTTON-EVENTS-01 disparando BUTTON_DOWN com `button="mic_btn"`.
3. Documentar em docstring da `BUTTON_MAP` que o Mic não vem por evdev: vem por HID-raw via `ds.state.micBtn`, injetado em `backend_pydualsense.read_state()`.
4. Nome canônico: `"mic_btn"` (segue o padrão de `l2_btn` e `r2_btn`, minúsculo com underscore).

## Escopo (touches autorizados)

**Arquivos a modificar:**
- `src/hefesto/core/backend_pydualsense.py` — injetar `"mic_btn"` em `buttons_pressed` quando `ds.state.micBtn` é `True`.
- `src/hefesto/core/evdev_reader.py` — comentário de classe explicando que Mic vem por HID-raw, não evdev (nenhuma mudança funcional aqui).
- `tests/fixtures/fake_controller.py` — expor atributo `mic_btn_pressed: bool` ou aceitar `"mic_btn"` dentro do set injetado.
- `tests/unit/test_controller.py` — teste opcional de `ControllerState` com `"mic_btn"` em `buttons_pressed`.

**Arquivos a criar:** nenhum.

**Arquivos NÃO tocar:**
- `src/hefesto/core/controller.py` — `ControllerState.buttons_pressed` já existe (adicionado por INFRA-BUTTON-EVENTS-01).
- `src/hefesto/core/events.py` — nenhum tópico novo; Mic flui como BUTTON_DOWN/UP com `button="mic_btn"`.
- `src/hefesto/daemon/lifecycle.py` — o diff de botões já cobre `"mic_btn"` sem mudança.

## Critérios de aceite

1. Quando o daemon roda com DualSense real e o usuário pressiona o botão Mic, `EventTopic.BUTTON_DOWN` é publicado no bus com payload `{"button": "mic_btn", "pressed": True}`.
2. Ao soltar, `EventTopic.BUTTON_UP` é publicado com `{"button": "mic_btn", "pressed": False}`.
3. `FakeController` consegue simular `mic_btn=True/False` num replay/cenário de teste.
4. Teste novo em `tests/unit/test_backend_pydualsense.py` (ou extensão do `test_controller.py`): mocka `pydualsense` com `state.micBtn=True`, chama `read_state()`, confirma que `"mic_btn" in state.buttons_pressed`.
5. Teste end-to-end em `tests/unit/test_daemon_lifecycle.py`: FakeController que alterna `mic_btn` produz sequência correta de BUTTON_DOWN/UP com `button="mic_btn"`.
6. `ruff check src/ tests/` limpo; `mypy src/hefesto` sem novos erros.
7. `./scripts/check_anonymity.sh` OK.
8. Smoke USB/BT continuam verdes.

## Invariantes a preservar

- **ADR-001 (backend síncrono):** não introduzir asyncio em `read_state()`; só leitura de atributo da pydualsense.
- **PT-BR** em comentários/docstrings/logs; **acentuação correta** em todo arquivo tocado.
- **Zero emojis**; glyphs Unicode intactos (A-04).
- **Nome canônico lowercase com underscore** — `"mic_btn"` consistente com `l2_btn`, `r2_btn`.
- **Não confundir bits de input (byte misc, bit 2) com bytes de output (outReport[9] mic LED)** — são direções opostas do HID; esta sprint só lê input.

## Plano de implementação

1. Editar `src/hefesto/core/backend_pydualsense.py` `read_state()`:
   - No ramo evdev (onde `self._evdev.is_available()` é `True`):
     ```python
     buttons = set(snap.buttons_pressed)
     try:
         if bool(getattr(ds.state, "micBtn", False)):
             buttons.add("mic_btn")
     except Exception:  # defensivo: state pode estar cru no primeiro tick
         pass
     buttons_pressed = frozenset(buttons)
     ```
     e passar `buttons_pressed=buttons_pressed` ao construir `ControllerState`.
   - No ramo fallback (sem evdev), fazer a mesma leitura de `ds.state.micBtn` — é o único botão que está garantido mesmo sem evdev, pois vem da pydualsense HID-raw direta.
2. Editar `src/hefesto/core/evdev_reader.py` — docstring de `BUTTON_MAP` ganha comentário: "O botão Mic **não** está aqui; vem por HID-raw via `ds.state.micBtn` (byte misc2 bit 0x04). Ver `PyDualSenseController.read_state()`."
3. Editar `tests/fixtures/fake_controller.py` — adicionar parâmetro de configuração `mic_btn_pressed: bool = False` que é propagado no `buttons_pressed` do `ControllerState` que ele retorna.
4. Novo teste em `tests/unit/test_backend_pydualsense.py` (criar se não existir) OU em `test_controller.py`: `test_read_state_includes_mic_btn_when_hid_bit_set`.
5. Teste de integração em `test_daemon_lifecycle.py` encadeando FakeController + bus subscribe + verificação de payload `{"button": "mic_btn", ...}`.
6. Rodar contratos de runtime.

## Aritmética

Sem meta numérica de linhas. Arquivos maiores tocados:
- `backend_pydualsense.py`: atualmente ~175 linhas. Adição: ~8 linhas. Projetado: ~183. OK.
- `fake_controller.py`: verificar tamanho atual — adição estimada <15 linhas.

## Testes

- `.venv/bin/pytest tests/unit -v --no-header -q` verde.
- Baseline FAIL_BEFORE: 0 (pós-INFRA-BUTTON-EVENTS-01). Esperado FAIL_AFTER: 0.
- Novos testes:
  - `tests/unit/test_backend_pydualsense.py::test_read_state_includes_mic_btn_when_hid_bit_set` (ou equivalente em `test_controller.py`).
  - `tests/unit/test_daemon_lifecycle.py::test_poll_loop_emits_mic_btn_down_up`.

## Proof-of-work esperado

- Diff final.
- Runtime real:
  ```bash
  HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
  HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt
  .venv/bin/pytest tests/unit -v --no-header -q
  .venv/bin/ruff check src/ tests/
  .venv/bin/mypy src/hefesto
  ./scripts/check_anonymity.sh
  ```
- Validação com hardware (se disponível): rodar daemon real, pressionar botão Mic, observar log `button_event` com `button="mic_btn"`. Registrar no commit body. Se não houver hardware, apontar explicitamente — FakeController cobre a gramática.
- Acentuação periférica: varredura em todos arquivos modificados.
- Hipótese verificada: `rg "micBtn|mic_btn" src/ tests/` deve mostrar pelo menos as injeções novas em `backend_pydualsense.py` e os testes.

## Riscos e não-objetivos

- **Não-objetivo:** aplicar mute no microfone do sistema (FEAT-AUDIO-CONTROL-01).
- **Não-objetivo:** acender o LED de mic do controle (INFRA-SET-MIC-LED-01).
- **Não-objetivo:** wire handler de `BUTTON_DOWN mic_btn` em `Daemon` (FEAT-HOTKEY-MIC-01 pós-desbloqueio).
- **Risco:** `ds.state` pode não estar inicializado no primeiro tick em alguns transportes (raro com kernel hid_playstation ativo). Mitigação: `getattr(ds.state, "micBtn", False)` + try/except. Nunca deixar propagar exceção para o poll loop.
- **Achado colateral possível:** se alguma das outras flags em `ds.state` (ex.: `touchBtn` para clique do touchpad) também não tiver keycode evdev confiável, registrar como sprint nova `INFRA-TOUCHPAD-HID-01` — não arrastar pra cá.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-DualSense_Unix/VALIDATOR_BRIEF.md`
- Código confirmado via grep: `.venv/lib/python3.10/site-packages/pydualsense/pydualsense.py:327` (`self.state.micBtn = (misc2 & 0x04) != 0`), `src/hefesto/core/backend_pydualsense.py:77-109`, `src/hefesto/core/evdev_reader.py:80-94`.
- Precedente: INFRA-BUTTON-EVENTS-01 (esta sprint consome o campo `buttons_pressed` criado lá).
- Desbloqueia: FEAT-HOTKEY-MIC-01 (#72).

---

*"O kernel não conta tudo — quem sabe é o HID bruto."*
