# UI-PROFILES-RADIO-GROUP-REDESIGN-01 — Redesign do grupo "Aplica a:"

**Tipo:** polish / refactor UX.
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** `UI-PROFILES-LAYOUT-POLISH-01` (MERGED).
**Origem:** achado H1 em `docs/process/discoveries/2026-04-23-perfis-layout.md`.

---

**Tracking:** label `type:polish`, `ui`, `ai-task`, `status:ready`.

## Sintoma

No modo simples da aba Perfis, o grupo "Aplica a:" usa 6 `GtkRadioButton` empilhados verticalmente (`src/hefesto/gui/main.glade:1210-1277`):

- `profile_radio_any` — Qualquer janela
- `profile_radio_steam` — Jogos da Steam
- `profile_radio_browser` — Navegador
- `profile_radio_terminal` — Terminal
- `profile_radio_editor` — Editor de código
- `profile_radio_game` — Jogo específico (+ entry "Nome do jogo")

Ocupa ~180px verticais, desproporcional ao resto do editor (~90px). Dominância visual confirmada em screenshot `/tmp/hefesto_perfis_simples_20260423T174245.png`.

## Decisão

Substituir os 6 radios por 1 `GtkComboBoxText` ou `GtkFlowBox` (2 colunas × 3 linhas).

Preferência: `GtkComboBoxText` — alinhado com padrão do projeto (presets de trigger, LED pattern etc. usam combo). Libera ~140px verticais.

## Critérios de aceite

- [ ] `profile_editor_simples` perde os 6 `GtkRadioButton`.
- [ ] Novo `GtkComboBoxText id=profile_aplica_a_combo` com 6 entries: "Qualquer janela", "Jogos da Steam", "Navegador", "Terminal", "Editor de código", "Jogo específico".
- [ ] Handler `on_profile_aplica_a_changed` em `profiles_actions.py` mostra/esconde `profile_game_entry_box` quando seleção == "Jogo específico".
- [ ] `_selected_simple_choice` e `_select_radio` refactorados para ler/escrever via `get_active_id`/`set_active_id`.
- [ ] Testes unitários: `test_profile_simple_combo_populates` + `test_profile_simple_combo_game_shows_entry` em `tests/unit/test_profiles_gui_sync.py`.
- [ ] Screenshot antes/depois + comparação visual (altura da coluna direita).
- [ ] Gates canônicos.

## Arquivos tocados

- `src/hefesto/gui/main.glade` — troca dos 6 radios por combo.
- `src/hefesto/app/actions/profiles_actions.py` — ajuste dos helpers + handler novo.
- `tests/unit/test_profiles_gui_sync.py` — 2 testes novos.

## Fora de escopo

- Mudar a matriz de presets (`_RADIO_IDS` → chaves do combo são o mesmo slug).
- Redesign do modo avançado.
