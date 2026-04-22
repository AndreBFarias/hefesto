# UI-DAEMON-LOG-WRAP-01 — Log do daemon em card destacado, com wrap e sem scroll horizontal

**Tipo:** UI.
**Wave:** V1.1 — fase 6.
**Estimativa:** XS (30min).
**Dependências:** UI-THEME-BORDERS-PURPLE-01 (consome `.hefesto-log` e `.hefesto-card`).

---

**Tracking:** issue a criar.

## Pedido do usuário (2026-04-22)

> em daemon, a área do Log saída do systemctl, precisa ser destacada do fundo normal, e ele não pode permitir rolagem pra direita, deveria dar quebra de linha e respeitar o bloco.

## Decisão

1. Envolver o `Gtk.TextView` do log em `Gtk.ScrolledWindow` com `hscrollbar_policy=NEVER, vscrollbar_policy=AUTOMATIC`.
2. Definir `set_wrap_mode(Gtk.WrapMode.WORD_CHAR)` no TextView.
3. Adicionar classes CSS `hefesto-card` no container pai e `hefesto-log` no TextView (UI-THEME-BORDERS-PURPLE-01 já define o estilo).
4. Font monospaced menor (11px via CSS) e fundo `#21222c` (2 tons abaixo do Drácula bg, pra destacar).

## Critérios de aceite

- [ ] `src/hefesto/gui/main.glade`:
  - `daemon_status_text` (TextView) fica dentro de `Gtk.ScrolledWindow` com `hscrollbar-policy = never`.
  - `wrap-mode = word-char`.
  - Container pai recebe `style_class = hefesto-card`.
  - TextView recebe `style_class = hefesto-log`.
- [ ] Teste: N/A (é só markup).
- [ ] Proof-of-work visual: rodar `systemctl --user status hefesto.service` com output longo, clicar "Ver Logs" na GUI, confirmar que:
  - Fundo é `#21222c` (destacado do fundo principal).
  - Borda roxa sutil.
  - Linhas longas quebram ao invés de gerar barra horizontal.
  - Scroll vertical funciona pra logs longos.
  - Screenshot + sha256.

## Arquivos tocados

- `src/hefesto/gui/main.glade` (só o bloco do log)

## Notas para o executor

- Se o `ScrolledWindow` já existe (em versões anteriores do glade), só trocar as policies e adicionar as classes.
- `wrap-mode="word-char"` quebra no espaço quando possível, no caractere quando não há espaço (URLs longas, tracebacks).
- Se systemctl devolve output com caracteres ANSI de cor, `TextView` mostra como literais (`\033[...`). Opcionalmente filtrar via `re.sub(r'\\x1b\\[[0-9;]*m', '', text)` antes de `buf.set_text`. **Faz** (é feio senão).
