# Descoberta GUI Fase 5: aba Perfis

Data: 2026-04-21
Escopo: HEFESTO-GUI fase 5 — aba Perfis (lista + editor de matcher)

## Contexto

Fase 5 da migração TUI→GTK3. A aba Perfis precisa exibir a lista de perfis
em disco (`~/.config/hefesto/profiles/*.json`) e um editor de matcher
(MatchCriteria/MatchAny + priority).

## Achado principal

**GtkPaned no GTK3 via Glade bloqueia o desenho de filhos complexos**
quando combinado com `GtkNotebook` + `GtkScrolledWindow` + `GtkTreeView`.

- Sintoma: `Gtk.Builder.add_from_file` carrega sem erro; widgets retornam
  `get_visible() == True` e allocations > 0; `tree.get_columns()` exibe
  `width` plausível; mas no `import -window` o conteúdo da TreeView da
  metade esquerda do Paned não é pintado — coluna `Nome`, label
  `Perfis salvos` e botões `Novo`/`Duplicar` ficam ausentes.
- Diagnóstico: TreeView isolada (mesmo código, janela sem Paned) renderiza
  corretamente. A falha é específica à combinação Paned ↔ Notebook ↔
  ScrolledWindow dentro do Glade.
- Correção: substituir `GtkPaned` por `GtkBox` horizontal com
  `expand=False` no lado esquerdo + `expand=True` no direito. Tudo
  renderiza como esperado.

## Regra N-para-N derivada

Adicionar ao arsenal do projeto: **evitar `GtkPaned` em abas de Notebook
via Glade**. Usar `GtkBox` horizontal com `width-request` no lado fixo.

## Segfaults colaterais (resolvidos antes)

1. `GtkComboBoxText` com `<items><item .../></items>` inline em Glade GTK3
   3.24 segfaulta `add_from_file`. Popular via
   `combo.append(id, text)` no `install_*`.
2. `<child internal-child="selection"><signal .../></child>` em
   `GtkTreeView` também segfaulta em alguns temas. Conectar o signal
   `changed` da selection programaticamente.
3. `<object class="GtkListStore"><columns>...</columns></object>`
   top-level com `GtkTreeViewColumn` + `<attributes>` inline também
   causou regressão intermitente. Criar store + colunas direto em Python
   (`Gtk.ListStore(GObject.TYPE_STRING, ...)` + `append_column`).

## Prova visual

`docs/process/discoveries/assets/2026-04-21-gui-fase5-profiles.png`
(janela Hefesto v0.1.0, aba Perfis selecionada, 3 perfis na lista,
editor à direita).

---

*"Regra de ouro do layout GTK3: o componente mais complexo sempre revela
o bug latente do componente parent."*
