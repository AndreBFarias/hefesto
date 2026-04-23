# BUG-PLAYER-LEDS-APPLY-01 — Player LEDs sem botão Aplicar e inoperantes ao marcar

**Tipo:** bug (feature incompleta).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma (FEAT-PLAYER-LEDS-APPLY-01 original já deveria cobrir isso — regressão ou incompleta).

---

**Tracking:** label `type:bug`, `P1`, `ui`, `hardware`, `ai-task`, `status:ready`.

## Sintoma

Usuário reporta em 2026-04-23 testando v2.1.0:

> "os leds do jogador ainda não possuem botão de aplicar e não funcionam quando eu deixo marcado."

Fluxo esperado (conforme sprint original **FEAT-PLAYER-LEDS-APPLY-01** em V1.2):

1. Aba Lightbar (ou Status/avançada) tem 5 checkboxes representando bitmask `0b11111` dos 5 LEDs do jogador no DualSense.
2. Usuário marca o padrão desejado (ex.: `0b10101`).
3. Clica em **Aplicar** (botão dedicado na seção — não o "Aplicar" do footer) ou aplica via footer global.
4. Handler IPC `led.player_set` com `{"mask": 0b10101}` vai ao daemon.
5. Daemon chama `controller.set_player_leds(mask)` → HID output report.
6. LEDs do controle refletem visualmente.

Hipóteses do que pode estar quebrado:

- **H1**: Checkboxes não têm signal `toggled` ligado ou callback não monta o payload corretamente.
- **H2**: Handler `led.player_set` não existe ou espera formato diferente.
- **H3**: Botão "Aplicar" dedicado foi removido na reorganização da aba; usuário precisa usar footer global; mas footer não sabe que há mudança pendente em Player LEDs.
- **H4**: `controller.set_player_leds` implementado no FakeController mas não no backend pydualsense real.

## Decisão

1. Auditar trio: `assets/profiles_default/*.json` (há chave `player_leds`?), `src/hefesto/core/led_control.py` (função `set_player_leds`?), `src/hefesto/daemon/ipc_server.py` (handler `led.player_set`?).
2. Se handler existe mas GUI não dispara: adicionar botão **Aplicar LEDs** próximo aos 5 checkboxes + callback que coleta bitmask + envia IPC.
3. Se handler não existe: criar seguindo o padrão dos outros LEDs.
4. Backend pydualsense: confirmar que `self.ds.setPlayerID(mask)` ou equivalente existe; se não, adicionar ao backend real via output report.
5. Teste `tests/unit/test_player_leds_apply.py`: mock IPC, verificar que toggle dos 5 checkboxes + clique em Aplicar envia payload correto.

## Critérios de aceite

- [ ] Botão "Aplicar LEDs" visível na aba onde vivem os 5 checkboxes.
- [ ] Marcar `0b10101` + Aplicar → LEDs do controle refletem (FakeController loga; hardware real confere via checklist HARDWARE-VALIDATION-PROTOCOL-01 item 1).
- [ ] Desmarcar tudo + Aplicar → todos os LEDs apagam (mask `0b00000`).
- [ ] Persistência no perfil: `profile.save` inclui `player_leds: <mask>`; reload do perfil reaplica automaticamente.
- [ ] Teste unitário cobrindo o fluxo.
- [ ] Screenshot da aba com o botão.

## Arquivos tocados (hipótese)

- `src/hefesto/app/actions/<aba>.py` (handler do botão novo).
- `src/hefesto/gui/main.glade` (botão + checkboxes wire-up).
- `src/hefesto/daemon/ipc_server.py` (handler, se ausente).
- `src/hefesto/core/led_control.py` (função, se ausente).
- `src/hefesto/profiles/schema.py` (campo `player_leds: int = 0` em `LedsConfig` se ausente).
- `src/hefesto/profiles/manager.py` (propagar no `_to_led_settings` — armadilha A-06).
- `tests/unit/test_player_leds_apply.py`.

## Proof-of-work runtime

```bash
systemctl --user start hefesto.service
sleep 2
# Via CLI
hefesto led player 0b10101
# FakeController deve logar; log: "led.player_mask_set mask=21"

# Via GUI
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.app.main &
# Marcar checkboxes 1, 3, 5
# Clicar em Aplicar LEDs
# Verificar log em structlog-pretty

.venv/bin/pytest tests/unit/test_player_leds_apply.py -v
.venv/bin/pytest tests/unit -q
```

## Fora de escopo

- Mudar paleta das cores do LED (LED do jogador é on/off binário, sem cor).
- Animação/fade dos LEDs.
