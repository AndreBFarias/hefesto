# CHORE-FAKEPATH-01 — Mover FakeController para `src/hefesto/testing/`

**Tipo:** chore (refactor de layout).
**Modelo sugerido:** sonnet (mecânico, repetitivo).
**Estimativa:** 1 iteração.
**Dependências:** nenhuma. Pode ser aplicada em qualquer momento após o merge da V1.

---

**Tracking:** issue [#76](https://github.com/AndreBFarias/hefesto/issues/76) — fechada por PR com `Closes #76` no body.

## Contexto

Armadilha **A-06** descoberta durante BUG-FREEZE-01 (2026-04-21): `hefesto daemon start` com `HEFESTO_FAKE=1` falha com `ModuleNotFoundError: No module named 'tests'`. Causa:

- `src/hefesto/daemon/main.py:19` faz `from tests.fixtures.fake_controller import FakeController` quando a env var está setada.
- `tests/` não é instalado como módulo Python pelo `pip install -e .` — só `src/hefesto/` entra no pacote.
- `./run.sh --smoke` contorna adicionando `tests/` ao `PYTHONPATH` ad-hoc. Mas `hefesto daemon start --foreground` puro da CLI quebra.

Sintoma para o usuário: smoke via wrapper funciona, mas chamada direta da CLI (comum em debugging manual e em ambientes sem script wrapper) não funciona com FakeController.

## Decisão

Mover `FakeController` para dentro do pacote canônico em `src/hefesto/testing/fake_controller.py`. Motivação:

- Fake é utilitário legítimo de teste e runtime (smoke/debug), não fixture exclusiva de pytest.
- Padrão estabelecido em ecossistema Python: `django.test`, `pytest.testing`, `numpy.testing`, etc. — pacote expõe `X.testing` como módulo público-mas-convencional.
- Uma vez no pacote, qualquer caller resolve o import sem manipular PYTHONPATH.

## Critérios de aceite

- [ ] Criar diretório `src/hefesto/testing/` com `__init__.py`.
- [ ] Mover `tests/fixtures/fake_controller.py` para `src/hefesto/testing/fake_controller.py` (preservando histórico via `git mv`).
- [ ] `src/hefesto/testing/__init__.py` reexporta: `from hefesto.testing.fake_controller import FakeController`.
- [ ] Atualizar imports em:
  - `src/hefesto/daemon/main.py:19` → `from hefesto.testing import FakeController`
  - `src/hefesto/core/controller.py:77` (docstring) → atualizar referência.
  - `tests/unit/test_daemon_lifecycle.py:16`
  - `tests/unit/test_fake_controller_capture.py:10`
  - `tests/unit/test_controller.py:11`
  - `tests/unit/test_ipc_server.py:31`
  - `tests/unit/test_autoswitch.py:21`
  - `tests/unit/test_led_and_rumble.py:18`
  - `tests/unit/test_profile_manager.py:20`
  - `tests/unit/test_udp_server.py:16`
- [ ] `run.sh` — remover `PYTHONPATH=./src:./tests` do modo smoke, se existir (agora é desnecessário).
- [ ] `tests/fixtures/__init__.py` mantido (pode ter outras fixtures futuras); NÃO deletar o diretório.
- [ ] Unit tests continuam passando (sem adicionar novos).
- [ ] `hefesto daemon start --foreground` com `HEFESTO_FAKE=1` agora funciona sem PYTHONPATH extra.

## Proof-of-work esperado

```bash
# 1. Pytest permanece verde
.venv/bin/pytest tests/unit -q

# 2. Import direto funciona
HEFESTO_FAKE=1 timeout 3 .venv/bin/hefesto daemon start --foreground 2>&1 | head -5
# Esperado: daemon_starting / controller_connected transport=usb, SEM ModuleNotFoundError.

# 3. Grep de limpeza — zero referências velhas
grep -rn "tests.fixtures.fake_controller\|tests\.fixtures\.fake_controller" src/ tests/
# Esperado: vazio.

# 4. Lint + anonimato
./scripts/check_anonymity.sh
.venv/bin/ruff check src/ tests/
```

## Arquivos tocados (previsão)

- `src/hefesto/testing/__init__.py` (novo)
- `src/hefesto/testing/fake_controller.py` (movido de tests/fixtures/)
- `src/hefesto/daemon/main.py` (import)
- `src/hefesto/core/controller.py` (docstring)
- 8 arquivos em `tests/unit/` (imports)
- `tests/fixtures/fake_controller.py` (deletado)
- `run.sh` (opcional, remover PYTHONPATH)

## Fora de escopo

- Mover outros fixtures (`hid_capture_usb.bin`, perfis de teste).
- Criar testes novos.
- Reorganizar layout geral de `tests/`.

## Notas para o executor

- Usar `git mv tests/fixtures/fake_controller.py src/hefesto/testing/fake_controller.py` para preservar histórico.
- Rodar `pytest` antes E depois do move para garantir zero regressão.
- Se algum import for missed, `grep -rn "fake_controller"` varre o repo.
- `src/hefesto/testing/` seguirá padrão de pacote público — docstring do `__init__.py` deve declarar: "Utilitários de teste e runtime; `FakeController` para smoke e debug sem hardware."
