# AUDIT-FINDING-PROFILE-MIC-LED-RESET-01 — mic LED não é resetado em profile switch

**Origem:** achados 3 e 25 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** M (≤6h). **Severidade:** alto.
**Tracking:** label `type:bug`, `ai-task`, `status:ready`.

## Contexto

`src/hefesto/core/led_control.py::apply_led_settings` chama `controller.set_mic_led(settings.mic_led)` incondicionalmente. Como `LedsConfig` (schema de perfil) não tem campo `mic_led`, o `_to_led_settings` em `profiles/manager.py` não o propaga — fica no default `False`. Resultado: cada `profile.switch` ou `autoswitch` emite `set_mic_led(False)` ao hardware, apagando o LED do mic se usuário o havia muteado via botão físico ou IPC.

Armadilha **A-06** em `VALIDATOR_BRIEF.md` cobre o caso "campo novo em `*Config` precisa sprint-par de profile-apply" mas não cobre o inverso (campo **ausente** no schema mas aplicado pelo `apply_*`).

## Objetivo

Três opções possíveis (escolher na execução; recomendada é **(c)**):

- **(a)** adicionar `mic_led: bool = False` a `LedsConfig`, propagar em `_to_led_settings`, populá-lo em `_build_profile_from_editor` (GUI).
- **(b)** criar função separada `apply_mic_led(controller, state)` invocada só por paths explícitos (IPC `led.mic_set` futuro); remover a chamada de `apply_led_settings`.
- **(c)** tratar `mic_led` como estado runtime puro, nunca persistido em perfil. Remover `controller.set_mic_led(settings.mic_led)` de `apply_led_settings` e remover o campo `mic_led` de `LedSettings` também (ou documentar como no-op).

Após decisão, atualizar `VALIDATOR_BRIEF.md` armadilha A-06 com variante adicional: "campo ausente em `*Config` mas aplicado pelo apply com default pode regredir estado runtime".

## Critérios de aceite

- [ ] Chamada `controller.set_mic_led(...)` em `apply_led_settings` removida OU condicional a campo `mic_led` presente em `LedsConfig`.
- [ ] Teste unitário em `tests/unit/test_led_and_rumble.py` ou novo `tests/unit/test_mic_led_persistence.py`: instancia FakeController, muteia mic via `set_mic_led(True)`, chama `apply_led_settings(controller, LedSettings(lightbar=(255,0,0)))` (sem mic_led explícito), confirma que `controller.mic_led_state` continua `True`.
- [ ] Teste unitário (se opção a): perfil JSON com `leds.mic_led: true` carrega e reaplica.
- [ ] `VALIDATOR_BRIEF.md` A-06 atualizada com variante.
- [ ] Suite passa verde; ruff + mypy limpos.
- [ ] Proof-of-work runtime: em hardware real, mutar mic (botão físico) → trocar perfil via `hefesto profile activate acao` → confirmar que LED do mic segue aceso.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
.venv/bin/pytest tests/unit/test_led_and_rumble.py tests/unit/test_profile_manager.py -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
# Hardware: hefesto daemon start --foreground &
# (botão mic físico) depois hefesto profile activate acao
# Confirmar visualmente que mic LED segue aceso
```

## Fora de escopo

- Adicionar IPC handler `led.mic_set` dedicado — separar em sprint futura se opção (b) for escolhida.
- Refactor maior de `LedSettings` para torná-lo opcional campo-a-campo (ex.: `Optional[bool]` para cada setting) — adiar para sprint de arquitetura.

## Notas

A GUI atualmente expõe mic_led via botão físico + IPC runtime, não via aba Perfis. Opção (c) mantém essa separação clara e é mais simples.
