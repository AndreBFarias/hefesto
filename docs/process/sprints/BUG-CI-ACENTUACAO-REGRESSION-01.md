# BUG-CI-ACENTUACAO-REGRESSION-01 — CI acentuacao vermelho em main desde pelo menos v2.2.1

**Tipo:** bug (CI/qualidade).
**Wave:** colateral descoberto durante execução de v2.2.2.
**Estimativa:** XS (0.25 iteração).
**Dependências:** nenhuma.

---

**Tracking:** label `type:bug`, `ci`, `quality`, `ai-task`, `status:ready`.

## Contexto

Durante a Fase A2b da release v2.2.2 (2026-04-24), `python3 scripts/validar-acentuacao.py --all` retornou **exit=1 com 10 violações** pré-existentes em `main` (HEAD `b913ed2`), fazendo o job `acentuacao` do `.github/workflows/ci.yml` falhar nos últimos 3 commits.

**Atualização 2026-04-24 pós-v2.2.2 publicada:** re-rodando o validator em `HEAD=b12e28e`, a contagem real caiu para **6 violações** — os fixes iterativos da v2.2.2 tocaram `release.yml` e o vocabulário mudou. Lista real abaixo (ignore a tabela histórica de 10 mais abaixo).

- `b913ed2 fix: BUG-DEB-SMOKE-PYDANTIC-V2-NOBLE-01 + L-21-7 no BRIEF` → CI failure
- `01b39bb docs: v2.2.1 publicada ...` → CI failure
- `b17b81b release: v2.2.1 — patch pós-v2.2.0 ...` → CI failure

O job `acentuacao` roda em `ci.yml` (push main + PR) mas **não bloqueia** `release.yml` (push tag), então v2.2.1 saiu mesmo com ci.yml vermelho — ruído que deveria ter sido detectado pelo validator-sprint em algum commit antes.

## Violações encontradas (estado real 2026-04-24 HEAD b12e28e — 6 violações)

| Arquivo | Linha | Palavra sem acento | Sugestão |
|---|---|---|---|
| `.github/workflows/release.yml` | 116 | `Historico` | `Histórico` |
| `.github/workflows/release.yml` | 116 | `iteracoes` | `iterações` |
| `tests/unit/test_firmware_updater.py` | 66 | `tambem` (string literal) | `também` |
| `tests/unit/test_firmware_updater.py` | 119 | `generico`, `binario` (string literal) | `genérico`, `binário` |
| `tests/unit/test_validar_acentuacao_glyphs.py` | 145 | `conteudo` (identifier Python) | renomear para `texto_final` |
| `tests/unit/test_validar_acentuacao_glyphs.py` | 146 | `conteudo` (mesma variável) | renomear para `texto_final` |

### Tabela histórica (v2.2.2 em voo, apenas referência)

| Arquivo | Linha | Palavra sem acento | Sugestão |
|---|---|---|---|
| `.github/workflows/release.yml` | 116 | `validacao` | `validação` |
| `.github/workflows/release.yml` | 117 | `tambem` | `também` |
| `.github/workflows/release.yml` | 118 | `nao` | `não` |
| `.github/workflows/release.yml` | 119 | `nao` | `não` |
| `.github/workflows/release.yml` | 121 | `nao` | `não` |
| `.github/workflows/release.yml` | 136 | `necessario` | `necessário` |
| `tests/unit/test_firmware_updater.py` | 66 | `tambem` (string literal) | `também` |
| `tests/unit/test_firmware_updater.py` | 119 | `generico`, `binario` (string literal) | `genérico`, `binário` |
| `tests/unit/test_validar_acentuacao_glyphs.py` | 145-146 | `conteudo` (identifier Python) | `conteudo_final` OU renomear |

**Análise:**

- 6 violações em `release.yml` são comentários descritivos em PT-BR sem acentuação. Fix trivial (substituir ASCII → Unicode acentuado).
- 3 violações em `tests/unit/test_firmware_updater.py` são string literals de fixture. Também fix trivial, strings mock podem ter acentos sem alterar semântica.
- 2 violações em `tests/unit/test_validar_acentuacao_glyphs.py` são **nome de variável local Python** (`conteudo = arq.read_text(...)`). Identifiers Python 3 aceitam Unicode mas por convenção PEP 8 evita-se. **Discussão:** o validador deveria ignorar identifiers Python? Ou o teste deveria renomear para `texto_final`/`dados` evitando o alerta?

## Decisão

Fix em 2 camadas:

1. **Texto em comentários/fixtures** (8 violações): adicionar acentuação correta.
2. **Identifier Python** (2 violações): renomear variável `conteudo` → `texto_final` em `test_validar_acentuacao_glyphs.py:145-146` para evitar falso positivo. Protocolo: nomes de variável não devem disparar o validador (a alternativa — adicionar whitelist no validador — é over-engineered para 2 ocorrências).

Após o fix, `python3 scripts/validar-acentuacao.py --all` retorna exit 0 e o job `acentuacao` volta a verde.

## Critérios de aceite

- [ ] `python3 scripts/validar-acentuacao.py --all` retorna exit 0 em `main`.
- [ ] Job `acentuacao` no CI passa (verificar na próxima run após merge).
- [ ] `git log --oneline origin/main..HEAD` contém commit `fix(quality): BUG-CI-ACENTUACAO-REGRESSION-01 — 10 violações pré-existentes`.
- [ ] CHANGELOG `[Unreleased]` ganha bullet no bloco `### Corrigido`.
- [ ] Nenhum teste quebra (`.venv/bin/pytest tests/unit -q --no-header`).

## Arquivos tocados

- `.github/workflows/release.yml` (linhas 116-136).
- `tests/unit/test_firmware_updater.py` (linhas 66, 119).
- `tests/unit/test_validar_acentuacao_glyphs.py` (linhas 145-146, renomear `conteudo` → `texto_final`).

## Proof-of-work

```bash
# Antes:
python3 scripts/validar-acentuacao.py --all; echo $?   # 1

# Aplicar fix.

# Depois:
python3 scripts/validar-acentuacao.py --all; echo $?   # 0
.venv/bin/pytest tests/unit -q --no-header              # sem regressão
```

## Fora de escopo

- Alterar o validador para ignorar identifiers Python (over-engineering, 2 ocorrências só).
- Reescrever `validar-acentuacao.py` inteiro.
- Adicionar pre-commit hook se ainda não existe.

## Notas

- Descoberto durante A2b da release v2.2.2 (2026-04-24) ao rodar validações pré-commit.
- Protocolo anti-débito 9.7: documentado como spec-nova, não como "TODO depois". Fix fora do escopo da v2.2.2 para não inflar release de cleanup com correção de texto não relacionada.
- Implicação pro CI: ci.yml vermelho persiste até esta sprint ser MERGED. release.yml (que dispara release) é ortogonal e não afetado.
