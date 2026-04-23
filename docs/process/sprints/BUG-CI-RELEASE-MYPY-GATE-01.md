# BUG-CI-RELEASE-MYPY-GATE-01 — release.yml aborta no mypy, nenhum release real desde v0.1.0

**Tipo:** bug P0 — CI/release quebrado há 5 tags.
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:bug`, `P0-urgent`, `ci`, `ai-task`, `status:ready`.

## Sintoma

`gh run list --workflow release.yml` mostra **5 failures consecutivas**: v1.0.0 (2026-04-21), v1.1.0, v1.2.0, v2.0.0 e v2.1.0 (2026-04-23). `gh release list` confirma que **só `v0.1.0` existe como release real** no GitHub — nenhum `.deb`, `.AppImage` ou wheel foi publicado desde então.

Causa raiz: job `build` em `.github/workflows/release.yml` linha 29 executa `mypy src/hefesto` como parte do step "Instalar e testar". `mypy` retorna ≥20 errors (GTK stubs ausentes, `unused type: ignore`, `backend_pydualsense.py:182` esperando `bits`/`bitmask` como kwargs do logger, `draft_config.py:144`/`:148` não aceita union em `tuple()`, plugin_api com generic `list` sem type arg). Step falha → jobs `appimage`, `deb`, `deb-install-smoke` e `github-release` ficam em `skipped`. Nada sobe no GitHub.

Observação: `ruff check` está verde localmente. O pipeline de CI é o único lugar que roda `mypy` hoje — não há pre-commit local que pegue isso, então a dívida acumulou silenciosamente.

## Decisão

Triagem em 3 opções ordenadas por pragmatismo:

**Opção A (recomendada)**: mover `mypy` do `release.yml` para `ci.yml` como job separado `typecheck` com `continue-on-error: true` por 30 dias (prazo para converter em gate). `release.yml` fica só com `ruff check + pytest tests/unit` — que realmente são bloqueadores de release. Vantagem: release sai em v2.1.0 hoje; débito `mypy` vira sprint própria sem bloquear usuários.

**Opção B**: fixar todos os mypy errors antes de destravar. Tempo: 4-6h. Sprint separada `CHORE-MYPY-CLEANUP-V22-01`. Release fica travado nesse período.

**Opção C**: `mypy --no-strict` ou ignorar módulos específicos via `overrides` em `pyproject.toml`. Meio-termo; corre risco de esconder regressões.

Escolha default **A**. Se usuário preferir B ou C, sprint reescrita; mas A libera v2.1.0 agora e endereça o débito técnico limpo num followup.

## Critérios de aceite

- [ ] `.github/workflows/release.yml`: step `mypy src/hefesto` removido do job `build`. `ruff check src/ tests/` e `pytest tests/unit -v` permanecem.
- [ ] `.github/workflows/ci.yml`: job novo `typecheck` com `mypy src/hefesto` e `continue-on-error: true`. Label do job inclui nota `débito técnico — gate rígido em 30 dias (sprint CHORE-MYPY-CLEANUP-V22-01)`.
- [ ] Sprint followup `CHORE-MYPY-CLEANUP-V22-01` criada (spec em `docs/process/sprints/`).
- [ ] Testar em branch de dev: `gh workflow run release.yml` via `workflow_dispatch` (se existir) ou empurrar tag de teste `v2.1.0-rc1`; workflow completa verde.
- [ ] Gates canônicos.

## Arquivos tocados

- `.github/workflows/release.yml`.
- `.github/workflows/ci.yml`.
- `docs/process/sprints/CHORE-MYPY-CLEANUP-V22-01.md` (spec nova, cria aqui).

## Proof-of-work runtime

```bash
# Simular localmente
.venv/bin/ruff check src/ tests/   # deve passar (passa hoje)
.venv/bin/pytest tests/unit -v     # deve passar (978 em baseline)

# Não rodar mypy no release.yml. Rodar em ci.yml como informational.

# Após push do fix, empurrar tag RC e ver workflow verde:
git tag v2.1.1-rc1
git push origin v2.1.1-rc1
gh run watch $(gh run list --workflow release.yml --limit 1 --json databaseId --jq '.[0].databaseId')
```

## Notas

- **Ação imediata pós-fix**: cria CHORE-CI-REPUBLISH-TAGS-01 para re-publicar v2.0.0 e v2.1.0 manualmente já que os CI daquelas tags abortaram sem publicar.
- Adicionar `workflow_dispatch` ao release.yml é recomendado — permite re-rodar release de tag antiga pelo gh cli sem precisar mover tag.

## Fora de escopo

- Consertar os ~20 mypy errors (vai para CHORE-MYPY-CLEANUP-V22-01).
- Migração para pyright/pyre.
