# FEAT-DEB-PACKAGE-01 — Pacote .deb para Ubuntu / Pop!_OS / Debian

**Tipo:** feat (packaging).
**Wave:** V1.2.
**Estimativa:** 2 iterações.
**Dependências:** nenhuma. Complementar a AppImage (já feita, PR #62) e FEAT-FLATPAK-BUNDLE-01 (#81).

---

**Tracking:** issue a criar.

## Motivação

Usuário em 2026-04-22:

> talvez falte lançar em flatpak né? E deb e app image?

AppImage: feito (PR #62). Flatpak: spec #81, pendente. **`.deb`**: sem spec. Pop!_OS/Ubuntu/Mint/Debian são ~60% da base Linux desktop relevante pro Hefesto — distribuir via `.deb` é o caminho mais natural (`apt install ./hefesto_1.1.0_amd64.deb`).

## Decisão

Pacote `.deb` nativo (não baseado em PyInstaller/AppImage), usando `dh_python3` pro Python + `dh-systemd` pro unit user. Artefato gerado automaticamente via GitHub Actions no release.

### Estrutura do pacote

```
hefesto_1.1.0_amd64.deb
├── DEBIAN/
│   ├── control
│   ├── postinst
│   ├── prerm
│   └── postrm
├── usr/
│   ├── bin/hefesto                   -> /usr/lib/python3/dist-packages/hefesto/cli/app.py
│   ├── bin/hefesto-gui               -> /usr/lib/python3/dist-packages/hefesto/app/main.py
│   ├── lib/python3/dist-packages/hefesto/ (todo o pacote)
│   ├── share/hefesto/assets/          (glade, glyphs, udev rules, service, profiles_default)
│   ├── share/applications/hefesto.desktop
│   ├── share/icons/hicolor/<sizes>/apps/hefesto.png
│   ├── share/man/man1/hefesto.1.gz    (opcional)
│   └── lib/udev/rules.d/
│       ├── 70-ps5-controller.rules
│       ├── 71-uinput.rules
│       └── 72-ps5-controller-autosuspend.rules
└── etc/
    └── systemd/user/                  (NÃO — unit user vai em /usr/lib/systemd/user/ pra disponibilizar sem copiar)
```

`control` (metadata):

```
Package: hefesto
Version: 1.1.0
Section: utils
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.10), python3-gi, python3-gi-cairo, gir1.2-gtk-3.0,
         gir1.2-ayatanaappindicator3-0.1, libhidapi-hidraw0, python3-pydantic,
         python3-structlog, python3-typer, python3-platformdirs
Recommends: python3-uinput
Maintainer: Hefesto Project <noreply@example.com>
Description: Daemon Linux para gatilhos adaptativos do controle DualSense
 Hefesto e um daemon user-level que habilita os gatilhos adaptativos do
 DualSense (Sony) em Linux, com suporte a perfis automáticos por janela
 ativa, lightbar RGB, rumble, emulação Xbox 360 via uinput, e GUI GTK3.
```

### postinst (pós-instalação)

```bash
#!/bin/bash
set -e

case "$1" in
    configure)
        # Reload udev rules
        if command -v udevadm >/dev/null 2>&1; then
            udevadm control --reload-rules
            udevadm trigger --action=change --subsystem-match=usb
        fi

        # Cache ícones GTK
        if command -v gtk-update-icon-cache >/dev/null 2>&1; then
            gtk-update-icon-cache -q -f /usr/share/icons/hicolor || true
        fi

        # Atualizar .desktop database
        if command -v update-desktop-database >/dev/null 2>&1; then
            update-desktop-database -q /usr/share/applications || true
        fi

        # NÃO habilita systemd user automaticamente — opt-in.
        echo ""
        echo "Hefesto instalado. Para habilitar auto-start do daemon:"
        echo "  systemctl --user enable --now hefesto.service"
        echo ""
        echo "Ou apenas abra o 'Hefesto' no menu de aplicativos."
        ;;
    abort-upgrade|abort-remove|abort-deconfigure) ;;
esac

exit 0
```

### prerm (antes de remover)

```bash
#!/bin/bash
set -e

case "$1" in
    remove|upgrade|deconfigure)
        # Sinaliza daemons dos usuários pra pararem (se houver)
        # systemd user é per-user; não dá pra fazer systemctl --user como root.
        # Melhor deixar usuário fazer: aviso no postrm.
        pkill -TERM -f 'hefesto\.app\.main' 2>/dev/null || true
        pkill -TERM -f 'hefesto daemon start' 2>/dev/null || true
        ;;
esac
exit 0
```

### Build automation

`packaging/debian/` com `control`, `changelog`, `rules`, `compat`, `source/format`.

Script `scripts/build_deb.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION=$(python3 -c "import tomllib; print(tomllib.loads(open('pyproject.toml','rb').read().decode())['project']['version'])")
dpkg-buildpackage -us -uc -b
mv ../hefesto_${VERSION}_amd64.deb dist/
```

CI: job novo em `.github/workflows/release.yml`:

```yaml
deb:
  runs-on: ubuntu-22.04
  steps:
    - uses: actions/checkout@v4
    - name: Install deb build tools
      run: sudo apt-get update && sudo apt-get install -y debhelper dh-python python3-all python3-setuptools
    - name: Build deb
      run: bash scripts/build_deb.sh
    - uses: actions/upload-artifact@v3
      with: { name: hefesto-deb, path: dist/*.deb }
```

Release automática no tag push: upload `hefesto_<ver>_amd64.deb` como asset.

## Critérios de aceite

- [ ] `packaging/debian/control`, `changelog`, `rules`, `compat`, `source/format` criados.
- [ ] `packaging/debian/hefesto.install` mapeia arquivos do source pra destino.
- [ ] `packaging/debian/hefesto.postinst`, `prerm`, `postrm` como descritos.
- [ ] `scripts/build_deb.sh` roda localmente em Ubuntu 22.04 produzindo `dist/hefesto_1.1.0_amd64.deb` válido (`lintian` sem ERROR; warnings aceitáveis).
- [ ] `.github/workflows/release.yml` inclui job `deb` que gera asset no release.
- [ ] Teste: `docker run --rm -it ubuntu:22.04 bash -c 'apt update && apt install -y ./hefesto_1.1.0_amd64.deb'` completa sem erro (fora do CI, manual). Instrução no README.
- [ ] README: seção "Instalação via .deb":
  ```
  curl -LO https://github.com/.../releases/download/v1.1.0/hefesto_1.1.0_amd64.deb
  sudo apt install ./hefesto_1.1.0_amd64.deb
  hefesto-gui
  ```

## Arquivos tocados

- `packaging/debian/*` (novos, ~10 arquivos)
- `scripts/build_deb.sh` (novo)
- `.github/workflows/release.yml` (+ job `deb`)
- `README.md` (+ seção instalação .deb)

## Notas para o executor

- **Dependências Python**: pydualsense e python-uinput **não** têm pacote Debian oficial. Duas opções:
  - (a) Listar como `Recommends` e instalar via `pip install` no postinst (pragmatismo; requer pip no sistema).
  - (b) Vendor essas libs dentro do .deb (adiciona ~5MB; zero dependência runtime externa). **Recomendo (b)** para v1 — copiar o site-packages do venv pro `/usr/lib/python3/dist-packages/hefesto_vendored/` e ajustar imports.
- **Architectures**: começar só com `amd64`. `arm64` (Raspberry Pi, Asahi) em sprint futura.
- **Signing**: repository signed (GPG) é overkill pra v1. Publicar só o asset no GitHub Release. Usuários confiam no checksum SHA256.
- **Versioning**: pegar version do `pyproject.toml` (fonte única de verdade). Cada release bump em ambos.
- **Lintian warnings** aceitáveis:
  - `hefesto: no-section-field` — section `utils` já setado.
  - `python-script-but-no-python3-dep` — fix: `Depends: python3`.
  - `new-package-should-close-itp-bug` — ignorar (não vamos submeter pro Debian oficial).

## Fora de escopo

- PPA launchpad (V2).
- Submissão pro repositório Debian oficial (V2+).
- `.rpm` (V2 — sprint irmã se houver demanda Fedora).
- ARM64 (V2).
