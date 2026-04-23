# BUG-APPIMAGE-VERSION-NAME-01 — AppImage gerado com nome "1.0.0" em vez da tag

**Tipo:** bug (packaging/cosmético).
**Wave:** V2.2 — achado colateral de tag v2.2.0.
**Estimativa:** 0.25 iteração.

---

**Tracking:** label `type:bug`, `P2-medium`, `packaging`, `appimage`, `ai-task`, `status:ready`.

## Sintoma

Run do release v2.2.0 (`24861148981`) gerou `Hefesto-1.0.0-x86_64.AppImage` em vez de `Hefesto-2.2.0-x86_64.AppImage`. Usuário que baixa o asset vê `1.0.0` no nome do arquivo, confundindo.

## Causa raiz

`scripts/build_appimage.sh` usa versão hardcoded `1.0.0` no nome do arquivo de saída, não lê do `pyproject.toml` como `build_deb.sh` faz.

## Decisão

Mesmo padrão de `build_deb.sh`: ler versão de `pyproject.toml` via `tomllib`/`tomli` e injetar no nome do AppImage.

## Critérios de aceite

- [ ] `scripts/build_appimage.sh` lê versão do `pyproject.toml`.
- [ ] Nome do AppImage segue padrão `Hefesto-${VERSION}-x86_64.AppImage`.
- [ ] CI release gera asset com nome correto.
- [ ] README atualizado se citar o nome.

## Arquivos tocados

- `scripts/build_appimage.sh`.
- Eventualmente `.github/workflows/release.yml` se houver referência fixa.

## Fora de escopo

- Rename da imagem dentro do bundle (apenas nome do arquivo externo).
