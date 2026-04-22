# UI-STATUS-STICKS-REDESIGN-01 — Redesign do bloco Sticks + Botões da aba Status

**Tipo:** UI/UX.
**Wave:** V1.1 — fase 6.
**Estimativa:** 1 iteração.
**Dependências:** FEAT-BUTTON-SVG-01 (glyphs + widget `ButtonGlyph`).

---

**Tracking:** issue a criar.

## Sintoma (reportado em 2026-04-22)

> A área de sticks e botões tá estranha. Tem que aparecer O nome do botão em Português e com primeira Letra maiúscula. Fora isso, seria muito bom mesmo se tivéssemos o svg dos botões originais do dsx (...) Aí só teria que melhorar a distribuição dos elementos do bloco.

Hoje (captura Image 3):
- "Botões pressionados: Nenhum" em itálico inglês-like.
- Sticks listados como `LX 128 / LY 123 / RX 128 / RY 127` em texto mono.
- Nenhum visual dos botões reais do controle.

## Decisão

Reestruturar `Sticks e botões` em **2 colunas** dentro de um `Gtk.Grid`:

### Coluna esquerda — Sticks (vertical)
- Duas "cápsulas" retangulares empilhadas, cada uma com título + `StickPreview` widget.
- Título: "Analógico Esquerdo (L3)" e "Analógico Direito (R3)".
- `StickPreview` já existe em `src/hefesto/gui/widgets/__init__.py` — reutilizar. Mostra um círculo com ponto que se move proporcionalmente ao stick.
- Abaixo de cada stick: valores numéricos em mono pequeno `X: 128  Y: 123`.

### Coluna direita — Botões pressionados (grid visual)
Grid 4 colunas × 4 linhas de `ButtonGlyph` (widget de FEAT-BUTTON-SVG-01):

```
[Cruz]  [Círculo]   [Quadrado]  [Triângulo]
[↑]     [↓]         [←]         [→]
[L1]    [R1]        [L2]        [R2]
[Share] [Options]   [PS]        [Touchpad]
```

Cada `ButtonGlyph` tem `tooltip_pt_br` (ex.: "Cruz — usado para pular/confirmar"). Quando o botão físico é pressionado, `set_pressed(True)` ilumina em roxo Drácula.

Layout resultante: bem mais compacto e informativo que a lista textual. O usuário vê os botões como eles são no controle, com feedback visual ao vivo.

## Contrato

Em `status_actions.py`, handler do evento de `ControllerState` recebe o `buttons_pressed: frozenset[str]` e faz:

```python
for name, glyph in self._button_glyphs.items():
    glyph.set_pressed(name in state.buttons_pressed)
```

Mapeamento `state.buttons_pressed → glyph_name`:
- `cross` → `cross`
- `circle` → `circle`
- `square` → `square`
- `triangle` → `triangle`
- `dpad_up` → `dpad_up` (e assim por diante)
- `l1` → `l1`
- `r1` → `r1`
- `l3` (stick esquerdo click) → sobrescreve cor do título "Analógico Esquerdo (L3)"
- `r3` → idem "Analógico Direito (R3)"
- `share`/`create` → `share`
- `options` → `options`
- `ps` → `ps`
- `touchpad` → `touchpad`

L2 e R2 são gatilhos analógicos — iluminam se `state.l2_raw > 30` / `state.r2_raw > 30` (threshold).

## Critérios de aceite

- [ ] `src/hefesto/gui/main.glade`: aba Status reconstruída no bloco "Sticks e botões" — `Gtk.Grid` 2 colunas.
- [ ] `src/hefesto/app/actions/status_actions.py`:
  - `install_status_polling` inicializa `self._button_glyphs = {name: ButtonGlyph(name, 28, tooltip=BUTTON_GLYPH_LABELS[name]) for name in ALL_BUTTONS}`.
  - `_on_state_update` atualiza glyphs conforme `state.buttons_pressed` + L2/R2 raw.
  - Atualiza títulos dos sticks: se `l3` pressionado, título fica em roxo Drácula; mesmo p/ R3.
- [ ] Grid de glyphs: 16 entradas total (4×4).
- [ ] `StickPreview` reutilizado (não mudar implementação; só apresentar maior — `request_size(120, 120)`).
- [ ] Remover do GLADE os labels antigos `LX`, `LY`, `RX`, `RY`, `Botões pressionados: Nenhum`.
- [ ] Teste `tests/unit/test_status_buttons_glyphs.py`: monkeypatch `ButtonGlyph.set_pressed`; envia `ControllerState(buttons_pressed=frozenset({"cross", "dpad_up"}))`; valida que `cross` e `dpad_up` receberam `set_pressed(True)`, outros `set_pressed(False)`.
- [ ] Proof-of-work visual: screenshot da aba Status com controle conectado e botões pressionados (algum pressionado aceso roxo).

## Arquivos tocados

- `src/hefesto/gui/main.glade`
- `src/hefesto/app/actions/status_actions.py`
- `tests/unit/test_status_buttons_glyphs.py` (novo)

## Notas para o executor

- Ao reconstruir o GLADE, preservar `id` dos widgets que outros mixins consomem (ex.: barras L2/R2 em `Gatilhos (ao vivo)` continuam como estão).
- Evitar gastar tempo em animações de transição — `set_pressed(True)` deve ser instantâneo (queue_draw imediato).
- Tooltip em cada glyph usa `BUTTON_GLYPH_LABELS[name]` da spec FEAT-BUTTON-SVG-01. Exemplo: "Touchpad — clique para trocar de perfil (PS+dpad_up)".
- Performance: o poll loop update event vem a 10Hz (`LIVE_POLL_INTERVAL_MS = 100`). Diff contra estado anterior para evitar queue_draw desnecessário:
  ```python
  if self._last_buttons != state.buttons_pressed:
      self._refresh_glyphs(state.buttons_pressed)
      self._last_buttons = frozenset(state.buttons_pressed)
  ```

## Fora de escopo

- Ícone animado quando botão é mantido (V2).
- Representação de pressão do touchpad (V2).
- Overlay de drift calibration (V2).
