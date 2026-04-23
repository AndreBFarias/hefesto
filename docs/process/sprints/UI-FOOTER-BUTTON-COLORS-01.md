# UI-FOOTER-BUTTON-COLORS-01 — Cores diferenciadas nos botões do footer (tema Dracula)

**Tipo:** polish.
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:polish`, `ui`, `ai-task`, `status:ready`.

## Contexto

Usuário em 2026-04-23 após inspecionar v2.1.0:

> "os botões da footer, deveriam ter uma cor de fundo diferenciada dos demais botões. Tenta usar verde, azul, amarelo queimado, cinza (nessa ordem e com tema Drácula pra guiar na escolha)."

Footer atual tem 4 botões fixos, persistentes em todas as abas:

1. **Aplicar** (leftmost) — verde (ação positiva/commit).
2. **Salvar Perfil** — azul (ação de persistência).
3. **Importar** — amarelo queimado/âmbar (ação cautelosa — traz conteúdo externo).
4. **Restaurar Default** (rightmost) — cinza (ação de destruição suave — reset).

Paleta Dracula canônica ([draculatheme.com](https://draculatheme.com/contribute)):

- Verde: `#50fa7b` (green).
- Azul: `#8be9fd` (cyan) ou `#bd93f9` (purple) — cyan é o mais próximo de "azul" clássico Dracula.
- Amarelo queimado: `#ffb86c` (orange) é o mais próximo; `#f1fa8c` (yellow) é claro demais.
- Cinza: `#44475a` (current line / selection) — neutro, fundo do próprio tema.

Usar cores como fundo sutil (opacity ~30%) ou borda lateral colorida para não poluir, seguindo o padrão de destaque do Dracula em editores. Texto continua branco/claro.

## Decisão

Adicionar 4 classes CSS em `src/hefesto/gui/theme.css`: `.btn-apply`, `.btn-save`, `.btn-import`, `.btn-restore`. Cada uma define `background-color` levemente tingida + `border-left: 3px solid <cor-dracula>` para marcar sem dominar. Glade marca os 4 botões do footer com essas classes (via `style_class` no GtkStyleContext).

## Critérios de aceite

- [ ] `theme.css` tem 4 classes definidas com paleta Dracula documentada no próprio CSS (comentário com origem).
- [ ] `main.glade` aplica `.btn-apply` ao "Aplicar", `.btn-save` ao "Salvar Perfil", `.btn-import` ao "Importar", `.btn-restore` ao "Restaurar Default".
- [ ] Visual: nas 8 abas, footer destaca os 4 botões com cores distintas mas discretas (não fluorescente).
- [ ] Hover/pressed states respeitam a cor base (não caem no cinza neutro padrão).
- [ ] Screenshot lado-a-lado antes/depois (uma aba qualquer mostrando o footer).
- [ ] Gates canônicos.

## Arquivos tocados

- `src/hefesto/gui/theme.css`.
- `src/hefesto/gui/main.glade` (4 `style_class` adicionados).

## Proof-of-work runtime

```bash
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.app.main &
sleep 2
import -window "$(xdotool search --name 'Hefesto' | head -1)" /tmp/footer_cores.png
kill %1

.venv/bin/pytest tests/unit -q
python3 scripts/validar-acentuacao.py --all
```

## Fora de escopo

- Repaginação de outros botões da GUI.
- Mudar tema global para Dracula (já está tematizado de forma próxima — só o footer ganha destaque).
