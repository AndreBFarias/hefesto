# Roadmap público — Hefesto - Dualsense4Unix

Estado: 2026-05-16. As datas são **intencionais (sem promessa)**: itens
forward-looking esperam dependências externas estáveis (libcosmic 1.0,
APIs cosmic-settings publicadas, etc.). Sem cronograma rígido — entrega
quando puder ser feita com qualidade.

## v3.3.0 — Tray fallback COSMIC + production-ready (atual, 2026-05-16)

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

## v3.4.0 — COSMIC nativo (forward-looking, sem data)

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

## v4.0.0 — Plataformas adicionais (long-term)

Sem data e sem prioridade de scheduling enquanto v3.4 estiver em
andamento. Pesquisa exploratória apenas.

- **Plasma applet nativo** — Plasmoid QML para integração com KDE
  Plasma 6 (paralelo ao applet COSMIC). Já funciona via SNI Ayatana
  padrão, mas Plasmoid daria controles inline (cor lightbar, slider
  rumble) sem janela.
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
