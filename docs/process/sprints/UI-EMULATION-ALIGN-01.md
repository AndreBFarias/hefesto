# UI-EMULATION-ALIGN-01 — Alinhar labels e valores da aba Emulação

**Tipo:** UI (polish).
**Wave:** V1.1 — fase 6.
**Estimativa:** XS (30-45min).
**Dependências:** nenhuma.

---

**Tracking:** issue a criar.

## Pedido do usuário (2026-04-22)

> Falta alinhar os termos, Iniciais, Até escrita, dá uma repensada no layout ali.

Captura Image 8 mostra:
```
        uinput: ● Disponível
Device virtual: Microsoft X-Box 360 pad (Hefesto virtual)
    VID:PID: 045E:028E (Xbox 360)
    /dev/input/js*: /dev/input/js0, /dev/input/js1
```

Labels tentam alinhar à direita mas alinhamento é frágil (whitespace em pango). "Combo sagrado" abaixo é outro bloco solto.

## Decisão

Reestruturar com `Gtk.Grid` 2 colunas (label à direita, value à esquerda). Classe `hefesto-card` pra dar destaque.

```
+---- Device virtual ---------------------------+
|     uinput:  [● Disponível]                  |
|     Device:  Microsoft X-Box 360 pad          |
|              (Hefesto virtual)                |
|    VID:PID:  045E:028E (Xbox 360)             |
|  Gamepads:   /dev/input/js0, /dev/input/js1   |
+-----------------------------------------------+

+---- Combo sagrado (trocar perfil) ------------+
|  Próximo:  PS + D-pad Cima                    |
|  Anterior: PS + D-pad Baixo                   |
|  Buffer:   150 ms                             |
|  Passthrough em emulação: Não                 |
+-----------------------------------------------+

[Testar criação] [Atualizar] [Editar daemon.toml]
```

Labels à direita (`halign=END`), valores à esquerda (`halign=START`), espaçamento 12px entre colunas.

## Critérios de aceite

- [ ] `src/hefesto/gui/main.glade` aba Emulação:
  - Dois `Gtk.Grid` dentro de `hefesto-card`.
  - Labels com `halign=end`, valores `halign=start`.
  - Remover espaços manuais (`    `) nos labels — usar `halign` + padding do grid.
  - "Combo sagrado" passa a mostrar "D-pad Cima" / "D-pad Baixo" (PT-BR capitalizado) em vez de `dpad_up`/`dpad_down`.
- [ ] `src/hefesto/app/actions/emulation_actions.py`: mapeamento `BUTTON_GLYPH_LABELS` (da spec FEAT-BUTTON-SVG-01) para traduzir nomes técnicos. Se spec FEAT-BUTTON-SVG-01 ainda não entregue, hardcode aqui (ok, não é débito).
- [ ] Teste: N/A markup.
- [ ] Proof-of-work visual: screenshot aba Emulação antes/depois, sha256 de cada.

## Arquivos tocados

- `src/hefesto/gui/main.glade`
- `src/hefesto/app/actions/emulation_actions.py` (pequeno ajuste de labels)

## Notas para o executor

- Botões de ação ("Testar criação de device virtual", "Atualizar", "Editar daemon.toml") ficam em `Gtk.Box` horizontal no fundo da aba, com `spacing=6`.
- Se algum label for >40 chars, `Gtk.Label.set_line_wrap(True)` + `set_width_chars(40)`.
