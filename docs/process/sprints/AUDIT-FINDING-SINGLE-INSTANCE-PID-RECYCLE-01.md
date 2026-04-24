# AUDIT-FINDING-SINGLE-INSTANCE-PID-RECYCLE-01 — Verificar `/proc/<pid>/comm` antes de matar predecessor

**Origem:** achado 10 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** S (≤3h). **Severidade:** médio (segurança defesa em profundidade).
**Tracking:** label `type:security`, `ai-task`, `status:ready`.

## Contexto

`src/hefesto/utils/single_instance.py::acquire_or_takeover` (linhas 87-113, 125-133) lê PID do pid file, confirma `is_alive` (que só checa `os.kill(pid, 0)` sem ESRCH), e envia SIGTERM. Se o PID foi reciclado pelo kernel após crash do daemon hefesto, o SIGTERM vai para outro processo do mesmo user (firefox, python script pessoal).

Janela real em Linux moderno com `pid_max=4194304` é pequena, mas princípio de defesa em profundidade: confirmar que o PID ainda é hefesto antes de matar.

## Objetivo

Introduzir helper `_is_hefesto_process(pid: int) -> bool` que lê `/proc/<pid>/comm` (ou cmdline) e confirma que o process name contém `hefesto` (ou é `python3` com `hefesto.app.main`/`hefesto daemon` em cmdline). Chamar antes de `_terminate_predecessor`.

Se o predecessor NÃO é hefesto:
- Logar warning `single_instance_pid_reciclado` com `expected_pattern` e `actual_comm`.
- Tratar pid file como órfão: apagar, prosseguir com aquisição sem matar.

## Critérios de aceite

- [ ] Helper `_is_hefesto_process(pid: int) -> bool` em `utils/single_instance.py`.
- [ ] `_terminate_predecessor` checa `_is_hefesto_process` antes de SIGTERM. Se False, loga warning e retorna (sem sinalizar).
- [ ] `acquire_or_takeover` e `acquire_or_bring_to_front` usam o novo fluxo — PID não-hefesto é tratado como órfão.
- [ ] Leitura de `/proc/<pid>/comm` é defensiva: `FileNotFoundError`, `PermissionError` → retorna False (conservador).
- [ ] Testes em `tests/unit/test_single_instance.py`:
  - `test_takeover_ignora_pid_reciclado` — simula pid file apontando para PID de processo não-hefesto (mock `_is_hefesto_process`), confirma que SIGTERM **não** é enviado.
  - `test_takeover_mata_predecessor_hefesto` — mock `_is_hefesto_process = True`, confirma SIGTERM enviado.
  - `test_is_hefesto_process_comm_ok` — cria arquivo fake `/tmp/.../comm` com "hefesto\n", confirma True.
  - `test_is_hefesto_process_noent` — pid inválido → False.
- [ ] Cov de `utils/single_instance.py` sobe de 55% para >70%.
- [ ] Suite completa segue verde.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
.venv/bin/pytest tests/unit/test_single_instance.py -v -q
.venv/bin/pytest tests/unit --cov=src/hefesto/utils/single_instance.py --cov-report=term-missing -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
```

## Fora de escopo

- Revisar `acquire_or_bring_to_front` na mesma sprint (mesmo pattern, apenas se tempo permitir).
- Mudar semântica de takeover (ex.: exigir confirmação do user) — fora.
- Adicionar uuid ou lock token — fora.

## Notas

`/proc/<pid>/comm` tem limite de 16 chars. "hefesto" cabe. "python3" também cabe mas precisaria cross-check com cmdline. Para daemon rodando como `hefesto daemon start`, `comm` = `hefesto`. Para GUI `hefesto.app.main`, `comm` = `python3` (precisa cmdline). Cobrir ambos casos.
