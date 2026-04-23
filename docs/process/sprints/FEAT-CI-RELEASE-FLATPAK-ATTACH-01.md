# FEAT-CI-RELEASE-FLATPAK-ATTACH-01 — Anexar bundle Flatpak ao release no GitHub

**Tipo:** feat (CI).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 0.5 iteração.
**Dependências:** BUG-CI-RELEASE-MYPY-GATE-01 (release.yml precisa estar verde antes).

---

**Tracking:** label `type:feat`, `ci`, `packaging`, `ai-task`, `status:ready`.

## Contexto

Estado atual (2026-04-23):

- `.github/workflows/release.yml` job `github-release` anexa `.whl`, `.tar.gz`, `.AppImage`, `.deb`.
- `.github/workflows/flatpak.yml` builda `br.andrefarias.Hefesto.flatpak` e sobe como artifact de workflow (retention 30 dias) — **não** é anexado ao release GitHub.
- Usuário pediu: "a cada tag, o CI cria o release com .deb, flatpak e appimage".

## Decisão

Fundir os dois workflows em um pipeline de release coeso:

**Opção A (recomendada)**: `release.yml` ganha job `flatpak` espelhando `flatpak.yml`. `github-release` precisa de `[build, appimage, deb, deb-install-smoke, flatpak]`. O `flatpak.yml` fica para triggers de PR (validate-only) — ou é fundido/deletado.

**Opção B**: `flatpak.yml` dispara em tag; ao final, usa `gh release upload` para anexar ao release existente (criado por `release.yml`). Corrida de timing — jobs paralelos podem ambos tentar criar/anexar.

Escolha **A**: mais simples, sem race. `flatpak.yml` vira `validate-only` em PRs.

## Critérios de aceite

- [ ] `release.yml` ganha job `flatpak` que replica o `build-flatpak` de `flatpak.yml`:
  - Instala flatpak + flatpak-builder + runtime GNOME//45.
  - Builda wheel, builda bundle, exporta `.flatpak`.
  - Upload como artifact `flatpak-${version}`.
- [ ] Job `github-release` inclui `needs: flatpak` e baixa o artifact + adiciona `*.flatpak` ao `gh release create`.
- [ ] `flatpak.yml` reduzido a `validate-manifest` (só PRs e pushes em main); remove ou deixa `build-flatpak` condicionalizado (`if: github.event_name != 'push' || startsWith(github.ref, 'refs/tags')` → skip em tag, porque `release.yml` cuida).
- [ ] Test-tag `v2.1.1-rc2` completa o pipeline com `.whl`, `.tar.gz`, `.AppImage`, `.deb`, `.flatpak` anexados.
- [ ] README atualizado com seção "Download" mostrando os 4 formatos disponíveis.

## Arquivos tocados

- `.github/workflows/release.yml` (job `flatpak` novo + wire no `github-release`).
- `.github/workflows/flatpak.yml` (validate-only em PRs/main).
- `README.md` (seção Download atualizada).

## Proof-of-work runtime

```bash
# Tag de teste
git tag v2.1.1-rc2
git push origin v2.1.1-rc2
gh run watch

# Após workflow verde:
gh release view v2.1.1-rc2 --json assets --jq '.assets[].name'
# Esperado:
# hefesto-2.1.1rc2-py3-none-any.whl
# hefesto-2.1.1rc2.tar.gz
# Hefesto-2.1.1rc2-x86_64.AppImage
# hefesto_2.1.1rc2_amd64.deb
# br.andrefarias.Hefesto.flatpak
```

## Fora de escopo

- Publicar no Flathub (requer submissão upstream, sprint separada futura).
- Snap package.
- Signing dos artifacts.
