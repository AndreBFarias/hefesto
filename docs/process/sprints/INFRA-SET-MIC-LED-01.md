# INFRA-SET-MIC-LED-01 — IController.set_mic_led e implementação no backend

**Tipo:** infra (pré-requisito de feat).
**Wave:** V1.1 (desbloqueio de FEAT-HOTKEY-MIC-01).
**Estimativa:** 0.5 iteração.
**Dependências:** nenhuma (paralelizável com INFRA-BUTTON-EVENTS-01 e INFRA-MIC-HID-01).
**Desbloqueia:** FEAT-HOTKEY-MIC-01 (#72) — permite que `controller.set_mic_led(muted)` reflita o estado de mute do sistema.

---

**Tracking:** issue [#92](https://github.com/AndreBFarias/hefesto/issues/92) — fechada por PR com `Closes #92` no body. Criada com labels `status:ready ai-task type:infra P1-high`.

## Contexto

`src/hefesto/core/led_control.py:5-6` admite explicitamente: "o backend (`IController.set_led`) só aceita a cor da lightbar hoje; os player LEDs e o mic LED dependem de API complementar no backend (a adicionar quando houver necessidade em W5.x)". A necessidade chegou: FEAT-HOTKEY-MIC-01 exige sincronizar o LED do controle com o estado de mute do sistema.

Descoberta confirmada via grep em `.venv/lib/python3.10/site-packages/pydualsense/pydualsense.py`:
- `DSAudio.setMicrophoneLED(value: bool)` em linha 884 — atribui a `self.microphone_led`.
- `prepareReport()` linha 546 (USB) e 610 (BT): `outReport[9] = self.audio.microphone_led` (USB) e `outReport[10] = ...` (BT) — pydualsense cuida da diferença USB/BT.
- `ds.audio = DSAudio()` é inicializado no `__init__` (linha 124).

Ou seja: basta `ds.audio.setMicrophoneLED(bool)` e a pydualsense consolida o report automaticamente (já faz `prepareReport` + `sendReport` num thread interno gerado por `register_available_events`). **Não precisamos chamar `prepareReport()` manualmente** — conferir com o padrão atual de `set_led` (`src/hefesto/core/backend_pydualsense.py:118-121`) que também só atribui `ds.light.setColorI(r, g, b)` sem disparar envio explícito.

## Decisão

1. Adicionar método abstrato `set_mic_led(muted: bool) -> None` em `IController` (`src/hefesto/core/controller.py`). Convenção de semântica: `muted=True` → LED aceso (vermelho, padrão do firmware indicando "mic off"); `muted=False` → LED apagado.
2. Implementar em `PyDualSenseController.set_mic_led(muted: bool)`:
   ```python
   ds = self._require()
   ds.audio.setMicrophoneLED(bool(muted))
   ```
3. Implementar em `FakeController` (tests/fixtures): registrar histórico `self.mic_led_history: list[bool]` para testabilidade.
4. Atualizar `src/hefesto/core/led_control.py::apply_led_settings` para também chamar `controller.set_mic_led(settings.mic_led)` — elimina o débito documentado no comentário das linhas 5-6 e 73-78.
5. Remover o comentário obsoleto "os player LEDs e o mic LED dependem de API complementar" — substituir por "Player LEDs ainda dependem de API complementar; mic LED já coberto".

## Escopo (touches autorizados)

**Arquivos a modificar:**
- `src/hefesto/core/controller.py` — novo método abstrato `set_mic_led`.
- `src/hefesto/core/backend_pydualsense.py` — implementação via `ds.audio.setMicrophoneLED`.
- `src/hefesto/core/led_control.py` — `apply_led_settings` chama `set_mic_led`; atualizar docstrings.
- `tests/fixtures/fake_controller.py` — stub com histórico.
- `tests/unit/test_led_and_rumble.py` (ou `test_led_brightness.py`) — novo teste de `apply_led_settings` propagando mic LED.
- `tests/unit/test_controller.py` — teste que FakeController registra chamadas.

**Arquivos a criar:** nenhum.

**Arquivos NÃO tocar:**
- `src/hefesto/daemon/udp_server.py` — já tem `_do_mic_led` (linha 184, 225) que opera via `store`, fora do escopo.
- `src/hefesto/core/evdev_reader.py` — input, não output.

## Critérios de aceite

1. `IController.set_mic_led(muted: bool) -> None` existe como `@abstractmethod`.
2. `PyDualSenseController.set_mic_led(True)` chama `ds.audio.setMicrophoneLED(True)`; `set_mic_led(False)` chama com `False`. Verificado via teste com mock de pydualsense.
3. `FakeController.set_mic_led(muted)` registra em histórico para inspeção de testes.
4. `apply_led_settings(controller, LedSettings(..., mic_led=True))` invoca `controller.set_mic_led(True)`.
5. Teste novo: `test_apply_led_settings_propagates_mic_led` em `tests/unit/test_led_and_rumble.py` (ou onde fizer sentido).
6. Comentário obsoleto em `led_control.py` (linhas 5-6 e 73-78) atualizado para refletir que mic LED agora está coberto.
7. `ruff check src/ tests/` limpo; `mypy src/hefesto` sem novos erros.
8. `./scripts/check_anonymity.sh` OK.
9. Smoke USB/BT continuam verdes (FakeController satisfaz o novo método).

## Invariantes a preservar

- **ADR-001 (backend síncrono)**: `set_mic_led` é síncrono, consistente com `set_led` e `set_rumble`.
- **PT-BR + acentuação correta** em docstrings/comentários/logs.
- **Zero emojis**; glyphs Unicode de estado intactos.
- **`IController` permanece interface pequena e estável** — adicionar um único método, sem gordura.
- **Nenhum backend novo, nenhum protocolo novo** — só extensão.
- **Não quebrar contrato existente:** toda implementação concreta de `IController` precisa implementar o novo método. `FakeController` entra no patch para não deixar a interface sem implementação em testes.

## Plano de implementação

1. Editar `src/hefesto/core/controller.py`:
   - Adicionar no bloco de métodos abstratos:
     ```python
     @abstractmethod
     def set_mic_led(self, muted: bool) -> None: ...
     ```
   - Atualizar docstring da classe mencionando o novo método.
2. Editar `src/hefesto/core/backend_pydualsense.py`:
   - Adicionar método concreto após `set_rumble`:
     ```python
     def set_mic_led(self, muted: bool) -> None:
         ds = self._require()
         ds.audio.setMicrophoneLED(bool(muted))
     ```
3. Editar `tests/fixtures/fake_controller.py`:
   - Adicionar `self.mic_led_history: list[bool] = []` no `__init__`.
   - Implementar `def set_mic_led(self, muted: bool) -> None: self.mic_led_history.append(bool(muted))`.
4. Editar `src/hefesto/core/led_control.py`:
   - Em `apply_led_settings`: após `controller.set_led(settings.lightbar)`, adicionar `controller.set_mic_led(settings.mic_led)`.
   - Atualizar docstring do módulo (linhas 5-6) e de `apply_led_settings` (linhas 73-78).
5. Novo teste em `tests/unit/test_led_and_rumble.py`:
   ```python
   def test_apply_led_settings_propagates_mic_led():
       fake = FakeController(...)
       apply_led_settings(fake, LedSettings(lightbar=(0,0,0), mic_led=True))
       assert fake.mic_led_history == [True]
   ```
6. Rodar contratos de runtime.

## Aritmética

Sem meta numérica de linhas.
- `controller.py`: ~115L → ~120L.
- `backend_pydualsense.py`: ~175L → ~180L.
- `led_control.py`: ~100L → ~102L.
- `fake_controller.py`: adição <8L.

Todos abaixo do limite de 800L.

## Testes

- `.venv/bin/pytest tests/unit -v --no-header -q` verde.
- Baseline FAIL_BEFORE: 0. Esperado FAIL_AFTER: 0.
- Novos testes:
  - `tests/unit/test_led_and_rumble.py::test_apply_led_settings_propagates_mic_led`.
  - Opcional: `tests/unit/test_backend_pydualsense.py::test_set_mic_led_calls_pydualsense_audio` com mock.

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
- Validação com hardware (se disponível): conectar DualSense, rodar um one-shot Python que chame `PyDualSenseController` e alterne `set_mic_led(True)` / `set_mic_led(False)` com sleep 1s entre. Observar LED de mic acender/apagar fisicamente. Registrar no commit body.
- Acentuação periférica: varredura em todos arquivos modificados.
- Hipótese verificada: `rg "set_mic_led" src/ tests/` deve mostrar declarações + chamadas em pelo menos 5 arquivos.

## Riscos e não-objetivos

- **Não-objetivo:** lidar com player LEDs (continua débito, manter TODO-reference no `led_control.py`).
- **Não-objetivo:** handler de BUTTON_DOWN mic_btn acionando set_mic_led (escopo de FEAT-HOTKEY-MIC-01 pós-desbloqueio).
- **Não-objetivo:** UDP `mic_led` method redesign — já funciona via `udp_server._do_mic_led`.
- **Risco:** `ds.audio` pode ser `None` se pydualsense não inicializou completamente. Mitigação: `_require()` já lança `RuntimeError` antes; `ds.audio` é criado no `__init__` da pydualsense (linha 124), então está garantido após `ds.init()`.
- **Risco de wiring duplicado:** UDP e hotkey chamarão `set_mic_led` concorrentemente. Não há race crítica (pydualsense thread interno já serializa sendReport), mas registrar para FEAT-HOTKEY-MIC-01.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-DualSense_Unix/VALIDATOR_BRIEF.md`
- Código confirmado via grep: `.venv/lib/python3.10/site-packages/pydualsense/pydualsense.py:124,546,610,876-914`, `src/hefesto/core/controller.py:72-107`, `src/hefesto/core/backend_pydualsense.py:118-126`, `src/hefesto/core/led_control.py:5-6,73-78`.
- Desbloqueia: FEAT-HOTKEY-MIC-01 (#72).

---

*"O LED não mente: ou acende, ou não acende."*
