# FEAT-COSMIC-GLOBAL-SHORTCUTS-01 — Atalhos globais via cosmic-settings

**Status:** **PLANNED** (forward-looking).
**Tipo:** feat (UX — alternativa ao combo HID PS+D-pad).
**Wave:** V3.4 (forward-looking COSMIC).
**Estimativa:** M — 2 iterações com hardware COSMIC.
**Dependências:** ADR-014 estável, cosmic-settings API de keybindings publicada por System76.

---

## Contexto

Hoje o Hefesto suporta troca de perfil via "combo sagrado" PS+D-pad (HID puro, independente de DE). Sprint 117 adicionou notifications opt-in. Próximo nível: integração com cosmic-settings para permitir o usuário registrar atalhos globais (ex: `Super+Shift+1` → ativar perfil "FPS") que disparam ações via D-Bus para o daemon.

## Decisão

Esperar a API de keybindings do cosmic-settings estabilizar. Quando vier:

1. Daemon expõe método IPC novo: `keybindings.register(profile_name, accelerator)` e `keybindings.unregister(profile_name)`.
2. Wrapper Python em `src/hefesto_dualsense4unix/integrations/cosmic_shortcuts.py` que registra atalhos via D-Bus em `com.system76.CosmicSettings.Keybindings` (ou nome canônico que System76 publicar).
3. Aba GUI "Atalhos" no GTK3 (nova) permite atribuir accelerator por perfil; persiste em `~/.config/hefesto-dualsense4unix/shortcuts.json`.
4. Notifica via toast quando atalho é disparado (reaproveita `desktop_notifications.notify`).

## Out-of-scope

- Atalhos globais em GNOME/KDE via portal XDG `org.freedesktop.portal.GlobalShortcuts` (sprint separada se demanda real).
- Combos HID adicionais além de PS+D-pad (já está bem coberto).

## Pre-requisitos

- API cosmic-settings keybindings estável e documentada (System76 — pendente em 2026-05).
- Sprint 116 (applet Rust) entregue, pois shortcuts naturalmente exigem applet pra apresentar UI no painel.

---

*Sprint stub gerado em 2026-05-16 (sessão V3.1).*
