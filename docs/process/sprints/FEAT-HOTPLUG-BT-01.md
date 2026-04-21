# FEAT-HOTPLUG-BT-01 — Auto-abertura da GUI ao parear DualSense via Bluetooth

**Tipo:** feat (plataforma).
**Wave:** V1.2.
**Estimativa:** 1 iteração.
**Dependências:** FEAT-HOTPLUG-GUI-01 (padrão base USB já estabelecido).

---

## Contexto

FEAT-HOTPLUG-GUI-01 cobre só USB: regra udev `ACTION=="add"` no `subsystem=usb` dispara o spawn da GUI. Bluetooth não gera esse evento no subsystem USB — o pareamento BT cria um nó em `hidraw` via protocolo L2CAP + hid-playstation, e o evento correspondente é `ACTION=="add"` em `subsystem=hidraw` ou `subsystem=input` (dependendo do kernel).

## Decisão

Adicionar regra complementar `74-ps5-controller-hotplug-bt.rules`:

```
# BT hotplug: detecta hidraw node com KERNELS batendo VID:PID via BT L2CAP
ACTION=="add", SUBSYSTEM=="hidraw", KERNELS=="0005:054C:0CE6.*", \
    TAG+="systemd", ENV{SYSTEMD_USER_WANTS}="hefesto-gui-hotplug.service"
ACTION=="add", SUBSYSTEM=="hidraw", KERNELS=="0005:054C:0DF2.*", \
    TAG+="systemd", ENV{SYSTEMD_USER_WANTS}="hefesto-gui-hotplug.service"
```

A unit `hefesto-gui-hotplug.service` já foi criada no HOTPLUG-01; o `pgrep` mantém idempotência (GUI já aberta = no-op).

## Critérios de aceite

- [ ] `assets/74-ps5-controller-hotplug-bt.rules` (novo).
- [ ] `scripts/install_udev.sh` copia a nova regra.
- [ ] Teste manual: parear DualSense via `bluetoothctl` com GUI fechada → GUI abre em ~3s.
- [ ] Teste manual: parear com GUI aberta → nada (pgrep bloqueia).
- [ ] `docs/usage/hotplug.md` ganha seção "Bluetooth".

## Arquivos tocados (previsão)

- `assets/74-ps5-controller-hotplug-bt.rules` (novo)
- `scripts/install_udev.sh`
- `docs/usage/hotplug.md`

## Notas

- `KERNELS=="0005:054C:0CE6.*"` varia conforme kernel; verificar com `udevadm info -a /dev/hidraw4` (exemplo) após parear.
- Se BT usar `subsystem=input` em vez de `hidraw` em algum kernel, adicionar regra de fallback.
- Pareamento inicial do controle ainda é manual (`bluetoothctl` ou Configurações do GNOME/COSMIC).

## Fora de escopo

- Interface de pareamento BT dentro da GUI do Hefesto.
- Suporte multi-controle BT simultâneos.
