# UI-THEME-BORDERS-PURPLE-01 — CSS GTK global: tema Drácula + bordas roxas nos interativos

**Tipo:** UI (tema).
**Wave:** V1.1 — fase 6.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma (acelera UI-MOUSE-CLEANUP-01 e UI-DAEMON-LOG-WRAP-01 por fornecer o CSS base).

---

**Tracking:** issue a criar.

## Pedido do usuário (2026-04-22)

> destacar melhor as bordas dos botões e listas suspensas saindo do preto pro roxo (somente a borda)

## Contexto

A GUI GTK3 herda o tema do sistema (Pop!_OS default = Pop dark). Botões/dropdowns ficam com bordas quase invisíveis sobre fundo escuro. Queremos CSS próprio que deixe o Hefesto consistente com paleta Drácula em qualquer distro.

Estilo:
- **Fundo**: `#282a36` (Drácula bg).
- **Texto**: `#f8f8f2`.
- **Bordas de widgets interativos** (`GtkButton`, `GtkComboBox`, `GtkEntry`, `GtkScale`, `GtkSwitch`): 1px sólida `#bd93f9` (roxo Drácula). Sem preenchimento extra.
- **Hover**: borda 2px `#ff79c6` (pink) + sem fundo.
- **Active/pressed**: preenchimento leve `rgba(189, 147, 249, 0.15)`.
- **Focus ring**: `#8be9fd` (cyan) 2px solid.
- **Abas (GtkNotebook)**: underline 2px `#bd93f9` na aba ativa.
- **TextView / log areas (UI-DAEMON-LOG-WRAP-01)**: fundo `#44475a` (Drácula current-line) com borda 1px roxa.

## Decisão

Criar `src/hefesto/gui/theme.css` com o CSS + injetar via `Gtk.CssProvider` com prioridade `GTK_STYLE_PROVIDER_PRIORITY_APPLICATION` no `HefestoApp.__init__`. Scoping: só afeta a janela do Hefesto, não vaza pro resto do sistema.

### Snippet canônico (`theme.css`)

```css
/* Drácula palette aplicada ao Hefesto */
.hefesto-window {
    background-color: #282a36;
    color: #f8f8f2;
}

.hefesto-window button {
    background-color: transparent;
    border: 1px solid #bd93f9;
    border-radius: 4px;
    color: #f8f8f2;
    padding: 6px 12px;
}
.hefesto-window button:hover {
    border: 2px solid #ff79c6;
    padding: 5px 11px; /* compensa o 1px a mais */
}
.hefesto-window button:active {
    background-color: rgba(189, 147, 249, 0.15);
    border-color: #bd93f9;
}
.hefesto-window button:disabled {
    border-color: #44475a;
    color: #6272a4;
}

.hefesto-window combobox,
.hefesto-window entry,
.hefesto-window spinbutton {
    background-color: #282a36;
    border: 1px solid #bd93f9;
    border-radius: 4px;
    color: #f8f8f2;
    padding: 4px 8px;
}

.hefesto-window combobox:focus,
.hefesto-window entry:focus {
    border: 2px solid #8be9fd;
    padding: 3px 7px;
}

.hefesto-window scale trough {
    background-color: #44475a;
    border: 1px solid #6272a4;
    border-radius: 4px;
}
.hefesto-window scale slider {
    background-color: #bd93f9;
    border: 1px solid #bd93f9;
    border-radius: 50%;
}

.hefesto-window notebook > header > tabs > tab {
    background: transparent;
    border: none;
    color: #6272a4;
    padding: 8px 14px;
}
.hefesto-window notebook > header > tabs > tab:checked {
    color: #f8f8f2;
    border-bottom: 2px solid #bd93f9;
}

/* Cards internos (ex.: log systemctl, mapeamento mouse) */
.hefesto-card {
    background-color: #21222c;
    border: 1px solid #44475a;
    border-radius: 6px;
    padding: 12px;
}

.hefesto-log textview {
    background-color: #21222c;
    color: #f8f8f2;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
}

.hefesto-status-ok     { color: #50fa7b; }
.hefesto-status-warn   { color: #f1fa8c; }
.hefesto-status-err    { color: #ff5555; }
.hefesto-accent-purple { color: #bd93f9; }
.hefesto-accent-pink   { color: #ff79c6; }
```

### Injeção

```python
# src/hefesto/app/theme.py
from gi.repository import Gdk, Gtk
from hefesto.app.constants import PACKAGE_ASSETS_DIR
from pathlib import Path

def apply_theme(window: Gtk.Window) -> None:
    css_path = PACKAGE_ASSETS_DIR / "theme.css"
    provider = Gtk.CssProvider()
    provider.load_from_path(str(css_path))
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    # Adiciona a classe .hefesto-window à janela principal
    window.get_style_context().add_class("hefesto-window")
```

Chamado em `HefestoApp.__init__` após `self.window = builder.get_object("main_window")`.

## Critérios de aceite

- [ ] `src/hefesto/gui/theme.css` (NOVO): CSS acima.
- [ ] `src/hefesto/app/theme.py` (NOVO): função `apply_theme(window)`.
- [ ] `src/hefesto/app/app.py` importa `apply_theme` e chama após inicializar a janela.
- [ ] `src/hefesto/gui/main.glade`: adicionar `style_class` `hefesto-card` nos containers que agrupam:
  - Bloco "Estado" da aba Status.
  - Bloco "Gatilhos (ao vivo)".
  - Bloco "Sticks e botões".
  - Bloco de mapeamento na aba Mouse (prepara UI-MOUSE-CLEANUP-01).
  - Área de log na aba Daemon (prepara UI-DAEMON-LOG-WRAP-01).
- [ ] `install.sh`: copiar `src/hefesto/gui/theme.css` junto com `main.glade` (já é embutido via `importlib.resources` ou `PACKAGE_ASSETS_DIR`).
- [ ] Teste `tests/unit/test_theme_css.py`: (a) arquivo `theme.css` existe; (b) `Gtk.CssProvider().load_from_path` não levanta em ambiente headless (se GTK disponível); (c) regex do CSS encontra `.hefesto-window` e `#bd93f9`.
- [ ] Proof-of-work visual:
  - Screenshot da janela em cada aba após aplicar o tema.
  - Hover sobre um botão → borda fica pink 2px.
  - Foco em combo → borda cyan.
  - Sha256 de cada captura.

## Arquivos tocados

- `src/hefesto/gui/theme.css` (novo)
- `src/hefesto/app/theme.py` (novo)
- `src/hefesto/app/app.py`
- `src/hefesto/gui/main.glade` (+ style_class em contêineres)
- `install.sh` (+ copy theme.css se sair do pacote Python)
- `tests/unit/test_theme_css.py` (novo)

## Notas para o executor

- `Gtk.CssProvider().load_from_path` pode levantar `GLib.Error` se o CSS tem erro de sintaxe — o CSS acima foi validado conceitualmente mas pequenas inconsistências podem ocorrer. Testar localmente com `lint-css` se disponível.
- `PACKAGE_ASSETS_DIR` pode ser `src/hefesto/gui/` (mesmo do `main.glade`). Ajustar import.
- Para o GTK pegar o CSS do nosso tema e ignorar o do sistema **nos widgets que marcarmos**, a classe `hefesto-window` deve existir no selector de TODOS os widgets filhos. GTK3 não tem scoping real como Shadow DOM; a solução é prefixar todos os seletores com `.hefesto-window`. **Fazer isso** — ver CSS acima.
- Font family "JetBrains Mono" é preferência; se o sistema não tem, GTK cai pro fallback `monospace`. Aceita sem ruído.
- Se o usuário instalar tema GTK muito agressivo (ex.: Whisker), nosso CSS ainda prevalece porque `STYLE_PROVIDER_PRIORITY_APPLICATION` é superior a `PRIORITY_USER` e `PRIORITY_THEME`. Documentar.

## Fora de escopo

- Tema claro (V2).
- Toggle runtime tema (V2).
- Tradução pro COSMIC theming nativo (V2 — FEAT-COSMIC-WAYLAND-01).
