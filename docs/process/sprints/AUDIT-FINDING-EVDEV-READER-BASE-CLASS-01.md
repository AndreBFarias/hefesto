# AUDIT-FINDING-EVDEV-READER-BASE-CLASS-01 — Extrair `_EvdevReconnectLoop` base para eliminar duplicação

**Origem:** achado 8 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** M (≤6h). **Severidade:** médio.
**Tracking:** label `type:refactor`, `ai-task`, `status:ready`.

## Contexto

`src/hefesto/core/evdev_reader.py` tem ~100 LOC duplicadas entre `EvdevReader._run` (linhas 153-208) e `TouchpadReader._run` (linhas 392-450):
- Loop de reconnect com backoff exponencial (0.5s → 5s).
- Try/except em `InputDevice(path)` + `read_loop`.
- `_reset_*_on_disconnect` hook.
- Grace period de 100ms entre tentativas.

Futuro reader (IMU, gyro, haptic) vai copiar o mesmo padrão pela terceira vez.

## Objetivo

Introduzir classe base `_EvdevReconnectLoop` em `core/evdev_reader.py` encapsulando o loop + backoff + reconnect. Subclasses implementam hooks:
- `_find_device() -> Path | None` — estratégia de descoberta.
- `_handle_event(event, ecodes) -> None` — processamento de eventos.
- `_reset_on_disconnect() -> None` — limpeza de estado.
- `_log_prefix() -> str` — prefixo para log events (`evdev_*` ou `touchpad_reader_*`).

`EvdevReader` e `TouchpadReader` herdam da base, implementam hooks, preservam API pública (`start`, `stop`, `is_available`, `snapshot`/`regions_pressed`).

## Critérios de aceite

- [ ] Classe `_EvdevReconnectLoop` em `core/evdev_reader.py` com o padrão comum. Não é exportada (underscore).
- [ ] `EvdevReader` e `TouchpadReader` herdam e reduzem `_run` para chamadas dos hooks.
- [ ] LOC total de `core/evdev_reader.py` reduz em ≥50 linhas (antes: 479; esperado: ≤430).
- [ ] API pública preservada: `from hefesto.core.evdev_reader import EvdevReader, TouchpadReader, EvdevSnapshot, find_dualsense_evdev, find_dualsense_touchpad_evdev, DUALSENSE_VENDOR, DUALSENSE_PIDS` funciona idêntico.
- [ ] Testes em `tests/unit/test_evdev_reader.py` (e touchpad) seguem verde sem alteração de semântica.
- [ ] Cobertura de `core/evdev_reader.py` não regride — idealmente sobe (menos código).
- [ ] ruff + mypy verdes; suite passa.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
wc -l src/hefesto/core/evdev_reader.py  # <= 430
.venv/bin/pytest tests/unit/test_evdev_reader.py tests/unit/test_touchpad_reader.py -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
.venv/bin/pytest tests/unit --cov=src/hefesto/core/evdev_reader.py --cov-report=term-missing -q
# Smoke runtime com controle conectado (dev):
HEFESTO_SMOKE_DURATION=3.0 ./run.sh --smoke   # confirma input via evdev
```

## Fora de escopo

- Refactor de `find_dualsense_evdev`/`find_dualsense_touchpad_evdev` para compartilharem helper — aceitável para outra sprint.
- Mudança de semântica do backoff (ex.: jitter, timeout máximo diferente) — preservar exatamente.
- Introduzir um terceiro reader — fora de escopo.
