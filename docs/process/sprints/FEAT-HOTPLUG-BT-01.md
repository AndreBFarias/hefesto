# FEAT-HOTPLUG-BT-01 — Auto-abertura da GUI ao parear DualSense via Bluetooth

**Tipo:** feat (plataforma — paridade BT do hotplug USB).
**Wave:** V1.2.
**Status:** ASSET APLICADO em produção (regra 74 já presente em `assets/` e `scripts/install_udev.sh`); spec retroativa formalizada em 2026-04-27 sob FEAT-BLUETOOTH-CONNECTION-01. Marca **PROTOCOL_READY** até registro humano da execução do item 8 do `CHECKLIST_HARDWARE_V2.md` em hardware BT real (lição L-21-6).
**Dependências:** FEAT-HOTPLUG-GUI-01 (regra 73 USB), BUG-TRAY-SINGLE-FLASH-01 (`acquire_or_bring_to_front` na GUI cobre o caso de pareamento com janela já aberta).

---

**Tracking:** issue [#82](https://github.com/AndreBFarias/issues/82).

## Causa-raiz identificada

A regra `73-ps5-controller-hotplug.rules` cobre apenas o caminho USB: `ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="054c", ATTR{idProduct}=="0ce6"|"0df2"`. Quando o DualSense é pareado via Bluetooth, o kernel **não** cria evento `add` no `subsystem=usb` — o pareamento acontece via L2CAP + `hid_playstation`, e o nó hidraw BT aparece com identificador estável `0005:054C:0CE6.<seq>` ou `0005:054C:0DF2.<seq>` no `subsystem=hidraw`.

Sem regra equivalente para BT, a GUI não abre automaticamente ao parear, mesmo que o resto do stack (backend pydualsense, evdev, daemon) já reconheça `transport=bt` perfeitamente (ver FEAT-BLUETOOTH-CONNECTION-01 §Contexto).

## Patch aplicado

**Arquivo novo:** `assets/74-ps5-controller-hotplug-bt.rules`

```
# BT hotplug: detecta hidraw node com KERNELS batendo VID:PID via BT L2CAP.
# Triggera hefesto-dualsense4unix-gui-hotplug.service (compartilhada com USB).
ACTION=="add", SUBSYSTEM=="hidraw", KERNELS=="0005:054C:0CE6.*", \
    TAG+="systemd", ENV{SYSTEMD_USER_WANTS}="hefesto-dualsense4unix-gui-hotplug.service"
ACTION=="add", SUBSYSTEM=="hidraw", KERNELS=="0005:054C:0DF2.*", \
    TAG+="systemd", ENV{SYSTEMD_USER_WANTS}="hefesto-dualsense4unix-gui-hotplug.service"
```

Cobre DualSense standard (`054C:0CE6`) e DualSense Edge (`054C:0DF2`). O wildcard `.*` no sufixo absorve a numeração do filho hidraw, que pode variar entre kernels (ex.: `0005:054C:0CE6.0001` em 6.1, `0005:054C:0CE6.0010` em 6.6).

**Arquivo editado:** `scripts/install_udev.sh` — copia a nova regra junto com as outras (linha 14 atual).

**Arquivo editado:** `install.sh` — gate do passo 3/9 verifica também `/etc/udev/rules.d/74-ps5-controller-hotplug-bt.rules`; texto descritivo lista cinco regras (FEAT-BLUETOOTH-CONNECTION-01 etapa A).

A unit `hefesto-dualsense4unix-gui-hotplug.service` já existe e é a mesma usada pela regra 73 (USB). O guard de duplicação fica inteiramente na GUI via `acquire_or_bring_to_front("gui", ...)` (BUG-TRAY-SINGLE-FLASH-01) — nada de `pgrep` no `ExecStartPre` (cobre A-11 também sob hidraw BT, onde múltiplos `ACTION=="add"` em <200 ms durante negociação L2CAP são esperados).

## Aplicação (manual, requer sudo)

```bash
sudo cp assets/74-ps5-controller-hotplug-bt.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Ou simplesmente rodar `./scripts/install_udev.sh` novamente (idempotente — copia as cinco regras).

## Verificação

Após pareamento BT (`bluetoothctl pair <MAC>` + `connect <MAC>`):

```bash
# Encontrar o hidraw BT correspondente
for hidraw in /dev/hidraw*; do
    info=$(udevadm info -a "$hidraw" 2>/dev/null | grep -E 'KERNELS=="0005:054C:(0CE6|0DF2)\.')
    if [[ -n "$info" ]]; then
        echo "DualSense BT em: $hidraw"
        echo "$info"
    fi
done
```

Esperado:
```
DualSense BT em: /dev/hidrawN
    KERNELS=="0005:054C:0CE6.000A"
```

(ou variante com `0DF2` se for DualSense Edge; o índice `.000A` varia)

Confirmar que a GUI abriu automaticamente:

```bash
pgrep -f "hefesto_dualsense4unix.app.main" >/dev/null && echo "GUI ativa" || echo "GUI não subiu"
```

Critério de aceite humano: GUI abre em ≤ 3 s após `bluetoothctl connect <MAC>`. Se não abrir, capturar:

```bash
journalctl --user -u hefesto-dualsense4unix-gui-hotplug.service --since "30 seconds ago"
udevadm monitor --kernel --subsystem-match=hidraw &
# em outra sessão: bluetoothctl connect <MAC>
```

## Por que `SUBSYSTEM=="hidraw"` e não `bluetooth`

O kernel `hid_playstation` cria o nó hidraw como ponto unificado independente do bus (USB ou BT). A unit precisa bater no momento em que o nó está pronto para escrita HID — isso só acontece no `add` do `hidraw`. Eventos do `subsystem=bluetooth` são puramente de stack (HCI, L2CAP) e disparam antes do hidraw existir, o que faria a GUI subir antes do daemon conseguir abrir o device.

## Limites conhecidos

- `KERNELS=="0005:054C:0CE6.*"` depende do formato `bus:vid:pid.seq` que o `hid_playstation` exporta. Se um kernel futuro mudar para `0005:054C:0CE6_<hash>` ou similar, abrir sprint de fallback.
- Múltiplos `ACTION=="add"` em hidraw BT durante negociação L2CAP — coberto por A-11 + `acquire_or_bring_to_front` na GUI; a unit pode disparar 2–3× em <200 ms e nada quebra.
- Pareamento inicial (`bluetoothctl pair`) ainda é manual; UI dedicada é não-objetivo (vide UI-BT-PAIRING-01 caso seja pedida no futuro).

## Registro em VALIDATOR_BRIEF.md

Já existe armadilha A-11 cobrindo race de udev `ACTION=="add"`. Após validação humana real, atualizar rodapé do BRIEF com timestamp da execução do item 8 do `CHECKLIST_HARDWARE_V2.md`.

## Fora de escopo

- Interface de pareamento BT dentro da GUI do Hefesto (sprint futura `UI-BT-PAIRING-01`).
- Suporte multi-controle BT simultâneos.
- Power management Bluetooth equivalente ao A-05 (USB autosuspend) — semântica diferente; se aparecer desconexão transiente em BT, abrir sprint `BT-POWER-01` separada.
- Áudio do DualSense via BT (protocolo Sony fechado).

---

*"O ferro é o mesmo; muda só o caminho até a forja."*
