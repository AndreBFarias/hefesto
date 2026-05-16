# FEAT-COSMIC-PANEL-WIDGET-01 — Widget de painel (bateria + perfil) em libcosmic

**Status:** **PLANNED** (forward-looking, depende sprint 116).
**Tipo:** feat (UX — visibilidade contínua no painel).
**Wave:** V3.4 (forward-looking COSMIC).
**Estimativa:** L — 3-5 iterações depois de 116.
**Dependências:** Sprint 116 (FEAT-COSMIC-APPLET-RUST-01) entregue.

---

## Contexto

Aplet de Sprint 116 expõe ícone clicável + popover. Esta sprint adiciona **widget de painel** dedicado mostrando informações contínuas (sem clique):

- Bateria do controle com % numérico.
- Nome curto do perfil ativo.
- Indicador de transport (USB/BT).

Diferente do applet (modal/popover), o widget é always-on no painel — pattern análogo ao widget de bateria do laptop em cosmic-panel.

## Decisão

Esperar libcosmic stabilizar a API de panel widgets (System76 ainda está iterando — 2026-05). Quando vier:

1. Adicionar trait `CosmicPanelWidget` implementada por um struct no mesmo crate da Sprint 116.
2. Widget consulta `daemon.state_full` via IPC a 2 Hz; renderiza texto compacto.
3. Configurável via cosmic-settings (toggle on/off, escolher quais campos exibir).
4. Quando daemon offline, widget esconde-se silenciosamente (sem placeholder zumbi).

## Out-of-scope

- Status de gatilhos/rumble em tempo real no widget (overkill).
- Widget alternativo em GTK3 panel applet (GNOME) — fora do escopo COSMIC.

---

*Sprint stub gerado em 2026-05-16 (sessão V3.1).*
