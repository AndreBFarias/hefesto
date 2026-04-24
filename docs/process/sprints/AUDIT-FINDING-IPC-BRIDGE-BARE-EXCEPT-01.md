# AUDIT-FINDING-IPC-BRIDGE-BARE-EXCEPT-01 — Extrair helper `_safe_call` + logs debug em `ipc_bridge.py`

**Origem:** achado 9 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** S (≤3h). **Severidade:** médio.
**Tracking:** label `type:refactor`, `ai-task`, `status:ready`.

## Contexto

`src/hefesto/app/ipc_bridge.py:142-282` tem 13 wrappers que seguem o padrão:
```python
def X(...) -> bool:
    try:
        _run_call(...)
        return True
    except Exception:
        return False
```

Padrão engole TUDO: daemon offline, timeout, validation error (pydantic), protocol error, bug interno. GUI recebe `False` sem distinguir caso. Usuário reclama "não funciona" e não há trilha no log.

## Objetivo

Introduzir helper interno `_safe_call(method, params, timeout)` que:
1. Captura apenas `(FileNotFoundError, ConnectionError, IpcError, OSError)` — erros de transporte/disponibilidade.
2. Loga `debug` para esses (not warning — esperados quando daemon offline).
3. Deixa outras exceções subirem — bug real.
4. Retorna tupla `(success: bool, result: Any | None)` ou apenas bool (decisão no spec).

Refatorar os 13 wrappers para usar o helper — cada um fica em 2-3 linhas.

## Critérios de aceite

- [ ] Função `_safe_call` existe em `ipc_bridge.py`, com assinatura clara.
- [ ] 13 wrappers públicos (profile_switch, trigger_set, led_set, rumble_set, rumble_stop, rumble_passthrough, rumble_policy_set, rumble_policy_custom, player_leds_set, mouse_emulation_set, apply_draft, profile_list, daemon_status_basic, daemon_state_full — conferir) usam `_safe_call` ou `_run_call + try/except` específico.
- [ ] Cada wrapper captura só `(FileNotFoundError, ConnectionError, IpcError, OSError)` ou delega ao `_safe_call`.
- [ ] Testes em `tests/unit/test_ipc_bridge.py`: (1) daemon offline retorna False + log debug; (2) daemon online retorna True; (3) exceção inesperada (ex.: ValueError) propaga — não é silenciada.
- [ ] Suite total segue verde; ruff + mypy verdes.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
.venv/bin/pytest tests/unit/test_ipc_bridge.py -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
grep -cn "except Exception:" src/hefesto/app/ipc_bridge.py  # deve cair de 13+ para <= 2
```

## Fora de escopo

- Mudança de API pública dos 13 wrappers — preservar bool return.
- Refactor do `_run_call` (executor lazy, timeout default) — preservar.
- Log formato/key naming — manter convenção existente.
