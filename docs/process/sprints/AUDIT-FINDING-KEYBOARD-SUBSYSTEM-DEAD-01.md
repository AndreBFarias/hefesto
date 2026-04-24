# AUDIT-FINDING-KEYBOARD-SUBSYSTEM-DEAD-01 — Deletar `KeyboardSubsystem` classe paralela não cabeada

**Origem:** achado 6 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** XS (≤1h). **Severidade:** alto (débito arquitetural, potencial regressão futura).
**Tracking:** label `type:cleanup`, `ai-task`, `status:ready`.

## Contexto

`src/hefesto/daemon/subsystems/keyboard.py:129-164` define `KeyboardSubsystem` com `start(ctx)`/`stop()`/`is_enabled()` — mas o wire-up real no `Daemon` usa as funções top-level `start_keyboard_emulation(daemon)` e `stop_keyboard_emulation(daemon)`. A classe só aparece em `__all__` e no teste `tests/unit/test_keyboard_wire_up.py`. Nenhum código de produção instancia.

API paralela inativa: se no futuro alguém mover o wire-up para usar o protocolo `Subsystem`, a classe vai entrar ativa e divergir silenciosamente do comportamento atual das funções.

## Objetivo

Opção recomendada: **(b) deletar `KeyboardSubsystem`**.

1. Remover classe `KeyboardSubsystem` de `src/hefesto/daemon/subsystems/keyboard.py`.
2. Remover `"KeyboardSubsystem"` do `__all__` do mesmo arquivo.
3. Remover ou reescrever `tests/unit/test_keyboard_wire_up.py` — testes que dependiam da classe migram para testar `start_keyboard_emulation`/`stop_keyboard_emulation` diretamente (se ainda relevantes).
4. Se `test_keyboard_wire_up.py` cobre apenas a classe, pode ser deletado e a cobertura passa para `test_keyboard_emulator.py` (já existente).

## Critérios de aceite

- [ ] `grep -rn "KeyboardSubsystem" src/ tests/` → vazio (classe, import e menção removidos).
- [ ] `test_keyboard_wire_up.py` adaptado ou removido; se removido, sua cobertura correspondente não regride (confirmar via `pytest --cov=src/hefesto/daemon/subsystems/keyboard.py --cov-report=term-missing`).
- [ ] Nada em `src/hefesto/daemon/lifecycle.py` ou `connection.py` refere `KeyboardSubsystem`.
- [ ] Suite passa; ruff + mypy limpos.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
grep -rn "KeyboardSubsystem" src/ tests/  # vazio
.venv/bin/pytest tests/unit/test_keyboard_emulator.py tests/unit/test_keyboard_wire_up.py -v -q
.venv/bin/pytest tests/unit --cov=src/hefesto/daemon/subsystems/keyboard.py --cov-report=term-missing -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
```

## Fora de escopo

- Opção (a) — migrar wire-up para usar `KeyboardSubsystem` via `PluginsSubsystem` registry. Seria refactor maior; preferível a remoção simples.
- Refactor de outros subsystems que tenham mesmo padrão paralelo — auditoria futura.
