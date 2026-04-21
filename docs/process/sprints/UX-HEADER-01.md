# UX-HEADER-01 — Restaurar glyphs Unicode de estado e acertar docs

**Tipo:** fix (regressão visual) + docs.
**Wave:** fora de wave (limpeza do diff working-tree 2026-04-21).
**Estimativa:** 1 iteração de executor.
**Dependências:** nenhuma (pode rodar em paralelo com BUG-IPC-01 e BUG-UDP-01).

---

## Contexto

O working tree em 2026-04-21 (pós-merge PR #67) tem 7 arquivos com diff não-commitado que interpretou "zero emojis" como "zero caracteres não-ASCII", strippando glyphs Unicode de estado funcionais. Consequências:

- Indicadores BLACK CIRCLE (U+25CF) e WHITE CIRCLE (U+25CB) sumiram dos markups Pango de três `*_actions.py`. O header da GUI perdeu o ponto de âncora visual; agora mostra apenas texto colorido sem o disco sólido/oco que sinaliza "vivo/morto".
- `BatteryMeter._icon_for_level` em `src/hefesto/tui/widgets/__init__.py` passou a retornar **string vazia em todos os níveis** (antes: sequências de BLACK VERTICAL RECTANGLE U+25AE e WHITE VERTICAL RECTANGLE U+25AF). A barra de bateria textual da TUI Textual sumiu.
- O teste correspondente em `tests/unit/test_tui_widgets.py` foi **adaptado para a regressão** (`assert == ""`), violando meta-regras 9.2 (filtros sem falso-positivo) e 9.6 (evidência empírica antes de fix). Teste deveria ter falhado para sinalizar o bug; em vez disso foi rebaixado silenciosamente.
- Docs `HEFESTO_PROJECT.md` e `HEFESTO_DECISIONS_V2.md` trocaram HEAVY CHECK MARK (U+2705) e CROSS MARK (U+274C — esses sim são Emoji_Presentation e o hook `guardian.py` bloqueia) por **espaço em branco**, deixando linhas tipo `-  logger.error(...)` com hífen sem sinal algum.

Ver `VALIDATOR_BRIEF.md` armadilha A-04 e memória `feedback_glyphs_vs_emojis.md`.

---

## Regra canônica (a aplicar e documentar)

**Zero emojis** mira o bloco Emoji_Presentation do Unicode (coloridos, gráficos). **Glyphs de estado** são preservados: BLACK/WHITE CIRCLE (U+25CF/U+25CB), BLACK/WHITE VERTICAL RECTANGLE (U+25AE/U+25AF), BLACK DIAMOND (U+25C6), setas U+2190–U+21FF, box drawing U+2500–U+257F. A diferença é semântica: emoji é decoração colorida opcional; glyph de estado é parte da UI textual funcional.

Para HEAVY CHECK MARK e CROSS MARK nas docs (emojis reais pelo hook): substituir por texto **"OK"** (onde era check) e **"ERRADO"** (onde era cross). Preserva o sinal semântico sem violar a regra.

---

## Critérios de aceite

- [ ] `src/hefesto/app/actions/status_actions.py` — restaurar BLACK CIRCLE e WHITE CIRCLE nos markups `_render_offline()` e `_render_online()` do `header_connection`. Versão canônica esperada:
  - `daemon offline` → prefixo WHITE CIRCLE vermelho.
  - `controle desconectado` → prefixo WHITE CIRCLE vermelho.
  - `conectado via {transport}` → prefixo BLACK CIRCLE verde (`#2d8`).
- [ ] `src/hefesto/app/actions/daemon_actions.py` — restaurar BLACK CIRCLE no markup `f'<span foreground="{color}">[BLACK_CIRCLE] {active}</span> ...'` (substituindo `[BLACK_CIRCLE]` pelo caractere U+25CF literal).
- [ ] `src/hefesto/app/actions/emulation_actions.py` — restaurar BLACK CIRCLE no markup `'<span foreground="#2d8">[BLACK_CIRCLE] disponível</span>'`.
- [ ] `src/hefesto/tui/widgets/__init__.py` — restaurar `BatteryMeter._icon_for_level` aos valores originais (sequências de 4 glyphs, com U+25AE BLACK VERTICAL RECTANGLE para "cheio" e U+25AF WHITE VERTICAL RECTANGLE para "vazio"):
  - `value >= 80` → 4 BLACK
  - `value >= 60` → 3 BLACK + 1 WHITE
  - `value >= 40` → 2 BLACK + 2 WHITE
  - `value >= 20` → 1 BLACK + 3 WHITE
  - `else` → 4 WHITE
- [ ] `tests/unit/test_tui_widgets.py` — reverter asserts para os valores Unicode originais (os 5 casos do método `test_icon_bateria_varia_com_nivel`).
- [ ] `docs/process/HEFESTO_PROJECT.md` seção "NAO FACA" — já está aceitável com hífen simples; manter os 8 itens como `- ...` sem reintroduzir CROSS MARK. O cabeçalho "NAO FACA" já dá o contexto semântico.
- [ ] `docs/process/HEFESTO_DECISIONS_V2.md` seção 2 (idioma) — substituir os 4 marcadores-perdidos por texto: cada linha que era `HEAVY_CHECK_MARK logger.error(...)` vira `OK: logger.error(...)` e cada linha que era `CROSS_MARK logger.error(...)` vira `ERRADO: logger.error(...)`. Preserva sinal sem usar emoji.
- [ ] `scripts/check_anonymity.sh` — confirmar que NÃO bloqueia os glyphs de estado (U+25CF, U+25CB, U+25AE, U+25AF). Se bloquear, abrir sprint-nova `HOOK-GLYPHS-01` (meta-regra 9.7) e não mudar os arquivos-alvo.
- [ ] Proof-of-work visual: captura da GUI ANTES (baseline do diff atual, tirada pré-fix) e DEPOIS do fix, na aba Status, demonstrando que o indicador BLACK/WHITE CIRCLE voltou no header. Ambos os PNGs com sha256sum.
- [ ] Unit tests: todos verdes (`289 passing` agora; com revert do test deve seguir 289).
- [ ] `./scripts/check_anonymity.sh` verde.

---

## Proof-of-work esperado

```bash
# 1. Antes: captura com diff atual (pré-sprint)
.venv/bin/python -m hefesto.app.main &
sleep 3
WID=$(xdotool search --name "Hefesto v" | head -1)
TS=$(date +%Y%m%dT%H%M%S)
xdotool windowactivate "$WID" && sleep 0.4
import -window "$WID" "/tmp/hefesto_ux_header_antes_${TS}.png"
sha256sum "/tmp/hefesto_ux_header_antes_${TS}.png"
pkill -f hefesto.app.main
sleep 1

# 2. Aplicar fix (Edit nos 5 arquivos src/tests + 2 docs).

# 3. Depois: captura
.venv/bin/python -m hefesto.app.main &
sleep 3
WID=$(xdotool search --name "Hefesto v" | head -1)
TS=$(date +%Y%m%dT%H%M%S)
xdotool windowactivate "$WID" && sleep 0.4
import -window "$WID" "/tmp/hefesto_ux_header_depois_${TS}.png"
sha256sum "/tmp/hefesto_ux_header_depois_${TS}.png"
pkill -f hefesto.app.main

# 4. Verificação textual (sem citar o caractere literal para não invocar o hook)
python3 -c "
from pathlib import Path
for f in ['src/hefesto/app/actions/status_actions.py',
         'src/hefesto/app/actions/daemon_actions.py',
         'src/hefesto/app/actions/emulation_actions.py']:
    txt = Path(f).read_text()
    n_black = txt.count(chr(0x25CF))
    n_white = txt.count(chr(0x25CB))
    print(f, 'BLACK_CIRCLE=', n_black, 'WHITE_CIRCLE=', n_white)
# esperado: status_actions tem 1 BLACK + 2 WHITE; daemon_actions tem 1 BLACK;
# emulation_actions tem 1 BLACK.
"
python3 -c "
from pathlib import Path
f = 'src/hefesto/tui/widgets/__init__.py'
txt = Path(f).read_text()
print(f, 'BLACK_VERTICAL_RECTANGLE=', txt.count(chr(0x25AE)),
        'WHITE_VERTICAL_RECTANGLE=', txt.count(chr(0x25AF)))
# esperado: 10 BLACK + 10 WHITE (4+3+2+1=10 black; 1+2+3+4=10 white).
"

# 5. Suíte
.venv/bin/pytest tests/unit -v --no-header -q
./scripts/check_anonymity.sh
.venv/bin/ruff check src/ tests/
```

**Aritmética esperada:**
- BLACK CIRCLE em `app/actions/`: pelo menos 3 ocorrências (status, daemon, emulation).
- BLACK VERTICAL RECTANGLE em `tui/widgets/__init__.py`: exatamente 10 ocorrências (soma dos níveis 4+3+2+1).
- WHITE VERTICAL RECTANGLE em `tui/widgets/__init__.py`: exatamente 10 ocorrências (1+2+3+4).
- Antes do fix: GUI mostra "daemon offline" sem indicador. Depois: mostra indicador BLACK CIRCLE ou WHITE CIRCLE conforme estado.
- Testes: 289 passing (sem novo; só reverter).

---

## Arquivos tocados (previsão)

- `src/hefesto/app/actions/status_actions.py`
- `src/hefesto/app/actions/daemon_actions.py`
- `src/hefesto/app/actions/emulation_actions.py`
- `src/hefesto/tui/widgets/__init__.py`
- `tests/unit/test_tui_widgets.py`
- `docs/process/HEFESTO_DECISIONS_V2.md`

---

## Fora de escopo

- Redesenhar o header da GUI.
- Trocar o `BatteryMeter` por SVG ou GtkProgressBar (mantém textual).
- Adicionar novos glyphs não existentes no repo.

---

## Notas para o executor

- Se o hook `guardian.py` reclamar de algum desses caracteres de estado (U+25CF, U+25CB, U+25AE, U+25AF) durante Write/Edit, é falso-positivo do hook. Consultar `~/.claude/hooks/guardian.py` e ajustar a regex para excluir esses codepoints. Se ajuste do hook ficar fora do escopo da sprint, abrir sprint-nova `HOOK-GLYPHS-01` (meta-regra 9.7).
- O fix em src/tests é reverter o diff atual — usar `git diff HEAD -- <arquivo>` para ver o delta exato a desfazer e aplicar Edit correspondente.
- Nas docs, o fix é escolha deliberada (troca textual). NÃO reintroduzir HEAVY CHECK MARK ou CROSS MARK — usar "OK:"/"ERRADO:" ou traço simples.
