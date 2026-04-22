# FEAT-AUDIO-CONTROL-01 — AudioControl autônomo (wpctl/pactl + debounce)

**Tipo:** feat (entrega parcial autocontida).
**Wave:** V1.1.
**Estimativa:** 0.5 iteração.
**Dependências:** nenhuma.
**Relacionada:** issue #72 (FEAT-HOTKEY-MIC-01) — escopo reduzido. Esta sprint entrega **apenas o módulo de controle de áudio**; o wire-up ao botão físico fica para uma sprint futura que será desbloqueada por INFRA-BUTTON-EVENTS-01 + INFRA-MIC-HID-01 + INFRA-SET-MIC-LED-01.

---

**Tracking:** issue [#93](https://github.com/AndreBFarias/hefesto/issues/93) — fechada por PR com `Closes #93` no body. Criada com labels `status:ready ai-task type:feature P2-medium`.

## Contexto

FEAT-HOTKEY-MIC-01 (issue #72) foi rejeitada em 2026-04-21 porque dependia de 3 peças de infraestrutura ausentes. Enquanto essas 3 infras (INFRA-BUTTON-EVENTS-01, INFRA-MIC-HID-01, INFRA-SET-MIC-LED-01) seguem seu curso, **a lógica de áudio em si é isolada e pode ser entregue agora**.

Esta sprint constrói `src/hefesto/integrations/audio_control.py` com uma classe `AudioControl` testável, auto-suficiente, que detecta se o sistema usa `wpctl` (PipeWire/WirePlumber) ou `pactl` (PulseAudio) e executa `toggle_default_source_mute()` via subprocess. Inclui debounce 200ms e retorno explícito do novo estado.

**Não faz wire-up** — não mexe em `Daemon`, `hotkey_daemon`, `lifecycle`, nem subscribe em event bus. Quando as 3 infras estiverem merged, uma sprint subsequente (vamos chamar de FEAT-MIC-BUTTON-WIRE-01 no futuro) vai consumir este módulo.

## Decisão

1. Classe `AudioControl` em `src/hefesto/integrations/audio_control.py`:
   - `__init__(self, clock: Callable[[], float] | None = None) -> None` — recebe clock injetável (default `time.monotonic`) para debounce testável.
   - Detecta backend no primeiro uso: `shutil.which("wpctl")` primeiro, fallback `shutil.which("pactl")`, fallback `None` (sem backend).
   - Cacheia a escolha em `self._backend: Literal["wpctl", "pactl", "none"]`.
   - `toggle_default_source_mute() -> bool`: chama o subprocess correto sem `shell=True`, parseia novo estado pelo `get` subsequente, retorna `True` se agora está mutado. Aplica debounce de 200ms (ignora chamadas dentro do intervalo; retorna o último estado cacheado).
   - Se backend = `"none"`: loga warning uma vez e retorna `False` sem tentar.
   - Nunca levanta; qualquer falha de subprocess vira `logger.warning` + retorno do último estado conhecido.
2. Comandos canônicos:
   - `wpctl`: toggle `wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle`; query `wpctl get-volume @DEFAULT_AUDIO_SOURCE@` (saída contém `[MUTED]` se mutado).
   - `pactl`: toggle `pactl set-source-mute @DEFAULT_SOURCE@ toggle`; query `pactl get-source-mute @DEFAULT_SOURCE@` (saída: `Mute: yes` ou `Mute: no`).
3. Timeout subprocess: 2s por chamada; `subprocess.run(..., timeout=2.0, check=False, capture_output=True, text=True)`.
4. Usar `structlog` via `hefesto.utils.logging_config.get_logger` — nunca `print`.

## Escopo (touches autorizados)

**Arquivos a modificar:** nenhum.

**Arquivos a criar:**
- `src/hefesto/integrations/audio_control.py`.
- `tests/unit/test_audio_control.py`.

**Arquivos NÃO tocar (esta sprint):**
- `src/hefesto/daemon/lifecycle.py` — wire-up é escopo futuro.
- `src/hefesto/integrations/hotkey_daemon.py` — idem.
- `src/hefesto/core/controller.py` — idem (`set_mic_led` é INFRA-SET-MIC-LED-01).
- `src/hefesto/core/events.py` — idem (BUTTON_DOWN publisher é INFRA-BUTTON-EVENTS-01).

## Critérios de aceite

1. `AudioControl` detecta `wpctl` quando `shutil.which("wpctl")` retorna path; fallback para `pactl`; fallback final `none` com warning único.
2. `toggle_default_source_mute()` chama subprocess correto **sem `shell=True`**.
3. Retorno é `bool` indicando novo estado (`True` = mutado).
4. Debounce 200ms: duas chamadas consecutivas dentro de 200ms retornam o mesmo valor; só a primeira executa subprocess. Clock injetável no `__init__` para teste.
5. Falha de subprocess (`FileNotFoundError`, timeout, exit != 0) não levanta: loga warning, retorna último estado conhecido (default `False` no primeiro erro).
6. Se nenhum backend disponível: `toggle_default_source_mute()` retorna `False` e loga warning **apenas na primeira chamada** (campo `_warned_no_backend: bool`).
7. Testes em `tests/unit/test_audio_control.py` com todos os cenários:
   - `test_detects_wpctl_when_available`.
   - `test_falls_back_to_pactl_when_no_wpctl`.
   - `test_no_backend_logs_warning_once_and_returns_false`.
   - `test_toggle_calls_wpctl_set_mute_without_shell`.
   - `test_toggle_calls_pactl_set_source_mute_without_shell`.
   - `test_parse_muted_state_from_wpctl_get_volume`.
   - `test_parse_muted_state_from_pactl_get_source_mute`.
   - `test_debounce_200ms_returns_cached_state`.
   - `test_subprocess_timeout_is_graceful`.
   - `test_subprocess_nonzero_exit_is_graceful`.
8. Mock via `unittest.mock.patch("subprocess.run")` e `patch("shutil.which")`; nenhum teste depende do sistema real ter wpctl/pactl.
9. `.venv/bin/ruff check src/ tests/` limpo; `.venv/bin/mypy src/hefesto` sem novos erros.
10. `./scripts/check_anonymity.sh` OK.

## Invariantes a preservar

- **NUNCA `shell=True`** — todo comando é lista de args. Explícito em FEAT-HOTKEY-MIC-01 nota original.
- **Zero emojis**; **PT-BR** em logs/docstrings/comentários; **acentuação correta** no arquivo inteiro.
- **Padrão `from __future__ import annotations`** no topo (arquivo novo).
- **Logging via structlog**: `from hefesto.utils.logging_config import get_logger; logger = get_logger(__name__)`.
- **Tipagem estrita**: `Literal["wpctl", "pactl", "none"]`, `bool`, sem `Any` gratuito.
- **Sem side-effects de import**: nenhum `subprocess.run` em top-level; detecção só no primeiro `toggle_default_source_mute`.
- **Armadilha A-01/A-03**: esta sprint não toca sockets; seguro.

## Plano de implementação

1. Criar `src/hefesto/integrations/audio_control.py`:
   ```python
   from __future__ import annotations

   import shutil
   import subprocess
   import time
   from collections.abc import Callable
   from typing import Literal

   from hefesto.utils.logging_config import get_logger

   logger = get_logger(__name__)

   DEBOUNCE_SEC = 0.2
   SUBPROCESS_TIMEOUT_SEC = 2.0
   Backend = Literal["wpctl", "pactl", "none"]


   class AudioControl:
       """Controla mute do microfone padrao do sistema via wpctl ou pactl.

       Auto-detecta backend no primeiro uso. Nao levanta: falhas viram
       warning + retorno do ultimo estado conhecido.
       """

       def __init__(self, clock: Callable[[], float] | None = None) -> None:
           self._clock = clock or time.monotonic
           self._backend: Backend | None = None
           self._last_call_at: float = 0.0
           self._last_known_muted: bool = False
           self._warned_no_backend: bool = False

       def _detect_backend(self) -> Backend:
           if shutil.which("wpctl"):
               return "wpctl"
           if shutil.which("pactl"):
               return "pactl"
           return "none"

       def _ensure_backend(self) -> Backend:
           if self._backend is None:
               self._backend = self._detect_backend()
               logger.info("audio_backend_detected", backend=self._backend)
           return self._backend

       def toggle_default_source_mute(self) -> bool:
           now = self._clock()
           if (now - self._last_call_at) < DEBOUNCE_SEC:
               logger.debug("audio_toggle_debounced")
               return self._last_known_muted
           self._last_call_at = now

           backend = self._ensure_backend()
           if backend == "none":
               if not self._warned_no_backend:
                   logger.warning("audio_backend_unavailable")
                   self._warned_no_backend = True
               return False

           try:
               if backend == "wpctl":
                   self._run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])
                   self._last_known_muted = self._query_wpctl_muted()
               else:
                   self._run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"])
                   self._last_known_muted = self._query_pactl_muted()
           except Exception as exc:
               logger.warning("audio_toggle_failed", backend=backend, err=str(exc))
           return self._last_known_muted

       def _run(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
           return subprocess.run(
               argv,
               timeout=SUBPROCESS_TIMEOUT_SEC,
               check=False,
               capture_output=True,
               text=True,
           )

       def _query_wpctl_muted(self) -> bool:
           result = self._run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"])
           return "[MUTED]" in (result.stdout or "")

       def _query_pactl_muted(self) -> bool:
           result = self._run(["pactl", "get-source-mute", "@DEFAULT_SOURCE@"])
           return "yes" in (result.stdout or "").lower()


   __all__ = ["AudioControl", "Backend", "DEBOUNCE_SEC"]
   ```
2. Criar `tests/unit/test_audio_control.py` cobrindo os 10 cenários listados. Usar `unittest.mock.patch` para `subprocess.run` e `shutil.which`. Clock injetado via parâmetro.
3. Rodar contratos de runtime.

## Aritmética

Arquivo novo:
- `audio_control.py`: ~90 linhas projetadas. Abaixo do limite 800L.
- `test_audio_control.py`: ~150 linhas projetadas. Tests isentos de limite.

## Testes

- `.venv/bin/pytest tests/unit/test_audio_control.py -v --no-header -q` verde (10+ testes).
- `.venv/bin/pytest tests/unit -v --no-header -q` — suite completa verde.
- Baseline FAIL_BEFORE: 0. Esperado FAIL_AFTER: 0.

## Proof-of-work esperado

- Diff final (git diff main).
- Runtime real:
  ```bash
  HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
  HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt
  .venv/bin/pytest tests/unit -v --no-header -q
  .venv/bin/ruff check src/ tests/
  .venv/bin/mypy src/hefesto
  ./scripts/check_anonymity.sh
  ```
- **Smoke ignora este módulo** — não há wire-up. Confirma só que a suite continua sã.
- **Validação semi-manual** (se o reviewer tiver wpctl no sistema): em Python REPL, `from hefesto.integrations.audio_control import AudioControl; a = AudioControl(); print(a.toggle_default_source_mute())` e observar `pavucontrol` → aba Input Devices → ícone do mic mudar. Não obrigatório, pois é coberto por testes com mock.
- Acentuação periférica: varredura em `audio_control.py` e `test_audio_control.py`.
- Hipótese verificada: `rg "shell=True" src/hefesto/integrations/audio_control.py` deve retornar zero matches.

## Riscos e não-objetivos

- **Não-objetivo (explícito):** wire-up ao botão físico Mic. Não mexe em `Daemon`, `hotkey_daemon.py`, `lifecycle.py`. Se durante a execução surgir tentação de "já conecta tudo", PARAR e dispatcha planejador-sprint pra abrir FEAT-MIC-BUTTON-WIRE-01 (protocolo anti-débito, meta-regra 9.7).
- **Não-objetivo:** configurar qual source (usa sempre `@DEFAULT_AUDIO_SOURCE@`).
- **Não-objetivo:** DaemonConfig.mic_button_toggles_system — toggle on/off do feature só faz sentido quando houver wire-up.
- **Risco:** `wpctl get-volume` saída pode variar entre versões (wireplumber antes de 0.4.12 não incluía `[MUTED]`). Mitigação: fallback para `pactl` ou aceitar ambiguidade — registrar no teste o formato assumido (`"[MUTED]" in stdout`).
- **Risco:** `@DEFAULT_SOURCE@` em `pactl` depende do servidor PulseAudio rodando. Se não rodar, `pactl` retorna exit != 0 — já tratado por `check=False` + warning.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-DualSense_Unix/VALIDATOR_BRIEF.md`
- Spec original: `docs/process/sprints/FEAT-HOTKEY-MIC-01.md` (cujo escopo amplo justifica esta cisão).
- Issue pai: #72.
- Código confirmado via grep: `src/hefesto/utils/logging_config.py` (logger factory), `src/hefesto/integrations/` (lista atual).

---

*"Faz a parte isolada agora. O casamento espera os pais chegarem."*
