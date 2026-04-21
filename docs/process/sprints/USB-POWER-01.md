# USB-POWER-01 — Desabilitar USB autosuspend para DualSense

**Tipo:** fix (causa-raiz de desconexão transiente).
**Wave:** fora de wave.
**Status:** APLICADA em 2026-04-21 (mesmo ciclo de BUG-IPC-01, BUG-UDP-01, UX-HEADER-01, UX-RECONNECT-01).
**Autor:** trazido de projeto irmão (desbloqueador Nintendo Switch) onde a mesma gotcha do Pop!_OS foi enfrentada e resolvida.

---

## Causa-raiz identificada

O kernel Linux com `CONFIG_USB_RUNTIME_PM=y` (default em Pop!_OS, Ubuntu, Fedora) suspende automaticamente dispositivos USB inativos após cerca de 2 segundos sem atividade mensurável. Para um gamepad polling HID a 60-120 Hz, isso gera desconexão transiente inesperada:

- hidraw devolve `ENODEV`.
- daemon entra em reconnect loop.
- GUI exibe "daemon offline" ou "tentando reconectar" mesmo com o controle fisicamente conectado.
- logs do systemd-udev mostram `power/runtime_status` alternando entre `active` e `suspended`.

O projeto irmão (desbloqueador Switch) enfrentou sintoma equivalente durante transferências USB e documentou a solução em três camadas: udev rule, fallback programático em `/sys/bus/usb/devices/*/power/`, e error handling correto distinguindo `ENODEV` de `EPERM`/`EACCES`.

Para o Hefesto, a camada udev é suficiente — não há injeção privilegiada envolvida, apenas polling contínuo.

## Patch aplicado

**Arquivo novo:** `assets/72-ps5-controller-autosuspend.rules`

```
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="054c", ATTR{idProduct}=="0ce6", ATTR{power/control}="on", ATTR{power/autosuspend_delay_ms}="-1"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="054c", ATTR{idProduct}=="0df2", ATTR{power/control}="on", ATTR{power/autosuspend_delay_ms}="-1"
```

Cobre DualSense standard (`054c:0ce6`) e DualSense Edge (`054c:0df2`).

**Arquivo editado:** `scripts/install_udev.sh` — copia a nova regra junto com as outras duas, e faz `udevadm trigger --action=change --subsystem-match=usb` adicional para aplicar também a controles já conectados sem precisar unplug.

## Aplicação (manual, requer sudo)

```bash
sudo cp assets/72-ps5-controller-autosuspend.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger --action=change --subsystem-match=usb
```

Ou simplesmente rodar `./scripts/install_udev.sh` novamente (idempotente).

## Verificação

```bash
# Procurar o DualSense ativo
for d in /sys/bus/usb/devices/*/; do
  vendor=$(cat "$d/idVendor" 2>/dev/null)
  product=$(cat "$d/idProduct" 2>/dev/null)
  if [[ "$vendor" == "054c" && "$product" == "0ce6" ]]; then
    echo "DualSense em: $d"
    echo "  power/control: $(cat $d/power/control)"
    echo "  power/autosuspend_delay_ms: $(cat $d/power/autosuspend_delay_ms)"
  fi
done
```

Esperado após a regra aplicada:
```
power/control: on
power/autosuspend_delay_ms: -1
```

Se mostrar `auto` / algum valor positivo, a regra não foi recarregada — refazer `udevadm control --reload-rules && udevadm trigger`.

## Por que não código programático em runtime

`fusectl` fez fallback em runtime (escreve em `/sys/bus/usb/devices/*/power/control`) porque o privilege sudo nem sempre está disponível no momento da instalação. Hefesto já requer udev rule para acesso hidraw (regra `70-ps5-controller.rules`), então a mesma barreira de sudo já foi vencida — dobrar em runtime seria redundante.

Se o usuário executar o daemon sem ter rodado `install_udev.sh`, o comportamento atual (mensagens `controller_connect_failed` com fallback a FakeController) cobre o caso. Mensagem clara na documentação de instalação é suficiente.

## Registro em VALIDATOR_BRIEF.md

Adicionar armadilha A-05 (USB autosuspend) na próxima iteração do brief, com referência a este arquivo.

## Fora de escopo

- Fallback programático sudo-less (fora do padrão do projeto).
- Power management Bluetooth (BT não sofre autosuspend USB; sofre L2CAP timeout separado — issue distinta).
- Kernel tunnable global (`/sys/module/usbcore/parameters/autosuspend`) — regra per-device é mais cirúrgica.

---

*"O vento não é visto; só o que ele move."*
