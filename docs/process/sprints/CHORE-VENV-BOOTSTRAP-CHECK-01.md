# CHORE-VENV-BOOTSTRAP-CHECK-01 — Script `dev-setup.sh` + check de sessão viva

**Tipo:** chore (DX).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 0.5 iteração.
**Dependências:** nenhuma. Operacionaliza lição L-21-4 de META-LESSONS-V21-BRIEF-01.

---

**Tracking:** label `type:chore`, `devex`, `ai-task`, `status:ready`.

## Contexto

Durante o ciclo V2.1 (AUDIT-V2-COMPLETE-01 + algumas sub-sprints) o executor rodou em sessões sem `.venv/` inicializado, `.venv/bin/pytest` inexistente. Confiou em "último baseline verde" em vez de reexecutar. Isso é débito silencioso — próxima sessão herda o mesmo ambiente quebrado.

Precisa de 2 peças:

1. **Script `scripts/dev-setup.sh`**: idempotente, recria `.venv` se ausente, instala `pip install -e ".[dev]"`, roda `.venv/bin/pytest --collect-only` como smoke, reporta contagem. Exit 0 se ok, 1 se falhou.
2. **Regra de execução**: todo spec V2.2+ cita `scripts/dev-setup.sh` no primeiro bullet do proof-of-work. BRIEF ganha linha na seção `[CORE] Contratos de runtime` dizendo "se `.venv/bin/pytest` não existe, rodar `scripts/dev-setup.sh` antes de qualquer gate".

## Decisão

Script bash simples — sem dependência de python externo, sem frameworks. Detecta se `.venv/` existe; se não, cria com `python3 -m venv .venv`. Se existe mas quebrado (pytest não importa), refaz. Sempre termina com `--collect-only` para confirmar que `hefesto` é importável.

## Critérios de aceite

- [ ] `scripts/dev-setup.sh` existe, é executável, idempotente.
- [ ] Rodar em ambiente limpo (`rm -rf .venv && bash scripts/dev-setup.sh`): cria `.venv`, instala deps, reporta `N tests collected`.
- [ ] Rodar em ambiente com `.venv` viva: retorna rápido, apenas confirma `pytest --collect-only` verde.
- [ ] Rodar em ambiente com `.venv` quebrada (simular `rm .venv/bin/pytest`): detecta, refaz, reporta.
- [ ] `VALIDATOR_BRIEF.md` seção `[CORE] Contratos de runtime` ganha linha:
  > Executor que chegar em sessão nova sem `.venv/bin/pytest` acessível DEVE rodar `bash scripts/dev-setup.sh` antes de qualquer gate. Execução cega é violação de L-21-4.
- [ ] README seção Contribuição menciona o script como primeiro passo.

## Arquivos tocados

- `scripts/dev-setup.sh` (novo).
- `VALIDATOR_BRIEF.md` (1 linha adicionada).
- `README.md` (seção Contribuição).

## Proof-of-work runtime

```bash
# Teste 1: ambiente limpo
rm -rf .venv
bash scripts/dev-setup.sh
# esperado: exit 0, mensagem final "Collected N tests"

# Teste 2: ambiente vivo
bash scripts/dev-setup.sh
# esperado: exit 0 rápido

# Teste 3: quebra induzida
rm -f .venv/bin/pytest
bash scripts/dev-setup.sh
# esperado: detecta, reinstala, exit 0
```

## Fora de escopo

- Dockerfile de dev.
- direnv / autoactivate via `.envrc`.
- pre-commit hook que detecta .venv quebrada (pode virar sprint futura se ajudar).
