# AUDIT-FINDING-IPC-SERVER-SPLIT-01 — Split de `ipc_server.py` (843 → ≤500 LOC/arquivo)

**Origem:** achado 13 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** L (2 iterações, ~8h). **Severidade:** médio.
**Tracking:** label `type:refactor`, `ai-task`, `status:ready`.

## Contexto

`src/hefesto/daemon/ipc_server.py` tem 843 LOC — excede o limite de 800 declarado em `VALIDATOR_BRIEF.md` seção "Padrões de código" ("Limite: 800 linhas por arquivo (exceto configs/registries/testes)"). É um handler dispatcher, não config. O método `_handle_profile_apply_draft` sozinho tem ~120 LOC (linhas 565-685) com 4 seções paralelas envolvidas em try/except.

## Objetivo

Split em 2-3 arquivos preservando API pública:

1. **`src/hefesto/daemon/ipc_server.py`** (alvo ~350 LOC): classe `IpcServer` (start/stop/probe/dispatch), constantes de error code, protocol version, `_json_rpc_*` helpers.

2. **`src/hefesto/daemon/ipc_handlers.py`** (novo, ~400 LOC): 19 métodos `_handle_*` movidos como funções top-level ou métodos de classe separada `IpcHandlers(server: IpcServer)`. Handler dispatch continua em `IpcServer._dispatch` via registry.

3. **`src/hefesto/daemon/ipc_rumble_policy.py`** (novo, ~80 LOC): `_apply_rumble_policy` + constantes relacionadas. (Opcionalmente absorvido em `core/rumble.py` se AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01 estiver mergeado primeiro — sprint deve declarar ordem explícita.)

4. **`_handle_profile_apply_draft`** virar classe `DraftApplier` com 1 método por seção (leds/triggers/rumble/mouse) — ou função com 4 helpers privados.

Alternativa conservadora: apenas extrair `ipc_handlers.py` e `_apply_rumble_policy`, mantendo `_handle_profile_apply_draft` como está (ou refactor menor).

## Critérios de aceite

- [ ] `wc -l src/hefesto/daemon/ipc_server.py` ≤ 500.
- [ ] `wc -l src/hefesto/daemon/ipc_handlers.py` ≤ 500.
- [ ] Nenhum `_handle_*` tem >100 LOC. `_handle_profile_apply_draft` ≤ 50 LOC ou removido em favor de `DraftApplier`.
- [ ] `from hefesto.daemon.ipc_server import IpcServer, MAX_PAYLOAD_BYTES, PROTOCOL_VERSION, ...` continua funcionando — compat de imports.
- [ ] `__all__` em `ipc_server.py` preserva os nomes públicos.
- [ ] Suite inteira segue verde sem mudança de tests (só ajuste de imports se necessário).
- [ ] ruff + mypy limpos.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
wc -l src/hefesto/daemon/ipc_server.py src/hefesto/daemon/ipc_handlers.py 2>/dev/null
.venv/bin/pytest tests/unit/test_ipc_server.py -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
# Smoke integração:
HEFESTO_FAKE=1 HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
```

## Fora de escopo

- Mudança de API pública IPC (métodos JSON-RPC, schemas) — preservar 100%.
- Migração para servidor NDJSON alternativo — preservar Unix socket + JSON-RPC 2.0.
- Unificar IPC + UDP — fora.

## Notas

Depende de ordem com AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01. Sugestão: executar RUMBLE-POLICY-DEDUP primeiro (que remove `_apply_rumble_policy` de dentro de `ipc_server.py`), o split fica mais limpo.
