# BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-03 — 3a reproducao do strip de glyphs ADR-011 + reforco do filtro

**Tipo:** bug (crítico — corrupcao silenciosa ja reproduzida 3x).
**Wave:** v3.0.x — patch.
**Estimativa:** 1 iteração (S/M).
**Branch:** `rebrand/dualsense4unix`. PR alvo: #103.
**Dependências:** BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01 (investigativa, 2 reproducoes), BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-02 (whitelist + filtro camada 1).

---

## Contexto

Em **2026-04-27**, durante auditoria do tray, o usuario rodou `scripts/validar-acentuacao.py --fix` em working tree com diff WIP da auditoria. O comando strippou silenciosamente **93 ocorrencias de glyphs Unicode protegidos por ADR-011** (`U+25CF ●`, `U+25CB ○`, `U+25D0 ◐`, `U+25B3 △`, `U+25A1 □`) em arquivos espalhados:

- `src/hefesto_dualsense4unix/app/actions/status_actions.py` (cascata de pontos verdes/vermelhos do header — 11 ocorrencias).
- `src/hefesto_dualsense4unix/app/actions/daemon_actions.py` (status do daemon — 6+ indicadores).
- `src/hefesto_dualsense4unix/app/actions/mouse_actions.py` (legenda de mapeamento de botoes: `△`, `○`, `□`).
- `src/hefesto_dualsense4unix/app/actions/emulation_actions.py` (1 ocorrencia).
- `src/hefesto_dualsense4unix/integrations/uinput_mouse.py` (3 ocorrencias).
- `src/hefesto_dualsense4unix/tui/widgets/__init__.py` (cascata de barras BatteryMeter).
- 11 sprints historicas em `docs/process/sprints/`.
- `docs/adr/012-gui-reconnect-state-machine.md`.

Especialmente revelador: o `--fix` strippou tambem o glyph **dentro do proprio comentario do filtro de protecao** em `scripts/validar-acentuacao.py:693` (`# colocasse "●" como "errada"` -> `# colocasse "" como "errada"`).

O usuário descartou a WIP via `git stash drop`, mas o bug raiz no script persiste — esta e a 3a reproducao documentada (V2.1, V2.2 pos-release, v3.0.x).

### Trechos confirmados via leitura direta (L-21-3)

- `scripts/validar-acentuacao.py:494-513` — whitelist `UNICODE_ALLOWED_RANGES`, `is_protected_codepoint`, `_contem_glyph_protegido` (introduzidos por GLYPHS-02). Cobrem U+2190-U+21FF (Arrows), U+2500-U+257F (Box Drawing), U+2580-U+259F (Block Elements), U+25A0-U+25FF (Geometric Shapes — inclui `●○◐△□▮▯` etc.).
- `scripts/validar-acentuacao.py:614-730` — função `corrigir_arquivo()`. Loop por linha; para cada par `(errada, correta)` em `_CORRECOES`, gera lista `subs: list[(start, end, replacement)]`; bloco `:690-708` filtra `subs` rejeitando aquelas cuja faixa `linha[s:e]` contem glyph protegido; aplica em ordem reversa `:710-723`.
- `tests/unit/test_validar_acentuacao_glyphs.py:105-154` — ja existem testes `test_arquivo_com_glyph_preservado` e `test_par_malicioso_bloqueado` que cobrem os casos previstos pelo filtro atual.
- `src/hefesto_dualsense4unix/app/actions/mouse_actions.py:24-31` — legenda de mapeamento contendo `Triangulo (△)`, `Circulo (○)`, `Quadrado (□)`, `D-pad (↑↓←→)`. Todos os 7 glyphs estao dentro de UNICODE_ALLOWED_RANGES.
- `src/hefesto_dualsense4unix/app/actions/status_actions.py:270,288,313` e `daemon_actions.py:537` — todas as ocorrencias de `○`/`●` de status estao em strings com texto PT-BR ja acentuado (sem palavras-alvo do dicionario na mesma linha).

### Diagnostico preliminar

A whitelist atual cobre todos os codepoints reportados. O filtro `:690-708` rejeita corretamente quando `linha[s:e]` contem glyph. Mas o filtro examina **apenas a faixa do match `re.finditer`** — **nao examina a linha inteira**. Se a linha tem `● Conectado Via {transport.upper()}`, e o regex casa `xao` em outra parte (caso hipotetico), o filtro deixa passar porque o slice nao toca o `●`. Em si isto e ortogonal: a substituicao acertaria so a palavra-alvo, preservando `●`.

A 3a reproducao sugere que o strip não esta vindo do `corrigir_arquivo()` em si — ele esta vindo de outro vetor (hook git, sub-script chamado por algum wrapper, normalize Unicode aplicado por agente paralelo). Mas as 3 reproducoes tem em comum o gatilho `--fix`. **Esta sprint trata o `corrigir_arquivo()` como última linha de defesa**: mesmo que o gatilho real venha de fora, o script ao ser invocado não pode permitir que a linha perca glyph protegido por nenhum caminho.

## Escopo (touches autorizados)

### Arquivos a modificar
- `scripts/validar-acentuacao.py` — reforco do filtro em `corrigir_arquivo()` (~30 linhas alteradas/adicionadas).

### Arquivos a criar
- `tests/unit/test_validar_acentuacao_glyphs_defense.py` — testes de regressao em camadas (~150 linhas, 5+ testes).

### Arquivos NAO a tocar
- `src/hefesto_dualsense4unix/**` — nenhum arquivo de runtime tocado nesta sprint. Os glyphs ja existentes em `status_actions.py`, `daemon_actions.py`, `mouse_actions.py`, `emulation_actions.py`, `uinput_mouse.py`, `tui/widgets/__init__.py` viram **fixtures de teste implicitas** (a sprint roda `--fix` contra eles em arvore limpa e exige diff vazio).
- `docs/adr/011-glyphs-vs-emojis.md` — ja documenta a whitelist; não alterar.
- `tests/unit/test_validar_acentuacao_glyphs.py` (ja existente, GLYPHS-02) — não alterar; o novo arquivo `_defense.py` e complementar, não substitui.
- Nenhum hook git, pre-commit config ou CI workflow nesta sprint (escopo cirurgico).

## Acceptance criteria

1. **Pre-pass por linha (defesa em profundidade)** — `corrigir_arquivo()` calcula `linha_tem_glyph_protegido = _contem_glyph_protegido(linha)` **uma vez por linha**, antes do loop de pares. Se True, **toda a linha e pulada para fix** — `subs` não e construido, nenhuma substituicao e considerada. Linha vai intacta para `novas_linhas`.
2. **Post-pass por linha (paranoia)** — Mesmo apos pre-pass + filtro existente, ao final da iteração da linha, comparar set de codepoints protegidos antes/depois da edicao. Se algum codepoint protegido sumiu, **reverter** para `linha_com_sep` original e logar warning em stderr no formato `[ADR-011 POST] {path}:{idx+1} — revertido (glyph perdido apos substituicao: {repr})`.
3. **Whitelist como conjunto módulo (acessibilidade para teste)** — Manter `UNICODE_ALLOWED_RANGES`, `is_protected_codepoint`, `_contem_glyph_protegido`. Não renomear (manter compat com `tests/unit/test_validar_acentuacao_glyphs.py` existente).
4. **Diagnostico aprimorado** — Quando pre-pass pula linha, NAO emite log (eh o caminho feliz, alta frequência, poluiria stderr). Quando post-pass reverte, SEMPRE emite warning. Quando o filtro existente camada 1 (`:694-707`) rejeita, manter mensagem atual `[ADR-011]`.
5. **Proof empirico em arvore limpa** — `git stash && git checkout HEAD -- . && python3 scripts/validar-acentuacao.py --all --fix && git status --short` retorna **vazio**. Zero diff. Este e o gate definitivo.
6. **Suite de testes nova passa**: `tests/unit/test_validar_acentuacao_glyphs_defense.py` com cobertura abaixo (criterio 7).
7. **Cobertura de testes minima**, todos passando:
   - `test_validar_acentuacao_preserva_glyph_pontuado` — linha contendo `● Online` + palavra-alvo do dicionario na mesma linha (ex: `● Conectado — verifica funcao status atual`). Sem o pre-pass, o filtro existente bloquearia a substituicao porque `linha[s:e]` da palavra-alvo nao contem glyph; com o pre-pass, a linha inteira e pulada e `funcao` permanece `funcao`. Asserta que `●` preservado E que `funcao` permanece (porque a linha esta marcada como protegida — comportamento intencional, ver "Decisao de design" abaixo).
   - `test_validar_acentuacao_preserva_glyph_em_par_malicioso` — variante explicita de `test_par_malicioso_bloqueado` (ja existente em `_glyphs.py`) usando os 5 codepoints reportados (`●○◐△□`). Garante que mesmo com `_CORRECOES[glyph] = ""` injetado, glyph sobrevive (camada 1 + pre-pass + post-pass).
   - `test_validar_acentuacao_preserva_glyph_em_docstring` — fixture `.py` com docstring contendo `"""Status: ● ativo"""` e palavra-alvo no codigo abaixo. Roda `--fix`. Glyph na docstring preservado.
   - `test_validar_acentuacao_preserva_dpad_arrows` — fixture com `D-pad (↑↓←→)` (codepoints U+2191, U+2193, U+2190, U+2192). Confirma que setas (Arrows block) sobrevivem identico ao caso BLACK CIRCLE.
   - `test_validar_acentuacao_preserva_face_buttons` — fixture com `△ ○ □ ×` (U+25B3, U+25CB, U+25A1, U+00D7). Note que `×` (U+00D7 MULTIPLICATION SIGN) **nao** esta em UNICODE_ALLOWED_RANGES; teste documenta o comportamento atual (×nao protegido) e serve como decisao explicita: se for desejado proteger `×`, sprint nova. Aqui o teste asserta que △○□ sobrevivem; `×` pode ou nao ser tocado pelo dicionario (provavelmente nao toca porque nao casa nenhum padrao).
   - `test_post_pass_reverte_se_glyph_perdido` — teste **white-box** que monkeypatcha o filtro camada 1 para fingir que falhou (ex: forca `_contem_glyph_protegido` a retornar False temporariamente apos o filtro), aplica substituicao que removeria glyph, e confirma que post-pass detectou e reverteu a linha.
   - `test_pre_pass_pula_linha_inteira` — teste branco-box: linha contendo glyph + palavra-alvo. Verifica que apos `--fix` a palavra-alvo permaneceu intacta (não foi corrigida) — comportamento intencional do pre-pass.
8. **Suite global verde**: `.venv/bin/pytest tests/unit -q` passa sem regressoes (baseline atual ~998 testes; esperado >= 1003 com 5 novos).
9. **Linters/types verdes**: `.venv/bin/ruff check scripts/ tests/unit/test_validar_acentuacao_glyphs_defense.py` e `.venv/bin/mypy scripts/validar-acentuacao.py` (se mypy ja cobre o script — verificar config; se não, sem regressao).
10. **Acentuacao do próprio fix**: novo arquivo de teste e bloco editado em `validar-acentuacao.py` passam por `python3 scripts/validar-acentuacao.py scripts/validar-acentuacao.py tests/unit/test_validar_acentuacao_glyphs_defense.py` sem violacoes.

### Decisão de design (importante registrar)

O **pre-pass** torna o comportamento mais conservador: linhas com glyph protegido NUNCA sao corrigidas, mesmo que tenham palavra-alvo de acento PT-BR legitima. Isto e aceitavel porque:

- Em codigo de runtime (`status_actions.py` etc.), linhas com `●`/`○` sao tipicamente strings de UI ja acentuadas corretamente em PT-BR (`● Conectado Via USB`, `○ Daemon Offline`).
- O custo de um falso-negativo (palavra sem acento na linha do glyph não corrigida) e infinitamente menor que o custo da regressao reportada (3 reproducoes, dezenas de arquivos corrompidos por ciclo).
- O modo `--check` (sem `--fix`) continua reportando a violacao normalmente — o usuário pode corrigir manualmente.
- Isto e explicitamente preferivel a tentativa de "corrigir e validar" (frageil, depende de ordem de operação).

## Invariantes a preservar

- **A-04 (BRIEF)** — strip de glyphs Unicode de estado e regressao critica. Sprint reforca a defesa **mas não remove** as camadas existentes (whitelist + filtro camada 1 + testes GLYPHS-02). Defesa e em camadas.
- **CORE/Acentuacao PT-BR** (BRIEF linha 92) — todo arquivo modificado pela sprint passa por varredura de acentuacao periferica.
- **CORE/Glyphs Unicode permitidos** (BRIEF linha 93) — `U+25CF`, `U+25CB`, `U+25AE/AF`, box drawing sao permitidos e devem ser preservados. Esta sprint operacionaliza a invariante.
- **L-21-2** — bug ja foi reproduzido 3x; sprint NAO precisa de mais reproducao em arvore limpa para abrir. Mas o **proof-of-work** exige o teste `git status --short` vazio em arvore limpa apos `--fix` (criterio 5).
- **L-21-3** — spec lista os trechos lidos (`scripts/validar-acentuacao.py:494-513,614-730`, `tests/unit/test_validar_acentuacao_glyphs.py:105-154`, `mouse_actions.py:24-31`, `status_actions.py:270,288,313`).
- **Protocolo anti-debito (9.7)** — se durante a execução o executor descobrir vetor de strip externo ao `corrigir_arquivo()` (hook, wrapper, agente), abrir sprint nova `BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-04` com o vetor identificado. Esta sprint trata defesa **dentro do script**.

## Plano de implementação

1. **Ler integralmente** `scripts/validar-acentuacao.py:614-730` (função `corrigir_arquivo`) e `:494-513` (whitelist). Anexar trechos no commit message.
2. **Reproduzir o bug** em arvore limpa: `git stash` + `git checkout HEAD -- .` + `python3 scripts/validar-acentuacao.py --all --fix` + `git status`. Documentar resultado (espera-se "diff vazio" mas se reproduzir agora e proof bonus).
3. **Implementar pre-pass** em `corrigir_arquivo()` apos linha 668 (`linha_busca = ...`):
   ```python
   # GLYPHS-03 pre-pass: linhas com glyph protegido nao sao corrigidas.
   # Defense-in-depth — mesmo que filtro camada 1 falhe (regex avancado,
   # pares ad-hoc, normalizacao Unicode externa), a linha sai intocada.
   if _contem_glyph_protegido(linha):
       novas_linhas.append(linha_com_sep)
       continue
   ```
4. **Implementar post-pass** apos a aplicação das substituicoes (depois de `nova = nova[:s] + r + nova[e:]` em ordem reversa, **antes** de `novas_linhas.append(nova + sep)`):
   ```python
   # GLYPHS-03 post-pass: paranoia. Se algum codepoint protegido sumiu
   # apos a substituicao, reverte a linha e loga.
   if _contem_glyph_protegido(linha) and not _contem_glyph_protegido(nova):
       perdidos = sorted({c for c in linha if is_protected_codepoint(ord(c))} - set(nova))
       print(
           f"[ADR-011 POST] {path}:{idx + 1} — revertido "
           f"(glyph(s) perdido(s) apos substituicao: {perdidos!r})",
           file=sys.stderr,
       )
       novas_linhas.append(linha_com_sep)
       total_subs -= len(aceitas)
       continue
   ```
   Observação: como o pre-pass ja pula linhas com glyph, o post-pass **so dispara** se alguem injetar glyph em par malicioso que não casava antes mas casa depois — caso teorico. Mantemos como cinto-e-suspensorio.
5. **Adicionar testes** em `tests/unit/test_validar_acentuacao_glyphs_defense.py` cobrindo todos os 7 cenarios do criterio 7. Usar mesma técnica de carregamento via `importlib.util.spec_from_file_location` ja usada em `test_validar_acentuacao_glyphs.py`.
6. **Rodar gates locais**:
   - `.venv/bin/pytest tests/unit/test_validar_acentuacao_glyphs.py tests/unit/test_validar_acentuacao_glyphs_defense.py tests/unit/test_validar_acentuacao.py -v`
   - `.venv/bin/pytest tests/unit -q`
   - `.venv/bin/ruff check scripts/ tests/unit/test_validar_acentuacao_glyphs_defense.py`
   - `python3 scripts/validar-acentuacao.py --all`
7. **Proof empirico** (criterio 5): em arvore limpa pos-commit, rodar `--all --fix` e confirmar `git status --short` vazio.
8. **Smoke USB+BT** (BRIEF contratos de runtime): script puro não toca runtime, mas sprint que tocar `scripts/` na cadeia de gates obriga smoke 2s para regredir-zero.
9. **Atualizar VALIDATOR_BRIEF.md** secao A-04 ou nova A-13 mencionando esta sprint, padrão "RESOLVIDA por GLYPHS-02 (whitelist) + GLYPHS-03 (pre/post-pass + testes em camadas)".
10. **Commit único** com mensagem `fix: BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-03 — pre/post-pass anti strip de glyphs ADR-011`.

## Aritmetica

- `scripts/validar-acentuacao.py`: atual 852L. Adicao: pre-pass (~6L) + post-pass (~12L) + comentarios (~6L) = +24L. Projetado: ~876L. **Limite 800L do BRIEF não se aplica ao script** (BRIEF linha 232: "exceto configs/registries/testes" — tratamos `scripts/` como tooling, não runtime). Sem violacao de limite.
- `tests/unit/test_validar_acentuacao_glyphs_defense.py`: novo, alvo ~150L com 7+ testes (cabecalho 20L + 7 funções de teste a ~15L cada + helpers ~25L).
- Spec sprint (este arquivo): ~250L (docs não tem limite).

Total mudanca de código runtime: 0L. Tooling: +24L em script + 150L em teste novo. Cobertura nova: 7 testes.

## Testes

- **Baseline antes do fix**: `.venv/bin/pytest tests/unit -q` esperado ~998 passed (4 skipped por hardware).
- **Apos fix**: esperado >= 1005 passed (998 + 7 novos), 0 failed, 4 skipped.
- **Smoke**: `HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=usb HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke` — espera traceback-free com `poll.tick >= 50` e `battery.change.emitted >= 1`.
- **Smoke BT**: `HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=bt HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke --bt` — idem.

## Proof-of-work esperado

```bash
# Preparacao
bash scripts/dev-setup.sh

# 1. Reproducao em arvore limpa pre-fix (registro forense)
git stash
git checkout HEAD -- .
python3 scripts/validar-acentuacao.py --all --fix
git status --short  # captura output (deve ser vazio agora; se reproduzir, anexar diff)
git checkout HEAD -- .  # limpa antes do fix
git stash pop  # restaura WIP do fix

# 2. Suites
.venv/bin/pytest tests/unit/test_validar_acentuacao_glyphs.py tests/unit/test_validar_acentuacao_glyphs_defense.py tests/unit/test_validar_acentuacao.py -v
.venv/bin/pytest tests/unit -q

# 3. Lint + types
.venv/bin/ruff check scripts/ tests/unit/test_validar_acentuacao_glyphs_defense.py
# mypy se aplicavel (verificar mypy.ini / pyproject.toml)

# 4. Acentuacao periferica nos arquivos tocados
python3 scripts/validar-acentuacao.py scripts/validar-acentuacao.py tests/unit/test_validar_acentuacao_glyphs_defense.py docs/process/sprints/BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-03.md

# 5. Proof definitivo — `--fix` em arvore limpa pos-fix nao altera nada
git status --short  # vazio
python3 scripts/validar-acentuacao.py --all --fix
git status --short  # continua vazio. Este e O GATE.

# 6. Smoke
HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=usb HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke
HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=bt  HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke --bt

# 7. Anonimato
./scripts/check_anonymity.sh

# 8. Hipotese verificada (lição L-21-4)
rg -n "is_protected_codepoint|_contem_glyph_protegido|UNICODE_ALLOWED_RANGES" scripts/validar-acentuacao.py
rg -n "_contem_glyph_protegido\(linha\)" scripts/validar-acentuacao.py  # deve aparecer 2x agora (pre-pass + post-pass)
```

## Riscos e nao-objetivos

- **Risco 1 — Falsos negativos em correcao**: linhas com glyph + palavra-alvo não terao acento corrigido. Mitigacao: documentado em "Decisão de design"; modo `--check` continua reportando; usuário corrige manual. Aceitavel.
- **Risco 2 — Vetor externo não coberto**: se o strip vem de hook/wrapper/agente fora do `corrigir_arquivo()`, esta sprint não fecha o vetor. Mitigacao: protocolo anti-debito — abrir GLYPHS-04 ao identificar vetor externo. Defesa em camadas continua melhor que falta de defesa.
- **Risco 3 — Performance**: `_contem_glyph_protegido(linha)` agora roda 1-2x por linha em `--fix`. Custo O(n) sobre numero de chars da linha. Para ~10k linhas em todo o repo, ainda < 100ms. Sem regressao perceptivel.
- **Nao-objetivo 1**: identificar gatilho real das 3 reproducoes. Continua em GLYPHS-01 (investigativa, sem prazo).
- **Nao-objetivo 2**: alterar `_PARES`/`_CORRECOES`/`WHITELIST_PATTERNS`. Fora de escopo.
- **Nao-objetivo 3**: implementar `--write`/`--verbose` (camada 2/3 de GLYPHS-02 que ainda não foram aplicadas — checar antes; se ja existem, ignorar; se não, e fora desta sprint).
- **Nao-objetivo 4**: tocar runtime de `src/hefesto_dualsense4unix/**`.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-Dualsense4Unix/VALIDATOR_BRIEF.md` — invariante "Glyphs Unicode de estado sao permitidos" (linha 93), armadilha A-04 (linhas 115-118), licao L-21-2 (`L-21-2` linhas 186-187), L-21-3 (linhas 189-190).
- Sprint precedente investigativa: `docs/process/sprints/BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01.md` — duas reproducoes documentadas (V2.1, V2.2 pos-release).
- Sprint precedente fix: `docs/process/sprints/BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-02.md` — whitelist + filtro camada 1 + dry-run + verbose. Esta sprint (03) constroi em cima.
- ADR canonico: `docs/adr/011-glyphs-vs-emojis.md`.
- Evidencia bruta da 2a reproducao: `docs/history/glyph-strip-regression-2026-04-23.diff` (711 linhas).
- Testes existentes: `tests/unit/test_validar_acentuacao_glyphs.py` (GLYPHS-02), `tests/unit/test_validar_acentuacao.py` (base).
- Memoria auto: `feedback_glyphs_vs_emojis.md` (racional ADR-011).

---

*"Três reproducoes do mesmo bug e desafio aberto a metodologia. A defesa em camadas não previne todos os gatilhos — mas garante que o ferimento não sangra."*
