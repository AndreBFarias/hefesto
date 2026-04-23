# UI-PROFILES-LAYOUT-POLISH-01 — Polish de layout da aba Perfis (investigação + fix)

**Tipo:** polish (investigativa).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:polish`, `ui`, `investigation`, `ai-task`, `status:ready`.

## Sintoma

Usuário reporta em 2026-04-23 após screenshot de v2.1.0:

> "ainda tem algo estranho na aba de perfis no layout, não sei o que é, o que sugere que façamos ali?"

Screenshot disponibilizado pelo usuário mostra:

- **Coluna esquerda**: `TreeView` com header "Nome / Prio / Match" + 5 linhas (André 5 any, browser 5 criteria, fallback -1000 any, meu_perfil 0 any, shooter 10 criteria). Seleção roxa em meu_perfil.
- **Coluna direita**: "Editor do perfil" com campos Nome/Prioridade/Aplica a (radio group com 6 opções).
- **Row inferior esquerda**: botões Novo/Duplicar/Remover/Ativar/Recarregar.
- **Row inferior direita**: botão Salvar isolado.
- **Footer global**: Aplicar/Salvar Perfil/Importar/Restaurar Default.

Hipóteses de "algo estranho" (usuário não especifica — sprint é investigativa):

- **H1**: Radio group "Aplica a:" tem 6 opções mas parece desalinhado (cada radio em linha própria ocupa muito espaço vertical).
- **H2**: Botão "Salvar" à direita isolado é redundante com "Salvar Perfil" do footer — pode confundir (dois salvars? qual usar?).
- **H3**: `TreeView` à esquerda não tem scroll visível; se houver 20+ perfis, pode cortar silenciosamente.
- **H4**: Headers das colunas do `TreeView` (Nome/Prio/Match) têm cor/contraste baixo vs. linhas — `THead` sem estilo distintivo.
- **H5**: Espaço vazio grande entre "Aplica a: Jogo específico" e o rodapé — coluna direita desbalanceada vs. esquerda.
- **H6**: Slider de Prioridade mostra "0" à direita mas sem labels de mínimo/máximo.

## Decisão

Sprint em duas fases:

**Fase 1 — Investigação (dry-run, sem Edit)**: capturar 3 screenshots (aba em 1280×720, 1920×1080, e com 15 perfis fictícios em `$XDG_CONFIG_HOME`) e listar cada anomalia visual observada. Entregar `docs/process/discoveries/2026-XX-perfis-layout.md` com os achados mapeados para Hx acima + outros descobertos.

**Fase 2 — Fix cirúrgico**: implementar só as correções que o usuário aprovar após ver o documento de achados. Sprints-filhas podem nascer se algum achado for complexo demais.

## Critérios de aceite

**Fase 1:**

- [ ] 3 screenshots capturados em resoluções distintas.
- [ ] Documento de achados em `docs/process/discoveries/` listando ≥3 anomalias com fragment do Glade correspondente.
- [ ] Recomendação de fix para cada achado (sem implementar).

**Fase 2 (após aprovação):**

- [ ] Fixes aplicados em `main.glade` / `theme.css`.
- [ ] Cada achado corrigido tem screenshot "após" para comparação.
- [ ] Gates canônicos.

## Arquivos tocados

- `src/hefesto/gui/main.glade` (fase 2).
- `src/hefesto/gui/theme.css` (fase 2).
- `docs/process/discoveries/2026-XX-perfis-layout.md` (fase 1, novo).

## Proof-of-work runtime

```bash
# Fase 1 — 3 capturas
for RES in 1280x720 1920x1080 1440x900; do
  # Xvfb + export DISPLAY se necessário
  HEFESTO_FAKE=1 .venv/bin/python -m hefesto.app.main &
  sleep 2
  # Switch para aba Perfis (coordinates ou keyboard nav)
  import -window "$(xdotool search --name 'Hefesto' | head -1)" /tmp/perfis_${RES}.png
  kill %1
done

# Visualizar os 3 lado-a-lado
# Anotar achados em docs/process/discoveries/
```

## Fora de escopo

- Redesign completo da aba (escopo é polish cirúrgico, não rewrite).
- Mudar modelo de dados (`Profile` schema é stable).
