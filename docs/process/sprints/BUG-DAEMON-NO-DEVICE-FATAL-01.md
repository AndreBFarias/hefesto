# BUG-DAEMON-NO-DEVICE-FATAL-01 — Daemon morre na inicialização sem DualSense conectado

**Tipo:** bug crítico (regressão de resiliência).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Branch:** `rebrand/dualsense4unix` (PR #103).
**Dependências:** nenhuma.
**Tracking:** label `type:bug`, `P0`, `daemon`, `ipc`, `hardware`, `ai-task`, `status:ready`.

---

## Contexto

Reproduzido em 2026-04-27 sem hardware conectado:

- `src/hefesto_dualsense4unix/core/backend_pydualsense.py:45` chama `ds.init()`.
- `pydualsense` internamente faz `__find_device()` e levanta `Exception("No device detected")` em `pydualsense.py:209` quando não encontra HID device com VID/PID `054c:0ce6`.
- Em `src/hefesto_dualsense4unix/daemon/connection.py:38`, `connect_with_retry` captura a exceção e entra em backoff exponencial (1s → 2s → 4s → ... → 30s, infinito enquanto `auto_reconnect=True`). Default em `DaemonConfig` (`lifecycle.py:58`) é `auto_reconnect=True`.
- Em `src/hefesto_dualsense4unix/daemon/lifecycle.py:146-150`, `Daemon.run()` chama `await connect_with_retry(self)` **antes** de `await self._start_ipc()`. Resultado: enquanto não conecta, **IPC server nunca sobe** → socket `$XDG_RUNTIME_DIR/hefesto-dualsense4unix/hefesto-dualsense4unix.sock` nunca é criado.

Cascata observada:
1. CLI/GUI batem no socket → `FileNotFoundError: [Errno 2]`.
2. systemd respawna 3× em 30s (`StartLimitBurst=3` em `assets/hefesto-dualsense4unix.service`); cada respawn enfrenta mesma exception → unit marcada `failed`.
3. Plug do controle DEPOIS do limite estourar não auto-restarta a unit.
4. GUI sobe (não depende do daemon para iniciar) mas todas as funcionalidades online ficam indisponíveis.

Modo FAKE (`HEFESTO_DUALSENSE4UNIX_FAKE=1`) não exibe esse problema porque `daemon/main.py:24` injeta `FakeController` que nunca lança "No device detected". Bug está restrito ao caminho real (`PyDualSenseController.connect()`).

Trechos confirmados via leitura (L-21-3):
- `src/hefesto_dualsense4unix/core/backend_pydualsense.py:40-56` — `connect()` instancia `pydualsense()` e chama `ds.init()` sem try/except.
- `src/hefesto_dualsense4unix/daemon/connection.py:35-57` — `connect_with_retry` faz backoff infinito em `auto_reconnect=True`.
- `src/hefesto_dualsense4unix/daemon/lifecycle.py:127-166` — ordem `connect_with_retry` (146) → `_start_ipc` (150).
- `src/hefesto_dualsense4unix/daemon/main.py:43` — `build_controller()` chama `PyDualSenseController()` no caminho real.
- `src/hefesto_dualsense4unix/testing/fake_controller.py:108` — `FakeController.connect()` é no-op.

---

## Escopo (touches autorizados)

**Arquivos a modificar:**
- `src/hefesto_dualsense4unix/core/backend_pydualsense.py` — tornar `connect()` resiliente; introduzir flag interno `_offline` quando `pydualsense.init()` levantar `Exception("No device detected")`; ajustar `is_connected()`, `read_state()`, `_require()` para retornar estado vazio sem quebrar quando offline.
- `src/hefesto_dualsense4unix/daemon/lifecycle.py` — reordenar `Daemon.run()` para subir IPC/UDP/autoswitch ANTES de tentar conectar; mover `connect_with_retry` para task em background (não-bloqueante).
- `src/hefesto_dualsense4unix/daemon/connection.py` — adicionar variante de retry "non-blocking" que vira asyncio.Task e respeita `_stop_event`.

**Arquivos a criar:**
- `tests/unit/test_backend_no_device_resilient.py` — cobre cenários do fix.

**Arquivos NÃO a tocar (invariantes do BRIEF):**
- `src/hefesto_dualsense4unix/testing/fake_controller.py` — modo FAKE permanece intocado (sintoma não se manifesta lá).
- `src/hefesto_dualsense4unix/daemon/ipc_server.py` — IPC permanece com `_probe_socket_and_cleanup` (A-01); só a ordem de inicialização muda no lifecycle.
- `assets/hefesto-dualsense4unix.service` — `StartLimit*` continua como teto anti-loop (A-10). Fix elimina a causa raiz dos respawns; teto fica como rede de segurança.
- `assets/profiles_default/*.json`, schemas pydantic — sem mudança de campo.
- Handlers IPC, GUI, scripts de install/uninstall — sem mudança.

---

## Acceptance criteria

1. Daemon sobe **com sucesso** sem hardware conectado: `systemctl --user is-active hefesto-dualsense4unix.service` retorna `active`.
2. Socket IPC `$XDG_RUNTIME_DIR/hefesto-dualsense4unix/hefesto-dualsense4unix.sock` existe ≤5s após start, mesmo sem controle.
3. `hefesto-dualsense4unix status` responde JSON com `connected=False`, `transport=None`, `battery_pct=None` — sem traceback.
4. `hefesto-dualsense4unix profile list` funciona offline (não depende de hardware).
5. Plug do controle após daemon offline: state passa para `connected=True, transport="usb"` em ≤10s sem restart de unit.
6. Unplug do controle com daemon vivo: state cai para `connected=False`; daemon não morre; tenta reconectar via `connect_with_retry` em background.
7. `pytest tests/unit -q` continua verde (1286+ testes; +N novos).
8. Smoke FAKE USB e BT de 2s preservados (`poll.tick >= 50`, `battery.change.emitted >= 1`, sem traceback).
9. Lint/types verdes: `ruff check src/ tests/` e `mypy src/hefesto_dualsense4unix`.
10. `./scripts/check_anonymity.sh` verde.

---

## Invariantes a preservar

- **A-01** (BRIEF): `_probe_socket_and_cleanup` em `IpcServer.start()`. Nada do fix toca `ipc_server.py` — só altera ordem de chamada.
- **A-07** (BRIEF): wire-up de subsystem novo precisa 3 pontos. Aqui o "subsystem" é o reconnect-task; precisa slot no dataclass `Daemon`, criação em `run()`, cancelamento em `_shutdown()`.
- **A-10** (BRIEF): single-instance via `acquire_or_takeover` no topo de `run_daemon` permanece. Não duplicar fontes de spawn.
- **L-21-3** (BRIEF): premissas sobre `connect_with_retry` foram lidas; trecho com a ordem (lifecycle.py:146-150) confirmado.
- **L-21-4** (BRIEF): rodar `bash scripts/dev-setup.sh` antes do primeiro `pytest` se sessão nova.
- **PT-BR + acentuação correta** em logs `INFO`+, comentários, docstrings dos arquivos tocados. Varredura periférica obrigatória pré-commit.
- **Zero emojis** em qualquer arquivo tocado.
- **`from __future__ import annotations`** no arquivo de teste novo.
- Nada de `print()` — usar `structlog` via `get_logger`.

---

## Plano de implementação

### Etapa 1: tornar `PyDualSenseController.connect()` resiliente

Em `src/hefesto_dualsense4unix/core/backend_pydualsense.py`:

1. Adicionar atributo interno `self._offline: bool = False` no `__init__`.
2. Em `connect()`, envolver `ds.init()` com try/except que catch da `Exception` cuja mensagem contém `"No device detected"` (string match exato — pydualsense não usa subclasse dedicada).
3. Em caso de catch:
   - `self._ds = None`
   - `self._offline = True`
   - `self._transport = None` (precisa ajustar tipo `Transport` para aceitar `None`, ou manter `"usb"` como sentinela e usar `is_connected()` para distinguir — preferir mudar `read_state()` para retornar `transport=None` quando offline).
   - Log `logger.info("controller_offline_no_device", retry=True)` (uma vez; não inundar).
   - Retornar normalmente (não relançar).
4. Em `connect()`, **outras** exceções (USB error transitório, permissão hidraw) continuam propagando para `connect_with_retry` fazer backoff. Só "No device detected" é tratado como offline-OK.
5. `is_connected()`: retorna `False` quando `self._ds is None` (já é o comportamento atual; basta confirmar).
6. `read_state()`: se `self._ds is None`, retornar `ControllerState` com defaults `connected=False, transport=None, battery_pct=None, l2_raw=0, r2_raw=0, raw_lx=128, raw_ly=128, raw_rx=128, raw_ry=128, buttons_pressed=frozenset()`. Validar que `ControllerState` aceita `transport=None` (se não, ajustar tipo `Transport` em `controller.py` para `Literal["usb","bt"] | None`).
7. `_require()`: ajustar para não levantar quando offline; em vez disso, retornar sentinela ou os setters (`set_trigger`, `set_led`, `set_rumble`, `set_mic_led`, `set_player_leds`) viram no-op com log debug. Setters offline: `if self._ds is None: logger.debug("setter_no_op_offline", op="..."); return`.

### Etapa 2: hot-reconnect probe no `connect()`

Subsequentes chamadas a `connect()` (vindas de `reconnect()` no `connection.py`) devem retentar `pydualsense().init()` toda vez. Lógica:

1. No início de `connect()`, se `self._ds is not None and self.is_connected()`: retornar (já conectado).
2. Caso contrário: zerar `self._ds`, tentar `pydualsense() + init()`. Em sucesso: limpar `_offline=False`, popular `_transport`, iniciar evdev. Em falha "No device detected": marcar `_offline=True`, retornar sem erro.

### Etapa 3: reordenar `Daemon.run()` em `lifecycle.py`

Em `src/hefesto_dualsense4unix/daemon/lifecycle.py:127-166`:

1. Subir IPC/UDP/autoswitch/poll_loop **antes** de tentar conectar:
   ```
   self._tasks = [asyncio.create_task(self._poll_loop(), name="poll_loop")]
   if self.config.ipc_enabled:
       await self._start_ipc()
   if self.config.udp_enabled:
       await self._start_udp()
   if self.config.autoswitch_enabled:
       await self._start_autoswitch()
   # ...
   # depois:
   self._tasks.append(asyncio.create_task(self._reconnect_loop(), name="reconnect_loop"))
   ```
2. Substituir `await connect_with_retry(self)` (bloqueante) por uma task em background `_reconnect_loop` que chama `connect_with_retry` continuamente; primeira tentativa não bloqueia o resto da inicialização.
3. `restore_last_profile(self)` continua sendo chamado, mas só após **primeira conexão bem-sucedida** (mover para dentro de `_reconnect_loop` no bloco pós-conexão, OU manter no `run()` aceitando que com daemon offline o profile não é restaurado até hardware aparecer — preferir 2ª opção: chamar `restore_last_profile` quando bus publica `CONTROLLER_CONNECTED`).
4. `_poll_loop` precisa tolerar `controller.read_state()` quando offline. Como `PyDualSenseController.read_state()` agora retorna estado vazio em offline (Etapa 1 item 6), o loop continua rodando sem exceções; só `bump("poll.tick")` continua.

### Etapa 4: novo método `_reconnect_loop`

Adicionar em `Daemon` ou em `connection.py`:

```python
async def reconnect_loop(daemon: Any) -> None:
    """Tenta conectar continuamente; quando offline, retenta a cada N segundos.
    
    Diferente de connect_with_retry: nunca bloqueia o boot; respeita _stop_event;
    quando conecta, dispara restore_last_profile uma única vez.
    """
    PROBE_INTERVAL_SEC = 5.0
    restored = False
    while not daemon._is_stopping():
        try:
            await daemon._run_blocking(daemon.controller.connect)
            if daemon.controller.is_connected():
                transport = daemon.controller.get_transport()
                daemon.bus.publish(EventTopic.CONTROLLER_CONNECTED, {"transport": transport})
                if not restored:
                    await restore_last_profile(daemon)
                    restored = True
                # já conectou; dorme intervalo maior para detectar unplug
                await asyncio.wait_for(daemon._stop_event.wait(), timeout=PROBE_INTERVAL_SEC * 6)
                continue
        except Exception as exc:
            logger.debug("reconnect_probe_failed", err=str(exc))
        # offline: dorme PROBE_INTERVAL_SEC e tenta de novo
        try:
            await asyncio.wait_for(daemon._stop_event.wait(), timeout=PROBE_INTERVAL_SEC)
            return
        except asyncio.TimeoutError:
            pass
```

Detalhes:
- Log `debug` (não `warning`) para tentativas falhadas — evita inundar journal a cada 5s.
- Log `info` apenas na transição offline→online e online→offline (controlado por flag local).
- A unidade systemd com `StartLimitBurst=3` deixa de ser acionada porque o daemon não morre mais.

### Etapa 5: ajuste do tipo `Transport` (se necessário)

Em `src/hefesto_dualsense4unix/core/controller.py`:

- Localizar `Transport = Literal["usb", "bt"]`.
- Avaliar se `ControllerState.transport` precisa virar `Transport | None`. Verificar consumidores via `rg "state.transport|transport=" src/`. Se for invasivo, **alternativa**: manter `transport: Transport = "usb"` mas adicionar campo `connected: bool` como fonte de verdade (já existe). Documentar que `transport` quando `connected=False` é "última transport conhecida ou default usb".

**Decisão recomendada (executor confirma na exploração):** manter `transport` como string e usar `connected=False` como sinal de offline. GUI/CLI já consultam `connected` primeiro. Reduz escopo.

---

## Aritmética

- `backend_pydualsense.py`: 235L atuais → +30L estimadas (try/except em `connect`, defaults em `read_state` offline, no-ops em setters) → ~265L. Limite 800L: OK.
- `lifecycle.py`: 445L atuais → +20L estimadas (reordenar `run()`, slot `_reconnect_task`, mover `restore_last_profile`) → ~465L. Limite 800L: OK.
- `connection.py`: 137L atuais → +30L estimadas (função `reconnect_loop`) → ~167L. Limite 800L: OK.
- `tests/unit/test_backend_no_device_resilient.py` (novo): ~150L estimadas, 6-8 testes. Sem limite (testes).

Total novo: ~80L em src + ~150L em tests = ~230L. Sprint compacta.

---

## Testes

### Novos (`tests/unit/test_backend_no_device_resilient.py`)

1. `test_connect_swallows_no_device_detected_marks_offline`: mock `pydualsense.init` para levantar `Exception("No device detected")`; assert `controller._offline is True`, `controller.is_connected() is False`, sem exception propagada.
2. `test_connect_propaga_outras_excecoes`: mock `init` para levantar `RuntimeError("hidraw permission denied")`; assert `RuntimeError` propagado (deixa `connect_with_retry` fazer backoff).
3. `test_read_state_offline_retorna_defaults`: controller offline; `read_state()` retorna `connected=False, battery_pct=0, buttons_pressed=frozenset()`, sem exception.
4. `test_setters_offline_sao_noop`: controller offline; `set_trigger`, `set_led`, `set_rumble`, `set_mic_led`, `set_player_leds` retornam sem exception e sem chamar nada do `pydualsense`.
5. `test_connect_apos_offline_recupera_quando_device_aparece`: mock `init` levanta `"No device detected"` na 1ª chamada; na 2ª retorna ok; `connect()` chamado 2× → 1ª marca offline, 2ª limpa offline e popula `_ds`.

### Novos (`tests/unit/test_daemon_lifecycle.py` ou `test_daemon_reconnect_loop.py`)

6. `test_run_inicia_ipc_antes_de_conectar`: monkey-patch `connect_with_retry` para nunca retornar (controle desconectado simulado); assert que `_start_ipc` foi chamado e `_ipc_server is not None` antes de timeout.
7. `test_reconnect_loop_publica_controller_connected_em_transicao`: simula `connect()` que falha 2× e sucede na 3ª; bus deve publicar `CONTROLLER_CONNECTED` exatamente 1× quando hardware aparece.
8. `test_reconnect_loop_respeita_stop_event`: `_stop_event.set()` durante o backoff faz a task retornar em ≤200ms.

### Baselines

- `pytest tests/unit -q`: FAIL_BEFORE = 0. FAIL_AFTER ≤ 0. (Sprint não pode introduzir falhas.)
- Suite total esperada: 1286 + 8 novos = 1294 (ajustar para número real do branch atual via `pytest --collect-only -q | tail -3` antes de redigir números no relatório).

---

## Proof-of-work esperado

### Diff final
- Arquivos modificados/criados conforme escopo. Diff completo em log de execução.

### Runtime real (comandos do BRIEF)

```bash
# Preparação ambiente (idempotente)
bash scripts/dev-setup.sh

# 1. Smoke USB FAKE (deve continuar verde)
HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=usb \
  HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke
# esperado: poll.tick >= 50, battery.change.emitted >= 1, sem traceback

# 2. Smoke BT FAKE (deve continuar verde)
HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=bt \
  HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke --bt

# 3. Unit tests
.venv/bin/pytest tests/unit -v --no-header -q

# 4. Lint + types
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto_dualsense4unix

# 5. Anonimato
./scripts/check_anonymity.sh
```

### Runtime real do bug (caminho não-FAKE, hardware desconectado)

Bash exato a executar e anexar saída ao relatório de execução:

```bash
# 1. Garantir controle DESCONECTADO antes do teste
# (user fisicamente desplugou — verificar com lsusb)
lsusb | grep -i 0ce6 && echo "FAIL: controle ainda conectado"

# 2. Subir daemon e validar que SOBE (não morre)
systemctl --user restart hefesto-dualsense4unix.service
sleep 5
systemctl --user is-active hefesto-dualsense4unix.service  # esperado: active

# 3. Socket IPC deve existir
ls /run/user/1000/hefesto-dualsense4unix/hefesto-dualsense4unix.sock  # esperado: existe

# 4. status via CLI deve responder com connected=False (não crash)
hefesto-dualsense4unix status  # esperado: connected=False, sem traceback

# 5. profile.list via IPC funciona (não depende de hardware)
hefesto-dualsense4unix profile list  # esperado: lista os perfis

# 6. Plug do controle: daemon deve detectar e atualizar state
# (user pluga, espera 5s)
hefesto-dualsense4unix status  # esperado: connected=True, transport=usb

# 7. Unplug com daemon vivo: state volta a connected=False sem matar daemon
# (user desconecta, espera 5s)
systemctl --user is-active hefesto-dualsense4unix.service  # esperado: active
hefesto-dualsense4unix status  # esperado: connected=False
```

### Acentuação periférica

Varredura em todos arquivos modificados (executar pré-commit):
```bash
.venv/bin/python scripts/check_acentuacao.py \
  src/hefesto_dualsense4unix/core/backend_pydualsense.py \
  src/hefesto_dualsense4unix/daemon/lifecycle.py \
  src/hefesto_dualsense4unix/daemon/connection.py \
  tests/unit/test_backend_no_device_resilient.py
```

### Hipótese verificada (L-21-3)

Antes de iniciar implementação, executor confirma via `rg`:
- `rg -n "ds.init\(\)" src/hefesto_dualsense4unix/core/backend_pydualsense.py` → bate na linha 45.
- `rg -n "connect_with_retry" src/hefesto_dualsense4unix/daemon/lifecycle.py` → bate na linha 146.
- `rg -n "_start_ipc" src/hefesto_dualsense4unix/daemon/lifecycle.py` → bate em linha após `connect_with_retry`.
- `rg -n "auto_reconnect: bool = True" src/hefesto_dualsense4unix/daemon/lifecycle.py` → bate na linha ~58.

Se algum identificador divergir do que está aqui, executor pausa e dispatcha `planejador-sprint` com o diff de premissa.

### Validação visual

Não aplicável — sprint não toca GUI/TUI. Não há captura PNG obrigatória.

---

## Riscos e não-objetivos

### Riscos

- **String match em `Exception("No device detected")`** é frágil — versões futuras de `pydualsense` podem mudar a mensagem. Mitigação: log da exception completa em DEBUG; teste de regressão com mensagem exata; comentário no código apontando para `pydualsense.py:209` como fonte. Se aparecer um match alternativo (ex: `OSError(ENODEV)`), tratar como mesmo caso.
- **`auto_reconnect=True` por default** com fix muda semântica do `connect_with_retry` em testes existentes? Mitigação: `test_daemon_connection.py` usa `_FakeController.connect()` que levanta `ConnectionError`, não `Exception("No device detected")`. Mantém comportamento.
- **Reorder `run()`** pode quebrar testes que dependem de ordem específica. Mitigação: rodar `pytest tests/unit/test_daemon_lifecycle.py -v` ANTES de qualquer mudança para baseline; depois confirmar que continuam passando após o reorder.
- **Hot-reconnect a cada 5s** pode poluir log se hardware ausente por horas. Mitigação: log em `debug` nas tentativas falhadas (não `warning`); transições offline→online e online→offline em `info`.

### Não-objetivos (fora desta sprint)

- **Detecção via udev/pyudev**: monitorar evento `add` do kernel para reagir instantaneamente ao plug. Polling de 5s é suficiente para o sintoma reportado. Se virar requisito, abrir `FEAT-DAEMON-UDEV-HOTPLUG-01`.
- **Ajustar `StartLimitBurst`** na unit systemd: mantém-se em 3/30s como rede de segurança contra crashes reais. Fix elimina os respawns por "No device detected".
- **Alterar `Transport` Literal para incluir `None`**: avaliado mas evitado por invasividade. Se executor encontrar bloqueio durante implementação, abrir sub-sprint `REFACTOR-TRANSPORT-OPTIONAL-01` em vez de inflar esta.
- **Refatorar `connect_with_retry` para fundir com `reconnect_loop`**: deixa-se as duas funções coexistindo. `connect_with_retry` fica disponível para CLI/standalone (`cmd_status.py`, `cmd_emulate.py`); `reconnect_loop` é específico do daemon.
- **Tray/GUI sinalizar "daemon offline tentando reconectar"**: GUI já tem state de `connected=False` (BUG-GUI-DAEMON-STATUS-INITIAL-01 RESOLVIDA). Bug visual de UI fora desta sprint.

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-Dualsense4Unix/VALIDATOR_BRIEF.md`
- Armadilha A-07 (wire-up de subsystem): aplicável ao `_reconnect_task` adicionado em `Daemon`.
- Armadilha A-10 (single-instance): preservada — não duplicar fontes de spawn.
- Lição L-21-3 (ler código antes de spec): trechos lidos listados em "Contexto".
- Lição L-21-4 (validar `.venv` em sessão nova): comando `bash scripts/dev-setup.sh` no proof-of-work.
- Sprint precedente BUG-GUI-DAEMON-STATUS-INITIAL-01 (GUI já tolera daemon offline).
- Sprint precedente AUDIT-FINDING-LOG-EXC-INFO-01 (`connect_with_retry` ganhou backoff exponencial e log com `exc_info=True`).
- Sprint precedente BUG-MULTI-INSTANCE-01 (unit ganhou `StartLimitBurst=3` — agora consequência, não causa).
