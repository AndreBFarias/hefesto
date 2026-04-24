# AUDIT-FINDING-IPC-DRAFT-RUMBLE-POLICY-01 — `profile.apply_draft` aplica política de rumble

**Origem:** achado 2 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** XS (≤1h). **Severidade:** alto.
**Tracking:** label `type:bug`, `ai-task`, `status:ready`.

## Contexto

`src/hefesto/daemon/ipc_server.py`:
- `_handle_rumble_set` (linhas 433-454) aplica política global de rumble via `_apply_rumble_policy`.
- `_handle_profile_apply_draft` seção rumble (linhas 649-658) chama `self.controller.set_rumble(weak=weak, strong=strong)` com valores brutos — bypassa `economia`/`balanceado`/`max`/`auto`/`custom`.

GUI → aba Rumble → "Aplicar perfil" usa `profile.apply_draft` → política é ignorada.

## Objetivo

No `_handle_profile_apply_draft`, substituir a chamada direta por escala via `_apply_rumble_policy` antes de enviar ao hardware, preservando também a persistência em `daemon.config.rumble_active = (weak, strong)` (valores **brutos**, conforme o handler `_handle_rumble_set` já faz).

## Critérios de aceite

- [ ] `_handle_profile_apply_draft` seção rumble: `eff_weak, eff_strong = _apply_rumble_policy(self.daemon, weak, strong)` seguido de `self.controller.set_rumble(weak=eff_weak, strong=eff_strong)`.
- [ ] `daemon_cfg.rumble_active = (weak, strong)` continua com valores **brutos** (para re-asserção do poll loop calcular mult de novo).
- [ ] Teste unitário novo em `tests/unit/test_ipc_server.py::test_apply_draft_rumble_aplica_policy`: mock daemon com `config.rumble_policy = "economia"` (0.3×), envia draft `{"rumble": {"weak": 200, "strong": 200}}`, confirma `controller.set_rumble` chamado com `(60, 60)`.
- [ ] Suite completa segue verde.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
.venv/bin/pytest tests/unit/test_ipc_server.py -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
```

## Fora de escopo

- Mudança de semântica da política "auto" (debounce de 5s) — fora de escopo, já coberta pela versão canônica em `_apply_rumble_policy`.
- Unificação das 3 cópias da lógica de política — coberta por `AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01`.
