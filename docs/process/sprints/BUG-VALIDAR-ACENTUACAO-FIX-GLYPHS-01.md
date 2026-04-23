# BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01 — Anomalia de working tree durante execução paralela (INVESTIGAÇÃO)

> **Atualização 2026-04-23**: hipótese original ("`--fix` apaga glyphs") **não reproduz** em execução controlada — rodar `scripts/validar-acentuacao.py --all --fix` em HEAD `7aea630` com working tree limpa resulta em zero modificações. Os glyphs Unicode de estado (`▮▯●○◐`) continuam sãos em HEAD. Sprint reclassificada como **investigativa** — causa raiz real não identificada. Delegada à sprint 9 (AUDIT-V2-COMPLETE-01) como item específico de auditoria.
>
> Spec original preservado abaixo por contexto histórico da hipótese inicial.

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
