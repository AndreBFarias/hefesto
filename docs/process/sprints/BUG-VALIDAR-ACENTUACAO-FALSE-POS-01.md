# BUG-VALIDAR-ACENTUACAO-FALSE-POS-01 — Falso-positivos no validar-acentuacao.py

**Tipo:** bug P1 — job CI `acentuacao` quebrado no `main` por regra errada + ambiguidade verbo/substantivo.
**Wave:** V2.2 — achado colateral de BUG-CI-RELEASE-MYPY-GATE-01.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:bug`, `P1-high`, `ci`, `ai-task`, `status:ready`.

## Sintoma

`python3 scripts/validar-acentuacao.py --all` falha no `main` com 2 violações:

```
docs/process/sprints/FEAT-FIRMWARE-UPDATE-PHASE3-01.md:16:referencia -> sugestão referência
docs/process/sprints/FEAT-MOUSE-TECLADO-COMPLETO-01.md:116:facilmente -> sugestão fácilmente
```

Reproduzido em HEAD limpo (`git stash && validar-acentuacao --all`): ambos pré-existem ao commit da fix de CI mypy. Job `acentuacao` em `.github/workflows/ci.yml` roda `--all` e bloqueia PRs.

## Análise

### Par `facilmente -> fácilmente` (sempre errado)

`scripts/validar-acentuacao.py:311` define `_par("f" + "acilmente", "f" + "á" + "cilmente")`. Em PT-BR, advérbios em `-mente` derivados de adjetivos paroxítonos acentuados **perdem** o acento gráfico do radical (o sufixo `-mente` muda a tonicidade). "Fácil" → "facilmente" sem acento. "Fácilmente" **não é palavra**.

Regra geral: pares `Xmente` só têm acento quando o adjetivo de origem é oxítona ou com acento próprio que se mantém — caso de "rápida" → "rapidamente" (sem acento em "rapidamente" também). A maioria dos advérbios em `-mente` **não leva** acento.

### Par `referencia -> referência` (falso-positivo contextual)

`scripts/validar-acentuacao.py:322` define `_par("refer" + "encia", "refer" + EC + "ncia")`. Em PT-BR, "referencia" é forma ambígua:
- Substantivo "referência" (paroxítona com acento na antepenúltima) — escrita correta com acento.
- Verbo "referenciar" conjugado (ele referencia, sem acento) — correto sem acento.

O par vale para 90% dos casos (substantivo). Para verbo, é falso-positivo contextual. Spec `FEAT-FIRMWARE-UPDATE-PHASE3-01.md:16` usa forma verbal:

> esta sprint **não** distribui, redistribui, incorpora, embala ou **referencia** blob proprietário

Par dispara incorretamente. Fix cirúrgico: reescrever a frase com substantivo ("faz referência a") ou sinônimo ("menciona"), mantendo o par no script (útil no geral).

## Decisão

1. **Remover par** `_par("f" + "acilmente", ...)` do script — sempre errado.
2. **Reescrever frase** no spec PHASE3 linha 16: `...embala ou referencia blob...` → `...embala ou faz referência a blob proprietário`.
3. Não whitelist-ar `docs/process/sprints/**` como path inteiro — specs são produto de trabalho canônico e devem passar na validação.

## Critérios de aceite

- [ ] `scripts/validar-acentuacao.py`: par `"f" + "acilmente"` removido.
- [ ] `docs/process/sprints/FEAT-FIRMWARE-UPDATE-PHASE3-01.md:16` reescrito com "faz referência a" (ou equivalente substantivado).
- [ ] `python3 scripts/validar-acentuacao.py --all` retorna zero violações.
- [ ] `pytest tests/unit/test_validar_acentuacao.py` continua verde (regra do par removido não deve quebrar fixture).
- [ ] Gates canônicos.

## Arquivos tocados

- `scripts/validar-acentuacao.py` (remove 1 linha).
- `docs/process/sprints/FEAT-FIRMWARE-UPDATE-PHASE3-01.md` (edita 1 linha).

## Proof-of-work runtime

```bash
.venv/bin/python scripts/validar-acentuacao.py --all
# esperado: "OK: nenhuma violacao"

.venv/bin/pytest tests/unit/test_validar_acentuacao.py -v
# esperado: todos verdes
```

## Fora de escopo

- Revisar outros 314 pares em busca de falso-positivos (sprint de auditoria separada, se demanda aparecer).
- Tornar `referencia` sensível a contexto sintático (parser PT-BR completo — overkill).
