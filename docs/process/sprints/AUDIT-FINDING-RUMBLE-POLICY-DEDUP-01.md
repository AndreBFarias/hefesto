# AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01 — Unificar `_effective_mult` (core) + eliminar duplicatas

**Origem:** achado 5 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** M (≤6h). **Severidade:** alto (drift risk).
**Tracking:** label `type:refactor`, `ai-task`, `status:ready`.

## Contexto

Três superfícies reimplementam a mesma lógica de multiplicador de política de rumble:

1. `src/hefesto/core/rumble.py:51-110` — `_effective_mult` (canônica; loga warn em política desconhecida).
2. `src/hefesto/daemon/subsystems/rumble.py:34-78` — `_effective_mult_inline` (sem log no fallback, ordem dos ifs trocada).
3. `src/hefesto/daemon/ipc_server.py:765-816` — `_apply_rumble_policy` wrapper que já importa `_effective_mult` do core diretamente — prova que a alegação "evitar import circular" da versão inline é **falsa na prática**.

Além disso: `ipc_server.py:809-812` faz writeback direto em `rumble_engine._last_auto_mult` e `._last_auto_change_at` — acesso de campos privados por fora, violando encapsulamento.

## Objetivo

1. Deletar `_effective_mult_inline` de `daemon/subsystems/rumble.py`.
2. Em `reassert_rumble` (mesma file), importar `_effective_mult` de `hefesto.core.rumble` e usar.
3. Em `RumbleEngine` (core/rumble.py), adicionar método público `update_auto_state(mult: float, change_at: float) -> None` que seta os campos privados. Substituir os writes diretos em `ipc_server.py:809-812` por essa chamada.
4. Remover a reexportação de `_effective_mult_inline` em `lifecycle.py:41-42, 433, 437`.
5. Ajustar testes que importam `_effective_mult_inline` para importar `_effective_mult`.

## Critérios de aceite

- [ ] `grep -rn "_effective_mult_inline" src/` → vazio (função deletada).
- [ ] `_effective_mult` único. Importado por `reassert_rumble` (subsystems/rumble.py) e `_apply_rumble_policy` (ipc_server.py).
- [ ] `RumbleEngine.update_auto_state(mult, change_at)` método público existe e é usado pelo `_apply_rumble_policy`.
- [ ] `grep -rn "rumble_engine\._last_auto" src/` → só aparece dentro de `RumbleEngine` (self._last_auto_mult/change_at) — writeback externo zerado.
- [ ] Testes existentes em `tests/unit/test_rumble_policy.py` e `tests/unit/test_subsystem_rumble.py` passam sem mudança de semântica. Novos testes para `update_auto_state` isolado.
- [ ] `lifecycle.py` não reexporta mais `_effective_mult_inline`. Reexportações em `__all__` atualizadas.
- [ ] ruff + mypy verdes; suite passa.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
grep -rn "_effective_mult_inline" src/       # vazio
grep -rn "rumble_engine\._last_auto" src/    # nada fora de core/rumble.py
.venv/bin/pytest tests/unit/test_rumble_policy.py tests/unit/test_subsystem_rumble.py -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
```

## Fora de escopo

- Refactor maior do `RumbleEngine` (ex.: separar política de throttle) — adiar.
- Alterar semântica da política `auto` (debounce, thresholds) — preservar comportamento atual.
- Testes de integração com hardware real — smoke existente já cobre.

## Notas

Cuidado com o comentário em `subsystems/rumble.py:11-12` que diz "reexportada por lifecycle.py para preservar backcompat com test_rumble_policy.py". Confirmar que o teste atual importa de `core/rumble.py` direto (é o único caminho canônico após o refactor). Se o teste importava da reexportação, ajustar o import.
