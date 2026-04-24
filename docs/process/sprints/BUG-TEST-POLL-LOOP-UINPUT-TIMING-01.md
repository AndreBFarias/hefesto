# BUG-TEST-POLL-LOOP-UINPUT-TIMING-01 — 4 testes flaky do poll loop em dev local

**Tipo:** bug (test timing / infra).
**Wave:** colateral descoberto durante execução de 59.3 (V2.3.0).
**Estimativa:** XS (0.25 iteração).
**Dependências:** nenhuma.

---

**Tracking:** label `type:bug`, `test`, `flaky`, `ai-task`, `status:ready`.

## Contexto

Durante a sprint 59.3 (Fase B+D), ao rodar `.venv/bin/pytest tests/unit -q`
em dev local com DualSense conectado e `/dev/uinput` funcional, observei
4 testes falhando em `tests/unit/test_poll_loop_evdev_cache.py`:

- `test_snapshot_chamado_exatamente_uma_vez_por_tick_sem_consumidores`
- `test_snapshot_chamado_exatamente_uma_vez_por_tick_com_hotkey_e_mouse`
- `test_snapshot_excecao_retorna_frozenset_vazio`
- `test_botoes_passados_ao_hotkey_manager_e_ao_mouse`

Assert típico: `poll.tick esperado >= 10, obtido 0`.

## Causa raiz

Os testes criam `Daemon` com `poll_hz=200` e aguardam `await asyncio.sleep(0.06)`
(60ms) antes de chamar `daemon.stop()`. Esperam ≥10 ticks.

No dev local, o startup sequencial do daemon (`connect_with_retry` + `restore_last_profile`
+ criação de tasks + `_start_keyboard_emulation` que abre `/dev/uinput` real
+ demais subsystems) leva mais de 60ms antes de ceder para o poll loop
executar. Quando o teste chama `stop()`, o event já é setado antes do
primeiro tick.

**No CI do GitHub Actions o teste passa** porque `/dev/uinput` não existe no
runner; `UinputKeyboardDevice.start()` retorna False rápido e o startup
fica sob 60ms. Confirmado empiricamente: sprint 80 e 59.2 passaram no CI.

Reproduzível: `git stash` das mudanças de 59.3 não corrige — o bug é
pré-existente, ativado sempre que o ambiente tem `/dev/uinput` + estrutura
de subsystems pesada o bastante para empurrar startup além da janela.

## Decisão

Fix em 2 camadas:

1. **Aumentar a janela de startup** nos 4 testes: `asyncio.sleep(0.06)` →
   `asyncio.sleep(0.2)` (200ms — 40 ticks a 200Hz, sobra para 10).
   Alternativa: desligar `keyboard_emulation_enabled` e `mouse_emulation_enabled`
   (já off) e adicionar `keyboard_emulation_enabled=False` nos DaemonConfig dos
   testes. **Preferir a 2ª**: explicita a intenção ("este teste não exercita
   keyboard") e remove a dependência de timing.

2. **Documentar** a lição: subsystems que fazem probing de hardware
   (uinput, evdev) durante `start()` têm custo variável entre ambientes.
   Testes do poll loop devem desabilitar subsystems não relevantes em
   vez de assumir que caberão no budget de tempo.

## Critérios de aceite

- [ ] 4 testes passam em `git stash` limpo no dev local (sem mudanças).
- [ ] 4 testes passam em dev local (com DualSense + uinput).
- [ ] Comando: `.venv/bin/pytest tests/unit/test_poll_loop_evdev_cache.py -q`
      retorna exit 0.
- [ ] CI continua verde (fix não regride o caminho que já passava).

## Arquivos tocados

- `tests/unit/test_poll_loop_evdev_cache.py` (5 chamadas `DaemonConfig(...)`;
  adicionar `keyboard_emulation_enabled=False` em cada).

## Proof-of-work

```bash
# Antes:
.venv/bin/pytest tests/unit/test_poll_loop_evdev_cache.py -q  # 4 failures

# Aplicar fix.

# Depois:
.venv/bin/pytest tests/unit/test_poll_loop_evdev_cache.py -q  # 9 passed
```

## Fora de escopo

- Refatorar o `_poll_loop` para iniciar ANTES dos subsystems (mudaria
  ordem de inicialização; fora do escopo deste fix).
- Mockar `UinputKeyboardDevice.start` globalmente nos testes (já há
  fixture autouse no conftest setando HEFESTO_FAKE=1; se quisermos mais
  isolamento, é outra sprint).

## Notas

- Descoberto durante Fase B+D da sprint 59.3 (2026-04-24) ao rodar `pytest tests/unit`
  em dev local.
- Anti-débito 9.7: documentado como spec-nova, não como "TODO depois".
