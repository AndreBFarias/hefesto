# BUG-DEB-SMOKE-PYDANTIC-V2-NOBLE-01 — Smoke do .deb falha em Noble também (pydantic v1)

**Tipo:** bug (packaging/CI).
**Wave:** V2.2.2 — patch da v2.2.1.
**Estimativa:** 0.5 iteração.
**Dependências:** BUG-DEB-PYDANTIC-V2-UBUNTU-22-01 (74, MERGED). Descoberto em 2026-04-24 no run `24864996747` ao disparar release v2.2.1.

---

**Tracking:** label `type:bug`, `packaging`, `ci`, `deb`, `ai-task`, `status:ready`.

## Sintoma

Após a sprint 74 declarar `python3-pydantic (>= 2.0)` no `control` e migrar o smoke job de `ubuntu-22.04` para `ubuntu-24.04`, o release v2.2.1 continuou falhando no mesmo job com:

```
hefesto : Depends: python3-pydantic (>= 2.0) but it is not going to be installed
E: Unable to correct problems, you have held broken packages.
```

## Causa raiz

Premissa da sprint 74 estava **errada**: Ubuntu 24.04 (Noble) **também empacota `python3-pydantic` versão 1.x** (mais especificamente `1.10.17-1build1`), não v2.x como assumi ao escrever o spec.

Ubuntu que entrega pydantic v2 nativo no apt:
- **Plucky (25.04)** em diante.
- Debian trixie/sid.

Quase nenhum runner de GitHub Actions atualmente é plucky.

## Consequência

`deb-install-smoke` falha → `github-release` job skipped → artifacts não publicados via workflow.

**Workaround aplicado em 2026-04-24** (após v2.2.1): release manual via `gh release create v2.2.1 <artifacts>` a partir do run 24864996747. Idêntico ao que foi feito em v2.2.0.

Este é o segundo release consecutivo onde o smoke bloqueia github-release e exige upload manual. Débito crescente.

## Decisão

Três opções, em ordem de preferência do implementador:

### Opção A (recomendação) — Remove constraint de versão do control, adiciona check runtime

1. `packaging/debian/control`: `Depends: ..., python3-pydantic, ...` (sem `(>= 2.0)`).
2. `src/hefesto/__init__.py` (ou novo `src/hefesto/_version_check.py`): ao import, checar `pydantic.VERSION` e imprimir warning em stderr se `< 2.0`, sugerindo `pip install --user 'pydantic>=2'`.
3. `release.yml` smoke volta para `ubuntu-22.04`, adiciona step `pip install --user 'pydantic>=2'` **antes** do `apt install`, e confirma import.

### Opção B — Migrar smoke para `ubuntu-25.04` (plucky)

Simples conceitualmente, mas runner plucky pode não estar disponível em todos os orgs/regiões. GitHub demora a promover ubuntu-latest.

### Opção C — Vendorizar pydantic v2 no `.deb`

Complexo: requer `pip install` em staging + cópia para `/opt/hefesto/vendor/` + `PYTHONPATH` no entrypoint. Maior blast radius.

## Critérios de aceite

- [ ] Workflow run triggered por push de tag ou workflow_dispatch completa sem `deb-install-smoke` falhar.
- [ ] Asset `hefesto_X.Y.Z_amd64.deb` publicado via `github-release` job (não manual).
- [ ] Usuário em Ubuntu 22.04 ou 24.04 consegue `sudo apt install ./hefesto_*.deb` sem erro (com workaround pip documentado no README da sprint 74).
- [ ] `hefesto version` após apt install retorna versão correta (não crasha por ImportError).
- [ ] Gates canônicos.

## Arquivos tocados (se opção A)

- `packaging/debian/control`.
- `.github/workflows/release.yml` (volta smoke para 22.04 + pip install step).
- `src/hefesto/__init__.py` (check pydantic version).

## Proof-of-work

```bash
# Local
bash scripts/build_deb.sh
dpkg-deb -I dist/hefesto_*.deb | grep -i pydantic
# esperado: Depends: ... python3-pydantic (sem constraint)

# CI
gh workflow run release.yml -f tag=v2.2.2
# esperado: todos os 5 jobs success, inclusive deb-install-smoke
gh release view v2.2.2 --json assets --jq '.assets | length'
# esperado: 5
```

## Fora de escopo

- Forçar usuário em v2.2.2+ a instalar pydantic manualmente (mensagem clara é suficiente).
- Testar o `.deb` em derivativas não-Ubuntu (Pop!\_OS, Mint).
- Remover fallback no `__init__.py` (sprint 73 / CHORE-VERSION-SYNC-GATE-01).

## Notas

Lição aprendida: sprint 74 fechou o ciclo de "pydantic v1" em Jammy mas não validou empiricamente em Noble. Antes de qualquer sprint de packaging que assume versão de lib do sistema, rodar `apt-cache policy python3-<pacote>` em 2+ releases alvo.
