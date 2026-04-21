# BUG-MOUSE-TRIGGERS-01 — Gatilhos param de funcionar quando modo Mouse está ativo

**Tipo:** fix (UX crítico).
**Wave:** V1.1.
**Estimativa:** 1-2 iterações (investigação + fix).
**Dependências:** nenhuma.

---

## Sintoma

Usuário aplica um efeito de gatilho (ex.: `Rigid`/`Galloping`) via aba Gatilhos — funciona. Liga toggle da aba Mouse para ativar emulação de mouse — o cursor do mouse responde aos sticks, mas os gatilhos deixam de aplicar (ou voltam a `Off`). O usuário espera que ambos coexistam: mouse emulado E triggers ativos.

## Diagnóstico (a confirmar via rg + leitura)

Hipóteses em ordem de probabilidade:

1. **Autoswitch pisa em triggers manuais**: ao ativar mouse, algum ponto do código pode re-aplicar o perfil ativo (fallback) que tem `triggers.{left,right} = "Off"`, sobrescrevendo o que o usuário tinha configurado manualmente. Verificar em `lifecycle.py::_dispatch_mouse_emulation` ou `_start_mouse_emulation` se chama `profile_manager.apply()`.

2. **Poll do mouse chama `controller.set_trigger(Off)` implicitamente**: `UinputMouseDevice.dispatch(state)` lê `l2_raw`/`r2_raw` do estado para emitir BTN_LEFT/BTN_RIGHT — se por algum motivo invoca `controller.set_trigger(...)` ou reseta o efeito, derruba o que foi aplicado.

3. **Conflito de backend**: `PyDualSenseController` pode não suportar triggers + polling agressivo simultâneos, causando re-envio do estado Off para o hardware.

4. **UI toggle Mouse também desliga triggers**: `on_mouse_toggle_set` pode estar limpando outras configurações (verificar).

## Critérios de aceite

- [ ] Investigação documentada: qual das 4 hipóteses (ou outra) é verdadeira. `rg` grep com identificadores (`set_trigger`, `trigger.set`, `profile_manager.apply`, `dispatch`) comprova a causa.
- [ ] Fix cirúrgico: isolar a causa. Mouse e Triggers devem poder coexistir sem um derrubar o outro.
- [ ] Teste unitário `tests/unit/test_mouse_triggers_coexist.py` (novo): cobre cenário mock onde `UinputMouseDevice.dispatch(state)` roda N vezes e o estado de `controller.set_trigger(...)` NÃO é chamado como side-effect.
- [ ] Proof-of-work runtime: com DualSense real plugado, aplicar trigger `Galloping` no R2 via aba Gatilhos → sentir vibração. Ligar mouse toggle → mouse funciona. Gatilhos continuam vibrando. Capturar print da GUI em cada estado.
- [ ] `.venv/bin/pytest tests/unit -q` verde (335+ testes).

## Arquivos tocados (previsão)

- `src/hefesto/daemon/lifecycle.py` (provável)
- `src/hefesto/integrations/uinput_mouse.py` (se o dispatch mexer em triggers)
- `src/hefesto/app/actions/mouse_actions.py` (se o toggle resetar)
- `tests/unit/test_mouse_triggers_coexist.py` (novo)

## Notas para o executor

- Começar por `rg "set_trigger|apply_profile|dispatch_mouse"` para mapear quem chama o quê.
- Se confirmar hipótese 1, remover chamada a `profile_manager.apply()` de dentro do start/dispatch do mouse.
- Se hipótese 3, aceitar que hardware limita e documentar ADR nova.
