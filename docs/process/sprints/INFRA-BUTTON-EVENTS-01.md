# INFRA-BUTTON-EVENTS-01 — Publicar EventTopic.BUTTON_DOWN no poll loop (diff de estados)

**Tipo:** infra (pré-requisito de feat).
**Wave:** V1.1 (desbloqueio de FEAT-HOTKEY-MIC-01).
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.
**Desbloqueia:** INFRA-MIC-HID-01, INFRA-SET-MIC-LED-01 (indiretamente), FEAT-HOTKEY-MIC-01 (#72).

---

**Tracking:** issue [#90](https://github.com/AndreBFarias/hefesto/issues/90) — fechada por PR com `Closes #90` no body. Criada com labels `status:ready ai-task type:infra P1-high`.

## Contexto

`src/hefesto/core/events.py:38` declara a constante `EventTopic.BUTTON_DOWN = "button.down"`, mas **nenhum componente no codebase publica nesse tópico**. O poll loop em `src/hefesto/daemon/lifecycle.py:149-185` só publica `STATE_UPDATE` e `BATTERY_CHANGE`; o comentário em `src/hefesto/integrations/hotkey_daemon.py:3-5` admite: "entregue pelo poll loop no futuro — em W8.1 consolidamos detecção de botão via diff de estados consecutivos".

A feature FEAT-HOTKEY-MIC-01 (#72) foi rejeitada pelo executor porque não existe publisher ativo. Esta sprint fecha a lacuna: diff entre `ControllerState.raw_buttons` (ou equivalente) de ticks consecutivos gera eventos `BUTTON_DOWN`/`BUTTON_UP` no bus, com payload canônico `{"button": str, "pressed": bool}`.

Observação crítica confirmada via grep (lição 4): `ControllerState.raw_buttons: int = 0` existe em `src/hefesto/core/controller.py:57` **mas nunca é preenchido** (backend e fake deixam no default). Quem tem botões prontos é `EvdevReader._pressed: set[str]`, sincronizado em `EvdevSnapshot.buttons_pressed: frozenset[str]` (`src/hefesto/core/evdev_reader.py:31-40, 271`). O caminho mais limpo é propagar o conjunto de botões para `ControllerState` e fazer o diff em nomes canônicos — evita reinventar bitmask e casa com o vocabulário já consumido por `HotkeyManager` (`src/hefesto/integrations/hotkey_daemon.py:66-76`, que já recebe `Iterable[str]`).

## Decisão

1. Adicionar campo `buttons_pressed: frozenset[str] = frozenset()` a `ControllerState` (imutável, compatível com default).
2. Preencher esse campo em `PyDualSenseController.read_state()` (ambos os ramos: evdev primário e fallback pydualsense — no fallback, deixa vazio por ora).
3. Preencher em `tests/fixtures/fake_controller.py` (o FakeController usado nos smokes) — manter default vazio, mas permitir replay injetar botões quando necessário.
4. No poll loop de `Daemon._poll_loop()` (lifecycle.py), manter `previous_buttons: frozenset[str]` entre ticks; a cada `state` novo, calcular `pressed_now = state.buttons_pressed - previous_buttons` e `released_now = previous_buttons - state.buttons_pressed`. Publicar `EventTopic.BUTTON_DOWN` com `{"button": name, "pressed": True}` para cada membro de `pressed_now`; idem `BUTTON_UP` com `"pressed": False` para `released_now`. Atualizar `previous_buttons = state.buttons_pressed` ao fim.
5. `store.bump("button.down.emitted")` e `store.bump("button.up.emitted")` por evento, para proof-of-work rastreável via `daemon.state_full`.
6. O `BUTTON_MAP` de `EvdevReader` já cobre 13 botões (cross, circle, triangle, square, l1, r1, l2_btn, r2_btn, create, options, ps, l3, r3). **Não adicionar Mic nesta sprint** — mapeamento do botão Mic é escopo de INFRA-MIC-HID-01. Apenas documentar em comentário que Mic, touchpad_press e dpad_* já aparecem por caminhos diferentes (dpad via `_refresh_dpad_buttons`; Mic via HID-raw, pendente).

## Escopo (touches autorizados)

**Arquivos a modificar:**
- `src/hefesto/core/controller.py` — campo novo `buttons_pressed: frozenset[str] = frozenset()` em `ControllerState`.
- `src/hefesto/core/backend_pydualsense.py` — popular `buttons_pressed=snap.buttons_pressed` no ramo evdev de `read_state()`.
- `src/hefesto/daemon/lifecycle.py` — loop de diff + publicação de `BUTTON_DOWN`/`BUTTON_UP`; contadores em `store.bump`.
- `tests/fixtures/fake_controller.py` — aceitar `buttons_pressed` no replay (default frozenset vazio).
- `tests/unit/test_controller.py` — ajustar assertions de `ControllerState` para tolerar o novo campo.
- `tests/unit/test_daemon_lifecycle.py` — adicionar teste de diff publicando BUTTON_DOWN/UP.

**Arquivos a criar:** nenhum.

**Arquivos NÃO tocar:**
- `src/hefesto/core/events.py` — constante já existe.
- `src/hefesto/integrations/hotkey_daemon.py` — consumidor separado; esta sprint só produz.
- `src/hefesto/core/evdev_reader.py` — `EvdevSnapshot.buttons_pressed` já está correto; não mexer no BUTTON_MAP (escopo de INFRA-MIC-HID-01).

## Critérios de aceite

1. `ControllerState` tem campo `buttons_pressed: frozenset[str]` com default vazio; frozen dataclass preservado.
2. `PyDualSenseController.read_state()` no ramo evdev propaga `snap.buttons_pressed` para o estado.
3. `Daemon._poll_loop()` publica exatamente um `EventTopic.BUTTON_DOWN` com `{"button": "<nome>", "pressed": True}` quando um botão aparece num tick e não estava no anterior; idem um `BUTTON_UP` com `"pressed": False` quando desaparece.
4. Contadores `store.bump("button.down.emitted")` e `store.bump("button.up.emitted")` são incrementados por evento.
5. Nenhum evento é emitido se `state.buttons_pressed == previous_buttons` (idempotência).
6. Teste novo em `test_daemon_lifecycle.py`: monta daemon com FakeController que retorna buttons_pressed={"cross"} no tick 1 e {"cross","circle"} no tick 2 e frozenset() no tick 3; subscreve no bus; valida 3 eventos (down cross, down circle, up cross, up circle) na ordem esperada.
7. Smoke USB e BT (2s cada) continuam verdes, com `poll.tick >= 50` e sem traceback.
8. `ruff check src/ tests/` limpo; `mypy src/hefesto` sem novos erros.
9. `./scripts/check_anonymity.sh` OK.

## Invariantes a preservar

- **Zero emojis gráficos**; glyphs Unicode de estado (U+25CF BLACK CIRCLE etc.) permanecem intactos onde já existem (A-04).
- **PT-BR obrigatório** em comentários, logs `INFO`+, docstrings.
- **Acentuação correta** em todo arquivo tocado (varredura periférica obrigatória pré-commit).
- **`ControllerState` permanece frozen dataclass** — qualquer mutação segue via factory.
- **Backend síncrono (ADR-001, V2-7)**: `read_state()` continua síncrono; diff roda no event loop async em `_poll_loop()`.
- **Armadilha A-01 / A-03**: não introduzir dependência de socket path; esta sprint só mexe em bus em memória.

## Plano de implementação

1. Editar `src/hefesto/core/controller.py`: adicionar `buttons_pressed: frozenset[str] = field(default_factory=frozenset)` (requer import `field`). Atualizar docstring do `ControllerState`.
2. Editar `src/hefesto/core/backend_pydualsense.py` `read_state()` ramo evdev: passar `buttons_pressed=snap.buttons_pressed` ao construir `ControllerState`. No ramo fallback (sem evdev), deixar default vazio com comentário explicando.
3. Editar `src/hefesto/daemon/lifecycle.py` `_poll_loop()`:
   - Antes do loop: `previous_buttons: frozenset[str] = frozenset()`.
   - Após `self.bus.publish(EventTopic.STATE_UPDATE, state)`, mas antes do `bump("poll.tick")`: computar `pressed_now = state.buttons_pressed - previous_buttons`; para cada nome em `sorted(pressed_now)`, `self.bus.publish(EventTopic.BUTTON_DOWN, {"button": name, "pressed": True})` e `self.store.bump("button.down.emitted")`.
   - Idem para `released_now = previous_buttons - state.buttons_pressed` publicando `BUTTON_UP` com `"pressed": False`.
   - Atualizar `previous_buttons = state.buttons_pressed` ao fim do bloco.
4. Ajustar `tests/fixtures/fake_controller.py`: adicionar parâmetro `buttons_pressed` (default frozenset vazio) em cada ControllerState fabricado; expor método utilitário `set_buttons(names: Iterable[str])` para testes.
5. Adicionar teste `test_poll_loop_emits_button_down_up_on_diff` em `tests/unit/test_daemon_lifecycle.py`.
6. Rodar suite completa de contratos de runtime.

## Aritmética

Sem meta numérica de linhas nesta sprint. Arquivo maior tocado:
- `lifecycle.py`: atualmente ~360 linhas. Adição estimada: ~12 linhas. Projetado: ~372 linhas. Continua abaixo do limite de 800.
- `controller.py`: ~115 linhas. Adição estimada: ~3 linhas. Projetado: ~118 linhas.

## Testes

- `.venv/bin/pytest tests/unit -v --no-header -q` — todos verdes.
- Baseline FAIL_BEFORE: 0 (suite atual verde). Esperado FAIL_AFTER: 0.
- Novo teste: `tests/unit/test_daemon_lifecycle.py::test_poll_loop_emits_button_down_up_on_diff`.

## Proof-of-work esperado

- Diff final (git diff main).
- Runtime real (contratos do BRIEF seção CORE):
  ```bash
  HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
  HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt
  .venv/bin/pytest tests/unit -v --no-header -q
  .venv/bin/ruff check src/ tests/
  .venv/bin/mypy src/hefesto
  ./scripts/check_anonymity.sh
  ```
- Expected: `poll.tick >= 50`, `battery.change.emitted >= 1`, `button.down.emitted >= 0` (depende do FakeController usado no smoke — pode ficar em 0 se fake não simular botões; registrar observação).
- Acentuação periférica: varredura em todos arquivos modificados.
- Hipótese verificada: `rg "EventTopic.BUTTON_DOWN" src/` deve mostrar pelo menos um publisher em `lifecycle.py` após o patch.

## Riscos e não-objetivos

- **Não-objetivo:** mapear botão Mic (escopo de INFRA-MIC-HID-01).
- **Não-objetivo:** expor set_mic_led no backend (escopo de INFRA-SET-MIC-LED-01).
- **Não-objetivo:** consumir BUTTON_DOWN em handler de mute audio (escopo de FEAT-HOTKEY-MIC-01 pós-desbloqueio).
- **Risco:** se `previous_buttons` não for resetado em reconnect, botões que estavam pressionados no momento da desconexão podem gerar BUTTON_UP fantasma no primeiro tick pós-reconnect. Mitigação: resetar `previous_buttons = frozenset()` após `_reconnect()`.
- **Achado colateral possível:** se `read_state()` fallback (sem evdev) ficar com `buttons_pressed` sempre vazio, botão físico no fallback continua silenciado. Registrar como sprint nova `INFRA-HID-BUTTON-FALLBACK-01` se o usuário pedir cobertura HID-raw pura.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-DualSense_Unix/VALIDATOR_BRIEF.md`
- Código confirmado via grep: `src/hefesto/core/events.py:38`, `src/hefesto/core/controller.py:57`, `src/hefesto/core/evdev_reader.py:31-40,80-94,271`, `src/hefesto/daemon/lifecycle.py:149-185`, `src/hefesto/integrations/hotkey_daemon.py:1-20`.
- Desbloqueia: FEAT-HOTKEY-MIC-01.md (issue #72), FEAT-HOTKEY-STEAM-01.md (issue #71; ganha publisher real).

---

*"Quem não publica, não é ouvido."*
