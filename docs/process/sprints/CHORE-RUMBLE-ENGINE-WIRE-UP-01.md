# CHORE-RUMBLE-ENGINE-WIRE-UP-01

**Origem:** achado colateral de FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01 (validação 2026-04-24, PR #99). Registrado no `VALIDATOR_BRIEF.md` como armadilha **A-13**.

**Status:** PLANEJADA (não executada).

## Resumo

`RumbleEngine` (`src/hefesto/core/rumble.py:135`) tem API completa (`link`, `set`, `tick`, `_compute_mult`, `update_auto_state`, `last_mult_applied`) mas **nunca é instanciado em produção**. `rg "RumbleEngine\(|rumble_engine\.link\(" src/hefesto/daemon` retorna zero matches. Todos os caminhos reais de rumble em produção usam funções standalone (`reassert_rumble`, `apply_rumble_policy`) que leem `daemon.config` e `daemon._profile_manager` diretamente.

A sprint FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01 (V2.5) adicionou `RumbleEngine.link(profile_manager=...)` e preparou o canal, mas o wire-up em si ficou de fora do escopo. Esta CHORE fecha o laço.

## Contexto

Estado atual (pós `51dbe92`, HEAD `main`):

- `src/hefesto/core/rumble.py:135-305` — classe `RumbleEngine` com métodos públicos `link(config, state_ref, *, profile_manager=None)`, `set(weak, strong)`, `tick()`, `stop()`, `update_auto_state(auto_mult, change_at, *, mult_applied=None)`. Propriedades: `last_applied`, `last_mult_applied`, `mult_applied`.
- `src/hefesto/daemon/ipc_handlers.py:222-224` — leitura opcional via `getattr(self.daemon, "_rumble_engine", None)` para expor `last_mult_applied` em `state_full`. Hoje sempre retorna None → 1.0 hardcoded é enviado ao cliente.
- `src/hefesto/daemon/ipc_rumble_policy.py:45-49` — leitura opcional via `getattr(daemon, "_rumble_engine", None)` para debounce state do modo "auto". Hoje sempre cai no fallback `last_auto_mult=0.7, last_auto_change_at=0.0`. **Efeito prático:** debounce do modo "auto" reseta a cada chamada IPC `rumble.set`, porque não há estado persistente entre chamadas sem o engine ativo.
- `src/hefesto/daemon/subsystems/rumble.py:31-87` — `reassert_rumble(daemon, now)` não depende do engine: usa `daemon._last_auto_mult` e `daemon._last_auto_change_at` diretamente (writeback em campos do próprio daemon). Funciona sem engine.
- `src/hefesto/daemon/subsystems/ipc.py:26-50` — `IpcSubsystem.start()` já seta `daemon._profile_manager = manager` (FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01). Ponto natural para também instanciar e linkar `RumbleEngine`.

## Escopo

### Decisão 1 — Onde instanciar

Criar no `Daemon.__init__` (não no subsystem) para garantir que o engine existe desde o bootstrap e pode ser referenciado por IPC antes do `IpcSubsystem.start()`:

```python
# src/hefesto/daemon/lifecycle.py Daemon.__init__
self._rumble_engine: RumbleEngine = RumbleEngine(
    controller=self.controller,
    min_interval_sec=DEFAULT_MIN_INTERVAL_SEC,
)
```

Alternativa rejeitada: instanciar em `subsystems/ipc.py`. Problema: `reassert_rumble` roda no poll loop do daemon antes do IpcSubsystem necessariamente estar up; queremos que debounce do modo "auto" compartilhe estado com o engine desde o tick 1.

### Decisão 2 — Onde linkar

Em `subsystems/ipc.py::IpcSubsystem.start()`, imediatamente após setar `daemon._profile_manager = manager`:

```python
if daemon is not None:
    daemon._profile_manager = manager
    engine = getattr(daemon, "_rumble_engine", None)
    if engine is not None:
        # state_ref = controller_state mais recente do store (duck-typed para battery_pct)
        snap = daemon.store.snapshot()
        state_ref = snap.controller  # pode ser None no startup; link aceita
        engine.link(daemon.config, state_ref, profile_manager=manager)
```

### Decisão 3 — Consolidar debounce state

Hoje há dois lugares guardando `_last_auto_mult` e `_last_auto_change_at`:

1. `Daemon` (atributos `_last_auto_mult`, `_last_auto_change_at`) — lidos/escritos por `reassert_rumble`.
2. `RumbleEngine` (atributos privados) — lidos via `getattr` em `apply_rumble_policy`.

Após wire-up, consolidar para uma fonte única. Opção A (preferida): remover atributos do `Daemon` e fazer `reassert_rumble` também ler do engine via `update_auto_state`. Opção B: remover do engine e fazer `apply_rumble_policy` ler do daemon diretamente. Executor escolhe com base em acoplamento; A é mais coerente com AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01 (engine é fonte canônica).

### Decisão 4 — `set_rumble` do poll loop passa pelo engine?

**Não nesta sprint.** Roteamento do `controller.set_rumble` hoje vem de 3 caminhos: `reassert_rumble`, `apply_rumble_policy` e passthrough UDP/jogo direto. Mudar todos para passarem pelo `engine.set()` + `engine.tick()` exige análise de throttle vs semântica de passthrough. Fica para sprint futura `REFACTOR-RUMBLE-UNIFIED-PIPELINE-01` se o usuário reportar artefato (double-throttle ou stop atrasado).

Esta sprint **apenas** pluga o engine de forma a não alterar comportamento observável; o engine passa a existir e a expor `last_mult_applied` correto via IPC `state_full`.

## Critérios mensuráveis (acceptance)

1. `Daemon.__init__` instancia `self._rumble_engine: RumbleEngine` com `controller` real.
2. `IpcSubsystem.start()` chama `engine.link(config, state_ref, profile_manager=manager)` após set de `_profile_manager`.
3. `rg "RumbleEngine\(|\._rumble_engine\s*=" src/hefesto/daemon` retorna pelo menos 2 matches (instanciação + link).
4. `apply_rumble_policy` agora encontra `daemon._rumble_engine` não-None e consome/atualiza debounce via `update_auto_state` (teste existente de debounce deixa de cair no fallback).
5. IPC `state_full` retorna `rumble.mult_applied` com valor real do último ciclo (não 1.0 hardcoded).
6. Teste novo `test_daemon_wires_rumble_engine_to_profile_manager` em `tests/unit/test_daemon_subsystems.py` (ou equivalente) valida: `daemon._rumble_engine._profile_manager is daemon._profile_manager`.
7. Teste novo `test_apply_rumble_policy_atualiza_engine_state` valida que, após chamada IPC `rumble.set`, `engine.last_mult_applied` reflete o mult calculado (não o valor inicial 1.0).
8. Zero regressão em `tests/unit/test_rumble_policy.py` (18 testes da sprint FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01 continuam passando).
9. Smoke USB + BT verdes (tick ≥50, battery ≥1).
10. Mypy zero erros. Ruff clean.

## Invariantes a preservar

- **A-06** (resolvida para rumble): override de perfil continua chegando ao hardware. Teste `test_engine_compute_mult_le_override_do_profile_manager` passa antes e depois.
- **A-07** (wire-up 3 pontos): listar no spec `(1) slot em Daemon, (2) instanciação em __init__, (3) link em subsystem start`. Adicionar teste de wire-up.
- **AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01**: `_effective_mult` continua fonte única. Nenhum ramo novo calcula mult fora dele.
- Smoke timing: instanciação do engine + link não deve atrasar startup; engine é objeto Python leve, sem I/O.

## Riscos técnicos

- Consolidação de debounce (Decisão 3): se executor escolher opção A mas `reassert_rumble` tem código que dependia de sobrescrever `daemon._last_auto_mult` em contexto específico (ex.: reset em `daemon.reload`), a migração precisa ser validada. Verificar `rg "_last_auto_mult" src/hefesto` antes de propor o patch.
- `state_ref` passado em `link()` hoje pode ser `None` no startup. `_compute_mult` já trata via `contextlib.suppress`. Não requer mudança.

## Não-objetivos

- NÃO unificar `controller.set_rumble` pelo engine — fica para `REFACTOR-RUMBLE-UNIFIED-PIPELINE-01`.
- NÃO alterar comportamento do passthrough UDP.
- NÃO mexer em smoke scripts.

## Plano de implementação (granular)

1. Confirmar via `rg "_last_auto_mult|_last_auto_change_at" src/hefesto` todos os consumidores.
2. Em `src/hefesto/daemon/lifecycle.py`: instanciar `self._rumble_engine = RumbleEngine(self.controller)` no `__init__`. Import local para evitar ciclo.
3. Em `src/hefesto/daemon/subsystems/ipc.py::IpcSubsystem.start()`: após `daemon._profile_manager = manager`, linkar engine. Tratar caso `snap.controller is None`.
4. Decidir Decisão 3 (opção A recomendada) e aplicar consolidação. Se A: remover `daemon._last_auto_mult` e `daemon._last_auto_change_at`, substituir consumidores em `reassert_rumble` por leitura/escrita via engine.
5. Adicionar testes #6, #7 do acceptance. Confirmar os 18 testes de rumble_policy ainda passam.
6. Rodar gates: pytest, ruff, mypy, smoke USB/BT, check_anonymity.
7. Proof-of-work com grep matches + contagem pytest + `state_full` via IPC real (ou mock de alta fidelidade) mostrando `rumble.mult_applied != 1.0`.

## Aritmética numérica

Baseline pós-51dbe92: 1332 testes. Projetado após esta sprint: 1332 + 2 (critérios 6 e 7) = **1334 mínimo**.

## Proof-of-work esperado

```bash
bash scripts/dev-setup.sh
.venv/bin/pytest tests/unit -q 2>&1 | tail -5
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke 2>&1 | tail -15
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt 2>&1 | tail -15
./scripts/check_anonymity.sh
rg "RumbleEngine\(|\._rumble_engine\s*=" src/hefesto/daemon
```

Esperado:

- Pytest ≥ 1334 passed.
- Ruff/mypy limpos.
- Grep retorna ≥ 2 matches (instanciação + link).
- A-13 pode ser marcada RESOLVIDA no `VALIDATOR_BRIEF.md` após merge.
