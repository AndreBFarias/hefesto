# FEAT-LED-BRIGHTNESS-03 — Persist handler GUI: brightness vai pro perfil salvo

**Tipo:** feat-completion (sprint-filha de FEAT-LED-BRIGHTNESS-01).
**Wave:** V1.1 — fase 5.
**Estimativa:** XS.
**Dependências:** FEAT-LED-BRIGHTNESS-01 (feita), FEAT-LED-BRIGHTNESS-02 (propaga no ProfileManager).

---

**Tracking:** issue a criar. Origem: armadilha **A-06** em `VALIDATOR_BRIEF.md`.

## Contexto

O slider `lightbar_brightness` existe na GUI e aplica no daemon via IPC (FEAT-LED-BRIGHTNESS-01). Mas: ao **salvar perfil** (ou ativar outro e voltar), o valor do slider é esquecido. O perfil persistido não contém o último brightness editado pelo usuário.

## Decisão

1. Handler `on_lightbar_brightness_changed` escreve em `self.draft.leds.lightbar_brightness` (depende de FEAT-PROFILE-STATE-01 — se `DraftConfig` ainda não foi implementado, armazenar em `self._last_brightness` transiente e serializar via profile save).
2. Ao salvar o perfil (aba Perfis → botão Salvar; ou rodapé Salvar Perfil de UI-GLOBAL-FOOTER-ACTIONS-01), o JSON resultante inclui `leds.lightbar_brightness`.
3. Ao carregar um perfil (profile.switch), a GUI recebe `state_full` com `leds.lightbar_brightness` e **move o slider** via `set_value(brightness)` — signals bloqueadas com guard pra não disparar um IPC loop.

## Critérios de aceite

- [ ] `src/hefesto/app/actions/lightbar_actions.py::on_lightbar_brightness_changed`: atualiza `self.draft.leds.lightbar_brightness` (via `model_copy`) se FEAT-PROFILE-STATE-01 já entregue. Caso contrário, escreve em `self._pending_brightness`.
- [ ] `src/hefesto/app/actions/profiles_actions.py::_save_profile_from_editor`: inclui `leds.lightbar_brightness` no Profile gerado. Similar pra `save_as_profile` do rodapé.
- [ ] `src/hefesto/app/actions/lightbar_actions.py::_refresh_lightbar_from_state`: lê `state_full['leds']['lightbar_brightness']` e atualiza slider via `_guard_refresh=True` pattern.
- [ ] Teste `tests/unit/test_lightbar_persist.py`: mock GUI actions; simular ciclo `set brightness 25 → save → load` → valor 25 preservado.
- [ ] Proof-of-work visual: slider em 25%, salvar perfil, trocar pra fallback, voltar — slider ainda em 25%. Screenshot.

## Arquivos tocados

- `src/hefesto/app/actions/lightbar_actions.py`
- `src/hefesto/app/actions/profiles_actions.py`
- `tests/unit/test_lightbar_persist.py` (novo)

## Notas para o executor

- **Guard pattern**:
  ```python
  self._refresh_guard = True
  try:
      self._get("lightbar_brightness_scale").set_value(brightness)
  finally:
      self._refresh_guard = False
  ```
  O handler `on_lightbar_brightness_changed` checa `if self._refresh_guard: return` no começo.
- Se o perfil vem sem `lightbar_brightness` (perfil v0 antigo), default 100 (sem dimming).
- Resolve formalmente A-06 (completando FEAT-LED-BRIGHTNESS-02 + 03). Marcar no BRIEF.
