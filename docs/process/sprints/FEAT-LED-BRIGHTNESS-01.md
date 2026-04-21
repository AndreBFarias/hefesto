# FEAT-LED-BRIGHTNESS-01 — Controle de luminosidade do lightbar

**Tipo:** feat (UX).
**Wave:** V1.1.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** issue [#70](https://github.com/AndreBFarias/hefesto/issues/70) — fechada por PR com `Closes #70` no body.

## Contexto

Lightbar do DualSense hoje aceita apenas RGB 0-255 por canal. A GUI (aba Lightbar) expõe cor via `GtkColorButton` e botões preset, mas não expõe luminosidade (brightness) independente da cor. O usuário quer um slider para atenuar sem mudar o matiz — ex.: cor favorita 50% menos intensa para não ofuscar à noite.

## Decisão

Implementar brightness como multiplicador aplicado aos valores RGB antes de enviar ao HID. Schema do perfil ganha campo opcional `leds.lightbar_brightness: float` (0.0-1.0, default 1.0); quando aplicado, os canais RGB viram `int(channel * brightness)` com clamp 0-255.

GUI ganha `GtkScale` 0-100 (%) na aba Lightbar ao lado da cor. Valor inicial 100 (máximo).

## Critérios de aceite

- [ ] `src/hefesto/profiles/schema.py` — `LedsConfig` (pydantic) ganha `lightbar_brightness: float = Field(default=1.0, ge=0.0, le=1.0)`. Retrocompatível: perfis v1 sem o campo assumem 1.0.
- [ ] `src/hefesto/core/led_control.py` — `LedSettings.apply_brightness(level: float) -> LedSettings` devolve cópia com cores escaladas + clamp. Uso: `backend.set_led(settings.apply_brightness(0.5))`.
- [ ] `src/hefesto/app/actions/lightbar_actions.py` — novo `GtkScale id="lightbar_brightness_scale"` (0-100) e handler `on_lightbar_brightness_changed(scale)`. Salva no state e chama `led.set` via IPC com RGB pós-escala.
- [ ] `src/hefesto/daemon/ipc_server.py` — método `led.set` aceita parâmetro opcional `brightness: float` que é multiplicado no backend.
- [ ] `src/hefesto/gui/main.glade` — aba Lightbar ganha label "Luminosidade" + `GtkScale` horizontal com `GtkAdjustment` 0-100 step 1 page 10 value 100.
- [ ] `assets/profiles_default/*.json` — todos os 4 existentes ganham `"lightbar_brightness": 1.0` explicitamente para clareza.
- [ ] Teste `tests/unit/test_led_brightness.py`: (a) default 1.0 não altera RGB; (b) 0.5 divide canais pela metade; (c) 0.0 zera; (d) clamp funciona para float > 1.0 (caso futuro).
- [ ] Proof-of-work visual: GUI com slider em 50% + PNG.

## Arquivos tocados (previsão)

- `src/hefesto/profiles/schema.py`
- `src/hefesto/core/led_control.py`
- `src/hefesto/app/actions/lightbar_actions.py`
- `src/hefesto/daemon/ipc_server.py`
- `src/hefesto/gui/main.glade`
- `assets/profiles_default/{bow,driving,fallback,shooter}.json`
- `tests/unit/test_led_brightness.py` (novo)

## Fora de escopo

- Luminosidade dos player LEDs (padrão hardware não suporta PWM nativo por LED).
- Curva de resposta não-linear (gamma correction) — opcional V2.

## Notas

- HID da DualSense não tem campo brightness nativo; o produto é pre-aplicado em software.
- Clamp: `max(0, min(255, int(channel * brightness)))`.
