# UI-MOUSE-CLEANUP-01 — Polimento da aba Mouse (remover "(fixo nesta versão)", diferenciar fundo)

**Tipo:** UI (polish).
**Wave:** V1.1 — fase 6.
**Estimativa:** XS.
**Dependências:** UI-THEME-BORDERS-PURPLE-01 (consome `.hefesto-card`).

---

**Tracking:** issue a criar.

## Pedido do usuário (2026-04-22)

> Em mouse vc foi brilhante, tá muito foda. Só tirar o fixo nessa versão, alinhar elementos e diferenciar o fundo do mapeamento.

## Decisão

1. **Remover** o parêntese `(fixo nesta versão)` da legenda do mapeamento. A versão atual **É** fixa (decisão FEAT-MOUSE-01), mas expressar isso visualmente é redundante. Se mudar no futuro, adiciona-se switch "Personalizar mapeamento".
2. Envolver o bloco do mapeamento em `Gtk.Frame` com `style_class = hefesto-card` — dá o fundo distinto (#21222c, tom abaixo do bg principal) + borda roxa sutil.
3. Alinhar os itens do mapeamento em `Gtk.Grid` 2 colunas (botão à esquerda, ação à direita). `halign` consistente.
4. Header do card: "Mapeamento (fixo)" em bold, com ícone pequeno `ButtonGlyph` do cross ao lado (visual hint que é sobre botões).

### Antes vs. depois (legenda)

**Antes:**
```
Mapeamento (fixo nesta versão):
Cross (X) ou L2 → botão esquerdo
...
```

**Depois:**
```
┌── Mapeamento ─────────────────────────────────┐
│  [Cruz] ou [L2]        →  Botão esquerdo      │
│  [Triângulo] ou [R2]   →  Botão direito       │
│  [R3]                  →  Botão do meio       │
│  [Círculo]             →  Enter               │
│  [Quadrado]            →  Esc                 │
│  [D-pad ↑↓←→]          →  Setas do teclado    │
│  Analógico esquerdo    →  Movimento           │
│  Analógico direito     →  Rolagem             │
└───────────────────────────────────────────────┘
```

Glyphs usados: `cross`, `triangle`, `l2`, `r2`, `r3`, `circle`, `square`, `dpad_up/down/left/right` via `ButtonGlyph` (FEAT-BUTTON-SVG-01).

## Critérios de aceite

- [ ] `src/hefesto/gui/main.glade` aba Mouse:
  - Bloco Mapeamento envolvido em `Gtk.Frame style_class=hefesto-card`.
  - `Gtk.Grid` 2 colunas; label esquerdo com `ButtonGlyph`, label direito com ação.
  - Header "Mapeamento" em bold (sem "fixo nesta versão").
  - Toggle `mouse_emulation_toggle` e sliders `mouse_speed_scale`, `mouse_scroll_speed_scale` ficam FORA do card (em bloco de controles).
- [ ] `src/hefesto/app/actions/mouse_actions.py`:
  - Constante `MAPPING_LEGEND` (pango markup) deprecada — substituída por widgets reais no GLADE.
  - Se preferir manter como fallback textual, atualizar string removendo "(fixo nesta versão)".
- [ ] Teste: N/A markup.
- [ ] Proof-of-work visual: screenshot aba Mouse com toggle OFF e ON; sha256.

## Arquivos tocados

- `src/hefesto/gui/main.glade`
- `src/hefesto/app/actions/mouse_actions.py` (pequeno ajuste na legenda)

## Fora de escopo

- Personalização do mapeamento (V2 — grande).
- Gesture touchpad (V2).
- Aceleração não-linear do cursor (V2).
