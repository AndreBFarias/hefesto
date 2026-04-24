# INFRA-EVDEV-TOUCHPAD-01 — Expor touchpad_press regionalizado via evdev

**Tipo:** feat (infra — aditivo).
**Wave:** V2.3 (bloqueadora de FEAT-KEYBOARD-UI-01).
**Estimativa:** XS (0.25 iteração).
**Dependências:** nenhuma.
**Sprint-mãe:** FEAT-MOUSE-TECLADO-COMPLETO-01 (destravamento de 59.3).

---

**Tracking:** label `type:feat`, `infra`, `evdev`, `ai-task`, `status:ready`.

## Contexto

`src/hefesto/core/evdev_reader.py:89` tem o comentário histórico:

> `touchpad_press: possível via BTN_TOUCH, mas keycode inconsistente — pendente.`

Esse comentário veio de uma tentativa antiga de escutar no **event20** (gamepad principal), onde o touchpad realmente não emite eventos de botão. `FEAT-KEYBOARD-UI-01 (59.3)` precisa mapear "touchpad esquerda → KEY_BACKSPACE / meio → KEY_ENTER / direita → KEY_DELETE", e sem `touchpad_press` regionalizado a sprint 59.3 fica bloqueada.

## Validação empírica (L-21-7)

Realizada em 2026-04-24, com DualSense USB conectado (VID:PID `054c:0ce6`, kernel driver `hid_playstation`):

```
$ ls /sys/class/input/event*/device/name  | grep -i dualsense
event20: Sony ... DualSense Wireless Controller            # gamepad principal
event21: Sony ... DualSense Wireless Controller Motion     # acelerômetro/giroscópio
event22: Sony ... DualSense Wireless Controller Touchpad   # <-- alvo

$ python3 -c "from evdev import InputDevice; d=InputDevice('/dev/input/event22'); print(d.capabilities(verbose=True))"
# Resultado relevante:
#   EV_KEY: BTN_LEFT (272), BTN_TOOL_FINGER (325), BTN_TOUCH (330), BTN_TOOL_DOUBLETAP (333)
#   EV_ABS: ABS_X (0-1919), ABS_Y (0-1079), ABS_MT_SLOT/POSITION_X/POSITION_Y/TRACKING_ID
```

Constatações:

1. **O touchpad do DualSense expõe SIM um event device separado** (`event22` na máquina de teste). O comentário histórico em `evdev_reader.py:89` estava errado porque olhava no device errado.
2. **`BTN_LEFT` (keycode 272) é estável** e corresponde ao **click físico** do touchpad (press firme até o clique mecânico do ponto pivô). Não vem de toque leve — isso é `BTN_TOUCH` (330).
3. **`ABS_X` (0-1919) e `ABS_Y` (0-1079)** dão a posição do ponto de click em coordenadas absolutas do touchpad. Resolução 1920×1080.
4. **`BTN_TOUCH` + `ABS_MT_*`** expõem tracking multi-touch (até 2 dedos). Fora de escopo desta sprint.

## Decisão

Criar `TouchpadReader` como **classe análoga a `EvdevReader`**, em `src/hefesto/core/evdev_reader.py` (mesmo módulo, para minimizar impacto). Descobre o touchpad device pelo PID + nome contendo "Touchpad"; abre thread dedicada que escuta `BTN_LEFT` + `ABS_X` e emite eventos regionalizados.

### Discriminação por região

Largura do touchpad = 1920px (0 a 1919). Regiões:

- `touchpad_left_press`: ABS_X < 640 (terço esquerdo)
- `touchpad_middle_press`: 640 ≤ ABS_X ≤ 1279
- `touchpad_right_press`: ABS_X ≥ 1280

A região é determinada no momento do evento `BTN_LEFT value=1` usando o último valor de `ABS_X` observado. Quando `BTN_LEFT value=0`, limpa o estado.

### Modo degradado

Caso o device `"...Touchpad"` não seja encontrado (ex: BT sem touchpad separado, firmware diferente), `TouchpadReader.start()` retorna `False` silenciosamente e `is_available()` devolve `False`. Sprint 59.3 consulta `is_available()` e fallback para "touchpad → KEY_ENTER" genérico sem regionalização.

## Critérios de aceite

- [ ] `find_dualsense_touchpad_evdev() -> Path | None` em `src/hefesto/core/evdev_reader.py` devolve path do event device com nome contendo "Touchpad" E vendor/product Sony DualSense.
- [ ] Classe `TouchpadReader` com API análoga a `EvdevReader`:
  - `__init__(device_path: Path | None = None)` — auto-descoberta se None.
  - `is_available() -> bool`.
  - `start() -> bool` — spawn thread; retorna True se device disponível.
  - `stop() -> None` — join thread.
  - `regions_pressed() -> frozenset[str]` — thread-safe; retorna subconjunto de `{"touchpad_left_press", "touchpad_middle_press", "touchpad_right_press"}`.
- [ ] Região calculada via limites 640 / 1280 sobre ABS_X.
- [ ] Auto-reconnect no mesmo padrão do `EvdevReader` (backoff exponencial 0.5→5s; libera estado ao perder conexão).
- [ ] Tests em `tests/unit/test_evdev_reader_touchpad.py` (novo):
  - `test_find_touchpad_encontra_device_correto` — mock de `list_devices` + `InputDevice` fake com nome/vendor/product.
  - `test_find_touchpad_ignora_gamepad_principal` — mesmo vendor/product, mas nome sem "Touchpad".
  - `test_region_from_x_left_middle_right` — função pura `_region_from_x(x: int) -> str` para os 3 casos + edge cases (x=0, x=639, x=640, x=1279, x=1280, x=1919).
  - `test_reader_emite_touchpad_left_press_ao_btn_left` — simula sequence de events (ABS_X=320, BTN_LEFT=1) → `regions_pressed()` retorna `{"touchpad_left_press"}`.
  - `test_reader_limpa_ao_btn_left_release` — mesmo, value=0 limpa.
  - `test_reader_is_available_false_se_device_ausente`.
- [ ] Suite unit passa sem regressão (`.venv/bin/pytest tests/unit -q --no-header`).
- [ ] Ruff + mypy limpos.
- [ ] Comentário `evdev_reader.py:89` (TODO pendente) **removido**.
- [ ] Hardware validation opcional: se o usuário tiver o controle conectado, rodar smoke "pressionar touchpad nas 3 regiões" via script utilitário e confirmar visual.

## Arquivos tocados

- `src/hefesto/core/evdev_reader.py` (adiciona `find_dualsense_touchpad_evdev`, `TouchpadReader` no mesmo módulo; remove comentário TODO de L89).
- `tests/unit/test_evdev_reader_touchpad.py` (novo).

## Proof-of-work

```bash
.venv/bin/pytest tests/unit/test_evdev_reader_touchpad.py -v
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src/hefesto/core/evdev_reader.py tests/unit/test_evdev_reader_touchpad.py
.venv/bin/mypy src/hefesto/core/evdev_reader.py

# Smoke com controle USB (opcional — requer interação humana):
.venv/bin/python3 -c "
from hefesto.core.evdev_reader import TouchpadReader
import time
r = TouchpadReader()
print('available:', r.is_available())
if r.start():
    print('Pressione o touchpad nas 3 regiões (15s)...')
    t0 = time.time()
    while time.time() - t0 < 15:
        s = r.regions_pressed()
        if s: print('  ', sorted(s))
        time.sleep(0.1)
    r.stop()
"
```

## Fora de escopo

- Multi-touch tracking (`ABS_MT_*`). Fica para sprint futura se precisar gesture.
- `BTN_TOUCH` (toque sem press) — 59.3 só precisa de click físico.
- Integração com `EvdevReader.buttons_pressed` existente (mantém canais separados; consumer decide quando consultar).
- Suporte a touchpads de outros controles (Edge etc) — discovery já é genérica por PID, mas teste empírico só feito com 054c:0ce6.

## Notas

- Achado: comentário histórico L89 em `evdev_reader.py` era impreciso. Sprint consolida fact pattern.
- L-21-7 aplicada: capabilities do `/dev/input/event22` foram listadas empiricamente antes do spec, não assumidas.
- Aritmética das regiões: 1920/3 = 640. Limites inteiros, sem sobreposição: `[0, 640)` / `[640, 1280]` / `[1280, 1920)`.

# "Toca que é bom. E discrimina, pô." — Jimi Hendrix, inferido a partir de capabilities.
