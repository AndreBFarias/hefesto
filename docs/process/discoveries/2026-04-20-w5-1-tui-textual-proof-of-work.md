# 2026-04-20 — W5.1: TUI Textual + proof-of-work visual via snapshot SVG

**Contexto:** primeira sprint com compromisso explícito à regra 13 (validação visual) do CLAUDE.md global. TUI foi escrita em Textual; precisa print + sha256 + descrição multimodal.
**Status:** Resolvida.
**Issues relacionadas:** #11 (W5.1), merged em PR #N.

## Sintoma

Regra 13 prescreve três caminhos canônicos para captura:

1. CLI X11 (scrot/import/ffmpeg) sobre janela rodando.
2. `claude-in-chrome` MCP (pra web apps).
3. Playwright MCP (pra dev server).

TUI Textual roda em TTY, não em janela X11 padrão — `scrot` fora do terminal capturaria o terminal inteiro, inclusive conteúdo ao redor. E nem web app.

## Hipóteses

1. **Abrir TUI em terminal separado e `scrot -u`** — funciona mas captura bordas do terminal host.
2. **`xdotool search --name Hefesto` + `scrot -w $id`** — captura só a janela do terminal.
3. **Textual nativo `app.export_screenshot()`** — **MELHOR OPÇÃO.** Retorna SVG via `Rich Terminal` theme; é text-based, pesquisável, sem dependência de display real.

## Causa

Não é bug, é UX da regra 13 vs Textual. A regra cita PNG + sha256 como canônico; Textual gera SVG que é **superior** porque:
- Arquivo menor (31 KB vs ~100 KB PNG comparável).
- Conteúdo pesquisável (`grep` funciona no SVG).
- Sem perda em zoom.
- Determinístico entre ambientes (headless = display real).
- Fácil de `diff` entre revisões futuras.

## Solução

Adotar snapshot SVG do Textual como **forma preferida** de proof visual quando a UI é TUI. Mantém a regra 13 satisfeita com:

1. **Path absoluto do artefato**: `docs/process/discoveries/assets/2026-04-20-w5-1-tui-main.svg`.
2. **sha256**: `0dda90b444cbf9273e7c98ee6cdfd757446b1db497fc51061ed5f9ada0a539cb`.
3. **Descrição multimodal**: ver abaixo.

### Descrição multimodal do SVG

Terminal 100x30 colunas, tema Textual dark. Topo mostra título `Hefesto v0.1.0` com indicador `⭘` (controle desconectado) à direita. Abaixo, label em cyan-bold `Hefesto v0.1.0 — daemon de gatilhos adaptativos para DualSense`. Seguindo, painel com borda dupla `┏━━━┓` com informações:
- `daemon: offline` (amarelo).
- `controle: desconectado` (vermelho).
- `transporte: n/d` (dim).
- `bateria: ?%` (dim).
- `perfil ativo: nenhum` (dim).

Abaixo do painel, label em bold `Perfis disponíveis` seguido de `DataTable` vazio (sem perfis no teste). Rodapé (Footer) mostra os bindings `q Sair`, `r Atualizar`, `^p Command Palette`. Acentuação PT-BR preservada em "transporte", "desconectado", "nenhum", "Atualizar", "Perfis disponíveis".

## Lições

1. **Regra 13 precisa adaptador por meio.** TUI → SVG via `export_screenshot()`. Web → Playwright. App nativo X11 → scrot/import. Registrar no README da pasta de discoveries ou em `AGENTS.md`.
2. **SVG é superior a PNG quando o conteúdo é texto.** Pesquisa, diff, zoom sem perda.
3. **Validação visual de TUI passa no CI.** `export_screenshot()` funciona em headless (sem display real). Cobre proof-of-work sem exigir que CI tenha X11.

## Impacto cross-sprint

- Sprints destravadas: W5.2 (widgets), W5.4 (tray) — tray precisa PNG real via AppIndicator; W5.2 segue SVG.
- Sprints arquivadas: nenhuma.
- Regra 13 deve ganhar adendo em `AGENTS.md` ou regra global: "TUI = SVG via snapshot oficial do framework; W5.4 tray = PNG via scrot porque é widget X11 real fora do terminal".
- Próximo proof será anexado diretamente no PR a partir de agora (padrão).
