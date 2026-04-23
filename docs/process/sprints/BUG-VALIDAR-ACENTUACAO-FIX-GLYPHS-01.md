# BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01 — Strip de glyphs Unicode (REPRODUZIDO 2x, causa raiz não identificada)

> **Status 2026-04-23 (segunda reprodução):** hipótese original **reproduziu** 2 vezes em sessões distintas. Primeira reprodução em V2.1 (22 arquivos, HEAD `b5b1a48`). Segunda em V2.2 pós-release (25 arquivos, HEAD `e6c0e29`). Tentativas de reprodução isolada rodando apenas `scripts/validar-acentuacao.py --all --fix` em árvore limpa resultaram em zero modificações — o bug depende de **contexto de execução** ainda não identificado (provavelmente combinação de hook + subagent + timing). Classificação: bug reproduzido, causa raiz não isolada. Próximo passo: `BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-02` (spec-filha para fix canônico + blindagem).

## Segunda reprodução (2026-04-23, V2.2 pós-release v2.2.0)

Sessão `92996300-00e0-48e9-8eca-b8dd99a26d86` rodou o ciclo V2.2 inteiro, publicou `v2.2.0` no GitHub (tag `f6ca6a8`, 5 assets). Timeline do estrago:

- **19:08:21 BRT** — commit `e6c0e29` criado (`docs: 2 sprints colaterais pós-release v2.2.0`, 2 arquivos novos, 112 insertions). Working tree limpo após commit.
- **~19:10:08 BRT (+107s)** — 25 arquivos tocados em batch (mtime idêntico até milésimos de segundo — operação atômica de script). 82 glyph strips totais (U+25CF, U+25CB, U+25AE, U+25AF, U+25D0 → espaço).
- **~19:16 BRT** — sessão crashou sem detectar/reverter o estrago.

### Arquivos afetados (25)

Código (6):
- `src/hefesto/app/actions/daemon_actions.py` (6 strips)
- `src/hefesto/app/actions/emulation_actions.py` (1)
- `src/hefesto/app/actions/mouse_actions.py` (1)
- `src/hefesto/app/actions/status_actions.py` (11)
- `src/hefesto/integrations/uinput_mouse.py` (1)
- `src/hefesto/tui/widgets/__init__.py` (5)

Testes "adaptados" para aceitar strings vazias (esconde regressão — viola meta-regras 9.2+9.6) (4):
- `tests/unit/test_daemon_status_initial.py` (5)
- `tests/unit/test_daemon_status_matrix.py` (1)
- `tests/unit/test_status_actions_reconnect.py` (3)
- `tests/unit/test_tui_widgets.py` (5)

Docs (15): `CHANGELOG.md`, `README.md`, `docs/adr/012-gui-reconnect-state-machine.md`, `docs/process/CHECKLIST_HARDWARE_V2.md`, 11 specs em `docs/process/sprints/` incluindo o próprio `BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01.md` (recursividade: spec corrompeu a própria evidência em code-blocks).

### Dado bruto preservado

`git diff HEAD` salvo em `docs/history/glyph-strip-regression-2026-04-23.diff` (711 linhas) para análise forense da sprint-filha.

### Hipótese refinada

Timeline aperta o disparo: entre `Write` dos 2 specs (19:07–19:08) e batch strip (19:10:08), o assistant da sessão anterior rodou `Bash: "Testar novamente o script"` (confirmado no session log `92996300.jsonl`). Candidatos para o script:

1. `scripts/validar-acentuacao.py --fix` (primeira hipótese, não reproduz isolada)
2. `pre-commit run --all-files` com algum hook que chama validar-acentuacao
3. Hook `.git/hooks/pre-commit` (8 hooks custom instalados)
4. Wrapper de subagent que aplica normalização Unicode antes de commitar

Fator comum entre as 2 reproduções: ambas ocorreram em contexto de execução **paralela/orquestrada** (primeira em SMOKE-DEB+SMOKE-FLATPAK; segunda pós-release com 2 specs criados em sequência). Nenhuma reproduziu em `--all --fix` isolado.

### Fix proposto (spec-filha, fora desta sprint)

- Blindar `scripts/validar-acentuacao.py` contra caracteres do bloco Geometric Shapes / Block Elements / Arrows conforme ADR-011 (whitelist explícita U+2190–U+21FF, U+2500–U+257F, U+2580–U+259F, U+25A0–U+25FF).
- Teste de regressão: arquivo fixture com glyphs canônicos → `--fix` deve deixar igual.
- Logging: `--fix` deve imprimir em `--verbose` cada caractere removido com código Unicode, para facilitar debugging futuro.

---

**Tipo:** bug (crítico — corrompe arquivos silenciosamente).
**Wave:** V2.1 — fora de bloco (emergencial).
**Estimativa:** 1 iteração.
**Dependências:** CHORE-ACENTUACAO-STRICT-HOOK-01 (o bug está no script criado por ela).

---

**Tracking:** issue a criar. Label: `type:bug`, `P0-urgent`, `ai-task`, `status:ready`.

## Sintoma

Durante execução paralela de SMOKE-DEB-INSTALL-CI-01 e SMOKE-FLATPAK-BUILD-CI-01 em 2026-04-23, um dos agents rodou `pre-commit run --all-files` ou `scripts/validar-acentuacao.py --all --fix` como gate de validação pré-commit. O modo `--fix` **apagou** (não substituiu — removeu completamente) glyphs Unicode de estado em 22 arquivos:

- `▮` (U+25AE BLACK VERTICAL RECTANGLE)
- `▯` (U+25AF WHITE VERTICAL RECTANGLE)
- `●` (U+25CF BLACK CIRCLE)
- `○` (U+25CB WHITE CIRCLE)
- `◐` (U+25D0 CIRCLE WITH LEFT HALF BLACK)

Exemplo de corrupção em `src/hefesto/tui/widgets/__init__.py`:

```diff
-            return "▮▮▮▮"
+            return ""
-            return "▮▮▮▯"
+            return ""
-            return "▮▮▯▯"
+            return ""
```

Exemplo em `src/hefesto/app/actions/status_actions.py`:

```diff
-'<span foreground="#2d8">● Conectado Via {transport.upper()}</span>'
+'<span foreground="#2d8"> Conectado Via {transport.upper()}</span>'
```

Arquivos afetados (reproduzível via `git diff` após rodar `--fix` em HEAD `b5b1a48`):

- `.github/workflows/release.yml`
- `CHANGELOG.md`
- `docs/adr/012-gui-reconnect-state-machine.md`
- `docs/process/sprints/BUG-DAEMON-AUTOSTART-01.md`
- `docs/process/sprints/BUG-DAEMON-STATUS-MISMATCH-01.md`
- `docs/process/sprints/BUG-FREEZE-01.md`
- `docs/process/sprints/FEAT-MOUSE-01.md`
- `docs/process/sprints/FEAT-MOUSE-02.md`
- `docs/process/sprints/POLISH-CAPS-01.md`
- `docs/process/sprints/UI-EMULATION-ALIGN-01.md`
- `docs/process/sprints/UI-PROFILES-EDITOR-SIMPLE-01.md`
- `docs/process/sprints/UX-BANNER-01.md`
- `docs/process/sprints/UX-RECONNECT-01.md`
- `src/hefesto/app/actions/daemon_actions.py`
- `src/hefesto/app/actions/emulation_actions.py`
- `src/hefesto/app/actions/mouse_actions.py`
- `src/hefesto/app/actions/status_actions.py`
- `src/hefesto/integrations/uinput_mouse.py`
- `src/hefesto/tui/widgets/__init__.py`
- `tests/unit/test_daemon_status_matrix.py`
- `tests/unit/test_status_actions_reconnect.py`
- `tests/unit/test_tui_widgets.py`

## Reabertura da armadilha A-04

VALIDATOR_BRIEF.md documenta A-04 como **RESOLVIDA** pela sprint UX-HEADER-01 em 2026-04-21:

> A-04: Diff working-tree 2026-04-21 removeu glyphs Unicode de estado. [...] Risco: interpretação errada de "zero emojis" strippou BLACK/WHITE CIRCLE (U+25CF/U+25CB) dos markups Pango, zerou `BatteryMeter._icon_for_level` (retorna `""` para todos os níveis). [...] Fix canônico: reverter os `*_actions.py` e `tui/widgets/__init__.py` ao HEAD~0 pré-diff.

Esta sprint **reabre A-04** sob nova vertente: o automator (`--fix`) reproduz o mesmo erro de interpretação. A armadilha deixa de ser "RESOLVIDA" e vira "RESOLVIDA + regressão automatizada via `--fix` até esta sprint".

## Decisão

Corrigir o `scripts/validar-acentuacao.py` para que:

1. O **dicionário de substituições** nunca contenha palavra-alvo que seja caractere Unicode solto ou token que inclua blocos Unicode de estado. Revisar todas as 315 entradas procurando por entradas exóticas.
2. O modo `--fix` **nunca** toque um caractere fora do par `(sem_acento, com_acento)` registrado no dicionário. Se houver código de fallback "limpa caracteres estranhos", remover.
3. O regex de match deve usar `\b` ou `(?<![\w])` para boundary em **apenas** caracteres ASCII letra/dígito/underscore. Caracteres Unicode de bloco geométrico (`▮▯●○◐`) nunca podem ser considerados parte de "palavra" no sentido do match.
4. Adicionar **teste de regressão A-04** bloqueando o bug:
   - `test_fix_preserva_glyph_black_circle`: input contém `"● Conectado"`, após `--fix` continua contendo `"● Conectado"`.
   - `test_fix_preserva_glyph_block_elements`: input com `"▮▮▮▯"`, após `--fix` preservado.
   - `test_fix_preserva_glyph_half_circle`: input com `"◐ Tentando"`, preservado.
   - `test_fix_preserva_caixa_batery`: teste exato do `BatteryMeter._icon_for_level`.

## Critérios de aceite

- [ ] Identificar a causa raiz no `--fix`: qual código está removendo os caracteres. Possibilidades a investigar: (a) regex com `re.sub` case-sensitive que casa qualquer non-ASCII; (b) normalização NFKD que foi aplicada ao conteúdo do arquivo, não só ao slug; (c) substituição por `.encode("ascii", "ignore").decode()` em algum lugar.
- [ ] Fix cirúrgico: o `--fix` só altera pares documentados no dicionário. Nenhum caractere fora desse contrato é tocado.
- [ ] 4 testes de regressão A-04 adicionados a `tests/unit/test_validar_acentuacao.py`.
- [ ] Rodar `scripts/validar-acentuacao.py --all --fix` em working tree limpa do HEAD → zero alterações (diff vazio). Isto é o proof-of-work definitivo.
- [ ] Atualizar VALIDATOR_BRIEF.md seção A-04 mencionando esta sprint.
- [ ] Rodar gates canônicos (pytest, ruff, anonymity, acento, smoke USB+BT).

## Arquivos tocados

- `scripts/validar-acentuacao.py` (editar — fix no `--fix`)
- `tests/unit/test_validar_acentuacao.py` (estender — 4 testes de regressão)
- `VALIDATOR_BRIEF.md` (atualizar A-04)

## Proof-of-work runtime

```bash
.venv/bin/pytest tests/unit/test_validar_acentuacao.py -v
.venv/bin/pytest tests/unit -q  # espera ≥ 982 passed (978 + 4 regressão)

# Proof definitivo — dry-run em árvore limpa
git status --short  # deve estar vazio
python3 scripts/validar-acentuacao.py --all --fix
git status --short  # continua vazio — --fix não alterou nada

./scripts/check_anonymity.sh
python3 scripts/validar-acentuacao.py --all
.venv/bin/pre-commit run --all-files

HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt
```

## Notas para o executor

- A causa raiz é quase certamente uma linha de normalização ampla. O script tem 677 linhas; isolar via `git log scripts/validar-acentuacao.py` e inspecionar implementação de `--fix`.
- O teste **mais importante** é `git status --short` vazio após rodar `--fix` em árvore limpa. Se sobrar qualquer arquivo no diff, o fix ainda não está pronto.
- Não redescobrir a roda: o script CORRIGE pares do dicionário. `--fix` deve iterar pares e fazer `re.sub(padrão_sem_acento, palavra_com_acento, conteúdo)`. Ponto. Nada mais.
- VALIDATOR_BRIEF atualização: manter a linha "RESOLVIDA pela UX-HEADER-01" e adicionar "+ regressão fechada por BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01 em 2026-04-23".

## Fora de escopo

- Rewrite do script. Escopo é **cirúrgico**: fix no `--fix`, 4 testes, update BRIEF.
- Mudar dicionário de palavras-risco.
- Mexer na whitelist de paths.
- Alterar comportamento do `--check-file` (só o `--fix` é afetado).
