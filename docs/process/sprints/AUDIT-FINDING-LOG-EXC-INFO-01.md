# AUDIT-FINDING-LOG-EXC-INFO-01 — Checklist: `exc_info=True` + edits pontuais (anti-pattern sistêmico)

**Origem:** achados 15, 16, 17, 18, 20 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** M (~4h, checklist). **Severidade:** baixo (observabilidade).
**Tracking:** label `type:observability`, `quality`, `ai-task`, `status:ready`.

## Contexto

A base tem **123 handlers `except ... Exception`** em `src/` — universalmente sem `exc_info=True`. Quando bug real acontece, debug fica cego. Além disso:
- 6+ locais com `except Exception: pass` silencioso em `backend_pydualsense.py`, `evdev_reader.py`, `subsystems/rumble.py`, `ipc_server.py`, `profiles/loader.py`.
- `connect_with_retry` em `connection.py:18-32` tem backoff fixo sem limite + loop sem checar `stop_event` durante sleep.
- `backend_pydualsense.py:75::is_connected` retorna default `True` se attr ausente — conservador seria `False`.

Esta sprint é **checklist agrupado** para resolver esses pontuais sem criar 10 sprints separadas.

## Objetivo

Checklist abaixo — executor escolhe subconjunto por tempo disponível, mas critérios de aceite mínimos ficam em "### Must-do" (10 itens).

### Must-do (obrigatório)

1. [ ] `daemon/lifecycle.py::_poll_loop` linha 345: adicionar `exc_info=True` ao `logger.warning("poll_read_failed", ...)`.
2. [ ] `daemon/connection.py::connect_with_retry` linha 29: `logger.warning("controller_connect_failed", ..., exc_info=True)`.
3. [ ] `daemon/ipc_server.py::_serve_client` linha 217-218: `logger.warning("ipc_client_error", err=str(exc), exc_info=True)`.
4. [ ] `daemon/ipc_server.py::_dispatch` linha 261: já usa `logger.exception` — confirmar e documentar.
5. [ ] `daemon/subsystems/plugins.py::_call_hook` linha 82: adicionar `exc_info=True` ao warn de plugin exception.
6. [ ] `core/backend_pydualsense.py:91-92, 117-118`: trocar `except Exception: pass` por `except AttributeError` (específico) OU adicionar `logger.debug("ds_state_read_falhou", exc_info=True); pass`.
7. [ ] `core/backend_pydualsense.py:75`: `is_connected` default `False` em vez de `True` para attr ausente.
8. [ ] `daemon/connection.py::connect_with_retry` linha 32: checar `daemon._stop_event.is_set()` dentro de `asyncio.sleep(backoff)` via `asyncio.wait_for` — permite shutdown durante retry loop.
9. [ ] `daemon/connection.py::connect_with_retry`: backoff exponencial com teto (ex.: `backoff = min(backoff * 2, 30.0)` após falha, reset para `reconnect_backoff_sec` no sucesso).
10. [ ] `core/rumble.py:201`, `daemon/subsystems/rumble.py:104`, `daemon/ipc_server.py:789-790`: adicionar `logger.debug("rumble_state_read_fallback", exc_info=True)` antes do `pass`.

### Nice-to-have (se tempo permitir)

11. [ ] Edits de itens 17, 19, 20, 21, 22, 23, 26 do relatório de auditoria (listados em "Achados 17, 19, 20, 21, 22, 23, 26 não geram sprint").
12. [ ] Normalizar `_json_rpc_error(req_id, CODE_INTERNAL, str(exc))` em `ipc_server.py:262` para não vazar `str(exc)` inteiro — usar `str(type(exc).__name__)` + mensagem genérica + log detalhado.

## Critérios de aceite

- [ ] 10 itens must-do aplicados.
- [ ] `grep -cn "exc_info=True" src/hefesto` aumenta em ≥ 8 (várias linhas antes tinham logger.warning sem flag).
- [ ] `backend_pydualsense.py::is_connected` retorna False (não True) se `connected` attr ausente — teste unitário confirma.
- [ ] `connect_with_retry` com backoff exponencial: teste em `tests/unit/test_daemon_connection.py` simula falhas consecutivas e confirma que o sleep cresce.
- [ ] Suite inteira segue verde; ruff + mypy limpos.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
grep -cn "exc_info=True" src/hefesto  # deve subir
.venv/bin/pytest tests/unit/test_daemon_connection.py tests/unit/test_poll_loop*.py -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
```

## Fora de escopo

- Revisar os 123 handlers exaustivamente — só os 10 críticos nesta sprint.
- Mudar formato de log (structlog → json) — fora.
- Adicionar observabilidade OpenTelemetry — fora.

## Notas

Esta sprint é oportunidade para cobrir os "edits prontos" que o relatório deixou fora de sprint (achados 17, 19, 20, 21, 22, 23, 26). Aplicar na mesma passagem de commit reduz churn.
