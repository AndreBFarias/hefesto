# FEAT-LED-BRIGHTNESS-02 — Propagação de `lightbar_brightness` no ProfileManager.apply()

**Tipo:** fix / feat-completion (sprint-filha de FEAT-LED-BRIGHTNESS-01).
**Wave:** V1.1 — fase 5.
**Estimativa:** XS.
**Dependências:** FEAT-LED-BRIGHTNESS-01 (já feita).

---

**Tracking:** issue a criar. Origem: armadilha **A-06** em `VALIDATOR_BRIEF.md`.

## Contexto

FEAT-LED-BRIGHTNESS-01 (PR #95) adicionou `lightbar_brightness` ao schema `LedsConfig`, aos 4 JSONs default e ao slider da GUI. Validador observou em 2026-04-21 que o mapper `_to_led_settings` (em `src/hefesto/profiles/manager.py`) ainda lê apenas o subconjunto fixo de campos antigos — o `lightbar_brightness` chega ao disco mas **não chega ao hardware** quando autoswitch troca perfil.

Trecho `src/hefesto/profiles/manager.py:85-93` (aproximado):

```python
def _to_led_settings(leds_config: LedsConfig) -> LedSettings:
    return LedSettings(
        r=leds_config.lightbar_rgb[0],
        g=leds_config.lightbar_rgb[1],
        b=leds_config.lightbar_rgb[2],
    )
```

Falta `brightness=leds_config.lightbar_brightness`.

## Decisão

1. Propagar `lightbar_brightness` para `LedSettings`. Se `LedSettings` ainda não tem o campo, adicionar (`src/hefesto/core/led_settings.py`).
2. Atualizar `_to_led_settings` em `manager.py`.
3. Adicionar teste de propagação em `tests/unit/test_profile_manager.py`.
4. Varredura em `_to_led_settings`-like para **outros campos** de `LedsConfig`: `player_leds`, `mic_led`. Se algum deles foi adicionado e não está sendo propagado, propagar também. (Já resolve pré-FEAT-PLAYER-LEDS-APPLY-01).

## Critérios de aceite

- [ ] `src/hefesto/core/led_settings.py` tem campo `brightness: int = 100` (default sem dimming).
- [ ] `src/hefesto/profiles/manager.py::_to_led_settings` lê e repassa `lightbar_brightness` de `LedsConfig`.
- [ ] `src/hefesto/core/backend_pydualsense.py::set_led(led_settings)` aplica brightness (chama `self._pds.lightbar.setBrightness(value)` ou equivalente).
- [ ] `tests/unit/test_profile_manager.py::test_apply_propaga_brightness`:
  - Monta `Profile` com `leds.lightbar_brightness = 25`.
  - `ProfileManager(controller=FakeController).apply(profile)` → `FakeController.last_led.brightness == 25`.
- [ ] Smoke USB: aplicar perfil com brightness baixo (25) em controle real → lightbar visivelmente mais apagada.

## Arquivos tocados

- `src/hefesto/core/led_settings.py`
- `src/hefesto/core/backend_pydualsense.py`
- `src/hefesto/testing/fake_controller.py` (registrar `last_led.brightness`)
- `src/hefesto/profiles/manager.py`
- `tests/unit/test_profile_manager.py`

## Notas para o executor

- `pydualsense.lightbar` API pode ter `setBrightness(value)` com `value: 0-3` ou `0-100`. Conferir e mapear. O slider da GUI gera 0-100; mapear pra range aceito pelo HW.
- Se `pydualsense` não expõe brightness (algumas versões não), implementar via HID raw (bit no report de LED). Documentar.
- Resolve parcialmente A-06 do BRIEF — marcar como "resolvido pra brightness" no comentário da armadilha. FEAT-LED-BRIGHTNESS-03 fecha o handler GUI.
