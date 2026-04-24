# FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01 — Override de policy de rumble por perfil

**Tipo:** feature (perfil + rumble engine).
**Wave:** V2.5 — sprint #6 da ordem recomendada em `docs/process/SPRINT_ORDER.md:436`.
**Porte:** M.
**Estimativa:** 2 iterações.
**Dependências:** FEAT-RUMBLE-POLICY-01 (V2.1, MERGED), AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01 (V2.4, MERGED), AUDIT-FINDING-IPC-SERVER-SPLIT-01 (V2.4, MERGED).

---

**Tracking:** label `type:feature`, `rumble`, `profiles`, `ai-task`, `status:ready`.

## Objetivo

`RumbleConfig` ganha campo opcional `policy: RumblePolicy | None = None` que sobrescreve a política global de rumble para aquele perfil específico. Quando setado, o multiplicador efetivo usado pelo `RumbleEngine` e por `apply_rumble_policy` sai do perfil; quando `None`, herda o global (comportamento atual preservado).

Uso esperado: perfil `fps` força `policy: "max"` para vibração cheia no combate; `navegacao` força `policy: "economia"` para não drenar bateria em navegação longa; `acao` deixa `None` e segue o slider global da GUI.

## Contexto

Estado atual (pós v2.4.1 + pós FEAT-FLATPAK-WLRCTL-BUNDLED-01, HEAD atual em `main`), confirmado via leitura:

- `src/hefesto/profiles/schema.py:144-148` — `RumbleConfig` hoje tem **um único campo**: `passthrough: bool = True`. Não existe Literal nomeado `RumblePolicy` no repositório inteiro (grep confirmou: zero hits).
- `src/hefesto/daemon/lifecycle.py:79` — Literal do policy global é **inline**: `rumble_policy: Literal["economia", "balanceado", "max", "auto", "custom"] = "balanceado"`. Precisa ser promovido a alias de tipo nomeado antes de ser reusado no schema (ver decisão em Escopo).
- `src/hefesto/daemon/subsystems/rumble.py:22-28` — `RUMBLE_POLICY_MULT` só cobre `economia/balanceado/max`; `auto` e `custom` são tratados fora desse dict por `_effective_mult`.
- `src/hefesto/core/rumble.py:51-110` — `_effective_mult(config, battery_pct, now, last_auto_mult, last_auto_change_at)` lê **exclusivamente** `config.rumble_policy` e `config.rumble_policy_custom_mult`. Assinatura atual **não recebe perfil**. Três chamadores:
    1. `core/rumble.py:237` — `RumbleEngine._compute_mult()` (tick do engine).
    2. `daemon/subsystems/rumble.py:61` — `reassert_rumble()` (re-asserção 5Hz no poll loop).
    3. `daemon/ipc_rumble_policy.py:51` — `apply_rumble_policy()` (IPC rumble.set + draft applier).
- `src/hefesto/profiles/manager.py:70-78` — `ProfileManager.apply()` toca apenas triggers e LEDs. **NÃO existe `_to_rumble_settings` nem `RumbleSettings`** — rumble nunca passou pelo pipeline de perfil. Esta sprint abre esse canal pela primeira vez.
- `src/hefesto/daemon/state_store.py:45-108` — `StateStore` guarda `_active_profile: str | None` (apenas slug). Recuperar `RumbleConfig` efetivo exige `load_profile(name)` em runtime OU cache do perfil ativo resolvido pelo `ProfileManager`.
- `assets/profiles_default/` — 9 JSONs: `acao.json`, `aventura.json`, `bow.json`, `corrida.json`, `esportes.json`, `fallback.json`, `fps.json`, `meu_perfil.json`, `navegacao.json`. Todos terão `rumble: {"passthrough": true}` hoje; precisam permanecer compatíveis (omissão de `policy` = herdar global).

Baseline pytest (2026-04-24 HEAD main): **1316 testes coletados**.

L-21-3 aplicada: o spec foi escrito após leitura de `schema.py` inteiro, `core/rumble.py` inteiro, `daemon/subsystems/rumble.py` inteiro, `daemon/ipc_rumble_policy.py` inteiro, `profiles/manager.py` inteiro e `daemon/lifecycle.py:79-80`. Premissas do prompt original que **divergiram do código real**:

- Prompt falava em `src/hefesto/subsystems/rumble.py` — caminho real é `src/hefesto/daemon/subsystems/rumble.py`.
- Prompt sugeriu `_to_rumble_settings` — **não existe**. Sprint precisa criá-lo (ou usar alternativa descrita em Escopo).
- Prompt sugeriu que `RumbleEngine` está em `src/hefesto/subsystems/rumble.py` — na verdade está em `src/hefesto/core/rumble.py:113`.
- Prompt sugeriu que `RumblePolicy` é um Literal já existente — **não é**. Está inline em `lifecycle.py:79`.

## Escopo

### Decisão 1 — Promover Literal inline a alias nomeado

Criar `RumblePolicy` como alias de tipo reutilizável. Local proposto: **novo arquivo** `src/hefesto/core/rumble_policy.py` (nome curto, dedicado), exportando:

```python
from typing import Literal

RumblePolicy = Literal["economia", "balanceado", "max", "auto", "custom"]

__all__ = ["RumblePolicy"]
```

Justificativa do arquivo novo em vez de declarar dentro de `schema.py` ou `core/rumble.py`: ambos já são importadores mútuos via TYPE_CHECKING; um módulo puro `rumble_policy.py` evita ciclos e serve ao schema (que não deve importar de `daemon/`) + ao config do daemon + ao engine, todos os três consumidores.

Refatorar `daemon/lifecycle.py:79` para usar `RumblePolicy` importado do novo módulo (substituindo o Literal inline, preservando default `"balanceado"`).

### Decisão 2 — Campo `policy` em `RumbleConfig`

Em `src/hefesto/profiles/schema.py:144`:

```python
from hefesto.core.rumble_policy import RumblePolicy

class RumbleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passthrough: bool = True
    policy: RumblePolicy | None = None
    policy_custom_mult: float | None = None  # só considerado quando policy == "custom"
```

Semântica:
- `policy is None` (default) → herdar `daemon.config.rumble_policy` (comportamento atual).
- `policy in ("economia", "balanceado", "max", "auto")` → ignorar global e usar este valor para o perfil.
- `policy == "custom"` **exige** `policy_custom_mult: float in [0.0, 2.0]`. Se ausente, schema rejeita via `field_validator` (análogo ao `_rgb_bytes` em `LedsConfig`). Justificativa do teto 2.0: espelha o teto atual usado por `_handle_rumble_policy_custom` em `ipc_handlers.py:330-340` (ver spec confirmar intervalo real durante execução).

Validator obrigatório (spec usa nome `_validate_custom_mult`):

```python
@model_validator(mode="after")
def _validate_custom_mult(self) -> "RumbleConfig":
    if self.policy == "custom" and self.policy_custom_mult is None:
        raise ValueError("rumble.policy='custom' exige policy_custom_mult")
    if self.policy_custom_mult is not None and not (0.0 <= self.policy_custom_mult <= 2.0):
        raise ValueError("policy_custom_mult fora de [0.0, 2.0]")
    return self
```

### Decisão 3 — Propagar override através de `_effective_mult`

Estender a assinatura de `_effective_mult` em `src/hefesto/core/rumble.py:51` adicionando **parâmetro keyword-only opcional** `profile_override: RumbleConfig | None = None`. Lógica:

```python
def _effective_mult(
    config: DaemonConfig,
    battery_pct: int,
    now: float,
    last_auto_mult: float,
    last_auto_change_at: float,
    auto_debounce_sec: float = 5.0,
    *,
    profile_override: RumbleConfig | None = None,
) -> tuple[float, float, float]:
    # Se perfil override policy, usar valores do perfil (com seu próprio custom_mult).
    if profile_override is not None and profile_override.policy is not None:
        effective_policy = profile_override.policy
        effective_custom_mult = (
            profile_override.policy_custom_mult
            if effective_policy == "custom"
            else config.rumble_policy_custom_mult
        )
    else:
        effective_policy = config.rumble_policy
        effective_custom_mult = config.rumble_policy_custom_mult
    # ... resto da função original operando sobre (effective_policy, effective_custom_mult) ...
```

Preserva compatibilidade: chamador que não passa `profile_override` continua lendo de `config`. Todos os testes atuais de `_effective_mult` passam sem alteração.

### Decisão 4 — Canal de acesso ao `RumbleConfig` do perfil ativo

Problema: `StateStore.active_profile` só guarda slug; `load_profile(name)` hit disco a cada tick seria custoso (chamado 5Hz em `reassert_rumble` + potencialmente 50Hz em `RumbleEngine._compute_mult`).

Solução: `ProfileManager.activate()` passa a armazenar referência ao `Profile` resolvido em atributo público do próprio manager: `self.active_profile_object: Profile | None`. Getter `get_active_rumble_config() -> RumbleConfig | None` exposto para os três consumidores de `_effective_mult`. Justificativa: `ProfileManager` já é o único a chamar `load_profile` no caminho de ativação; cache é natural ali. Incremento: ~5 linhas em `manager.py`.

Alternativa rejeitada: guardar `Profile` completo em `StateStore` — violaria invariante atual ("store guarda slug"); mais intrusivo.

Plumbing dos três consumidores:

1. **`RumbleEngine._compute_mult`** (`core/rumble.py:228-244`): engine já tem `self._config` via `link()`. Adicionar parâmetro de `link()`: `link(config, state_ref, profile_manager=None)`. `_compute_mult` lê `profile_override = profile_manager.get_active_rumble_config() if profile_manager else None` antes de chamar `_effective_mult`.
2. **`reassert_rumble`** (`daemon/subsystems/rumble.py:31-75`): recebe `daemon`; acessa `daemon._profile_manager.get_active_rumble_config()`. Adiciona parâmetro `profile_override=...` ao call de `_effective_mult` em linha 61.
3. **`apply_rumble_policy`** (`daemon/ipc_rumble_policy.py:19-72`): lê `profile_manager = getattr(daemon, "_profile_manager", None)`; `profile_override = profile_manager.get_active_rumble_config() if profile_manager else None`; passa ao `_effective_mult` em linha 51.

### Decisão 5 — Reação a `profile.switch` (critério 4 do prompt)

Quando `profile.switch` ativa perfil novo, `ProfileManager.activate()` já atualiza `self.active_profile_object`. Como os três consumidores **leem o override em cada chamada** (sem cache próprio), a próxima chamada de `_compute_mult` / `reassert_rumble` / `apply_rumble_policy` **automaticamente** enxerga o novo policy. Não há necessidade de método "invalidate" — invariante central da Decisão 4.

Edge case coberto: perfil ativo é **removido** via `delete()`. `ProfileManager.delete()` (`manager.py:51-56`) atualmente já limpa `active_profile`; o spec estende para limpar também `active_profile_object = None`, caindo em herdar global.

### Arquivos a modificar

- `src/hefesto/profiles/schema.py` — import de `RumblePolicy`; campo `policy` e `policy_custom_mult` em `RumbleConfig`; validator `_validate_custom_mult`; exportar `RumbleConfig` (já exportado).
- `src/hefesto/profiles/manager.py` — atributo `active_profile_object`; atualizar em `activate()` e `delete()`; método `get_active_rumble_config()`.
- `src/hefesto/core/rumble.py` — assinatura de `_effective_mult` ganha `profile_override`; `RumbleEngine.link()` aceita `profile_manager=None`; `_compute_mult` lê override.
- `src/hefesto/daemon/lifecycle.py:79` — substituir Literal inline por import de `RumblePolicy`.
- `src/hefesto/daemon/subsystems/rumble.py` — `reassert_rumble` passa `profile_override` adiante.
- `src/hefesto/daemon/ipc_rumble_policy.py` — `apply_rumble_policy` passa `profile_override` adiante.
- `src/hefesto/daemon/subsystems/ipc.py:41,72` — se `RumbleEngine.link()` for chamado aqui (executor confirma via grep em iteração), estender chamada com `profile_manager=manager`.

### Arquivos a criar

- `src/hefesto/core/rumble_policy.py` — ~8 linhas, só define `RumblePolicy = Literal[...]` + `__all__`.

### Arquivos NÃO tocar

- `assets/profiles_default/*.json` — 9 arquivos permanecem inalterados. Omissão de `policy` = comportamento atual preservado. Testar explicitamente que `load_profile("fps")` em disco NÃO ganha o campo `policy` salvo por serialização (ver Testes).
- `src/hefesto/core/led_control.py`, `apply_led_settings` — irrelevante (não há contrapartida rumble de hardware aqui; `set_rumble` é invocado no engine, não no `apply`).
- `src/hefesto/daemon/ipc_handlers.py:304-343` — handlers `rumble.policy_set` / `rumble.policy_custom` continuam mexendo em **config global**. Override de perfil é via edição do JSON (GUI/CLI) + `profile.switch` — não há handler IPC novo nesta sprint.
- GUI (`src/hefesto/gui/main.glade`, `src/hefesto/app/**`) — expor override na GUI fica para **sprint futura** (candidata: `FEAT-RUMBLE-PER-PROFILE-GUI-01`, V2.6). Esta sprint entrega só o backend.
- `tests/unit/test_led_and_rumble.py::TestApplyLedSettings` — teste `test_apply_led_settings_nao_toca_mic_led` (A-06 variante inversa) é de LEDs, irrelevante aqui.

### Testes a adicionar

Em `tests/unit/test_rumble_policy.py` (já tem 31 testes; adicionar bloco `class TestProfileOverride`):

1. `test_override_none_usa_global` — perfil sem `policy` → `_effective_mult` lê `config.rumble_policy`; mult == global.
2. `test_override_economia_sobrescreve_global_max` — `config.rumble_policy="max"`, `profile_override.policy="economia"` → mult == 0.3.
3. `test_override_custom_usa_policy_custom_mult_do_perfil` — `profile_override.policy="custom"`, `policy_custom_mult=1.5` → mult == 1.5 (NÃO lê `config.rumble_policy_custom_mult`).
4. `test_override_auto_preserva_debounce_state` — `profile_override.policy="auto"`, battery 10% → mult 0.3; debounce state propagado no retorno.

Em `tests/unit/test_profile_manager.py` (já tem 13 testes; adicionar `class TestActiveRumbleConfig`):

5. `test_activate_cacheia_profile_object` — após `activate("fps")`, `manager.active_profile_object` aponta para o Profile carregado.
6. `test_get_active_rumble_config_sem_perfil_ativo` — retorna None.
7. `test_get_active_rumble_config_com_override` — perfil com `policy="economia"` → retorna `RumbleConfig(policy="economia", ...)`.
8. `test_delete_perfil_ativo_limpa_cache` — `delete()` do perfil ativo zera `active_profile_object`.
9. `test_switch_entre_overrides_muda_config` — activate A (policy="max"), depois activate B (policy="economia") — `get_active_rumble_config()` reflete B.
10. `test_switch_de_override_para_none_volta_a_herdar` — activate A (policy="max"), depois activate fallback (policy=None) — `get_active_rumble_config().policy is None`.

Em `tests/unit/test_rumble_policy.py` (integração engine ↔ manager):

11. `test_engine_compute_mult_le_override_do_profile_manager` — `RumbleEngine.link(config, state, profile_manager=pm)`, `pm` com perfil policy="economia", `config.rumble_policy="max"` → `engine._compute_mult()` retorna 0.3.
12. `test_reassert_rumble_usa_override_do_perfil` — `reassert_rumble(daemon, now)` com `daemon._profile_manager` tendo override → `set_rumble` chamado com valores multiplicados pelo override, não pelo global.

Schema (em `tests/unit/test_profile_schema.py` se existir, senão criar bloco ou adicionar a arquivo de schema existente — executor confirma via grep):

13. `test_rumble_config_policy_none_default` — `RumbleConfig()` tem `policy=None, policy_custom_mult=None`.
14. `test_rumble_config_policy_custom_sem_mult_rejeita` — `RumbleConfig(policy="custom")` levanta `ValidationError`.
15. `test_rumble_config_policy_custom_mult_fora_intervalo_rejeita` — `RumbleConfig(policy="custom", policy_custom_mult=3.0)` levanta `ValidationError`.
16. `test_rumble_config_policy_economia_sem_mult_ok` — `RumbleConfig(policy="economia")` aceito (custom_mult não requerido para policies fixas).

JSONs default (verificação de não-regressão):

17. `test_profiles_default_nao_definem_policy_override` — loop sobre `assets/profiles_default/*.json`; todos devem satisfazer `profile.rumble.policy is None`. Garante que a sprint não esqueceu de um arquivo.

**Total de testes novos: 17.** Pytest deve subir de 1316 para **≥1333** (alvo: 1333; margem `+1` para algum split incidental, mas o número mínimo é 1333).

### Critérios mensuráveis (acceptance)

1. `RumbleConfig` aceita campo `policy: RumblePolicy | None = None` e `policy_custom_mult: float | None = None`. Schema valida cinco literais + None. `policy="custom"` sem mult é rejeitado.
2. `_effective_mult` ganha keyword-only `profile_override: RumbleConfig | None = None`. Sem o parâmetro, comportamento idêntico ao pré-sprint (todos os testes atuais de `_effective_mult` passam sem alteração).
3. Quando `profile_override.policy is not None`, o mult é calculado a partir do perfil; quando `None` ou `profile_override is None`, herda do `config` global.
4. `ProfileManager.activate(name)` popula `active_profile_object` com o `Profile` carregado; `delete()` do perfil ativo zera esse cache.
5. `ProfileManager.get_active_rumble_config()` devolve o `RumbleConfig` do perfil ativo ou `None`.
6. Os três consumidores de `_effective_mult` (`RumbleEngine._compute_mult`, `reassert_rumble`, `apply_rumble_policy`) leem o override via `profile_manager.get_active_rumble_config()` antes de chamar `_effective_mult` e passam como `profile_override`.
7. `RumbleEngine.link()` aceita novo parâmetro keyword-only opcional `profile_manager=None`. Passada via `daemon/subsystems/ipc.py` na inicialização.
8. Após `profile.switch` via IPC, a próxima chamada de rumble no hardware (pelo engine ou reassert) reflete o novo override — **sem** chamada manual de `rumble.policy_set`.
9. Após `profile.switch` saindo de um perfil com override para um sem override, mult volta a herdar do `config.rumble_policy` global.
10. `policy_custom_mult` só é consultado quando `policy == "custom"`; para policies fixas do perfil, custom do perfil é ignorado em favor da tabela `RUMBLE_POLICY_MULT` normal.
11. Os 9 JSONs default em `assets/profiles_default/` não são modificados nesta sprint e continuam carregando sem erro — o teste #17 falha se algum ganhou `policy` por acidente.
12. Pytest sobe de 1316 para ≥1333 (17 novos). `mypy src/hefesto` passa com as novas anotações (zero erros — gate rígido pós-v2.2).
13. Cobertura de `src/hefesto/profiles/manager.py`, `src/hefesto/core/rumble.py` e `src/hefesto/daemon/ipc_rumble_policy.py` **não regride >1pp** comparada ao baseline atual.

## Invariantes a preservar

- **A-06 canônica**: campo novo em `RumbleConfig` → mapper responsável DEVE ser atualizado. Nesta sprint o "mapper" é o trio `_effective_mult` + `ProfileManager.get_active_rumble_config` + `RumbleEngine.link`. Teste #11 (`test_engine_compute_mult_le_override_do_profile_manager`) é o teste de integração A-06-compliant: campo chega ao engine, não vira letra morta.
- **A-06 variante inversa**: o override de policy afeta **multiplicador**, não estado runtime de hardware. Não inventar setter `controller.set_rumble_policy()` — política é cálculo puro em software. `apply_rumble_policy` continua só retornando `(weak, strong)` efetivos; não há novo path pelo qual o `apply()` do `ProfileManager` escreva no controller.
- **L-21-3** aplicada no spec (premissas confirmadas via leitura; divergências do prompt original listadas em Contexto).
- **L-21-4**: executor em sessão nova roda `bash scripts/dev-setup.sh` antes de qualquer gate.
- **Zero emojis gráficos + acentuação PT-BR correta** em todos arquivos tocados (inclusive `RumblePolicy` docstring se houver). Varredura automática do validador já cobre isso.
- **AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01**: `_effective_mult` permanece a única fonte de cálculo do mult. Nenhum ramo novo escreve `engine._last_auto_*` fora de `update_auto_state()`.
- **AUDIT-FINDING-IPC-SERVER-SPLIT-01**: `apply_rumble_policy` continua em módulo dedicado; a sprint **não** volta a inlinar o cálculo no `ipc_server.py`.
- **Pydantic extra="forbid"**: `RumbleConfig` mantém `model_config = ConfigDict(extra="forbid")`. Campos novos declarados explicitamente.

## Aritmética numérica

Meta: pytest count 1316 → ≥1333.

- Testes novos declarados: 17 (listados em detalhe na seção Testes).
- Testes modificados: 0 (testes existentes de `_effective_mult` passam sem tocar porque `profile_override` tem default None).
- Projetado: 1316 + 17 = 1333.
- Limite inferior aceitável: 1333. Valor menor = algum teste do plano ficou fora; executor deve justificar no proof-of-work.

Cobertura (heurística, não gate):

- `src/hefesto/profiles/manager.py` hoje ~95% (13 testes diretos). Adição de `active_profile_object` + `get_active_rumble_config` tem testes dedicados (#5-#10) → cobertura mantém ou sobe.
- `src/hefesto/core/rumble.py` hoje alta (~92%). Novo branch `profile_override is not None` tem testes #1-#4 → cobertura mantém.
- `src/hefesto/daemon/ipc_rumble_policy.py` hoje ~89%. Novo plumbing do override testado por #12 → cobertura mantém.

## Plano de implementação (granular)

1. Criar `src/hefesto/core/rumble_policy.py` com `RumblePolicy = Literal[...]` + `__all__`. Ajustar import em `src/hefesto/daemon/lifecycle.py:79` para `rumble_policy: RumblePolicy = "balanceado"`.
2. Em `src/hefesto/profiles/schema.py:144`: adicionar import de `RumblePolicy`; adicionar `policy` e `policy_custom_mult`; adicionar `_validate_custom_mult`. Rodar `.venv/bin/pytest tests/unit/test_profile_schema.py -x` (ou arquivo equivalente — executor grep).
3. Adicionar testes #13-#16 (schema). Todos devem passar após passo 2.
4. Em `src/hefesto/profiles/manager.py`: adicionar `active_profile_object`, `get_active_rumble_config()`, atualizar `activate()` e `delete()`. Adicionar testes #5-#10.
5. Em `src/hefesto/core/rumble.py`: estender `_effective_mult` com `profile_override`; estender `RumbleEngine.link()` com `profile_manager=None`; `_compute_mult` lê override. Adicionar testes #1-#4.
6. Em `src/hefesto/daemon/subsystems/rumble.py:61`: passar `profile_override` para `_effective_mult`. Em `src/hefesto/daemon/ipc_rumble_policy.py:51`: mesmo.
7. Em `src/hefesto/daemon/subsystems/ipc.py`: ao instanciar/linkar `RumbleEngine`, passar `profile_manager=manager` (executor confirma ponto exato via grep `rumble_engine.*link`).
8. Adicionar teste #17 (profiles default sem `policy`). Adicionar testes #11-#12 (integração engine ↔ manager e reassert com override).
9. Rodar smoke USB + smoke BT (2s cada). Esperado: sem traceback, tick ≥50, battery ≥1. Output: anexar no proof-of-work.
10. Rodar `.venv/bin/pytest tests/unit -q` + `.venv/bin/ruff check src/ tests/` + `.venv/bin/mypy src/hefesto` + `./scripts/check_anonymity.sh`.
11. Varredura de acentuação em todos arquivos modificados: `rg "(funcao|validacao|politica|configuracao|descricao|acao)[^a-záéíóúâêôãõç]" src/ tests/` deve retornar zero matches nos arquivos da sprint.

## Proof-of-work esperado (do executor)

```bash
bash scripts/dev-setup.sh
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke 2>&1 | tail -20
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt 2>&1 | tail -20
.venv/bin/pytest tests/unit -q 2>&1 | tail -5
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto
./scripts/check_anonymity.sh
rg "(funcao|validacao|politica|configuracao|descricao|acao)[^a-záéíóúâêôãõç]" src/hefesto/core/rumble_policy.py src/hefesto/core/rumble.py src/hefesto/profiles/schema.py src/hefesto/profiles/manager.py src/hefesto/daemon/lifecycle.py src/hefesto/daemon/subsystems/rumble.py src/hefesto/daemon/ipc_rumble_policy.py tests/unit/test_rumble_policy.py tests/unit/test_profile_manager.py || echo "acentuacao OK"
```

Output textual obrigatório no PR/commit:

- Contagem antes/depois de pytest: `1316 -> <N>` (N ≥ 1333).
- Zero erros mypy + zero warnings ruff.
- Smoke USB + BT sem traceback; `poll.tick >= 50`; `battery.change.emitted >= 1`.
- Lista dos 17 testes novos com status (todos passando).
- Hipótese verificada: `rg "RumblePolicy"` em `src/` deve mostrar usos em `core/rumble_policy.py`, `core/rumble.py`, `daemon/lifecycle.py`, `profiles/schema.py` — nenhum outro local.

Validação visual: **não aplicável** — sprint é 100% backend. GUI não é tocada (ver Arquivos NÃO tocar).

## Riscos e não-objetivos

### Riscos técnicos

- **R1: Ciclo de import.** `schema.py` importa `core/rumble_policy.py`; `core/rumble.py` também; ambos poderiam puxar algo de `schema.py` indiretamente. Mitigação: `rumble_policy.py` **só contém** o alias `Literal` + `__all__`; zero imports de outros módulos do projeto. Risco fechado na origem.
- **R2: Custo de `get_active_rumble_config` no hot path.** `reassert_rumble` roda 5Hz e `RumbleEngine._compute_mult` pode rodar até 50Hz. Método é O(1) (só lê atributo do manager, sem disco). Impacto desprezível.
- **R3: `apply_rumble_policy` chamado via `ipc_handlers.py:266` (rumble.set) aplicando override pode surpreender usuário que setou policy global explicitamente.** Decisão semântica: **perfil ganha do global**. É o comportamento pedido pelo prompt ("perfil fps quer max, navegacao quer economia — sem setar global cada vez"). Documentar em release notes da V2.5.
- **R4: Existir `tests/unit/test_profile_schema.py` ou não.** Executor grep: `ls tests/unit/test_profile*`. Se arquivo não existir, adicionar testes #13-#16 a `tests/unit/test_profile_manager.py` com marker claro `class TestRumbleConfigSchema`.
- **R5: `apply_rumble_policy` tem guard `if daemon_cfg is None`.** Se `profile_manager` também None (smoke mode sem daemon full), código cai em `profile_override=None` e herda config. Garantido por `getattr(daemon, "_profile_manager", None)` com fallback.

### Não-objetivos desta sprint

- Expor override na GUI. Fica para `FEAT-RUMBLE-PER-PROFILE-GUI-01` (sprint candidata V2.6).
- Adicionar `policy_custom_mult` específico por perfil editável via IPC (`rumble.policy_custom_profile`). Sprint futura se houver demanda.
- Modificar JSONs default para popular `policy` em perfis específicos (ex.: `fps` ganhar `"max"` de fábrica). É decisão de curadoria de produto; fica para sprint separada `CURADORIA-PROFILES-RUMBLE-DEFAULTS-01`.
- Migrar `rumble_policy_custom_mult` do `DaemonConfig` para `policy_custom_mult` — quebraria compat com o IPC handler atual. Mantém nomes distintos no global e no perfil.

## Rollback

1. Reverter commits da sprint (git revert <SHA-merge>).
2. Garantir que nenhum JSON em `assets/profiles_default/*.json` foi modificado (critério #11 já garante).
3. `policy` em JSON de usuário salvo manualmente pós-sprint vira campo desconhecido pós-rollback (pydantic `extra="forbid"` rejeita). Mitigação: se rollback ocorrer com usuários na base, release notes instrui remover `"policy"` do JSON custom antes de downgrade.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-DualSense_Unix/VALIDATOR_BRIEF.md` — A-06, L-21-3, L-21-4.
- Precedentes:
    - `docs/process/sprints/FEAT-RUMBLE-POLICY-01.md` — introduziu policy global.
    - `docs/process/sprints/AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01.md` — consolidou `_effective_mult` como fonte única.
    - `docs/process/sprints/AUDIT-FINDING-IPC-SERVER-SPLIT-01.md` — extraiu `apply_rumble_policy`.
    - `docs/process/sprints/FEAT-LED-BRIGHTNESS-02.md` — modelo de A-06 (schema → mapper → apply) resolvido.
- Tabela de ordem: `docs/process/SPRINT_ORDER.md:436`.
