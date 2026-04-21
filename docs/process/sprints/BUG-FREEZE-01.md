# BUG-FREEZE-01 — GUI congela quando daemon está lento/offline

**Tipo:** fix (crítico — bloqueia UX).
**Modelo sugerido:** sonnet (refactor pontual bem delimitado).
**Estimativa:** 1 iteração.
**Dependências:** nenhuma. Pode rodar em paralelo com POLISH-CAPS-01 e FEAT-MOUSE-01.

---

## Causa-raiz identificada

`src/hefesto/app/ipc_bridge.py::_run_call()` chama `asyncio.run()` síncrono para cada RPC. É invocado por três timers GLib na thread principal:

```
LIVE_POLL_INTERVAL_MS   = 50   ms  → 20 Hz  (src/hefesto/app/actions/status_actions.py:51)
STATE_POLL_INTERVAL_MS  = 500  ms  →  2 Hz  (src/hefesto/app/actions/status_actions.py:52)
RECONNECT_POLL_INTERVAL_S = 2   s  → 0.5 Hz (src/hefesto/app/actions/status_actions.py:53-55)
```

Em operação normal (socket respondendo < 5 ms), a GUI é fluida. Mas quando o daemon está lento ou offline, `asyncio.open_unix_connection` bloqueia até falhar — podendo levar centenas de milissegundos ou mais, especialmente se o socket-resto existe mas o processo morreu. 20 chamadas/s × latência alta na thread principal = **janela GTK congela**.

Sintoma observado pelo usuário em 2026-04-21: GUI dá freezy (congela por frames longos) enquanto o daemon está reiniciando ou o socket está em estado transiente.

## Decisão arquitetural

Mover todas as chamadas IPC síncronas para uma thread worker dedicada (ThreadPoolExecutor com 1 worker), com callback de resultado via `GLib.idle_add` para atualizar widgets na thread principal. Padrão clássico de apps GTK com I/O de rede.

Também: **reduzir a frequência do live poll** de 50 ms para 100 ms (10 Hz); 20 Hz de polling via IPC era excessivo para uma UI humana.

E: **timeout curto no connect** — se o socket não responde em 250 ms, desistir e retornar `None` (o polling do próximo tick tenta de novo).

### Arquitetura proposta

```
src/hefesto/app/ipc_bridge.py (reescrito):

_EXECUTOR: ThreadPoolExecutor | None = None     # lazy-init, 1 worker

def _run_call(method, params=None, timeout=0.25):
    """Síncrono mas com timeout curto — mesmo assim, NÃO chamar da thread GTK."""

def call_async(method, params, on_success, on_failure=None, timeout=0.25):
    """Dispara RPC na thread worker; callbacks re-postados via GLib.idle_add."""
```

Nos três ticks de `status_actions.py`:

```python
def _tick_live_state(self) -> bool:
    call_async("daemon.state_full", None,
               on_success=self._render_live_state,
               on_failure=lambda _exc: None)
    return True
```

### Mudança adicional em `ipc_client.py`

Expor helper `IpcClient.connect_with_timeout(timeout)` que envolve `asyncio.wait_for(open_unix_connection, timeout)`. Se `TimeoutError`, levanta `IpcError(-1, "timeout")` — handler trata como falha de IPC normal.

## Critérios de aceite

- [ ] `src/hefesto/app/ipc_bridge.py` reescrito:
  - `_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="hefesto-ipc")` lazy-init.
  - Função síncrona `_run_call()` preservada para uso fora da GUI (CLI, testes) mas DOC documentado que não deve ser chamada da thread GTK.
  - Nova função `call_async(method, params, on_success, on_failure=None, timeout_s=0.25)`: submete ao executor, no `.add_done_callback` re-posta sucesso/falha via `GLib.idle_add(callback, result)`.
  - Helpers existentes `daemon_state_full()`, `profile_list()`, `profile_switch()`, `trigger_set()` etc. passam a aceitar parâmetro opcional `async_mode=False`; quando `True`, usam `call_async`.
- [ ] `src/hefesto/cli/ipc_client.py`: novo `connect()` aceita `timeout: float | None = None` que envolve `asyncio.wait_for(open_unix_connection, timeout)`. `TimeoutError` vira `IpcError(-1, "conexao timeout")`. `call()` também aceita timeout opcional por RPC.
- [ ] `src/hefesto/app/actions/status_actions.py`: os três `_tick_*` usam `call_async` ou equivalente para não bloquear a thread GTK. A máquina de reconnect recebe state pelo callback.
- [ ] `src/hefesto/app/constants.py`: `LIVE_POLL_INTERVAL_MS = 100` (10 Hz em vez de 20 Hz).
- [ ] `src/hefesto/app/actions/daemon_actions.py`: o botão "Reiniciar daemon" (`subprocess.run(..., timeout=10)`) também passa para thread worker — não pode bloquear GTK por 10s.
- [ ] Teste novo `tests/unit/test_ipc_bridge_async.py`: (a) `call_async` não bloqueia; (b) callback de sucesso é invocado; (c) callback de falha invocado em `IpcError`/`FileNotFoundError`; (d) timeout honrado.
- [ ] Teste novo `tests/unit/test_ipc_client_timeout.py`: `connect(timeout=0.1)` em socket inexistente levanta `IpcError` em <200ms.
- [ ] Proof-of-work runtime:
  - GUI aberta com daemon rodando → header "● Conectado Via USB", zero jank.
  - `systemctl --user stop hefesto.service` enquanto GUI aberta → GUI permanece responsiva (arrastar janela, trocar aba) mesmo com daemon morto. Header migra para "◐ Tentando Reconectar..." em ≤ 2s.
  - Botão "Reiniciar Daemon" dispara subprocess e GUI não trava durante os 10s de timeout do subprocess.
  - Capturas: online, reconnecting, pós-restart.
- [ ] `.venv/bin/pytest tests/unit -q` verde.
- [ ] `./scripts/check_anonymity.sh` OK. `ruff` OK.

## Proof-of-work esperado

```bash
# Antes: reproduzir freeze
.venv/bin/python -m hefesto.app.main &
sleep 3
WID=$(xdotool search --name "Hefesto" | head -1)
# Derrubar daemon
systemctl --user stop hefesto.service
# Tentar arrastar/trocar aba durante 10s e gravar screencast
ffmpeg -f x11grab -video_size 1280x720 -framerate 15 -i :1 -t 10 \
    /tmp/hefesto_freeze_antes.mp4
pkill -f hefesto.app.main; sleep 1

# Aplicar fix

# Depois: GUI responsiva mesmo com daemon morto
.venv/bin/python -m hefesto.app.main &
sleep 3
WID=$(xdotool search --name "Hefesto" | head -1)
systemctl --user stop hefesto.service
ffmpeg -f x11grab -video_size 1280x720 -framerate 15 -i :1 -t 10 \
    /tmp/hefesto_freeze_depois.mp4
systemctl --user start hefesto.service
sleep 3
TS=$(date +%Y%m%dT%H%M%S)
import -window "$WID" "/tmp/hefesto_freeze_restored_${TS}.png"
sha256sum /tmp/hefesto_freeze_restored_*.png
pkill -f hefesto.app.main

.venv/bin/pytest tests/unit -q
./scripts/check_anonymity.sh
.venv/bin/ruff check src/ tests/
```

## Arquivos tocados (previsão)

- `src/hefesto/app/ipc_bridge.py` (refactor principal)
- `src/hefesto/cli/ipc_client.py` (timeout nos métodos)
- `src/hefesto/app/actions/status_actions.py` (usar call_async nos ticks)
- `src/hefesto/app/actions/daemon_actions.py` (subprocess em thread)
- `src/hefesto/app/constants.py` (LIVE_POLL_INTERVAL_MS)
- `tests/unit/test_ipc_bridge_async.py` (novo)
- `tests/unit/test_ipc_client_timeout.py` (novo)

## Fora de escopo

- Trocar para biblioteca `asyncio`+`gbulb` (event loop integrado com GTK) — mudança grande, mantém padrão ThreadPool.
- Recebimento de eventos push do daemon (hoje só polling) — sprint futura.
- WebSocket ou outro protocolo — fora do caminho.

## Notas para o executor

- Padrão canônico Python+GTK com I/O em thread:
  ```python
  def on_result(widget_state):
      # executa na thread principal via GLib.idle_add
      widget.set_markup(...)

  def worker():
      result = blocking_ipc_call()
      GLib.idle_add(on_result, result)

  executor.submit(worker)
  ```
- `GLib.idle_add(callback, *args)` retorna `False` para remover — retornar `False` explicitamente no callback para evitar repetição acidental.
- O worker pode levantar exceção; capturar e postar via `GLib.idle_add(on_failure, exc)`.
- O teste deve usar `unittest.mock.patch` em `asyncio.open_unix_connection` para simular timeout sem precisar de socket real.
- Se encontrar achado colateral, abrir sprint-nova (meta-regra 9.7). NÃO fixar inline fora do escopo.
