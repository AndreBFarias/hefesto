# FEAT-KEYBOARD-PERSISTENCE-01 — Persistência de key bindings por perfil

**Tipo:** feat (médio — aditivo).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Modelo sugerido:** opus.
**Dependências:** FEAT-KEYBOARD-EMULATOR-01 (merged).
**Sprint-mãe:** FEAT-MOUSE-TECLADO-COMPLETO-01 (dividida em 3 filhas).

---

**Tracking:** label `type:feat`, `profiles`, `kbd-emu`, `ai-task`, `status:ready`.

## Contexto

FEAT-KEYBOARD-EMULATOR-01 entregou `UinputKeyboardDevice` + `DEFAULT_BUTTON_BINDINGS`
hardcoded cobrindo Options/Share/L1/R1. Agora falta expor overrides por perfil: o
usuário quer salvar "neste perfil Triangle emite KEY_C" sem afetar os outros.

Armadilha A-06 é **certeira** aqui: campo novo em `ProfileConfig` exige mapper
propagando + teste integration. Planejador-mestre já avisou.

## Decisão

1. **Schema**: adicionar em `src/hefesto/profiles/schema.py`:
   ```python
   class Profile(BaseModel):
       ...
       key_bindings: dict[str, list[str]] | None = None
   ```
   - `None` = usar `DEFAULT_BUTTON_BINDINGS` do core.
   - `{}` = desativar todos os bindings do perfil.
   - `{"triangle": ["KEY_C"]}` = override isolado.
   - Validador garante nomes `KEY_*` conhecidos via `evdev.ecodes` lookup.

2. **Mapper em `profiles/manager.py`** (A-06 — NÃO ESQUECER):
   - `ProfileManager.apply(profile)` resolve o `key_bindings` efetivo:
     `profile.key_bindings if not None else DEFAULT_BUTTON_BINDINGS`.
   - Propaga via `daemon._keyboard_device.set_bindings(resolved)` se device existe.
   - Precisa de canal do manager para o daemon — hoje manager só recebe
     `controller`. Opções: (a) injetar `keyboard_device` opcional no manager;
     (b) publicar evento no bus que o daemon consome; (c) manager ganha método
     `apply_keyboard(device)` chamado pelo `Daemon` após profile.switch.
     Escolher opção **(c)** por ser menos invasiva e symmetric ao padrão de
     `apply_led_settings(controller, settings)`.
   - Adicionar helper puro `_to_key_bindings(profile) -> dict[str, tuple[str, ...]]`
     análogo a `_to_led_settings`.

3. **JSONs defaults**: `assets/profiles_default/*.json` ganham `"key_bindings": null`
   para usar defaults. 1 perfil exemplo (criar `teclado_c.json` ou reaproveitar
   `text_editor.json` se existir) com `"key_bindings": {"triangle": ["KEY_C"]}`
   como amostra.

4. **IPC**: `profile.switch` já chama `manager.activate` que chama `apply` — se
   `apply_keyboard(device)` for invocado junto, propagação é automática. Validar
   com smoke IPC real.

## Critérios de aceite

- [ ] `Profile.key_bindings: dict[str, list[str]] | None` com validator.
- [ ] `_to_key_bindings(profile)` resolve `None` → defaults, `{}` → vazio,
      `{"triangle": ["KEY_C"]}` → `{"triangle": ("KEY_C",)}`.
- [ ] `ProfileManager.apply_keyboard(device)` invocado pelo daemon em `profile.switch`.
- [ ] Teste `tests/unit/test_profile_key_bindings.py::test_apply_propaga_key_bindings`
      (armadilha A-06) com FakeController + mock de keyboard_device, confirma que
      `set_bindings` é chamado com o mapping resolvido.
- [ ] Teste `test_to_key_bindings_none_usa_defaults`,
      `test_to_key_bindings_vazio_desativa`,
      `test_to_key_bindings_override_parcial`.
- [ ] Teste IPC: `tests/unit/test_ipc_profile_switch_propaga_teclado.py` —
      switch de perfil com override faz daemon ver `set_bindings(novo_mapping)`.
- [ ] Validator rejeita `KEY_INEXISTENTE` com erro claro.
- [ ] JSONs default têm `key_bindings: null` (8 perfis).
- [ ] Smoke USB+BT verdes sem traceback.
- [ ] Suite unit passa sem regressão (>1036).

## Arquivos tocados

- `src/hefesto/profiles/schema.py` — campo novo + validator.
- `src/hefesto/profiles/manager.py` — `_to_key_bindings`, `apply_keyboard`.
- `src/hefesto/daemon/lifecycle.py` — hook no `profile_activated` para chamar
  `manager.apply_keyboard(daemon._keyboard_device)` **ou** via IPC subsystem.
- `assets/profiles_default/*.json` — adicionar `"key_bindings": null`.
- `tests/unit/test_profile_key_bindings.py` (novo).
- `tests/unit/test_ipc_profile_switch_propaga_teclado.py` (novo).

## Proof-of-work runtime

```bash
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto
./scripts/check_anonymity.sh
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt

# Cenário manual:
# 1. Criar perfil "test_c" com {"triangle": ["KEY_C"]}.
# 2. hefesto profile switch test_c
# 3. Pressionar triangle via FakeController input injection ou hardware real.
# 4. Verificar journal: 'key_binding_emit button=triangle keys=["KEY_C"]'.
```

## Notas para o executor

- Armadilha A-06: mapper precisa de teste **dedicado**. Sem ele sprint é rejeitada.
- Hook do daemon após `profile.activate`: ver exemplo de `apply_led_settings`
  chamado dentro de `ProfileManager.apply()`. Mesma ideia: `manager.apply_keyboard`
  recebe `device_or_none` e chama `set_bindings` se vivo.
- Sprint-mãe ainda tem filha FEAT-KEYBOARD-UI-01 para UI TreeView + L3/R3 +
  onboard. Esta entrega aqui destrava a próxima.

## Fora de escopo

- UI de edição de bindings (fica para FEAT-KEYBOARD-UI-01).
- L3/R3 abrindo teclado virtual (fica para FEAT-KEYBOARD-UI-01).
- Inversão R2/L2 (fica para FEAT-KEYBOARD-UI-01 depois que UI existir).

# "Não há nada permanente, exceto a mudança." — Heráclito
