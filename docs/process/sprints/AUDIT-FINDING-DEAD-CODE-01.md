# AUDIT-FINDING-DEAD-CODE-01 — Remover dead code: `profiles/autoswitch.py::start_autoswitch` + `_noop` + sentinels em `validar-acentuacao.py`

**Origem:** achados 7 e 21 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** XS (≤1h). **Severidade:** médio.
**Tracking:** label `type:cleanup`, `ai-task`, `status:ready`.

## Contexto

1. `src/hefesto/profiles/autoswitch.py:120-135` (função `start_autoswitch`) e `:138-142` (helper `_noop`) nunca são importados em código de produção. Grep confirma:
   ```
   $ grep -rn "from hefesto.profiles.autoswitch" src/ tests/
   (vazio)
   ```
   O wire-up real usa `daemon/subsystems/autoswitch.py::start_autoswitch` (mesmo nome, assinatura diferente).

2. `scripts/validar-acentuacao.py:319, 376, 380, 381` tem 4 entradas sentinel em `_PARES` que têm `errada == correta` — o loop de dedup (linha 389) rejeita essas, então não afetam o comportamento. São "doc-in-code" para lembrar que as palavras não devem entrar no dicionário.

## Objetivo

1. Deletar `profiles/autoswitch.py::start_autoswitch` e `_noop`. Remover do `__all__`.
2. Em `validar-acentuacao.py`, converter os 4 sentinels num set explícito `NOT_WORDS_ALREADY_CORRECT` com comentário explicativo, OU deletar os sentinels e documentar em comentário separado.

## Critérios de aceite

- [ ] `profiles/autoswitch.py`: função `start_autoswitch` e `_noop` removidas. `__all__` sem essas entradas. Arquivo continua tendo `AutoSwitcher`, `DEFAULT_POLL_INTERVAL_SEC`, `DEFAULT_DEBOUNCE_SEC`, `WindowReader`.
- [ ] Coverage de `profiles/autoswitch.py` sobe para ~100% (linhas 128-142 estavam no miss list).
- [ ] `validar-acentuacao.py`: sentinels tratados. Se deletados, adicionar comentário `# Palavras já corretas sem acento — não adicionar a _PARES: menor, depois, categoria, prioridade`.
- [ ] Testes de `test_validar_acentuacao.py` continuam passando — nenhuma regressão.
- [ ] Suite total passa verde; ruff + mypy limpos.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
grep -rn "start_autoswitch\|_noop" src/hefesto/profiles/  # vazio
.venv/bin/pytest tests/unit/test_validar_acentuacao.py -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
```

## Fora de escopo

- Refactor maior de `validar-acentuacao.py` para usar regex combinado alternation (melhoria de perf) — sprint separada futura.
- Revisão de outros módulos para dead code — escopo de auditoria seguinte.
