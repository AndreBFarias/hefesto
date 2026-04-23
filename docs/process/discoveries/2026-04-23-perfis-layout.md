# Discovery — UI-PROFILES-LAYOUT-POLISH-01 (aba Perfis)

**Data:** 2026-04-23
**Sprint:** UI-PROFILES-LAYOUT-POLISH-01 (fases 1 + 2 combinadas)
**Contexto:** usuário reportou "ainda tem algo estranho na aba de perfis no layout, não sei o que é". Sprint investigativa + fixes cirúrgicos dos achados óbvios, com H1/H5 documentados para sprint-filha.

---

## Metodologia

1. GUI spawnada via `PYTHONPATH=...:/usr/lib/python3/dist-packages /usr/bin/python3 -m hefesto.app.main` (contorno A-12).
2. `XDG_CONFIG_HOME=/tmp/hefesto-test-profiles` com **19 perfis** (9 defaults + 10 `teste_NN`) para estressar H3.
3. 2 screenshots capturados com `DISPLAY=:1 import -window`:
   - `/tmp/hefesto_perfis_investigacao_20260423T174226.png` (sha256 `397a86eff053ddf304d334f72d4a45ecf8b4d619f328275a1937ad92b011d5b0`) — perfil "Ação" selecionado, modo avançado.
   - `/tmp/hefesto_perfis_simples_20260423T174245.png` (sha256 `7617c77c1d45da1c6bf0d4f5acc613d84d7b470eafbd602e3d2b0a56c371d36e`) — perfil "meu_perfil" selecionado, modo simples (6 radios visíveis).
4. Resolução: 1920x1080 @ 144Hz (`xrandr`), janela GUI em default 1100x680.

---

## Achados (mapeamento Hx → veredicto)

### H1 — Radio group "Aplica a:" vertical com 6 opções

**Status:** CONFIRMADO. **Aplicar nesta sprint: NÃO** (critério "requer aprovação" do spec — redesign UX).

**Fragmento Glade:** `src/hefesto/gui/main.glade:1210-1277`.

O grupo usa 6 `GtkRadioButton` empilhados via `GtkBox orientation=vertical`:
- `profile_radio_any` (Qualquer janela)
- `profile_radio_steam` (Jogos da Steam)
- `profile_radio_browser` (Navegador)
- `profile_radio_terminal` (Terminal)
- `profile_radio_editor` (Editor de código)
- `profile_radio_game` (Jogo específico)

**Problema observado:** ocupa ~180px de altura vertical, dominando a coluna direita no modo simples. Desproporcional ao resto do editor (Nome + Prioridade + botão Salvar somam ~90px).

**Recomendação para sprint-filha `UI-PROFILES-RADIO-GROUP-REDESIGN-01`:** converter para `GtkComboBoxText` com as 6 opções. Libera ~140px verticais e alinha com padrão UX do projeto (outras abas usam ComboBox para presets). Alternativa: `GtkFlowBox` com 2 colunas × 3 linhas, que preserva affordance de radio mas reduz footprint.

Mock ASCII da opção ComboBox:
```
Nome:         [meu_perfil             ]
Prioridade:   [====o=======] 0
Aplica a:     [Qualquer janela    v]
                └─ Jogos da Steam
                   Navegador
                   Terminal
                   Editor de código
                   Jogo específico
[Nome do jogo: eldenring]  (só se "Jogo específico")
```

### H2 — Botão "Salvar" (direita) duplica "Salvar Perfil" (footer)

**Status:** REFUTADO. **Não remover.** Investigação empírica mostrou funções **distintas**:

- `profile_save_button` → `on_profile_save` em `src/hefesto/app/actions/profiles_actions.py:229`
  - Chama `_build_profile_from_editor()` (lê **os campos do editor na aba Perfis**: nome, prioridade, radios/match).
  - Persiste o **perfil em edição** selecionado na TreeView.
  - Toast: `"Perfil salvo: <name>"`.

- `btn_footer_save_profile` → `on_save_profile` em `src/hefesto/app/actions/footer_actions.py:135`
  - Abre **diálogo de nome**, lê o `DraftConfig` global (triggers/LEDs/rumble/mouse das outras abas).
  - Cria um **NOVO perfil nomeado** a partir do estado atual do controle.
  - Fluxo: `self.draft.to_profile(nome)` → `save_profile(profile)`.

Confundir os dois seria dano permanente. Mantido. Registra-se que o naming merece label mais claro — possível sprint futura `UI-PROFILES-SAVE-BUTTONS-CLARIFY-01` para renomear (ex.: "Salvar edição" vs. "Exportar estado atual como perfil"). Não é escopo agora.

### H3 — TreeView sem scroll

**Status:** REFUTADO. **Não precisa fix.**

**Fragmento Glade:** `src/hefesto/gui/main.glade:1062-1074` já envolve o `profiles_tree` em `GtkScrolledWindow`:
```xml
<object class="GtkScrolledWindow">
  <property name="hscrollbar-policy">never</property>
  <property name="vscrollbar-policy">automatic</property>
  <property name="hexpand">True</property>
  <property name="vexpand">True</property>
  <child>
    <object class="GtkTreeView" id="profiles_tree">
```

Com 19 perfis o scroll não apareceu na altura 680px default (todos couberam). Em monitor menor (720p) ou com 30+ perfis, o `vscrollbar-policy=automatic` aparece sozinho. Estruturalmente OK.

### H4 — Headers das colunas "Nome / Prio / Match" com baixo contraste

**Status:** CONFIRMADO. **Aplicar nesta sprint: SIM.**

**Arquivo tocado:** `src/hefesto/gui/theme.css`.

Observação visual: os headers renderizam em um bege/branco (#f8f8f2, default da `.hefesto-window`) sem destaque versus as linhas. Drácula purple (#bd93f9) já é a cor de accent do projeto (usada em bordas de button, underline de tab ativa). Aplicar no header button do treeview.

**Fix:**
```css
.hefesto-window treeview header button,
.hefesto-window treeview header button label {
    color: #bd93f9;
    font-weight: bold;
}
```

### H5 — Espaço vazio na coluna direita (modo simples)

**Status:** CONFIRMADO. **Aplicar nesta sprint: NÃO** (critério "requer aprovação" — redistribuição estrutural).

**Fragmento Glade:** `src/hefesto/gui/main.glade:1201-1383` (`profile_editor_stack`) + `:1386-1399` (rodapé com Salvar).

Entre o rodapé `profile_editor_hint` (modo avançado) ou último radio (modo simples) e o botão Salvar à direita, há ~200-250px vazios em resolução 1100x680. Fix limpo exigiria:
- Redistribuir via `GtkGrid` com mais campos simultâneos.
- Adicionar preview (ex.: `GtkLabel` com o JSON resultante).
- Comprimir altura da coluna com `vexpand=False` no stack (mas isso quebra a aba de preset avançado que tem 3 inputs grid).

**Recomendação para sprint-filha `UI-PROFILES-RIGHT-PANEL-REBALANCE-01`:** preview ao vivo + reorganização via grid. Fora de escopo agora.

### H6 — Slider de Prioridade sem labels de mínimo/máximo

**Status:** CONFIRMADO. **Aplicar nesta sprint: SIM.**

**Fragmento Glade:** `src/hefesto/gui/main.glade:1183-1194` (`profile_priority_scale`) + `:38-44` (`profile_priority_adj`, range 0-100).

Observação: o `GtkScale` mostra somente o valor corrente à direita via `draw-value=True` + `value-pos=right`. Em 0-100 sem marks o usuário não sabe se está numa escala absoluta, percentual ou 0-1000 (o spec chutou 0-1000 — na verdade é 0-100).

**Fix:** adicionar `<marks>` ao `GtkScale` com valores `0`, `50`, `100` visíveis abaixo do trilho. Glade syntax:
```xml
<marks>
  <mark value="0" position="bottom">0</mark>
  <mark value="50" position="bottom">50</mark>
  <mark value="100" position="bottom">100</mark>
</marks>
```

Abordagem alternativa (2 `GtkLabel` flanqueando o `GtkScale` num `GtkBox` horizontal) também funciona mas obriga refactor do grid row. Marks nativas são 1 edit limpo.

### H7 (achado novo) — Inconsistência de range: spec citou 0-1000, código é 0-100

**Status:** CATALOGADO. **Não-fix.**

Spec original (sintoma §H6) dizia "GtkLabel '0' à esquerda... '1000' à direita". `profile_priority_adj` em `main.glade:38-44` tem `lower=0 upper=100`. Tooltip em `:1191` confirma "0-100". Armadilha de briefing, não de código. Documentado para evitar repetição em planejamento futuro.

### H8 (achado novo) — Modo avançado como default para perfis com match complexo

**Status:** CATALOGADO. **Não-fix** (comportamento intencional de `_populate_editor` em `profiles_actions.py:303-344`).

Ao clicar num perfil com `match.type == "criteria"` (como "Ação"), a GUI força modo avançado — correto para preservar dados. Mas a transição é abrupta: o switch "Modo avançado" vira sozinho sem feedback visual. Candidato a tooltip explicativo futuro.

---

## Fixes aplicados nesta sprint (fase 2)

| Hx | Arquivo              | Natureza                                                                      |
|----|----------------------|-------------------------------------------------------------------------------|
| H4 | `theme.css`          | Regra CSS para headers do treeview com accent `#bd93f9` + bold.              |
| H6 | `main.glade`         | 3 `<mark>` no `profile_priority_scale` (0 / 50 / 100, position=bottom).       |

## Fixes não aplicados (sprints-filhas propostas)

| Hx | Sprint-filha ID                              | Natureza                                          |
|----|----------------------------------------------|---------------------------------------------------|
| H1 | `UI-PROFILES-RADIO-GROUP-REDESIGN-01`        | Converter 6 radios verticais em ComboBox ou FlowBox 2×3. |
| H5 | `UI-PROFILES-RIGHT-PANEL-REBALANCE-01`       | Preview ao vivo do perfil em JSON + reflow do grid. |

H2 (remover Salvar isolado) foi **refutado** após inspeção dos handlers — NÃO vira sprint.

## Refutados (sem sprint)

- **H2**: `on_profile_save` e `on_save_profile` têm semântica distinta.
- **H3**: `GtkScrolledWindow` já estrutural em `main.glade:1062`.

---

## Proof visual

- `/tmp/hefesto_perfis_investigacao_20260423T174226.png` — antes, modo avançado.
- `/tmp/hefesto_perfis_simples_20260423T174245.png` — antes, modo simples (6 radios).

Screenshots "depois" no relatório de proof-of-work da sprint.
