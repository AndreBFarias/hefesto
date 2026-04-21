# UX-BANNER-01 — Banner com logo + nome no canto superior esquerdo da GUI

**Tipo:** feat (UX / identidade visual).
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

## Contexto

Hoje o header da GUI do Hefesto é só texto: `Hefesto v0.1.0 daemon de gatilhos adaptativos para DualSense`. Funcional, mas anônimo visualmente. O usuário (autor) tem um projeto irmão (FogStripper — removedor de background) com um padrão estabelecido de banner: logo circular à esquerda + wordmark grande à direita, bem na parte superior da janela. Quer importar essa mesma linguagem visual para o Hefesto.

Referência visual: na GUI do FogStripper o banner tem:
- Logo circular (~60-80 px) à esquerda, posicionado colado ao topo-esquerdo.
- Nome grande "FogStripper" em bold ao lado direito do logo.
- Espaço vertical suficiente antes do conteúdo principal começar.

Hefesto já tem assets prontos em `assets/appimage/`:
- `Hefesto.png` (256x256 RGBA).
- `Hefesto.svg` (vetorial).

## Decisão

Adicionar um banner no topo de `src/hefesto/gui/main.glade`, acima da linha de abas (`GtkNotebook`). Estrutura:

```
GtkBox (horizontal, margin-top/bottom 12, margin-left 14)
  ├─ GtkImage id="app_logo" (GdkPixbuf de assets/appimage/Hefesto.png, scaled 64x64)
  └─ GtkLabel id="app_wordmark"  (markup: <span size='xx-large' weight='bold'>Hefesto</span>)
  └─ GtkLabel id="app_subtitle" (pequeno, cinza: "daemon de gatilhos adaptativos para DualSense")
```

O status global "● conectado via usb / ◐ tentando reconectar / ○ daemon offline" (UX-RECONNECT-01) continua no canto superior-direito — não colide.

## Critérios de aceite

- [ ] `src/hefesto/gui/main.glade` — novo `GtkBox` banner antes do `notebook` principal, com os 3 widgets (logo, wordmark, subtitle).
- [ ] `src/hefesto/app/app.py` (ou `main.py`) — no bootstrap, carregar `assets/appimage/Hefesto.png` via `GdkPixbuf.Pixbuf.new_from_file_at_scale()` ao tamanho alvo (64x64 ou 72x72) e aplicar ao `GtkImage` pelo id.
- [ ] Caminho do PNG resolvido via `hefesto.app.constants` (não hardcode absoluto; usa `BASE_DIR / "assets" / "appimage" / "Hefesto.png"`).
- [ ] Wordmark "Hefesto" em bold, tamanho ~xx-large, mesma fonte do tema.
- [ ] Subtitle "daemon de gatilhos adaptativos para DualSense" em cinza claro, tamanho normal.
- [ ] Versão `v0.1.0` DESAPARECE do header principal — fica escondida (pode migrar para aba Daemon ou footer, à escolha do executor).
- [ ] Status de conexão (UX-RECONNECT-01) permanece visível no canto superior direito.
- [ ] Proof-of-work visual: captura antes/depois da janela na aba Status. Descrição multimodal confirmando logo visível, wordmark legível, acentuação PT-BR correta.
- [ ] Tests unitários continuam verdes (header não tem teste direto; sanity check).
- [ ] `./scripts/check_anonymity.sh` OK.

## Arquivos tocados (previsão)

- `src/hefesto/gui/main.glade`
- `src/hefesto/app/app.py` (ou onde carrega o Builder)
- `src/hefesto/app/constants.py` (se precisar expor `LOGO_PATH`)

## Fora de escopo

- Animação ou hover no logo.
- Trocar fonte global do app.
- Redesenhar abas ou widgets internos.
- Criar novo ícone/logo — usar o Hefesto.png existente.

## Notas para o executor

- GdkPixbuf aceita SVG se build tiver librsvg — mas PNG pré-escalado é mais robusto entre ambientes.
- Margens do banner: top 10-14 px, left 14 px, bottom 6-8 px. Conservador para não empurrar o notebook muito para baixo.
- Se banner for posicionado dentro do mesmo GtkBox do status de conexão, usar `pack_start(banner, expand=False)` e `pack_end(status_label, expand=False)` para manter layout limpo.
