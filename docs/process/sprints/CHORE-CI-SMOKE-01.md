# CHORE-CI-SMOKE-01 — Rodar `./run.sh --smoke` no CI

**Tipo:** chore (CI).
**Wave:** V1.1.
**Estimativa:** 0.5 iteração.
**Dependências:** CHORE-FAKEPATH-01 (para que o daemon start + fake funcione sem PYTHONPATH hack).

---

## Contexto

`.github/workflows/ci.yml` hoje roda `ruff check`, `mypy`, `pytest tests/unit`. Não roda smoke de runtime-real (meta-regra 9.8). Um refactor pode passar nos testes unitários mas quebrar o boot do daemon — só pegaria num usuário real. Com `FakeController` em `src/hefesto/testing/` (após CHORE-FAKEPATH-01), dá pra rodar `./run.sh --smoke` em CI sem hardware.

## Decisão

Adicionar job `runtime-smoke` no `ci.yml`:

```yaml
runtime-smoke:
  runs-on: ubuntu-latest
  needs: lint-test
  strategy:
    matrix:
      transport: [usb, bt]
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - name: Install deps
      run: |
        sudo apt-get update
        sudo apt-get install -y libhidapi-dev libudev-dev libxi-dev
        pip install -e ".[dev]"
    - name: Smoke transport=${{ matrix.transport }}
      run: |
        HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=${{ matrix.transport }} \
          HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke ${{ matrix.transport == 'bt' && '--bt' || '' }}
    - name: Assert no AssertionError in logs
      run: |
        ! grep -q "AssertionError\|Traceback" /tmp/hefesto_smoke_*.log 2>/dev/null
```

## Critérios de aceite

- [ ] Job `runtime-smoke` no `ci.yml`, matrix usb+bt.
- [ ] Falha do job é bloqueante do merge.
- [ ] `run.sh --smoke` salva log em `/tmp/hefesto_smoke_<transport>.log` (adicionar `tee` ao script).
- [ ] Passa em CI primeira vez (validar com PR dummy).

## Arquivos tocados (previsão)

- `.github/workflows/ci.yml`
- `run.sh` (adicionar `tee` no smoke)

## Fora de escopo

- Testes integration com hardware real (sem runner físico).
- Jobs de distros distintas (cobrir Ubuntu 22.04 é suficiente inicial).
