# Descoberta GUI Fase 8: tray + close-to-tray + launcher desanexado + auditoria

Data: 2026-04-21
Escopo: HEFESTO-GUI fase 8 — o usuário reportou que fechar a janela "dava
kill", e queria o Hefesto rodando em background enquanto joga Steam.
Foram feitos ajustes de arquitetura UX e uma auditoria passo a passo
das 7 abas com correções.

## Comportamento antes

- `on_window_destroy` → `Gtk.main_quit()`: fechar a janela matava a GUI.
- `install.sh` não instalava a unit systemd do daemon; usuário tinha que
  descobrir `hefesto daemon install-service` sozinho.
- `./run.sh` no terminal: shell mostrava `[1] killed` ao fim. Deselegante
  e bloqueava o terminal enquanto rodava.
- Gatilhos abriam em `Rigid` com força 200 por padrão — perigoso de
  clicar `Aplicar` sem ler.
- Perfis abriam com editor vazio mesmo tendo 3 perfis na lista.
- TextView da aba Daemon não rolava pro final após refresh.
- `profile.list` só usava IPC; com daemon offline, GUI mostrava lista
  vazia apesar de ter perfis no disco.

## Mudanças estruturais

- **AppTray** (`src/hefesto/app/tray.py`): dataclass com AppIndicator
  (Ayatana ou legado), menu `[status dinâmico] Abrir painel | Perfis >
  <lista> | Sair do Hefesto`. Perfis atualizados a cada 3s via
  `profile_list` (com fallback para disco quando daemon offline).
- **Close-to-tray** em `HefestoApp`: signal trocado de `destroy` para
  `delete-event`; handler esconde a janela se o tray está disponível,
  retornando `True` para cancelar o `destroy`. `Sair` no menu do tray
  seta `_quitting=True` e chama `Gtk.main_quit()`.
- **Launcher desanexado**: `~/.local/bin/hefesto-gui` agora usa
  `setsid nohup ./run.sh </dev/null >/dev/null 2>&1 &` + `disown`.
  Shell não fica preso nem imprime `killed` ao fim.
- **Auto-install systemd**: `install.sh` agora cria symlink
  `~/.local/bin/hefesto → .venv/bin/hefesto` (consumido pelo
  `ExecStart=%h/.local/bin/hefesto daemon start --foreground` da unit),
  roda `hefesto daemon install-service`, e inicia via
  `systemctl --user start hefesto.service`. Falha do `systemctl` não é
  fatal (aviso no log).
- **`uninstall.sh`** chama `daemon uninstall-service`, remove symlink e
  launcher.

## Correções de auditoria UX

- `triggers_actions.py`: default trocado de `Rigid` → `Off` (não aplica
  gatilho rígido por engano).
- `profiles_actions.py`: `_reload_profiles_store` seleciona o primeiro
  perfil se `select_name` não resolve; editor passa a popular ao abrir.
- `daemon_actions.py`: `_set_daemon_text` cria mark, `scroll_to_mark`
  para o final após refresh (vê o final do log sem scroll manual).
- `ipc_bridge.py` `profile_list()`: quando daemon responde `[]` ou
  falha, cai de volta para `load_all_profiles()` com
  `active: False`. Tray e aba Perfis mostram perfis mesmo offline.

## Prova de concepção

- Janela fechada com o X mantém `python -m hefesto.app.main` vivo (`ps`
  estado `S`), tray disponível.
- Ícone/menu do tray aparece no systray do GNOME/Pop via
  `AyatanaAppIndicator3`.
- `systemctl --user is-active hefesto.service` retorna `active` após
  `./install.sh`.
- Aba Status mostra `conectado via usb`, bateria `100 %`, perfil ativo
  `fallback` (FakeController fallback quando hardware ausente).

Prova visual final:
`docs/process/discoveries/assets/2026-04-21-gui-fase8-status-daemon-online.png`

## Bugs descobertos e fixos

1. `hefesto daemon start` roda em foreground e travava o `install.sh`.
   Trocado por `systemctl --user start`.
2. Unit systemd aponta para `~/.local/bin/hefesto`, mas o pip instala
   em `.venv/bin/hefesto`. Criado symlink no `install.sh`.
3. `AppIndicator3.Indicator` não expõe `IndicatorStatus` como atributo
   da classe; precisa acessar pelo namespace do módulo
   (`AyatanaAppIndicator3.IndicatorStatus`). Resolvido armazenando a
   referência do namespace no resolver.

---

*"A única GUI elegante é a que some do caminho quando você só quer
jogar, e volta quando você chama."*
