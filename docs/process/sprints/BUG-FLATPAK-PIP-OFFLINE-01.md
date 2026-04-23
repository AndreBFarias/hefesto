# BUG-FLATPAK-PIP-OFFLINE-01 — python-uinput via pip falha no sandbox offline

**Tipo:** bug (CI/packaging).
**Wave:** V2.2 — achado colateral de FEAT-KEYBOARD-EMULATOR-01 push.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:bug`, `ci`, `flatpak`, `ai-task`, `status:ready`.

## Sintoma

Run `24860360876` (2026-04-23) do workflow Flatpak Build falhou no step "Construir Flatpak" ao tentar baixar `python-uinput` via pip dentro do sandbox do flatpak-builder:

```
Running: pip3 install --prefix=/app --no-build-isolation python-uinput
WARNING: Retrying ... Failed to establish a new connection:
  [Errno -3] Temporary failure in name resolution
ERROR: Could not find a version that satisfies the requirement python-uinput
ERROR: No matching distribution found for python-uinput
```

Sandbox do `flatpak-builder` por design isola rede após os downloads iniciais de `sources:`. Qualquer `pip install` em build-commands precisa de wheels pré-baixadas como `sources`.

## Reprodução

```bash
cd ~/Desenvolvimento/Hefesto-DualSense_Unix
flatpak-builder --user --force-clean --repo=flatpak-repo \
  flatpak-build-dir flatpak/br.andrefarias.Hefesto.yml
# módulo python-uinput falha com -3 (name resolution)
```

Pré-existe a esta sessão — primeiro run falho registrado é `24852219105` (push do v2.1.0).

## Decisão

Duas opções:

**Opção A (recomendada):** declarar `python-uinput` como fonte `git` em `flatpak/br.andrefarias.Hefesto.yml` (`type: git`, `url: https://github.com/tuomasjjrasanen/python-uinput`, `tag: ...`). `flatpak-builder` baixa durante a fase de sources (com rede) e o build offline apenas compila.

**Opção B:** gerar wheel local via `pyproject-build` e declarar como `type: file` (path local). Mais controle, mais manutenção.

Preferência: **A**. Alinha com o padrão dos outros módulos Python do manifest.

## Critérios de aceite

- [ ] `flatpak/br.andrefarias.Hefesto.yml` declara `python-uinput` como `sources: [{type: git, url: ..., tag: ...}]`.
- [ ] `scripts/build_flatpak.sh` (se existir) continua funcionando localmente.
- [ ] Workflow Flatpak Build verde no próximo push.
- [ ] Gates canônicos verdes.

## Arquivos tocados

- `flatpak/br.andrefarias.Hefesto.yml` (declarar fonte de python-uinput).

## Proof-of-work

```bash
# Local build
bash scripts/build_flatpak.sh  # deve completar sem tentar pip online

# Remote validation — push em branch de teste ou re-run do workflow
gh workflow run flatpak.yml
gh run watch $(gh run list --workflow flatpak.yml --limit 1 --json databaseId --jq '.[0].databaseId')
```

## Fora de escopo

- Migrar para org.gnome.Platform//48 ou outra versão (ver sprint BLOCKED).
- Publicar no Flathub.
