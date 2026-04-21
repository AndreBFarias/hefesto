# Descoberta GUI Fase 6: abas Daemon + Emulação

Data: 2026-04-21
Escopo: HEFESTO-GUI fase 6 — controle de systemd --user + status da emulação
Xbox360 virtual.

## Conteúdo entregue

### Aba Daemon
- Combo de unit: `hefesto.service` vs `hefesto-headless.service`.
- Label de status com cor (verde ativo, vermelho inativo ou ausente) e
  indicador `auto-start: enabled|disabled`.
- Switch `Auto-start` (enable/disable) com guard contra reentrância.
- Botões Start, Stop, Restart, Atualizar e Ver logs.
- TextView monospace mostrando `systemctl --user status <unit>` ou
  `journalctl --user -u <unit> -n 80`.
- Subprocess com `timeout=5` + graceful fallback quando `systemctl` ou
  `journalctl` ausentes.

### Aba Emulação
- Disponibilidade do `python-uinput` e `/dev/uinput`, com diagnóstico em
  3 estados (disponível, sem permissão, módulo ausente).
- Metadata fixa do device virtual (nome, VID 045E:028E Xbox360).
- Listagem dinâmica de `/dev/input/js*` existentes.
- Exibição do combo sagrado atual (next/prev/buffer_ms/passthrough) lido
  dos defaults de `hotkey_daemon`.
- Botão "Testar criação de device virtual" que instancia `UinputGamepad`
  e faz start/stop de verdade — fail visível no status bar.
- Botão "Editar daemon.toml" que materializa o arquivo em
  `config_dir()/daemon.toml` (com template default) e abre via
  `xdg-open`.

## Riscos

- Emulation tab não grava config ainda; é read-only + shortcut para o
  toml. Edição WYSIWYG fica para uma sprint futura quando o daemon tiver
  reload de config (hoje `daemon.reload` é placeholder).
- `systemctl status` demora até 5s; a UI fica ligeiramente travada
  enquanto espera. Aceitável para toggle manual, mas se virar
  bottleneck, migrar para `subprocess.Popen` + watch com
  `GLib.io_add_watch`.

## Prova visual

- `docs/process/discoveries/assets/2026-04-21-gui-fase6-daemon.png`
- `docs/process/discoveries/assets/2026-04-21-gui-fase6-emulation.png`

---

*"A boa GUI mostra o estado real do sistema, não o que o usuário quer
acreditar que está acontecendo."*
