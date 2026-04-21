# Descoberta GUI Fase 7: install.sh + uninstall.sh + run.sh + .desktop

Data: 2026-04-21
Escopo: HEFESTO-GUI fase 7 — integração com o shell Linux (menu de
aplicativos, ícone, launcher).

## Entregas

- `install.sh` (raiz): cria `.venv/` com `--system-site-packages`
  (necessário para herdar os bindings `python3-gi` instalados via apt),
  instala o pacote editável, gera `~/.local/share/applications/hefesto.desktop`
  apontando para `./run.sh`, copia ícone para
  `~/.local/share/icons/hicolor/256x256/apps/hefesto.png`, roda
  `gtk-update-icon-cache` + `update-desktop-database` e cria launcher
  em `~/.local/bin/hefesto-gui`.
- `uninstall.sh`: reverte tudo, preservando `.venv/` (remoção manual
  explícita: `rm -rf .venv`).
- `run.sh` estendido: default agora é `--gui` (abre
  `python -m hefesto.app.main`). Mantém `--smoke`, `--daemon`, `--fake`,
  `--bt`, `--usb` do fluxo daemon.
- Categoria `.desktop`: `Settings;HardwareSettings;` (corrige hint do
  `desktop-file-validate` que recusava `Utility;HardwareSettings;Game;`
  como "múltiplas categorias principais").

## Detalhe crítico

O `.venv` precisa ser criado com `--system-site-packages` porque o
PyGObject/GTK3 bindings não são instaláveis via `pip` (dependem de
introspection `.gir` do sistema). Sem a flag, `import gi` falha dentro
do venv mesmo com `python3-gi` instalado no sistema. A checagem de
`import gi` foi movida para DEPOIS da criação do venv (antes era feita
no `python3` system e podia falhar mesmo com bindings disponíveis via
apt, por detalhes de path).

## Prova visual

- `docs/process/discoveries/assets/2026-04-21-gui-fase7-installed.png`
  (GUI aberta via `~/.local/bin/hefesto-gui` com 7 abas: Status, Gatilhos,
  Lightbar, Rumble, Perfis, Daemon, Emulação).

## Fluxo completo do usuário

```bash
# primeira instalação
./install.sh

# rodar
hefesto-gui          # via launcher em ~/.local/bin
./run.sh             # direto do repo
./run.sh --smoke     # daemon em modo fake 2s

# remover artefatos do shell (mantém venv)
./uninstall.sh

# wipe total
rm -rf .venv
```

---

*"O melhor código é aquele que o usuário instala com um único comando e
não precisa voltar a olhar."*
