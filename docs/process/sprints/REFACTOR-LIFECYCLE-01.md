# REFACTOR-LIFECYCLE-01 — Quebrar `lifecycle.py` em subsistemas modulares

**Tipo:** refactor (arquitetural).
**Wave:** V1.2 / V2.0.
**Estimativa:** 2 iterações.
**Dependências:** idealmente após V1.1 fechar (os fixes desta onda estabilizam o comportamento antes do refactor).

---

## Contexto

`src/hefesto/daemon/lifecycle.py` concentra hoje ≥ 300 linhas com responsabilidades heterogêneas: poll loop, IPC start/stop, UDP start/stop, autoswitch, mouse emulation, battery debouncer, signal handlers, shutdown. O arquivo é central mas mistura níveis de abstração — fica difícil: (a) adicionar um subsistema novo (ex.: FEAT-METRICS-01); (b) testar um subsistema em isolamento; (c) escrever um plugin externo (FEAT-PLUGIN-01).

## Decisão

Quebrar em pacote `src/hefesto/daemon/subsystems/`:

```
daemon/
├── lifecycle.py          (orquestrador slim, ≤ 120 linhas)
├── state_store.py        (permanece)
├── subsystems/
│   ├── __init__.py       (registry + protocolo Subsystem)
│   ├── base.py           (Protocol Subsystem: start/stop/tick)
│   ├── poll.py           (poll_loop + battery debouncer)
│   ├── ipc.py            (IPC server)
│   ├── udp.py            (UDP server)
│   ├── autoswitch.py     (profile autoswitcher)
│   ├── mouse.py          (uinput mouse dispatch)
│   └── rumble.py         (rumble passthrough + throttle)
```

Cada subsistema implementa `Subsystem` protocol:

```python
class Subsystem(Protocol):
    name: str
    async def start(self, daemon: DaemonContext) -> None: ...
    async def stop(self) -> None: ...
    def is_enabled(self, config: DaemonConfig) -> bool: ...
```

`Daemon.run()` reduz-se a: resolve config → para cada subsystem habilitado, start → await stop_event → para cada subsystem, stop. `DaemonContext` (dataclass) expõe `controller`, `bus`, `store`, `config`, `executor` para os subsystems.

## Critérios de aceite

- [ ] Novo pacote `src/hefesto/daemon/subsystems/` com os 6 módulos listados.
- [ ] `lifecycle.py` ≤ 120 linhas após refactor. Só orquestração.
- [ ] `DaemonContext` dataclass em `daemon/context.py`.
- [ ] Registry de subsystems em `subsystems/__init__.py` (lista ordenada, idempotente).
- [ ] Cada subsystem tem teste unitário isolado em `tests/unit/test_subsystem_*.py` (mockando `DaemonContext`).
- [ ] `Daemon.run()` continua passando os 335+ testes atuais sem mudança de API pública.
- [ ] Smoke USB+BT continua verde: `HEFESTO_FAKE=1 ./run.sh --smoke`.
- [ ] ADR-015 (novo) documentando o padrão Subsystem e como adicionar um novo.

## Proof-of-work

```bash
wc -l src/hefesto/daemon/lifecycle.py   # esperado: ≤ 120
find src/hefesto/daemon/subsystems -name '*.py' | wc -l  # esperado: 7+ (__init__ + 6 subsystems + base)
.venv/bin/pytest tests/unit -q
HEFESTO_FAKE=1 ./run.sh --smoke
```

## Arquivos tocados (previsão)

- `src/hefesto/daemon/lifecycle.py` (slim)
- `src/hefesto/daemon/context.py` (novo)
- `src/hefesto/daemon/subsystems/__init__.py` (novo)
- `src/hefesto/daemon/subsystems/base.py` (novo)
- `src/hefesto/daemon/subsystems/{poll,ipc,udp,autoswitch,mouse,rumble}.py` (6 novos)
- `tests/unit/test_subsystem_*.py` (6 novos)
- `docs/adr/015-subsystems-pattern.md` (novo)

## Fora de escopo

- Trocar asyncio por outro runtime.
- Plugin loader externo (FEAT-PLUGIN-01 depende disso mas vem separado).
- Alterar event bus ou state store.

## Notas

- Manter retrocompatibilidade: testes antigos (`test_daemon_lifecycle.py`) continuam passando sem modificação.
- Ordem de start importa: controller → poll → ipc → udp → autoswitch → mouse → rumble. Registry preserva ordem de lista.
