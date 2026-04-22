# BUG-RUMBLE-APPLY-IGNORED-01 — "Aplicar rumble" não respeita os valores setados

**Tipo:** fix (funcional).
**Wave:** V1.1 — fase 5.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** issue a criar.

## Sintoma (reportado em 2026-04-22)

> Mas ao aplicar ele não respeita essa decisão.

Usuário configura sliders `weak` e `strong` na aba Rumble, clica "Aplicar rumble", **não sente a vibração** com os valores setados. "Testar por 500 ms" pulsa rapidamente, mas "Aplicar" e deixar ligado não produz vibração contínua esperada.

## Diagnóstico provável

Há dois caminhos possíveis (executor confirma via `rg` antes de aplicar fix):

**Hipótese A — IPC aceita mas daemon não persiste:**
O handler `rumble.set` em `src/hefesto/daemon/ipc_server.py` pode estar chamando `RumbleEngine.pulse()` em vez de `.set()`. `pulse()` dura ~500ms por design. `.set()` é contínuo.

**Hipótese B — RumbleEngine throttle devora o comando:**
`src/hefesto/core/rumble_engine.py` tem throttle de 20ms entre comandos (decisão V2). Se o daemon envia rumble, depois envia outro comando HID (ex.: LED), o controle pode estar priorizando o último comando HID, zerando rumble.

**Hipótese C — Poll loop zera rumble a cada tick:**
Se `poll_loop` envia `controller.write()` a cada tick e `write()` inclui rumble resetado, o valor definido por IPC é sobrescrito em <20ms.

## Investigação canônica (primeiro passo do executor)

```bash
# Confirmar qual handler "rumble.set" faz
rg -n "rumble\.set|rumble_set|apply_rumble|RumbleEngine" src/hefesto/daemon/ src/hefesto/core/

# Ver se poll_loop toca rumble
rg -n "rumble|write\b" src/hefesto/daemon/lifecycle.py

# Ver a API IPC
rg -n "\"rumble\\." src/hefesto/daemon/ipc_server.py
```

## Decisão

**Fix canônico** (independente da hipótese):

1. Modelo explícito de **estado de rumble ativo** em `DaemonConfig`:
   ```python
   @dataclass
   class DaemonConfig:
       ...
       rumble_active: tuple[int, int] | None = None  # (weak, strong) ou None p/ passthrough
   ```
2. Handler IPC `rumble.set` atualiza `daemon.config.rumble_active`.
3. `poll_loop` **sempre** re-aplica `rumble_active` via `controller.set_rumble(weak, strong)` a cada ~200ms (5Hz) se `rumble_active is not None`. Isso é barato e garante sobreposição mesmo que outras escritas HID zerem o motor.
4. Handler IPC `rumble.stop` zera `rumble_active = (0, 0)`.
5. Handler IPC `rumble.passthrough {enabled: bool}` zera `rumble_active = None` — devolve controle para jogo/autoswitch.

Botão "Aplicar rumble" na GUI chama `rumble.set {weak, strong}`. Botão "Parar" chama `rumble.stop`. Botão "Testar por 500 ms" preservado (manda `rumble.pulse` que aplica por 500ms via timer e volta).

## Critérios de aceite

- [ ] `src/hefesto/daemon/lifecycle.py`: `DaemonConfig.rumble_active: tuple[int, int] | None = None`.
- [ ] `src/hefesto/daemon/lifecycle.py`: helper `_reassert_rumble(now)` chamado a cada 200ms no `_poll_loop` (nova variável de deadline `next_rumble_assert_at`). Idempotente.
- [ ] `src/hefesto/daemon/ipc_server.py`: handlers `rumble.set`, `rumble.stop`, `rumble.passthrough` atualizam `daemon.config.rumble_active`.
- [ ] `src/hefesto/app/actions/rumble_actions.py`:
  - Botão "Aplicar rumble" chama IPC `rumble.set` com `(weak, strong)`.
  - Botão "Parar" chama `rumble.stop`.
  - Sliders não disparam `rumble.set` em cada movimento (apenas ao clicar Aplicar). Evita spam IPC.
- [ ] Teste `tests/unit/test_rumble_persistent.py`:
  - (a) `rumble.set (50, 100)` → `daemon.config.rumble_active == (50, 100)`.
  - (b) mock controller; 5 ticks de poll loop re-afirma rumble.
  - (c) `rumble.stop` → `rumble_active == (0, 0)`.
  - (d) `rumble.passthrough {enabled: True}` → `rumble_active is None`, poll_loop não chama `set_rumble`.
- [ ] Proof-of-work com hardware real:
  1. Daemon vivo, controle conectado.
  2. `.venv/bin/hefesto status` → connected True.
  3. Via GUI, Rumble: weak=60, strong=120, Aplicar.
  4. Segurar controle por 3s → vibração contínua perceptível.
  5. "Parar" → vibração cessa.
  6. Log do daemon mostra re-assert a cada 200ms.

## Arquivos tocados

- `src/hefesto/daemon/lifecycle.py`
- `src/hefesto/daemon/ipc_server.py`
- `src/hefesto/app/actions/rumble_actions.py`
- `tests/unit/test_rumble_persistent.py` (novo)

## Fora de escopo

- Política global de rumble (aba inteira) → **spec FEAT-RUMBLE-POLICY-01**. Aqui resolvemos apenas a persistência do "Aplicar".
- Rumble-per-profile → cobre em FEAT-PROFILES-PRESET-06.

## Notas para o executor

- `controller.set_rumble(weak, strong)` é síncrono e barato — re-asserção a 5Hz adiciona <0.2% de CPU.
- Cuidado com `throttle=20ms` do `RumbleEngine`: re-asserção a cada 200ms sempre respeita o throttle.
- Se o controle está em "passthrough mode" (jogo envia rumble via gamepad virtual Xbox360 emulado), re-asserção do `rumble_active` **pode conflitar**. Solução: quando `daemon.config.emulation_enabled == True` E `rumble_active is None`, re-asserção pula. Se usuário fixou `rumble_active != None` em modo emulação, ele venceu — seu valor sobrescreve o do jogo. Documentar isso no docstring.
