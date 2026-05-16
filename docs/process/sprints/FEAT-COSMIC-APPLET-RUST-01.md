# FEAT-COSMIC-APPLET-RUST-01 — Applet nativo COSMIC em Rust + libcosmic

**Status:** **PLANNED** (forward-looking, sem implementação na sessão v3.1.x).
**Tipo:** feat (long-term — integração nativa).
**Wave:** V3.4 (forward-looking COSMIC).
**Estimativa:** XL — 5–10 iterações + curva de aprendizado Rust/libcosmic.
**Dependências:** v3.1.1+ (notification + IPC estáveis).

---

## Contexto

ADR-014 documenta esta como "Camada 3 — Applet nativo COSMIC (fora de escopo)". A `v3.1.0` cobriu camadas 1 (XlibBackend), 2 (WaylandPortalBackend), 2.1 (cascade portal→wlrctl) e 4 (tray fallback notification). Camada 3 fica para sprint dedicada com hardware COSMIC validado + Rust toolchain configurado.

## Decisão

Adiar implementação. Quando vier:

1. Crate `cosmic-applet-hefesto-dualsense4unix` em diretório separado (`packaging/cosmic-applet/`).
2. Usar `libcosmic` (https://github.com/pop-os/libcosmic) como framework — segue padrões de outros applets de System76.
3. Aplicativo se comunica com o daemon Python via IPC Unix socket existente (`$XDG_RUNTIME_DIR/hefesto-dualsense4unix/hefesto-dualsense4unix.sock`) via método `daemon.state_full`.
4. UI mínima: ícone no painel + popover com bateria + perfil ativo + lista de perfis (click → IPC `profile.switch`).
5. Empacotamento: cargo build → bundle no `.deb` + Flatpak.

## Pre-requisitos antes de pegar esta sprint

- Hardware COSMIC validado (já temos — sprint 103).
- Rust nightly + cargo + libcosmic SDK instalado no ambiente do dev.
- Familiaridade com Iced (toolkit do libcosmic).
- API IPC estável (já temos desde v2.x).

## Critérios de aceite

1. Crate compila em modo release: `cargo build --release` produz binary nativo Linux x86_64.
2. Applet adiciona-se ao painel COSMIC via "Configurações > Painel > Applets".
3. Ícone mostra estado: cinza se daemon offline, colorido se controle conectado, vermelho se bateria <15%.
4. Click no ícone abre popover com bateria + perfil ativo + lista clicável dos perfis.
5. Click em perfil dispara `profile.switch` via IPC; UI atualiza em <500ms.
6. Empacotamento via `.deb` (postinst registra applet no `~/.config/cosmic/com.system76.CosmicPanel/`).
7. Validação manual com hardware: applet aparece, comunica com daemon, troca perfil.

## Out-of-scope nesta sprint

- Integração com cosmic-settings para shortcuts globais (sprint 118).
- Widget de painel separado para bateria (sprint 119).
- Tray icon GTK3 continua funcional como fallback (sprint 104 entregue).

---

*Sprint stub gerado em 2026-05-16 (sessão V3.1) para rastrear backlog forward-looking.*
