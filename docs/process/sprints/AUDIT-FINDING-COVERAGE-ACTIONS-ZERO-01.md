# AUDIT-FINDING-COVERAGE-ACTIONS-ZERO-01 — Cobertura de actions/ GUI — padrão `_FakeMixin` + GTK opt-in

**Origem:** achados 12, 14, 24 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** L (2 iterações, ~8h). **Severidade:** médio.
**Tracking:** label `type:test`, `quality`, `ai-task`, `status:ready`.

## Contexto

Módulos em `src/hefesto/app/actions/` estão em 0% de cobertura:
- `rumble_actions.py` 171 LOC
- `triggers_actions.py` 223 LOC
- `firmware_actions.py` 178 LOC
- `emulation_actions.py` 86 LOC
- `trigger_specs.py` 50 LOC

`app/tray.py` 132 LOC, `cli/cmd_tray.py` 59 LOC também zerados. Outros módulos de actions em 20-50% cov. `utils/single_instance.py` 55%, `daemon/subsystems/keyboard.py` 60%, `daemon/subsystems/mouse.py` 53% — branches de erro não exercitadas em código crítico (segurança, wire-up).

Também: `tests/unit/test_input_actions.py::_FakeMixin` usa `__get__` dinâmico para rodar o mixin sem herdar GTK. Padrão funcional mas pode mascarar bugs quando mixin depende de estado de outros mixins do MRO.

## Objetivo

1. Aplicar o padrão `_FakeMixin` (de `test_input_actions.py`) para criar testes unitários para pelo menos os 3 maiores actions modules em 0%: `rumble_actions.py`, `triggers_actions.py`, `firmware_actions.py`. Foco em lógica pura (sem depender de widgets reais).

2. Adicionar testes de integração com GTK real marcados `@pytest.mark.skipif(not GTK_AVAILABLE)` para `InputActionsMixin` — complementa `_FakeMixin` cobrindo widget real.

3. Aumentar cobertura de `utils/single_instance.py` (branches de erro: fd leak, flock contention, PID inválido) e `daemon/subsystems/mouse.py` e `keyboard.py` (falhas de uinput, fallback sem evdev).

4. Meta: cobertura total sobe de 63% → ≥70%.

## Critérios de aceite

- [ ] Novo arquivo `tests/unit/test_rumble_actions.py` com ≥5 testes usando `_FakeMixin` pattern. Cobre: `on_rumble_test_left_pressed`, `on_rumble_stop`, `on_rumble_policy_changed`, `on_rumble_slider_changed`, `_apply_rumble_to_draft`.
- [ ] Novo arquivo `tests/unit/test_triggers_actions.py` com ≥5 testes. Cobre: seleção de preset, aplicação no draft, mudança de side, preview.
- [ ] Novo arquivo `tests/unit/test_firmware_actions.py` com ≥3 testes (ou smoke de non-crash se feature for opcional).
- [ ] Cobertura `rumble_actions.py` ≥ 50%, `triggers_actions.py` ≥ 50%, `firmware_actions.py` ≥ 40%.
- [ ] `test_input_actions.py` ganha 2-3 testes marcados `@pytest.mark.skipif` com `GTK_AVAILABLE` — exercita o mixin contra `Gtk.ListStore` / `Gtk.TreeView` real.
- [ ] Cov de `utils/single_instance.py` ≥ 70% (sobe de 55%). Testes para branch de PID reciclado (se AUDIT-FINDING-SINGLE-INSTANCE-PID-RECYCLE-01 já mergeado, incluir integração).
- [ ] Cov total dos testes sobe de 63% para ≥ 70%.
- [ ] Suite completa segue verde; ruff + mypy limpos.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
.venv/bin/pytest tests/unit/test_rumble_actions.py tests/unit/test_triggers_actions.py \
    tests/unit/test_firmware_actions.py tests/unit/test_input_actions.py tests/unit/test_single_instance.py \
    -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/pytest tests/unit --cov=src/hefesto --cov-report=term 2>&1 | tail -30
# Esperado: TOTAL >= 70%
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
```

## Fora de escopo

- Testar `app/tray.py` (132 LOC 0%) — AppIndicator + GTK tray, difícil em headless. Vira sprint separada com xvfb-run ou skip marker.
- Testar `cli/cmd_tray.py` — idem.
- Cobrir 100% — meta 70% é realista.
- Refactor dos actions files para facilitar teste (extrair lógica pura) — sprint futura se 50% não for atingido.
