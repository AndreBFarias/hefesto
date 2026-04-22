# FEAT-BUTTON-SVG-01 — 16 SVGs originais dos botões do DualSense + widget `ButtonGlyph`

**Tipo:** feat (assets + widget).
**Wave:** V1.1 — fase 6.
**Estimativa:** 2 iterações.
**Dependências:** nenhuma (mas **é pré-requisito** de UI-STATUS-STICKS-REDESIGN-01).

---

**Tracking:** issue a criar.

## Contexto

Pedido do usuário em 2026-04-22:

> Seria muito bom mesmo se tivéssemos o svg dos botões originais do dsx. Pode pegar pra gente? Não precisa ser os originais obviamente, qualquer um seria melhor.

Como usamos tema Drácula e precisamos zero risco de IP (anonimato — AI.md v4.0 §1), desenhamos **originais minimalistas** seguindo a paleta Drácula:

- **Base (face buttons)**: `#282a36` (bg), traço em `#f8f8f2` (fg).
- **Acento quando pressionado**: `#bd93f9` (roxo Drácula).
- **Sucesso/ativo**: `#50fa7b` (verde Drácula).
- **Destaque secundário**: `#ff79c6` (pink Drácula).

Estilo: **traços limpos 2px, preenchimento plano, sem sombras nem gradientes**. Aspecto "stencil" icônico, compatível com GTK sobre fundo escuro.

## Os 16 glyphs

Organizados em `assets/glyphs/` (novo diretório). Cada SVG 32x32px viewBox, sem dependência de fontes.

### Face buttons (4)
- `cross.svg` — X em traços diagonais.
- `circle.svg` — círculo vazado 2px.
- `square.svg` — quadrado vazado 2px.
- `triangle.svg` — triângulo equilátero vazado 2px.

### D-pad (4)
- `dpad_up.svg` — seta pra cima com base trapezoidal (estilo "stem").
- `dpad_down.svg` — seta pra baixo.
- `dpad_left.svg` — seta pra esquerda.
- `dpad_right.svg` — seta pra direita.

### Triggers/bumpers (4)
- `l1.svg` — retângulo arredondado com "L1" dentro em mono font.
- `r1.svg` — idem "R1".
- `l2.svg` — retângulo arredondado mais alto + seta de curso, "L2".
- `r2.svg` — idem "R2".

### System (4)
- `touchpad.svg` — retângulo largo, bordas arredondadas, ícone de 3 pontos.
- `share.svg` — "Create" button do DualSense: um "<" indicando.
- `options.svg` — 3 linhas horizontais (≡).
- `ps.svg` — logo genérico "PS" em lettering minimalista neutro (sem logo oficial).

### Sticks (bonus, 2)
- `stick_l.svg` — círculo externo + círculo interno com "L" centrado.
- `stick_r.svg` — idem "R".

### Mic (bonus, 1)
- `mic.svg` — ícone clássico de microfone (oval + base) para FEAT-HOTKEY-MIC-01 futuro.

## Widget `ButtonGlyph`

```python
# src/hefesto/gui/widgets/button_glyph.py
from gi.repository import Gtk, GdkPixbuf

class ButtonGlyph(Gtk.DrawingArea):
    """Exibe um glyph SVG, com estado pressionado.

    Uso:
        g = ButtonGlyph("cross", size=24)
        g.set_pressed(True)  # muda cor de preenchimento pra roxo Drácula
    """
    def __init__(self, name: str, size: int = 24, tooltip_pt_br: str | None = None):
        super().__init__()
        self._name = name
        self._size = size
        self._pressed = False
        self._load_pixbuf_pair()
        self.set_size_request(size, size)
        self.connect("draw", self._on_draw)
        if tooltip_pt_br:
            self.set_tooltip_text(tooltip_pt_br)

    def set_pressed(self, pressed: bool) -> None:
        if pressed != self._pressed:
            self._pressed = pressed
            self.queue_draw()
    ...
```

Duas variantes de cada SVG:
- `assets/glyphs/<nome>.svg` — padrão (traço fg #f8f8f2).
- `assets/glyphs/<nome>_active.svg` — pressionado (preenchimento roxo #bd93f9).

`ButtonGlyph` carrega os dois via `GdkPixbuf.Pixbuf.new_from_file_at_scale` e desenha o pixbuf apropriado conforme estado.

## Critérios de aceite

- [ ] Diretório `assets/glyphs/` com 19 SVGs (16 pedidos + 2 sticks + 1 mic). Cada SVG válido (passa em `xmllint --noout`).
- [ ] `scripts/generate_glyph_active.py` (opcional): gera a versão `_active.svg` automaticamente substituindo `fill="#f8f8f2"` por `fill="#bd93f9"`.
- [ ] `src/hefesto/gui/widgets/__init__.py` já existe — adicionar `button_glyph.py` ao lado de `battery_meter.py`, `trigger_bar.py`, `stick_preview.py`.
- [ ] `src/hefesto/gui/widgets/button_glyph.py` (NOVO): classe `ButtonGlyph`.
- [ ] Mapa canônico `BUTTON_GLYPH_LABELS` em PT-BR capitalizado (consumido por UI-STATUS-STICKS-REDESIGN-01):
  ```python
  BUTTON_GLYPH_LABELS = {
      "cross": "Cruz",
      "circle": "Círculo",
      "square": "Quadrado",
      "triangle": "Triângulo",
      "dpad_up": "D-pad Cima",
      "dpad_down": "D-pad Baixo",
      "dpad_left": "D-pad Esquerda",
      "dpad_right": "D-pad Direita",
      "l1": "L1",
      "r1": "R1",
      "l2": "L2",
      "r2": "R2",
      "l3": "L3",
      "r3": "R3",
      "share": "Share",
      "options": "Options",
      "ps": "PS",
      "touchpad": "Touchpad",
      "mic": "Microfone",
  }
  ```
- [ ] Teste `tests/unit/test_button_glyph.py`:
  - (a) todos os 19 SVGs existem em `assets/glyphs/`.
  - (b) carregando `ButtonGlyph("cross")` não levanta.
  - (c) `set_pressed(True)` altera flag e dispara `queue_draw` (mock).
- [ ] `install.sh`: copiar `assets/glyphs/` para `~/.local/share/hefesto/glyphs/` (path resolvido via `find_assets_dir` padrão).
- [ ] Proof-of-work visual: desenhar os 19 glyphs em uma grade de teste (script `scripts/preview_glyphs.py` abre uma janela GTK3 mostrando todos). Screenshot + sha256.

## Arquivos tocados

- `assets/glyphs/*.svg` (19 arquivos novos)
- `scripts/generate_glyph_active.py` (novo, opcional)
- `scripts/preview_glyphs.py` (novo, só p/ proof-of-work)
- `src/hefesto/gui/widgets/button_glyph.py` (novo)
- `src/hefesto/gui/widgets/__init__.py` (+ export)
- `tests/unit/test_button_glyph.py` (novo)
- `install.sh` (+ copy `assets/glyphs/`)

## Paleta Drácula (referência canônica)

```
Background:       #282a36
Current Line:     #44475a
Foreground:       #f8f8f2
Comment:          #6272a4
Cyan:             #8be9fd
Green:            #50fa7b
Orange:           #ffb86c
Pink:             #ff79c6
Purple:           #bd93f9  ← acento principal do projeto
Red:              #ff5555
Yellow:           #f1fa8c
```

## Notas para o executor

- SVGs manuscritos. Pode usar ferramentas como `inkscape` ou escrever à mão. Importante: **zero** imagem raster, tudo vetorial.
- Evitar licenças ambíguas — **NÃO usar** Font Awesome (licensa OFL com cláusulas), Lucide (MIT OK mas tem sua identidade), Material icons (Apache 2.0 OK mas Google-branded). Desenhar original é mais limpo e mantém anonimato do projeto.
- Para o glyph `ps`, evitar qualquer traço do logo Sony — usar lettering minimalista mesmo (dois círculos pequenos com "P" e "S" centrados, por exemplo).
- Para `touchpad`, usar retângulo 2:1 com 3 pontinhos no centro — abstração universal.
- Se `inkscape` não estiver disponível no dev env, `librsvg-bin` (`rsvg-convert`) serve pra validar que o SVG renderiza.

## Fora de escopo

- Animação dos glyphs (V2).
- Versão colorida por tema (V2 — suporte a temas além do Drácula).
- Glyphs para touchpad multi-touch (V2).
