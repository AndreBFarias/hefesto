# Roadmap público — Hefesto - Dualsense4Unix

Estado: 2026-05-16. As datas são **intencionais (sem promessa)**: itens
forward-looking esperam dependências externas estáveis (libcosmic 1.0,
APIs cosmic-settings publicadas, etc.). Sem cronograma rígido — entrega
quando puder ser feita com qualidade.

## v3.3.0 — Tray fallback COSMIC + production-ready (2026-05-16)

Sprints **MERGED**:

- `FEAT-COMPACT-WINDOW-FALLBACK-01` — janela compacta 320×90
  sempre-on-top como surrogate de tray em DEs que não implementam
  `org.kde.StatusNotifierWatcher` (Pop!_OS COSMIC, ambientes minimalistas).
  Auto + opt-out via `HEFESTO_DUALSENSE4UNIX_COMPACT_WINDOW=0`.
- `FEAT-NOTIFY-ACTION-OPEN-01` — notificações D-Bus
  (controlador desconectado, bateria baixa) ganham botão "Abrir
  Hefesto" que restaura a janela principal via `ActionInvoked`.
- `DOC-TROUBLESHOOTING-01` — `docs/usage/troubleshooting.md`
  cobrindo controle USB+BT, tray oculto, Flatpak sandbox + udev,
  pydantic v1 em Jammy/Noble, cascade Wayland.
- `DOC-DE-COMPATIBILITY-MATRIX-01` — matriz README reescrita com
  honestidade empírica (validações reais vs comunidade).
- `DOC-FLATPAK-SANDBOX-NOTE-01` — README explica sandbox `--device=all`,
  socket IPC compartilhado, `install-host-udev.sh`.
- `INSTALL-UDEV-SUDO-CHECK-01` — `scripts/install-host-udev.sh`
  detecta sudo sem NOPASSWD e avisa antes de travar.

## v3.3.1 — Install perfeito + udev incondicional (2026-05-16)

Sprints **MERGED**:

- `INSTALL-UDEV-UNCONDITIONAL-01` — `install.sh` aplica udev sempre
  (era opt-in via prompt; usuários puláveis ficavam sem controle
  funcionando). Re-cópia idempotente.
- `INSTALL-FLATPAK-UDEV-SYNC-01` — quando Flatpak Hefesto está
  instalado, install propaga regras via `flatpak run --command=install-host-udev.sh`.
- `BUNDLE-INSTALL-HOST-UDEV-DEB-01` — `build_deb.sh` bundla
  `scripts/install-host-udev.sh` em `/usr/share/hefesto-dualsense4unix/scripts/`
  para re-aplicação manual fora do `apt install`.

## v3.4.0 — i18n EN + a11y + packaging multi-distro + CI matrix (atual, 2026-05-16)

Sprints **MERGED**:

- `FEAT-I18N-INFRASTRUCTURE-01` — `utils/i18n.py` com `init_locale()`
  + `_()` wrapper canônico; resolução de catálogos via 5 candidate
  paths (XDG, `~/.local`, `/usr/share`, `/app/share`, wheel package).
- `FEAT-I18N-MARK-STRINGS-01` — ~210 strings marcadas como
  traduzíveis: Glade (~190 labels), `tray.py`, `compact_window.py`,
  `gui_dialogs.py`.
- `FEAT-I18N-CATALOGS-01` — pipeline `scripts/i18n_extract.sh` +
  `scripts/i18n_compile.sh` (xgettext/msgfmt) + `po/{en,pt_BR}.po`
  com 232 mensagens × 2 idiomas.
- `INSTALL-LOCALE-FILES-01` — locale bundlado em 5 destinos:
  `install.sh` → `~/.local/share/locale/`, `.deb` → `/usr/share/locale/`,
  AppImage GUI → `AppDir/usr/share/locale/`, Flatpak → `/app/share/locale/`,
  wheel via `pyproject.toml` include.
- `FEAT-A11Y-ATK-LABELS-01` — 15 botões críticos com
  `<accessibility><property name="AtkObject::accessible-name">` para
  screen readers (Orca anuncia "Aplicar gatilho adaptativo no L2" em
  vez de "botão sem nome").
- `FEAT-A11Y-HIGH-CONTRAST-01` — `theme.css` ganhou bloco
  `@media (prefers-contrast: more)` + classe `.hefesto-dualsense4unix-high-contrast`
  com paleta WCAG AAA (preto, branco, amarelo `#ff0`). Detecção
  automática via `Gtk.Settings.gtk-theme-name`.
- `CHECKLIST-A11Y-MANUAL-01` — `CHECKLIST_VALIDACAO_v3.4.0.md` com
  seção Acessibilidade (Tab/Enter/Esc, mnemonics, Orca).
- `FEAT-PACKAGING-ARCH-01` — `packaging/arch/PKGBUILD` +
  `hefesto-dualsense4unix.install` (hook `post_install` recarrega
  udev + carrega uinput) + README.
- `FEAT-PACKAGING-FEDORA-01` — `packaging/fedora/hefesto-dualsense4unix.spec`
  pronto para `rpmbuild`/Copr + README.
- `FEAT-PACKAGING-NIX-01` — `flake.nix` raiz + `packaging/nix/package.nix`
  com `buildPythonApplication` + README com guia NixOS / home-manager.
- `CI-SMOKE-DOCKER-MATRIX-01` — job `smoke-multi-distro` em
  `.github/workflows/ci.yml` com matrix `fedora:40 + archlinux:latest +
  debian:12` em containers Docker. Build + install + smoke
  `hefesto-dualsense4unix version` + `i18n EN` por distro.
- `CI-CACHE-PIP-01` — `cache: 'pip'` chaveado por hash de
  `pyproject.toml` em todos os `setup-python@v5` que rodam pip
  install (ci.yml + release.yml, 7 jobs).

## v3.5.x — comunidade (forward-looking, sem data)

Itens dependentes de contribuição comunitária ou cleanup acumulado.

- **Idiomas extras** (ES, FR, DE) — infra v3.4.0 cobre via
  `scripts/i18n_extract.sh --add LANG`; aguarda PRs da comunidade.
- **Wayland-only cleanup** — avaliar deprecar XlibBackend agora que
  WaylandCascadeBackend é estável.
- **Plasma applet QML** — Plasmoid nativo para KDE Plasma 6 (paralelo
  ao COSMIC applet de v4.0).

## v4.0.0 — COSMIC nativo + plataformas adicionais (forward-looking, sem data)

Espera **upstream libcosmic 1.0 estável** + APIs publicadas pelo
projeto System76. Atualmente em alpha; lançamento depende de Pop!_OS
24.04 final ou 25.04.

- `FEAT-COSMIC-APPLET-RUST-01` (XL) — applet nativo Rust + libcosmic
  no painel COSMIC (substitui janela compacta v3.3.0). Stub spec em
  `docs/process/sprints/FEAT-COSMIC-APPLET-RUST-01.md`.
- `FEAT-COSMIC-GLOBAL-SHORTCUTS-01` (M) — atalhos globais (PS+D-pad
  combo, alternar perfil) registrados via `cosmic-settings keybindings`
  API quando publicada. Stub em `FEAT-COSMIC-GLOBAL-SHORTCUTS-01.md`.
- `FEAT-COSMIC-PANEL-WIDGET-01` (L) — widget de painel mais rico que o
  applet (preview rumble, sliders inline). Depende de 116. Stub em
  `FEAT-COSMIC-PANEL-WIDGET-01.md`.
- **Flatpak permissions polish** — substituir `--device=all` por
  `--device=hidraw + --device=input + --device=uinput` quando
  freedesktop-sdk publicar granularidade fina.
- **systemd-portable** — daemon empacotado como portable service para
  distros sem `--user` services.

## Princípios

- **Sem prazo** quando depender de upstream alheio. Promessa de data é
  promessa quebrada quando a dependência atrasa.
- **Backlog explícito** em `docs/process/sprints/*.md` com status
  `PLANNED|IN_PROGRESS|MERGED|DEFERRED|ABANDONED`.
- **Cada release tem CHANGELOG completo** com sprints MERGED listadas.
- **Não vendemos features futuras** como se já existissem — usuários
  veem só o que está empacotado.

Veja [`CHANGELOG.md`](../../CHANGELOG.md) para histórico de releases
e [`docs/process/sprints/`](sprints/) para spec detalhada de cada sprint.
