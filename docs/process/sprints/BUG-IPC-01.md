# BUG-IPC-01 — Socket IPC com detecção de socket vivo e isolamento do smoke

**Tipo:** fix (crítico).
**Wave:** fora de wave (correção pós-PR #67).
**Estimativa:** 1 iteração de executor.
**Dependências:** nenhuma.

---

## Contexto

`src/hefesto/daemon/ipc_server.py` hoje faz `unlink()` cego no `start()` e `stop()`, sem testar se outro daemon está vivo no mesmo path. Quando há dois processos daemon ativos (tipicamente: `hefesto.service` systemd + `./run.sh --smoke` ad-hoc), o segundo apaga o socket do primeiro e depois apaga o próprio no shutdown, deixando o daemon de produção órfão do filesystem. A GUI então mostra "daemon offline" apesar de `systemctl --user is-active hefesto.service` reportar `active`.

Reproduzido em 2026-04-21: sessão do usuário abriu a GUI, daemon systemd estava ativo há 24min, socket foi destruído por dois smokes, GUI ficou offline o tempo todo. Ver `VALIDATOR_BRIEF.md` armadilhas A-01 e A-03.

O fix tem dois eixos:

1. **Detecção de socket vivo** no `IpcServer.start()`. Tentar `socket.connect()` temporário antes do `unlink()`. Se conectar com sucesso, falhar com `OSError` claro ("socket ocupado por outro daemon em <path>"). Se falhar com `ConnectionRefusedError` ou `FileNotFoundError`, seguir com `unlink()` + listener novo.
2. **Isolamento do socket do smoke** via env var `HEFESTO_IPC_SOCKET_NAME` (default `hefesto.sock`). Smoke exporta `HEFESTO_IPC_SOCKET_NAME=hefesto-smoke.sock` antes de iniciar. Daemon de produção mantém o default. `ipc_socket_path()` respeita a env.

---

## Critérios de aceite

- [ ] `IpcServer.start()` não apaga socket vivo. Se detectar outro daemon escutando, `raise RuntimeError("socket ocupado por outro daemon em <path>")` com log `logger.error`. Testar via unit test com dois `IpcServer` tentando iniciar no mesmo path.
- [ ] `IpcServer.stop()` só faz `unlink()` do path **se o server próprio ainda é o owner** — compara `stat().st_ino` antes de deletar, ou confia que só deleta se o server foi o último criado por essa instância. Registrar a decisão no docstring.
- [ ] `hefesto.utils.xdg_paths.ipc_socket_path()` passa a respeitar env `HEFESTO_IPC_SOCKET_NAME` (default `hefesto.sock`). Novo unit test em `tests/unit/test_xdg_paths.py` (arquivo novo se não existir).
- [ ] `run.sh --smoke` exporta `HEFESTO_IPC_SOCKET_NAME=hefesto-smoke.sock` antes de chamar o daemon. `run.sh --gui` e `run.sh --daemon` não alteram (usam o default).
- [ ] Unit test em `tests/unit/test_ipc_server.py` cobre: (a) start em path livre; (b) start em path com socket vivo de outro server → falha controlada; (c) start em path com socket morto (arquivo-resto) → unlink e recria; (d) stop remove o próprio socket.
- [ ] Todos os 289 testes unitários pré-existentes continuam passando.
- [ ] Runtime-real: `./run.sh --smoke` + `./run.sh --smoke --bt` bootam OK sem tocar o socket de produção; `.venv/bin/pytest tests/unit -q` verde.

---

## Proof-of-work esperado

```bash
# 1. Unit tests específicos
.venv/bin/pytest tests/unit/test_ipc_server.py tests/unit/test_xdg_paths.py -v

# 2. Smoke com daemon systemd ativo (reproduz o cenário original)
systemctl --user is-active hefesto.service   # esperado: active
HEFESTO_FAKE=1 HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
# Esperado: smoke loga "ipc_server_listening path=.../hefesto-smoke.sock"
ls -la /run/user/1000/hefesto/hefesto.sock    # ainda existe (não foi apagado pelo smoke)

# 3. Cenário dois daemons no mesmo path (teste manual do fix)
.venv/bin/python -c "
import asyncio
from hefesto.daemon.ipc_server import IpcServer
# ... deixar primeiro server rodando e tentar segundo no mesmo path → esperar RuntimeError
"

# 4. Suíte completa
.venv/bin/pytest tests/unit -v --no-header -q
./scripts/check_anonymity.sh
.venv/bin/ruff check src/ tests/
```

**Aritmética esperada do proof-of-work:**
- Unit tests novos: pelo menos 4 em `test_ipc_server.py` (start livre, start ocupado, start resto-morto, stop) e 2 em `test_xdg_paths.py` (default + env override).
- Suíte total: 289 atuais + novos = ≥295 passing.

---

## Arquivos tocados (previsão)

- `src/hefesto/daemon/ipc_server.py` — lógica de start/stop com detecção.
- `src/hefesto/utils/xdg_paths.py` — ler `HEFESTO_IPC_SOCKET_NAME`.
- `run.sh` — exportar var no modo smoke.
- `tests/unit/test_ipc_server.py` — novo ou estendido.
- `tests/unit/test_xdg_paths.py` — novo.

---

## Fora de escopo

- Qualquer mudança no schema JSON-RPC ou nos 10 métodos existentes.
- Lock file para serialização de daemons (mais pesado que necessário).
- Migração de socket para TCP/port (regressão de performance e segurança).

---

## Notas para o executor

- `socket.AF_UNIX` + `SOCK_STREAM` para probe; timeout curto (0.1s).
- `ConnectionRefusedError` = socket-resto; `FileNotFoundError` = sem socket; sucesso = outro daemon vivo.
- Preservar PT-BR em logs, docstrings, mensagens de erro.
- Não tocar nada fora dos arquivos previstos. Se achar regressão colateral, abrir sprint nova (meta-regra 9.7).
