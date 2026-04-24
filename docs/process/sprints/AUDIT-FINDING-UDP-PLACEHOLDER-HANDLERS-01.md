# AUDIT-FINDING-UDP-PLACEHOLDER-HANDLERS-01 — UDP PlayerLED/MicLED propagam no hardware + clamp RGB

**Origem:** achados 1 e 19 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** S (≤3h). **Severidade:** alto.
**Tracking:** label `type:bug`, `ai-task`, `status:ready`.

## Contexto

O servidor UDP (compatibilidade DSX / Paliverse) em `src/hefesto/daemon/udp_server.py` declara 6 tipos de instrução no docstring do módulo, mas 3 dos handlers só fazem `store.bump(...)` sem propagar ao hardware. Dois desses (PlayerLED, MicLED) têm backend funcional disponível em `PyDualSenseController` (`set_player_leds`, `set_mic_led`). Jogos DSX-compatíveis enviam esses comandos e recebem confirmação silenciosa sem efeito. Um achado adicional: UDP `RGBUpdate` não faz clamp 0-255 nos bytes — inconsistência com IPC `led.set` que valida.

## Objetivo

1. `_do_player_led`: decodificar `bitmask` em `tuple[bool, bool, bool, bool, bool]` e chamar `self.controller.set_player_leds(bits)`.
2. `_do_mic_led`: chamar `self.controller.set_mic_led(state)` após decodificar bool.
3. `_do_rgb_update`: clampar `int(v)` em `[0, 255]` para cada canal antes de passar ao `set_led`.
4. `_do_trigger_threshold`: decidir na spec se entra neste escopo ou vira sprint separada — sugestão **fora de escopo** aqui (semântica ambígua no schema).

## Critérios de aceite

- [ ] `_do_player_led` chama `controller.set_player_leds(bits)` com tuple de 5 bool derivado do bitmask. Bit `i` → `bits[i]`.
- [ ] `_do_mic_led` chama `controller.set_mic_led(state)` com bool derivado de `params[0]`.
- [ ] `_do_rgb_update` usa `max(0, min(255, int(v)))` para cada canal ou levanta ValueError se fora de range (decisão no spec — sugestão clamp silencioso para manter compat com clients imprecisos).
- [ ] `store.bump(...)` preservado em todos os 3 handlers para métricas.
- [ ] Testes unitários em `tests/unit/test_udp_server.py`: 1 teste por handler confirmando que o método do mock controller é chamado com os args corretos. Mock controller pode usar `FakeController` de `hefesto.testing`.
- [ ] Comentários obsoletos "backend ainda não expõe player LED API" / "backend ainda não expõe" removidos.
- [ ] Proof-of-work runtime: smoke UDP real enviando payload `{"version":1,"instructions":[{"type":"PlayerLED","parameters":[0,21]}]}` e confirmando `counters["udp.applied.PlayerLED"] >= 1` + hardware respondendo.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
.venv/bin/pytest tests/unit/test_udp_server.py -v --no-header -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
HEFESTO_FAKE=1 HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
```

Esperado: `tests/unit/test_udp_server.py` passa com ≥3 novos testes. Suite total segue 1140+ pass. Smoke verde.

## Fora de escopo

- `_do_trigger_threshold` — semântica do campo não definida no schema DSX público; separar para outra sprint de produto com decisão de owner.
- Rate limiting — já implementado e correto.
- Schema JSON-RPC / documentação do protocolo — atualização de `docs/protocol/udp-schema.md` vira edit paralelo no mesmo commit se trivial.

## Notas

Antes de abrir PR: rodar `grep -rn "UDP" docs/protocol/` para atualizar qualquer doc de protocolo que afirme que os 3 handlers são noop.
