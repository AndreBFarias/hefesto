# FEAT-PLAYER-LEDS-APPLY-01 — Envio real dos Player LEDs ao hardware

**Tipo:** feat (fecha lacuna funcional).
**Wave:** V1.1 — fase 5.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** issue a criar.

## Sintoma (reportado em 2026-04-22)

> leds do jogador não funciona ou falta um botão aplicar.

Captura mostra 5 checkboxes de LED + presets "Todos / Player 1 / Player 2 / Nenhum" com legenda:

> *Seleção fica registrada para salvar no perfil ativo; envio direto ao hardware chega em extensão futura do backend.*

Ou seja, a UI foi entregue sem o backend. Cumprir a promessa.

## Contexto técnico

DualSense tem 5 LEDs frontais (os "tickmarks" ao redor do touchpad que indicam player 1-4 no PS5). São bitmask de 5 bits. A lib `pydualsense` expõe:

- `PlayerID = 0..4` para player number (4 LEDs iluminados padrão PlayerN).
- Controle direto via `dualsense.setPlayerID(N)` OU `dualsense.lightbar.setPlayerNumber(N)` (depende versão).
- Para bitmask custom (5 LEDs arbitrários), precisa setar `dualsense.player_number` bit-a-bit ou usar report HID bruto.

Hoje `src/hefesto/core/backend_pydualsense.py` já tem método `set_player_leds(bitmask: int)` (verificar) ou é preciso adicionar.

## Decisão

1. Contrato core `IController.set_player_leds(bits: tuple[bool, bool, bool, bool, bool]) -> None`.
2. Implementação em `PyDualSenseController.set_player_leds` via `self._pds.setPlayerID(...)` se o bitmask casar com PlayerID canônico; caso contrário, escrita HID direta (ver snippet abaixo).
3. Handler IPC novo `led.player_set {bits: [bool, bool, bool, bool, bool]}`.
4. Aba Lightbar da GUI:
   - Handler `on_player_leds_preset_all` etc. já existe (hoje só seta checkboxes). Agora também chama IPC `led.player_set` com bitmask correspondente.
   - Checkboxes individuais: handler `on_player_led_toggled` chama `led.player_set` com bitmask recalculado.
   - Legenda atualizada: remover "envio direto ao hardware chega em extensão futura" (falsidade).
5. `DraftConfig.leds.player_leds` (spec FEAT-PROFILE-STATE-01) já prevê o slot.

## Implementação HID direta (se pydualsense não expõe bitmask arbitrário)

```python
# DualSense output report 0x02 (USB) ou 0xa2 (BT) contém 2 bytes de flags Player LED:
# byte[43] bits 0-4 = LED1..LED5 on/off (com mask bit em outro byte).
# Referenciar docs/protocol/dualsense-hid.md se existir, ou brincar com:
#   dualsense = self._pds  # pydualsense.dualsense instance
#   dualsense.player_number = bitmask_int  # se atributo existe
#   dualsense.writeReport()
```

Executor deve confirmar via `dir(dualsense)` + reverse engineering controlado (script de teste isolado antes de mexer no daemon).

## Contrato IPC

```json
// request
{"jsonrpc":"2.0","id":"1","method":"led.player_set","params":{"bits":[true,true,false,false,false]}}
// response
{"jsonrpc":"2.0","id":"1","result":{"status":"ok","bits":[true,true,false,false,false]}}
```

## Critérios de aceite

- [ ] `src/hefesto/core/controller.py`: interface `IController` ganha `set_player_leds(bits: tuple[bool, bool, bool, bool, bool]) -> None`.
- [ ] `src/hefesto/core/backend_pydualsense.py`: implementação real com pydualsense. Se bitmask não é PlayerID canônico, usa HID direto.
- [ ] `src/hefesto/testing/fake_controller.py`: implementação no-op que guarda `self.last_player_leds` para testes.
- [ ] `src/hefesto/daemon/ipc_server.py`: handler `led.player_set`. Retorna bitmask aplicado.
- [ ] `src/hefesto/app/ipc_bridge.py`: função `player_leds_set(bits) -> bool`.
- [ ] `src/hefesto/app/actions/lightbar_actions.py`:
  - Handler de cada checkbox chama `player_leds_set(bits)`.
  - Presets "Todos/Player 1/Player 2/Nenhum" chamam `player_leds_set(bits_preset)`.
- [ ] `src/hefesto/gui/main.glade`: atualizar legenda (remover promessa "extensão futura").
- [ ] Teste `tests/unit/test_player_leds.py`:
  - FakeController recebe set; `last_player_leds` reflete.
  - IPC handler retorna response correto.
- [ ] Proof-of-work com hardware real:
  1. Abrir GUI.
  2. Aba Lightbar → Player LEDs: marcar só LED1 e LED3. Ver hardware: LEDs 1 e 3 acendem, 2/4/5 apagam.
  3. Preset "Todos" → 5 LEDs acendem. Preset "Nenhum" → 5 apagam.
  4. Screenshot + foto do controle (opcional; descrever em texto o que se vê).

## Arquivos tocados

- `src/hefesto/core/controller.py`
- `src/hefesto/core/backend_pydualsense.py`
- `src/hefesto/testing/fake_controller.py`
- `src/hefesto/daemon/ipc_server.py`
- `src/hefesto/app/ipc_bridge.py`
- `src/hefesto/app/actions/lightbar_actions.py`
- `src/hefesto/gui/main.glade`
- `tests/unit/test_player_leds.py` (novo)

## Fora de escopo

- Animação pulsante dos LEDs (V2 se houver demanda).
- Sync com PlayerID do perfil (pegar o `priority` e mapear pra Player N) — ideia boa, mas sai de escopo.

## Notas para o executor

- Antes de mexer no daemon, criar `scripts/test_player_leds.py` isolado que conecta via pydualsense direto e testa todas as combinações `(bit0, bit1, bit2, bit3, bit4)` (32 combos). Confirma qual atributo/método da lib aplica. Só então portar pro backend.
- `PlayerID` da pydualsense pode estar "off-by-one" (PlayerID=0 pode acender LED central sozinho em vez de nenhum). Mapear empiricamente.
- Bitmask persiste no controle até próximo comando HID — não precisa re-asserção.
- Aviso: pydualsense pode ter bug em setPlayerID que zera lightbar RGB. Se aparecer, enviar `setColorI` novamente após `setPlayerID`. Documentar em discovery se acontecer.

## Armadilha candidata (descobrir durante execução)

Se ocorrer um "campo novo em LedsConfig precisa atualizar `_to_led_settings`" (A-06 do BRIEF), seguir o padrão: adicionar `player_leds` ao `LedsConfig` schema + `_to_led_settings` + JSONs de perfil default + teste de propagação.
