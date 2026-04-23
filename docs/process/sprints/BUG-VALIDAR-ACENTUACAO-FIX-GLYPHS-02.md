# BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-02 — Blindar validar-acentuacao.py contra strip de glyphs

**Tipo:** bug (crítico — prevenção de regressão já reproduzida 2x).
**Wave:** V2.2.1 — patch release.
**Estimativa:** XS (0.5 iteração).
**Dependências:** BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01 (sprint-mãe investigativa; ambas reproduções documentadas).

---

**Tracking:** label `type:bug`, `P0-urgent`, `prevention`, `ai-task`, `status:ready`.

## Contexto

`BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01` registrou duas reproduções empíricas do strip de glyphs Unicode de estado (U+25CF, U+25CB, U+25AE, U+25AF, U+25D0) em `scripts/validar-acentuacao.py --fix`:

- **V2.1 (2026-04-22):** 22 arquivos, HEAD `b5b1a48`, durante execução paralela de SMOKE-DEB-INSTALL-CI-01 + SMOKE-FLATPAK-BUILD-CI-01.
- **V2.2 pós-release (2026-04-23 19:10:08 BRT):** 25 arquivos, HEAD `e6c0e29`, session `92996300`; crash antes de detectar. Evidência bruta em `docs/history/glyph-strip-regression-2026-04-23.diff` (711 linhas).

Tentativas de reprodução isolada em árvore limpa falharam. Gatilho específico não-isolado. **Este spec não busca identificar o gatilho — busca blindar o script para que o gatilho, quando ocorrer, não destrua arquivos.**

## Decisão

Três camadas complementares:

### Camada 1 — Whitelist explícita de blocos Unicode (defesa principal)

`scripts/validar-acentuacao.py` passa a ter:

```python
# Ranges permitidos por ADR-011 — jamais remover.
UNICODE_ALLOWED_RANGES = [
    (0x2190, 0x21FF),  # Arrows
    (0x2500, 0x257F),  # Box Drawing
    (0x2580, 0x259F),  # Block Elements
    (0x25A0, 0x25FF),  # Geometric Shapes
]

def is_protected_codepoint(cp: int) -> bool:
    return any(lo <= cp <= hi for lo, hi in UNICODE_ALLOWED_RANGES)
```

Antes de aplicar qualquer substituição em modo `--fix`, verificar se o caractere-alvo é protegido. Se for, abortar substituição e emitir warning.

### Camada 2 — Modo `--fix` em dry-run por default

`--fix` sem flag `--write` imprime o diff que seria aplicado mas não escreve. Para escrever, exigir `--fix --write` explícito. Previne invocação acidental por hooks/wrappers/subagents.

Migração: workflows existentes que chamam `--fix` precisam passar a chamar `--fix --write`. Auditar pre-commit hooks e CI.

### Camada 3 — Logging verboso de remoções

`--fix --write --verbose` imprime, para cada caractere removido:
- codepoint Unicode (ex: `U+25CF`)
- nome oficial (ex: `BLACK CIRCLE`)
- bloco (ex: `Geometric Shapes`)
- arquivo:linha
- contexto (±20 chars ao redor)

Facilita debug em reprodução futura. Output em stderr para não poluir diff.

## Critérios de aceite

- [ ] `scripts/validar-acentuacao.py` define `UNICODE_ALLOWED_RANGES` e `is_protected_codepoint()` conforme ADR-011.
- [ ] `--fix` sem `--write` é dry-run (imprime, não escreve). Comportamento previamente implícito em `--fix` agora exige flag explícita.
- [ ] Caractere protegido em modo `--fix --write` emite warning em stderr e **não é removido**.
- [ ] Flag `--verbose` imprime codepoint + nome + bloco + arquivo:linha + contexto de cada remoção.
- [ ] Teste novo `tests/unit/test_validar_acentuacao_glyphs.py`:
  - Fixture com arquivo contendo `●○▮▯◐` e strings PT-BR válidas/inválidas.
  - Asserta que `--fix --write` deixa glyphs intactos.
  - Asserta que acentuação PT-BR é corrigida normalmente.
  - Asserta que `--fix` sem `--write` não modifica arquivos.
- [ ] `docs/history/glyph-strip-regression-2026-04-23.diff` continua preservado (ver GLYPHS-01).
- [ ] README seção "Scripts de desenvolvimento" (se existir) documenta o novo comportamento `--fix/--write/--verbose`.
- [ ] CHANGELOG v2.2.1 entry "Added: proteção contra remoção de glyphs Unicode de estado em scripts/validar-acentuacao.py (ADR-011)".

## Arquivos tocados

- `scripts/validar-acentuacao.py` (modificação).
- `tests/unit/test_validar_acentuacao_glyphs.py` (novo).
- `CHANGELOG.md` (entry v2.2.1).
- `README.md` (seção scripts, se existir).

## Proof-of-work

```bash
# 1. Teste regressão passa
.venv/bin/pytest tests/unit/test_validar_acentuacao_glyphs.py -v

# 2. Fixture com glyph ACEITA
cat > /tmp/glyph-fixture.md <<'EOF'
● online (U+25CF)
○ offline (U+25CB)
facilmentee (typo — DEVE ser corrigido)
EOF
python3 scripts/validar-acentuacao.py --fix --write --verbose /tmp/glyph-fixture.md
# esperado: fix só a linha "facilmentee", glyphs mantidos

# 3. Dry-run não escreve
cp /tmp/glyph-fixture.md /tmp/glyph-before.md
python3 scripts/validar-acentuacao.py --fix /tmp/glyph-fixture.md  # sem --write
diff /tmp/glyph-fixture.md /tmp/glyph-before.md
# esperado: diff vazio (nenhuma modificação)

# 4. Gates canônicos
.venv/bin/pytest -q
.venv/bin/mypy src/hefesto scripts
```

## Riscos e mitigações

| Risco | Severidade | Mitigação |
|---|---|---|
| Quebra de workflows existentes que usam `--fix` implícito | Médio | Deprecation warning por 1 release; migrar pre-commit hooks + CI no mesmo PR |
| Whitelist cobre range mas não caso específico | Baixo | Cobertura de teste inclui U+25CF, U+25CB, U+25AE, U+25AF, U+25D0 + range boundaries (U+25A0, U+25FF) |
| `--verbose` poluir stdout de scripts encadeados | Baixo | Log em stderr, não stdout |

## Notas para o executor

- O script atual em `scripts/validar-acentuacao.py` tem 811 linhas — re-ler antes de editar. Identificar função de substituição que aplica replacements e inserir checagem ali.
- Memória auto do Claude em `feedback_glyphs_vs_emojis.md` contém o racional do ADR-011 — consultar para edge cases.
- Pre-commit hook atual: `.pre-commit-config.yaml` chama o script como `acentuacao-strict`. Se ele invoca `--fix`, adaptar para `--fix --write` ou remover dependência.

## Fora de escopo

- **Identificar** o gatilho que causa strip (isso fica com GLYPHS-01 investigativa; esperamos a 3ª reprodução para ter mais dados).
- Refactor arquitetural do script (fora do escopo patch).
- Whitelist dinâmica via config (YAGNI — ranges ADR-011 são fixos).

## Referências

- `docs/adr/011-glyphs-vs-emojis.md` — decisão canônica.
- `docs/process/sprints/BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01.md` — sprint-mãe investigativa.
- `docs/history/glyph-strip-regression-2026-04-23.diff` — evidência bruta da 2ª reprodução.
- Memória auto: `feedback_glyphs_vs_emojis.md`.
