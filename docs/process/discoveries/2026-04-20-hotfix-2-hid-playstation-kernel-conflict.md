# 2026-04-20 — HOTFIX-2: `hid_playstation` kernel driver consome reports HID do DualSense

**Contexto:** smoke runtime logo após HOTFIX-1. Com os atributos lidos certos, era esperado que triggers analog aparecessem quando pressionados. Não apareceram.
**Status:** Resolvida (backend híbrido via evdev).
**Issues relacionadas:** #49 (HOTFIX-2, closed), merged em PR #51. Cruza com #26 (W9.1 HidHide exploratório — pode ser arquivada).

## Sintoma

Script imprimindo em tempo real toda vez que **qualquer** campo do `ds.state` mudasse, por 15s, pedindo explicitamente pro usuário apertar botões, mover sticks, pressionar triggers:

```
Detectou 1 mudancas em 15s:
  +0.10s LX: 128 -> -6
```

A única mudança detectada foi noise inicial do primeiro report. `L2_value`, `R2_value`, todos os botões (`cross`, `circle`, `triangle`, `square`) e sticks permaneceram nos valores iniciais.

Confirmação cruzada: `evdev` raw no mesmo device mostrou eventos chegando:

```
type=3 code=1 value=124   # ABS_Y
type=3 code=3 value=127   # ABS_RX
type=3 code=1 value=123
...
total events: 30
```

Ou seja, o **kernel estava decodificando**, mas o pydualsense não.

## Hipóteses

1. **Usuário não pressionou** — descartada pelo evdev raw mostrando eventos no mesmo instante.
2. **`sendReport` thread do pydualsense travou** — improvável, porque o primeiro report foi processado (battery = 100) e não havia exceção no log.
3. **OUTPUT report do pydualsense mal-formatado faz device parar de enviar** — descartada testando só INIT sem enviar nada.
4. **Kernel driver captura /dev/hidraw antes do pydualsense** — **CONFIRMADA**:
   ```
   $ lsmod | grep -iE "playstation|hid_sony"
   hid_playstation        45056  0
   ff_memless             24576  1 hid_playstation
   led_class_multicolor   16384  1 hid_playstation

   $ ls /dev/input/by-id/ | grep -i dualsense
   usb-Sony_Interactive_Entertainment_DualSense_Wireless_Controller-if03-joystick -> ../js0
   ```

## Causa

Kernel Linux 6.17 em Pop!_OS 22.04 tem o módulo `hid_playstation` carregado por padrão. Ele reconhece o DualSense, cria `/dev/input/js0` + event24-26, e passa a consumir os reports HID do `/dev/hidraw5`. `pydualsense.init()` consegue ler o primeiro report (onde battery.Level é decodificado), mas a partir daí o kernel "absorve" os reports de input em tempo real.

No Windows, o problema equivalente existe e é resolvido pelo **HidHide** (esconde o device de outros drivers). No Linux, o equivalente seria `echo '<id>' > /sys/bus/hid/drivers/playstation/unbind`, que exige root e quebra o suporte kernel (LEDs via sysfs, rumble via ff-memless).

## Solução

Arquitetura híbrida:

- **Input** via `evdev` (`/dev/input/event24`). O kernel já decodifica tudo: ABS_Z/RZ = L2/R2 analog, ABS_X/Y/RX/RY = sticks, BTN_SOUTH/EAST/NORTH/WEST = cross/circle/triangle/square, ABS_HAT0X/Y = d-pad, BTN_MODE = PS.
- **Output** via `pydualsense` (HID-raw). Set de triggers, LED, rumble continuam funcionando porque são envios unidirecionais ao device.

Implementação em PR #51:
- `src/hefesto/core/evdev_reader.py`: `EvdevReader` com thread dedicada, snapshot thread-safe, mapeamento canônico de botões.
- `src/hefesto/core/backend_pydualsense.py`: `PyDualSenseController` aceita `evdev_reader` injetável; `connect()` inicia o reader automaticamente; `read_state()` usa evdev como fonte primária, cai em pydualsense como fallback.

## Lições

1. **Adapter em Linux precisa considerar o driver do kernel.** Pacote Python "fala HID direto" não significa que ele é o único falando.
2. **Evdev é a API canônica do Linux pra gamepads.** Mesmo que o protocolo HID do DualSense seja público, o kernel já decodifica — usar evdev é mais barato e evita guerra com o driver.
3. **OUTPUT e INPUT não precisam ser o mesmo caminho.** Split funciona bem: uma biblioteca cuida de receber, outra cuida de enviar.
4. **Diagnóstico com dois caminhos paralelos economiza tempo.** Ter evdev raw E pydualsense sendo testados em paralelo evidenciou instantaneamente qual deles estava cego.

## Impacto cross-sprint

- Sprints destravadas: INFRA.2 (input real agora aparece), W8.1 hotkey combos (BTN_MODE + HAT0X/Y detectáveis), W6.3 emulation virtual (não conflita mais com leitura própria).
- Sprints arquivadas: #26 (W9.1 HidHide-like) pode ser fechada como "não necessária" — evdev resolveu sem `unbind` do driver.
- ADRs afetadas: ADR-001 (backend pydualsense) ganha extensão explicando o split input/output.
- Decisões V2/V3: V2-7 (`transport`) continua OK; nenhuma outra decisão quebrou.
- Novos limites: precisamos do usuário no grupo `input` ou ACL no event* — `uaccess` via logind já resolve; validado com `ls -l /dev/input/event24` mostrando `+` (ACL ativa).
