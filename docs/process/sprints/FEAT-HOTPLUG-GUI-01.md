# FEAT-HOTPLUG-GUI-01 — GUI abre automaticamente ao conectar o DualSense

**Tipo:** feat (UX).
**Wave:** V1.1.
**Estimativa:** 1 iteração.
**Dependências:** BUG-DAEMON-AUTOSTART-01 (GUI precisa conectar rápido).

---

**Tracking:** issue [#75](https://github.com/AndreBFarias/hefesto/issues/75) — fechada por PR com `Closes #75` no body.

## Contexto

Usuário pluga o DualSense no USB. Espera que a GUI do Hefesto apareça automaticamente — não precisar abrir pelo menu ou lembrar do tray. Hoje o daemon detecta a conexão (via udev rule de permissão já existente), mas a GUI é quietamente iniciada apenas via tray ou menu.

## Decisão

Instalação de **udev rule de hotplug** (ação `add`) que executa um script spawnando a GUI no contexto do usuário da sessão ativa:

```
# assets/73-ps5-controller-hotplug.rules
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="054c", ATTR{idProduct}=="0ce6", \
    TAG+="systemd", ENV{SYSTEMD_USER_WANTS}="hefesto-gui-hotplug.service"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="054c", ATTR{idProduct}=="0df2", \
    TAG+="systemd", ENV{SYSTEMD_USER_WANTS}="hefesto-gui-hotplug.service"
```

Acompanhado de unit `hefesto-gui-hotplug.service` (user scope, oneshot):

```ini
# assets/hefesto-gui-hotplug.service
[Unit]
Description=Spawn Hefesto GUI on DualSense hotplug
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c "pgrep -f 'hefesto.app.main' >/dev/null || %h/.local/bin/hefesto-gui"
```

O `pgrep` garante **idempotência**: se a GUI já estiver aberta, não relança.

Regra opt-in: durante o `install.sh`, prompt pergunta "auto-abrir Hefesto ao conectar o controle?" default Y.

## Critérios de aceite

- [ ] `assets/73-ps5-controller-hotplug.rules` (novo) — udev rule `ACTION=="add"`.
- [ ] `assets/hefesto-gui-hotplug.service` (novo) — unit user oneshot.
- [ ] `scripts/install_udev.sh`: copia a nova regra ao lado das existentes.
- [ ] `install.sh`: instala a unit user (`mkdir -p ~/.config/systemd/user && cp assets/hefesto-gui-hotplug.service ~/.config/systemd/user/` + `systemctl --user daemon-reload + enable hefesto-gui-hotplug.service`). Prompt opt-out com flag `--no-hotplug-gui`.
- [ ] `uninstall.sh` (`--udev`): remove tudo, inclusive a unit user e a rule 73.
- [ ] Teste manual: plugar DualSense com GUI fechada → GUI abre em ~2s. Plugar com GUI aberta → nada acontece (idempotência).
- [ ] Documentação em `docs/usage/hotplug.md` descrevendo como ligar/desligar.

## Arquivos tocados (previsão)

- `assets/73-ps5-controller-hotplug.rules` (novo)
- `assets/hefesto-gui-hotplug.service` (novo)
- `scripts/install_udev.sh`
- `install.sh`
- `uninstall.sh`

## Notas

- **Segurança**: a unit roda como usuário, não root. udev só marca o device com tag systemd; o `SYSTEMD_USER_WANTS` faz o systemd user gerenciar o spawn na sessão ativa.
- **DISPLAY/WAYLAND_DISPLAY**: herdados pelo systemd user service automaticamente em sessões GNOME/Pop!_OS modernas.
- **Bluetooth hotplug**: BT não gera ACTION=="add" USB; precisa regra separada em hidraw ou bluez. **Fora do escopo** desta sprint — sprint irmã `FEAT-HOTPLUG-GUI-BT-01` futura.
- **Múltiplos controles**: se usuário plugar 2 DualSenses em < 2s, duas triggers da unit são disparadas mas o `pgrep` bloqueia a segunda. OK.

## Fora de escopo

- Suporte Bluetooth.
- Fechar GUI automaticamente quando controle é desconectado (controverso — usuário pode querer permanecer).
- Notificação libnotify "Hefesto detectou o controle".
