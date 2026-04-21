# BUG-ANON-01 — `VALIDATOR_BRIEF.md` viola `check_anonymity.sh`

**Tipo:** fix (conformidade com anonimato obrigatório).
**Wave:** fora de wave (achado colateral durante BUG-UDP-01).
**Estimativa:** 1 iteração de executor, diff mínimo.
**Dependências:** nenhuma.

---

## Contexto

Durante o proof-of-work de `BUG-UDP-01`, ao rodar `./scripts/check_anonymity.sh`, o script retornou exit=1 com as seguintes violações:

```
VALIDATOR_BRIEF.md:21:2. `~/.claude/CLAUDE.md` — extensões: meta-regras 9.6–9.8, validação visual 13–14, ciclo de sprint §15.
VALIDATOR_BRIEF.md:62:2. **claude-in-chrome MCP** — só se a sprint for validada via navegador.
```

Meta-regra §2 (CLAUDE.md global) proíbe menção a "Claude" em qualquer arquivo não-excluído do check. `VALIDATOR_BRIEF.md` está na raiz do repo e NÃO aparece na exclusion list (`LICENSE`, `NOTICE`, `CHANGELOG.md`, `docs/process/**`, `docs/history/**`, `tests/fixtures/**`).

Origem: commit `835964f` ("chore: VALIDATOR_BRIEF + specs de sprints de correção pós-PR #67"). O arquivo foi introduzido sem passar pelo gate de anonimato.

---

## Critérios de aceite

- [ ] `./scripts/check_anonymity.sh` retorna vazio e exit=0.
- [ ] Escolher uma abordagem:
  - (a) Remover as menções a `~/.claude/CLAUDE.md` e `claude-in-chrome MCP` do `VALIDATOR_BRIEF.md`, substituindo por formulações neutras (ex.: "manual global do agente", "MCP do navegador").
  - (b) Mover `VALIDATOR_BRIEF.md` para `docs/process/` (onde o anonimato é relaxado) e manter um link simbólico (ou equivalente) na raiz — atenção ao check `scripts/check_anonymity.sh` se seguir links.
  - (c) Adicionar `VALIDATOR_BRIEF.md` à exclusion list do script (explicitar que o BRIEF é meta-processo, análogo a `docs/process/`). Decisão recomendada.
- [ ] Suite `tests/unit` permanece verde (≥290 passing).

---

## Proof-of-work esperado

```bash
./scripts/check_anonymity.sh && echo "anonimato OK"
.venv/bin/pytest tests/unit -q
```

---

## Arquivos tocados (previsão)

- `VALIDATOR_BRIEF.md` — editar linhas 21 e 62, OU
- `scripts/check_anonymity.sh` — adicionar `VALIDATOR_BRIEF.md` à exclusion list.

---

## Fora de escopo

- Outros arquivos do repo (nenhuma outra violação conhecida no check atual).
- Re-estruturar a política de anonimato.

---

## Notas para o executor

- Achado durante `BUG-UDP-01`. Não foi fixado inline (meta-regra 9.7: scope atômico).
- A linha 62 menciona uma ferramenta MCP real, então (c) é provavelmente a abordagem certa — análoga a `docs/process/` que já é whitelisted.
