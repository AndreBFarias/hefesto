# UI-PROFILES-RIGHT-PANEL-REBALANCE-01 — Redistribuir espaço vazio da coluna direita

**Tipo:** polish / UX.
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** `UI-PROFILES-LAYOUT-POLISH-01` (MERGED).
**Origem:** achado H5 em `docs/process/discoveries/2026-04-23-perfis-layout.md`.

---

**Tracking:** label `type:polish`, `ui`, `ai-task`, `status:ready`.

## Sintoma

Na aba Perfis, a coluna direita (Editor do perfil) tem ~200-250px de espaço vazio entre o último campo/radio e o botão "Salvar" no rodapé. Visível tanto em modo simples quanto avançado — mais grave em simples. Screenshot de referência: `/tmp/hefesto_perfis_simples_20260423T174245.png`.

Coluna esquerda (lista de perfis) ocupa toda altura útil com o `GtkScrolledWindow`. Coluna direita fica "flutuando no topo" e desbalanceia o layout.

## Decisão

Adicionar um **preview ao vivo** do Profile resultante (JSON pretty-printed) abaixo do editor. Ideias complementares:

1. `GtkFrame class="hefesto-card"` com `GtkLabel wrap=True` mostrando o JSON atualizado a cada change signal dos inputs.
2. Ou, menos invasivo: `GtkExpander label="Preview JSON"` colapsado por default.
3. Ou, terceira opção: listar os 3 últimos perfis ativados (mini-histórico).

Preferência inicial: preview JSON expandido (item 1) — diagnóstico útil ao usuário avançado.

## Critérios de aceite

- [ ] Preview aparece abaixo do `profile_editor_stack` e acima do rodapé Salvar.
- [ ] Preview atualiza em tempo real quando qualquer campo muda (nome, prioridade, radios, entries avançadas).
- [ ] `_build_profile_from_editor` é reutilizado no handler de preview (fonte única da verdade).
- [ ] Se `_build_profile_from_editor` lançar `ValidationError`, preview mostra `"<perfil inválido: <msg>>"` em vez de crashar.
- [ ] Teste unitário: `test_profile_preview_updates_on_name_change` em `tests/unit/test_profiles_gui_sync.py`.
- [ ] Screenshot antes/depois mostrando rebalanceamento.
- [ ] Gates canônicos.

## Arquivos tocados

- `src/hefesto/gui/main.glade` — novo `GtkFrame` + `GtkLabel` para preview.
- `src/hefesto/gui/theme.css` — class `.hefesto-profile-preview` com fonte monoespaçada.
- `src/hefesto/app/actions/profiles_actions.py` — `_refresh_preview()` e wiring.
- `tests/unit/test_profiles_gui_sync.py` — teste novo.

## Fora de escopo

- Mudar o `_build_profile_from_editor`.
- Redesign do modo avançado (tratado em sprint-filha separada se necessário).
