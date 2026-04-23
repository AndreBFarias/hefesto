# QUICKSTART-PROFILES-SCREENSHOT-01 — Captura da aba Perfis no quickstart

**Tipo:** docs (polish visual do onboarding).
**Wave:** V2.1 — Bloco A.
**Estimativa:** < 1 iteração.
**Dependências:** GUI funcionando com `HEFESTO_FAKE=1`.

---

**Tracking:** issue a criar. Label: `type:docs`, `P3-low`, `ai-task`, `status:ready`.

## Contexto

`docs/usage/quickstart.md` tem 6 screenshots cobrindo tela inicial, Triggers, LEDs, Rumble, Mouse, Daemon. Falta a aba **Perfis** — que é o núcleo da UX pós-v1.1 (7 presets canônicos + meu_perfil, editor simples/avançado, autoswitch por janela). Usuário novo chega na seção "6. Trocar de perfil" do quickstart e tenta ler sem referência visual.

## Decisão

Capturar 1 screenshot canônica da aba Perfis com 8 linhas visíveis, referenciar na seção existente.

### Passos do executor

```bash
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.app.main &
GUI_PID=$!
sleep 4
WID=$(xdotool search --name "Hefesto" | head -1)
[ -z "$WID" ] && { echo "janela não encontrada"; kill $GUI_PID; exit 1; }
xdotool windowactivate "$WID" && sleep 0.5

# Trocar para aba Perfis. Posição da aba é a 3ª ou 4ª no notebook superior.
# Estratégia 1: atalho de teclado se existir.
# Estratégia 2: clicar via xdotool em coordenadas do label "Perfis".
# Preferir 1 se houver; confirmar em glade qual tecla.

TS=$(date +%Y%m%dT%H%M%S)
OUT="/tmp/hefesto_gui_perfis_${TS}.png"
import -window "$WID" "$OUT"
sha256sum "$OUT"
cp "$OUT" docs/usage/assets/quickstart_07_perfis.png
kill $GUI_PID
```

## Critérios de aceite

- [ ] `docs/usage/assets/quickstart_07_perfis.png` existe, dimensões plausíveis (≥ 800×600), pelo menos 6 dos 8 perfis visíveis na treestore/listview.
- [ ] Acentuação correta visível se `PROFILE-DISPLAY-NAME-01` já foi mergeada (opcional — pode ser rodada antes/depois; se antes, aparece `Ação`, `Navegação` acentuado; se depois, aparece `acao`, `navegacao` ASCII, o que é aceitável para esta sprint).
- [ ] `docs/usage/quickstart.md` seção "6. Trocar de perfil" referencia a imagem com texto descritivo em PT-BR.
- [ ] Skill `validacao-visual` invocada: sha256 + descrição multimodal 3-5 linhas (elementos visíveis, contraste, ausência de traceback na console).
- [ ] Nenhum outro arquivo modificado — mudança cirúrgica.

## Arquivos tocados

- `docs/usage/assets/quickstart_07_perfis.png` (novo)
- `docs/usage/quickstart.md` (editar seção 6)

## Proof-of-work

- PNG absoluto + sha256 no corpo do commit.
- Antes/depois da seção do quickstart (diff deve mostrar só o `![texto](assets/...)` novo).

## Notas para o executor

- Se `xdotool search --name "Hefesto"` retornar múltiplos WIDs (tray + janela principal), pegar o de maior área via `xdotool getwindowgeometry`.
- Se a aba Perfis não renderizar (bug latente): abrir discovery `docs/process/discoveries/2026-04-23-perfis-aba-vazia.md` com sintoma, **NÃO** silenciar com screenshot falso. A skill `validacao-visual` bloquearia de qualquer forma.
- Aspecto: preferir aspect 16:10 (janela em tamanho padrão). Não redimensionar manualmente — captura o que o WM deu.

## Fora de escopo

- Refazer os 6 screenshots existentes.
- Criar GIF animado (docs-quickstart-01 já fez isso para fluxos críticos).
- Capturar telas com o editor de perfil aberto — fica para sprint futura se tiver sentido.
