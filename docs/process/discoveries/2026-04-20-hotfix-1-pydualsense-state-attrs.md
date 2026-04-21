# 2026-04-20 — HOTFIX-1: `pydualsense` expõe triggers analog em `L2_value`/`R2_value`, não em `L2`/`R2`

**Contexto:** smoke de abertura da sprint INFRA.2 (captures HID determinísticos). Primeira interação runtime-real com DualSense físico conectado via cabo.
**Status:** Resolvida.
**Issues relacionadas:** #48 (HOTFIX-1, closed), merged em PR #50.

## Sintoma

Smoke contra device real:

```
$ python3 -c "from pydualsense import pydualsense as P; ds=P(); ds.init(); print(ds.state.L2, ds.state.R2)"
False False
```

E em loop de 20s com instruções explícitas ao usuário pra segurar L2/R2:

```
L2=  0 [                                ] | R2=  0 [                                ] | bat=  0%
...
L2=  0 [                                ] | R2=  0 [                                ] | bat=100%
```

Battery subia de 0 → 100 (evidência de que algum report chegou), mas L2/R2 permaneciam em zero. Testes unit passavam porque mocks injetavam `state.L2=0` e o código fazia `int(False)=0`.

## Hipóteses

1. **Usuário não pressionou** — descartada após 20s de monitoramento contínuo.
2. **pydualsense não atualiza state em runtime** — parcialmente verdadeira. Battery atualizou, então reports chegavam. Logo não era travamento do thread inteiro.
3. **Atributo errado no backend** — CONFIRMADA. Via `dir(ds.state)`, apareceu `L2_value` e `R2_value` como atributos separados. `grep` no fonte de `pydualsense.py`:
   ```
   295:  self.state.L2 = bool(states[5])
   296:  self.state.R2 = bool(states[6])
   299:  self.state.L2_value = states[5]
   300:  self.state.R2_value = states[6]
   ```
4. **`ds.state.battery` não existia** — CONFIRMADA via `hasattr()`. Battery vive em `ds.battery` (top-level, objeto `DSBattery` com `Level` e `State`).

## Causa

Leitura dos atributos errados. Três pontos distintos no `src/hefesto/core/backend_pydualsense.py`:

- `state.L2 / state.R2` são **bool** (botão apertado totalmente). Uso de `int(bool)` sempre dava 0 ou 1.
- `state.battery` não existia; o backend retornava 0 silenciosamente via `getattr(default=None)`.
- `is_connected()` checava `ds.conType is not None`, mas `conType` permanecia setado mesmo após erro; `ds.connected` (bool) é o canônico.

## Solução

PR #50 / commit único. `backend_pydualsense.py`:

```python
l2_raw = int(getattr(state, "L2_value", 0)) & 0xFF
r2_raw = int(getattr(state, "R2_value", 0)) & 0xFF
# battery via ds.battery.Level
battery = getattr(ds, "battery", None)
level = getattr(battery, "Level", None)
# is_connected via ds.connected
return bool(getattr(self._ds, "connected", True))
```

Smoke após fix: `battery_pct=100` confirmado (antes: sempre 0).

## Lições

1. **W1.1 passou em unit test mas não em runtime.** Isso expôs um furo na cobertura: mocks espelhavam a API que eu inventei, não a API real do `pydualsense`. Toda sprint que toca adapter externo deve ter smoke runtime-real na DoD.
2. **Ler o fonte do pacote antes de assumir a API.** `dir()` + `grep` resolveu em 30s. Tentativa de deduzir "como deve ser" custou mais.
3. **Meta-regra 9.8 (validação runtime-real) não é supérflua.** Sem device, o bug ficava invisível pro CI.

## Impacto cross-sprint

- Sprints destravadas: INFRA.2 pôde começar (mas travou em outro bug, HOTFIX-2).
- Sprints afetadas retroativamente: W1.3 (poll loop), W4.2 (daemon.status via IPC), W5.3 (CLI battery/status) — todas lendo o atributo errado sem reclamar. Fix corrige todas.
- ADRs afetadas: ADR-001 (pydualsense backend) ganha nota de rodapé sobre o mapeamento de atributos.
- Decisões V2/V3: nenhuma mudança semântica; V2-7 (`transport: Literal["usb", "bt"]`) continua válida.
