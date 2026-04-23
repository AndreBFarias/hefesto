# CHORE-CI-REPUBLISH-TAGS-01 — Re-publicar v2.0.0 e v2.1.0 com artifacts

**Tipo:** chore (correção histórica).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 0.5 iteração.
**Dependências:** BUG-CI-RELEASE-MYPY-GATE-01 + FEAT-CI-RELEASE-FLATPAK-ATTACH-01.

---

**Tracking:** label `type:chore`, `ci`, `packaging`, `ai-task`, `status:ready`.

## Contexto

Como `release.yml` abortava no gate mypy, nenhum dos 5 últimos releases (v1.0.0, v1.1.0, v1.2.0, v2.0.0, v2.1.0) tem artifacts publicados no GitHub. Usuários que tentam `curl -LO .../v2.1.0/hefesto_2.1.0_amd64.deb` recebem 404.

Após BUG-CI-RELEASE-MYPY-GATE-01 desbloquear o pipeline, re-publicar manualmente as 2 tags mais recentes (v2.0.0 e v2.1.0). Para v1.x, decidir com usuário: re-publicar ou deixar como "histórico não empacotado".

## Decisão

Duas vias — não mutuamente exclusivas:

**Via A — Re-trigger via workflow_dispatch**:
- Adicionar `workflow_dispatch` com input `tag` ao `release.yml` (esta sprint faz isso se BUG-CI-RELEASE-MYPY-GATE-01 não fez).
- Rodar `gh workflow run release.yml -f tag=v2.1.0` e `gh workflow run release.yml -f tag=v2.0.0`.
- Pipeline re-builda artifacts da tag e cria release.

**Via B — Upload local dos artifacts já construídos**:
- O `.deb` v2.1.0 foi buildado localmente (`dist/hefesto_2.1.0_amd64.deb`, SHA256 `db56770a...`).
- Usar `gh release create v2.1.0 --title "Hefesto v2.1.0" --notes-file CHANGELOG.md dist/hefesto_2.1.0_amd64.deb` para publicar imediatamente mesmo sem CI.

Preferência: **via A após mypy-gate consertado**. Via B apenas como emergência se CI continua quebrado.

## Critérios de aceite

- [ ] `release.yml` tem trigger `workflow_dispatch` com input `tag` (string, required).
- [ ] `gh release view v2.0.0 --json assets` lista `.whl`, `.tar.gz`, `.AppImage`, `.deb`, `.flatpak`.
- [ ] `gh release view v2.1.0 --json assets` idem.
- [ ] `curl -IL https://github.com/AndreBFarias/hefesto/releases/download/v2.1.0/hefesto_2.1.0_amd64.deb` retorna `200 OK`.
- [ ] README.md links de download apontam para v2.1.0 e funcionam.
- [ ] Decisão sobre v1.x registrada em `docs/history/releases-nao-publicados.md` (histórico curto explicando causa + se os .deb locais foram preservados).

## Arquivos tocados

- `.github/workflows/release.yml` (input workflow_dispatch).
- `docs/history/releases-nao-publicados.md` (novo, histórico).
- README.md (verificar links de download).

## Proof-of-work runtime

```bash
gh workflow run release.yml -f tag=v2.0.0
gh workflow run release.yml -f tag=v2.1.0
gh run watch
gh release view v2.1.0 --json assets --jq '.assets[].name'
curl -IL https://github.com/AndreBFarias/hefesto/releases/download/v2.1.0/hefesto_2.1.0_amd64.deb | head -2
```

## Fora de escopo

- Re-publicar v1.0.0/v1.1.0/v1.2.0 (decisão do usuário — registrar o que ele pedir).
- Renumerar ou mover tags (destrutivo; não fazer).
