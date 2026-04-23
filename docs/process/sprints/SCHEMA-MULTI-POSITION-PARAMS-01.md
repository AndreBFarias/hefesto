# SCHEMA-MULTI-POSITION-PARAMS-01 — Schema aceita `params` aninhado para modos multi-position

**Tipo:** feat (schema + core + perfis).
**Wave:** V2.1 — Bloco B.
**Estimativa:** 1-2 iterações.
**Dependências:** PROFILE-DISPLAY-NAME-01 (roda depois, reusa infra de perfis).

---

**Tracking:** issue a criar. Label: `type:feature`, `P2-medium`, `ai-task`, `status:ready`.

## Contexto

`TriggerConfig.params` em `src/hefesto/profiles/schema.py:62-66` hoje é `list[int]`. Não suporta formas aninhadas do tipo `[[0,1],[2,3],...]` que `MultiPositionFeedback` e `MultiPositionVibration` (em `src/hefesto/core/trigger_effects.py:239-260`) aceitariam como input canônico para expressar 10 posições de resistência/vibração independentes ao longo do curso do gatilho.

Sintoma concreto: `FEAT-PROFILES-PRESET-06` teve que representar `aventura` e `corrida` com modos substitutos (`SlopeFeedback`, `Vibration`) porque o schema rejeita params aninhado. Perdemos granularidade.

`build_from_name()` em `:331-339` já aceita `list[int] | dict[str,int]` e faz `*params` — é o ponto de extensão natural para também aceitar `list[list[int]]`.

## Decisão

1. Estender schema para aceitar `params: list[int] | list[list[int]]`, mantendo backcompat total.
2. Estender `build_from_name()` para dispatchar correto quando nested.
3. Migrar 2 perfis default onde multi-position faz sentido (`aventura`, `corrida`).

### Matriz de decisão dos 8 perfis

| Perfil | Decisão | Modo alvo | Justificativa |
|---|---|---|---|
| `acao` | manter | Resistance/SlopeFeedback | Jogos de ação genéricos funcionam com degradê |
| `aventura` | **migrar** | MultiPositionFeedback | Exploração se beneficia de zonas distintas — começo leve, meio firme, fim rígido |
| `corrida` | **migrar** | MultiPositionVibration | Acelerador quer vibração crescente com curso do gatilho (escala 0→10) |
| `esportes` | manter | Vibration simples | Chute/passe não precisa gradiente complexo |
| `fps` | manter | WeaponRifle/Rigid | Canônico para mira/tiro, multi-position não agrega |
| `fallback` | **proibido migrar** | qualquer | Perfil universal precisa ser o mais estável — zero risco de config exótica |
| `meu_perfil` | manter | o que o usuário definir | Perfil do usuário, nunca sobrescrever defaults |
| `navegacao` | manter | Off/Bow | Sem interação com gatilho |

Total migrado: **2 perfis**.

### Mudanças de código

**Schema** (`src/hefesto/profiles/schema.py:62-66`):
```python
class TriggerConfig(BaseModel):
    mode: str
    params: list[int] | list[list[int]] = Field(default_factory=list)

    @field_validator("params", mode="after")
    @classmethod
    def _validate_params(cls, v: list[int] | list[list[int]]) -> list[int] | list[list[int]]:
        if not v:
            return v
        first = v[0]
        if isinstance(first, list):
            assert all(isinstance(x, list) for x in v), "params aninhado: todos os elementos devem ser list[int]"
            assert all(all(isinstance(n, int) for n in x) for x in v), "params aninhado: valores devem ser int"
        else:
            assert all(isinstance(x, int) for x in v), "params simples: todos devem ser int"
        return v

    @property
    def is_nested(self) -> bool:
        return bool(self.params) and isinstance(self.params[0], list)
```

**Factory dispatch** (`src/hefesto/core/trigger_effects.py:331-339`):
```python
def build_from_name(mode: str, params: list[int] | list[list[int]] | dict[str, int]) -> TriggerEffect:
    if mode == "MultiPositionFeedback":
        if params and isinstance(params[0], list):
            strengths = _flatten_multi_position(params)  # helper novo
        else:
            strengths = list(params)
        return MultiPositionFeedback(strengths=strengths)
    if mode == "MultiPositionVibration":
        # idem
        ...
    # demais modos: comportamento atual preservado
```

**Helper `_flatten_multi_position`**:
```python
def _flatten_multi_position(nested: list[list[int]]) -> list[int]:
    """Achata [[start0, end0], [start1, end1], ...] em [val0, val1, ...]
    expandindo para as 10 posições canônicas do gatilho DualSense."""
    # Regra: cada sublista [start, end] define a força na zona correspondente
    # Posições 0-1: zona inicial (stick neutro→leve)
    # Posições 2-5: zona média
    # Posições 6-9: zona final (aperto máximo)
    # Se nested tem 5 sublistas, distribui 2 posições por sublista.
    # Se nested tem 10 sublistas, usa 1:1 (cada [x] é posição x).
    # Validação: len(nested) ∈ {2, 5, 10}.
    ...
```

**Perfis migrados** — exemplo `aventura.json`:
```json
{
  "triggers": {
    "l2": {"mode": "MultiPositionFeedback", "params": [[2], [3], [4], [5], [6], [7], [8], [9], [10], [10]]},
    "r2": {"mode": "MultiPositionFeedback", "params": [[2], [3], [4], [5], [6], [7], [8], [9], [10], [10]]}
  }
}
```

`corrida.json`:
```json
{
  "triggers": {
    "l2": {"mode": "Rigid"},
    "r2": {"mode": "MultiPositionVibration", "params": [[0], [1], [2], [4], [6], [7], [8], [9], [10], [10]]}
  }
}
```

(Valores exatos a afinar pelo executor conforme semântica dos modos.)

## Critérios de aceite

- [ ] Schema aceita ambos formatos (`list[int]` e `list[list[int]]`).
- [ ] Validator pydantic rejeita misturas (`[[1,2], 3]` → erro claro).
- [ ] `build_from_name` com `mode="MultiPositionFeedback"` e params aninhado retorna instância correta com strengths de len 10.
- [ ] `aventura.json` e `corrida.json` migrados; carregam sem erro.
- [ ] Demais 6 perfis (`acao`, `esportes`, `fps`, `fallback`, `meu_perfil`, `navegacao`) preservam config atual — diff vazio em `git diff` para esses arquivos exceto `display_name` se sprint 1 já rodou.
- [ ] Teste `tests/unit/test_schema_multi_position.py` (novo, ≥ 6 casos): roundtrip, validação, flatten, build correto, aventura carrega, corrida carrega.
- [ ] Estender `tests/unit/test_profile_loader.py`: `test_loader_aventura_nested_params` e `test_loader_corrida_nested_params`.
- [ ] Estender `tests/unit/test_profile_manager.py`: `test_apply_propaga_multi_position` — A-06 check — `TriggerSettings` recebe 10 strengths expandidos após `apply()`.
- [ ] Smoke USB+BT verde com `profile.switch` para `aventura` e `corrida`.
- [ ] Sem traceback em log; log estruturado emite `trigger.mode.applied mode=multi_position_feedback` ou equivalente.
- [ ] `CHECKLIST_HARDWARE_V2.md` (sprint 8) inclui item de validação tátil para aventura/corrida.

## Arquivos tocados

- `src/hefesto/profiles/schema.py`
- `src/hefesto/core/trigger_effects.py`
- `src/hefesto/profiles/manager.py` (se propagação precisar ajuste — avaliar durante execução)
- `assets/profiles_default/aventura.json`
- `assets/profiles_default/corrida.json`
- `tests/unit/test_schema_multi_position.py` (novo)
- `tests/unit/test_profile_loader.py` (estender)
- `tests/unit/test_profile_manager.py` (estender)

## Proof-of-work runtime

```bash
.venv/bin/pytest tests/unit/test_schema_multi_position.py tests/unit/test_profile_loader.py tests/unit/test_profile_manager.py -v
.venv/bin/ruff check src/hefesto/profiles src/hefesto/core/trigger_effects.py
.venv/bin/mypy src/hefesto/profiles src/hefesto/core
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt

# Switch para aventura via IPC e confirmar ausência de traceback
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.daemon.main &
DPID=$!
sleep 2
echo '{"jsonrpc":"2.0","id":1,"method":"profile.switch","params":{"name":"aventura"}}' | socat - UNIX-CONNECT:$XDG_RUNTIME_DIR/hefesto/hefesto.sock
echo '{"jsonrpc":"2.0","id":2,"method":"profile.switch","params":{"name":"corrida"}}' | socat - UNIX-CONNECT:$XDG_RUNTIME_DIR/hefesto/hefesto.sock
kill $DPID
```

## Notas para o executor

- **A-06 check obrigatório**: `_to_led_settings` não precisa mudança, mas `_to_trigger_settings` (ou equivalente que converte `TriggerConfig → TriggerSettings`) precisa detectar params aninhado e passar corretamente ao factory. Teste `test_apply_propaga_multi_position` prova end-to-end.
- **Validação tátil é impossível sem hardware** nesta sessão. O executor confia no smoke (ausência de traceback + chamada correta ao `set_triggers`). CHANGELOG v2.1.0 vai ter nota explícita: "aventura/corrida migradas para multi-position, validação tátil pendente; reverter via `git checkout v2.0.0 -- assets/profiles_default/{aventura,corrida}.json` se sensação regredir".
- **Helper `_flatten_multi_position`**: a semântica de "como as 10 posições mapeiam em zonas" depende do DualSense. Começar com mapeamento trivial (1:1 se nested tem 10, duplicado se nested tem 5, grupo-5 se nested tem 2). O executor pode ajustar se a documentação `trigger-modes.md` já canoniza algo diferente.
- **Perfis fora da migração** — **NÃO mexer** em `fallback.json`. Fallback é o perfil de segurança; quebrar ali derruba autoswitch em situações patológicas.
- **Roundtrip JSON**: `json.dumps(ensure_ascii=False, indent=2)` preserva estrutura aninhada legível. `json.loads` reconstrói corretamente. Teste de roundtrip deve cobrir os dois formatos.

## Fora de escopo

- Interface GUI para editar params aninhado (editor atual assume slider simples; versão avançada fica para sprint futura).
- Migrar `acao`, `esportes` — por decisão explícita; multi-position não melhora ali.
- Curva personalizada (spline) — é V2.x.
- Importar perfis multi-position de formato externo (.pco, .reasonable) — fora de escopo.
