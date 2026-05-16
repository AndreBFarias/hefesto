# SPRINT_PLAN_COSMIC.md — Plano de execução pós-v3.0.0 com hardening COSMIC

> **Materialização das sprints pendentes** + **compatibilidade forte com Pop!_OS COSMIC** (Wayland nativo, cosmic-comp 1.0+).
>
> **Contexto:** v3.0.0 publicada em 2026-04-27 com hardening pós-publicação round 2 já incorporado (commits 04975f0..ce4c4fe). Tag mais recente: `v3.0.0`. Working tree limpo em `main`.
>
> **Ambiente do mantenedor (validação primária):** Pop!_OS 24.04 COSMIC 1.0 + Wayland + DualSense USB (054c:0ce6) conectado. `XDG_SESSION_TYPE=wayland`, `XDG_CURRENT_DESKTOP=COSMIC`, `WAYLAND_DISPLAY=wayland-1`, `DISPLAY=:1` (XWayland também ativo).
>
> **Princípio:** cada sprint produz código MERGED com validação registrada. Sprints `PROTOCOL_READY` exigem execução humana antes de promoção. Numeração continua a do `SPRINT_ORDER.md` original (101+).

---

## Sumário das Waves

| Wave | Objetivo | Sprints | Prioridade |
|------|----------|---------|------------|
| **V3.1** | Hardening COSMIC — regressões pós-rebrand | 101–105 | P0 (bloqueador) |
| **V3.2** | Pendências v3.0.0 do CHANGELOG | 106–110 | P1 |
| **V3.3** | Sprints históricas pendentes (SPRINT_ORDER.md) | 111–115 | P1–P2 |
| **V3.4** | COSMIC nativo (forward-looking, opt-in) | 116–119 | P2–P3 |
| **V3.5** | Polish/UX a partir de uso real | aberto | P3 |

---

## Wave V3.1 — Hardening COSMIC (regressões pós-rebrand) — P0

Objetivo: restaurar a compatibilidade COSMIC plena que existia em **v2.4.1** e foi perdida no rebrand `Hefesto → Hefesto - Dualsense4Unix` (commit 7f4687a..08e92b8, 2026-04-25). Sem essas sprints, o autoswitch de perfil em COSMIC puro (cosmic-comp sem XWayland) cai silenciosamente em `fallback.json`.

### 101 — BUG-COSMIC-WLR-BACKEND-REGRESSION-01

**Tamanho:** S | **Modelo:** opus | **Status:** PENDING

**Problema:** o arquivo `src/hefesto/integrations/window_backends/wlr_toplevel.py` existia em `v2.4.1` (sprint `BUG-COSMIC-WLR-BACKEND-01`) e implementava `WlrctlBackend` para cobrir compositors wlroots-like (COSMIC, Sway, Hyprland, niri, river) via protocolo `wlr-foreign-toplevel-management-unstable-v1`. No rebrand para `hefesto_dualsense4unix`, o arquivo foi removido junto com a renomeação massiva, mas não foi re-criado no novo namespace. Atualmente `src/hefesto_dualsense4unix/integrations/window_backends/` só tem `base.py`, `null.py`, `wayland_portal.py`, `xlib.py`.

**Consequência:** em COSMIC + Wayland puro (sem XWayland), `detect_window_backend()` retorna `WaylandPortalBackend`, que tenta `org.freedesktop.portal.Window.GetActiveWindow` — método **não implementado** pelo `xdg-desktop-portal-cosmic` (estado em 2026-05). Portal retorna `None`, autoswitch fica preso no fallback.

**Entrega:**
1. Re-criar `src/hefesto_dualsense4unix/integrations/window_backends/wlr_toplevel.py` (porte literal do v2.4.1, imports atualizados para `hefesto_dualsense4unix.*`).
2. Atualizar `src/hefesto_dualsense4unix/integrations/window_detect.py` para usar `_WaylandCascadeBackend` (portal → wlrctl → null) em vez de `WaylandPortalBackend` direto.
3. Adicionar testes em `tests/unit/test_wlrctl_backend.py` (porte do v2.4.1 + 3 testes novos: cascade portal-falha→wlrctl-ok, ambos-falham→None, wlrctl-bin-ausente→None imediato).
4. Atualizar `docstring` do módulo `window_detect.py` documentando cascade.

**Validação:**
- `pytest tests/unit/test_wlrctl_backend.py tests/unit/test_window_detect_factory.py` verde.
- `ruff` + `mypy --strict` verdes.
- Manual em COSMIC real: `apt install wlrctl` (ou Flatpak/Arch equivalente) + abrir 2 apps + rodar `python -c "from hefesto_dualsense4unix.integrations.window_detect import get_active_window_info; print(get_active_window_info())"` → muda conforme janela ativa.

### 102 — BUG-COSMIC-INSTALL-SH-REGRESSION-01

**Tamanho:** S | **Modelo:** opus | **Status:** PENDING

**Problema:** `install.sh` em `v2.4.1` tinha bloco completo de:
- Flag `--force-xwayland`
- Detecção automática `DESKTOP_IS_COSMIC=1` via `XDG_CURRENT_DESKTOP`
- Prompt interativo (com `--yes` instala silencioso) para `apt install wlrctl`
- Prompt interativo para gravar `GDK_BACKEND=x11` no `.desktop` (force XWayland)
- Mensagens de erro acionáveis em distros sem `wlrctl` no apt (Arch/Fedora/source)

Todo esse bloco foi removido no rebrand. `install.sh` atual tem `0 menções` a `cosmic|wlrctl|wayland|xwayland`. `packaging/debian/control` preservou `Recommends: ydotool | wlrctl` (correto), mas `install.sh` em source install não detecta.

**Entrega:**
1. Restaurar flag `--force-xwayland` no parser de args.
2. Restaurar detecção `DESKTOP_IS_COSMIC` baseada em `XDG_CURRENT_DESKTOP`.
3. Bloco interativo (com `--yes` = sim a tudo): instalar `wlrctl` via apt + opcionalmente ativar XWayland no `.desktop`.
4. Mensagens de erro com alternativas para distros sem `wlrctl` no repo.
5. Mensagem informativa no fim do `install.sh` quando rodando em COSMIC dizendo qual backend foi configurado.

**Validação:**
- `bash -n install.sh` (syntax check).
- `shellcheck install.sh` se disponível.
- Manual em COSMIC: `./install.sh --yes` instala wlrctl, GDK_BACKEND opcional aplicado.
- Manual em GNOME/KDE: bloco COSMIC pulado, fluxo normal.

### 103 — FEAT-COSMIC-NATIVE-VALIDATION-01

**Tamanho:** M | **Modelo:** opus | **Status:** PENDING

**Problema:** ADR-014 declara "validação manual é responsabilidade do mantenedor antes de marcar Camada 2 como produção ready". v2.4.1 declarou COSMIC compat mas não há documento de validação em hardware real COSMIC 1.0 final (não-alpha).

**Entrega:**
1. Rodar suite completa em ambiente do mantenedor (COSMIC + DualSense USB conectado):
   - Daemon start/stop limpo.
   - Conexão controle USB; bateria; lightbar magenta via CLI.
   - Smoke `./run.sh --smoke` USB.
   - Autoswitch: abrir Firefox + Cyberpunk (steam ou exe) e ver mudança de perfil.
   - GUI GTK3 abre e renderiza sob Wayland.
   - Tray icon em `cosmic-panel` (testar; se não renderiza, documentar e abrir sprint dedicada).
   - Service `systemctl --user enable --now` ativo após login.
2. Documentar resultado em `docs/process/discoveries/2026-05-15-cosmic-1.0-validation.md`.
3. Atualizar matriz de compatibilidade no `README.md` para mover Pop!_OS 22.04 → 24.04 COSMIC para "OK" (USB + autoswitch + tray + GUI).
4. Atualizar `CHECKLIST_VALIDACAO_v3.md` com seção dedicada COSMIC (5–8 itens reproduzíveis).

**Validação:** documento de discoveries + README + checklist atualizados em commit único.

### 104 — FEAT-COSMIC-TRAY-FALLBACK-01

**Tamanho:** S | **Modelo:** opus | **Status:** PENDING

**Problema:** `cosmic-panel` (panel da COSMIC) ainda não tem suporte estável a `StatusNotifierItem` / `AppIndicator`. Em distros 2026, tray icon do Hefesto pode não renderizar nativamente. Hoje o código em `src/hefesto_dualsense4unix/integrations/tray.py` tenta `AyatanaAppIndicator3 → AppIndicator3` e cai em `is_available()=False` sem fallback acionável.

**Entrega:**
1. Detectar COSMIC em runtime: se `XDG_CURRENT_DESKTOP=COSMIC` e tray indisponível, exibir notificação D-Bus uma vez no startup com instruções para usuário (instalar `cosmic-applet-status-notifier` quando existir, ou usar `hefesto-dualsense4unix-gui` standalone).
2. Adicionar fallback `--gui-standalone` no CLI: abre GUI sem tray (window persistente). Já existe a GUI; só precisa flag para suprimir warning de tray-ausente.
3. Documentar em `README.md` seção "Pop!_OS COSMIC" — workaround.

**Validação:**
- Manual em COSMIC: confirmar mensagem D-Bus aparece + flag `--gui-standalone` funciona.

### 105 — CHORE-COSMIC-DOC-UPDATE-01

**Tamanho:** XS | **Modelo:** sonnet | **Status:** PENDING

**Entrega:**
1. Atualizar `docs/adr/014-cosmic-wayland-support.md` registrando o cascade portal→wlrctl como "implementado v3.1.0".
2. Atualizar `README.md` seção "Instalação" → Flatpak para mencionar COSMIC como alvo primeira-classe.
3. Atualizar matriz de compatibilidade no `README.md`: "Pop!_OS 24.04 COSMIC | 6.18+ | 256+ | OK | ? | depende | autoswitch via wlrctl" — fica documentado.

---

## Wave V3.2 — Pendências v3.0.0 do CHANGELOG

Reportadas em `CHANGELOG.md` seção `[Unreleased]` → `Pendente (não fechado em v3.0.0)`.

### 106 — VALIDATION-V3-HARDWARE-USB-01

**Tamanho:** M | **Status:** PROTOCOL_READY (requer hardware — disponível agora)

**Entrega:** rodar `CHECKLIST_VALIDACAO_v3.md` em ambiente real e marcar checkboxes. Anexar logs.

### 107 — BUG-GUI-QUIT-RESIDUAL-01 (#32)

**Tamanho:** M | **Status:** PENDING

**Problema:** GUI trava em `futex` após `Gtk.main_quit()` em alguns casos (intermitente).

**Entrega:** investigar via `py-spy dump <pid>`; suspeita atual: `tray.stop()` D-Bus call bloqueia GLib mainloop. Fix: timeout ou call em thread separada.

### 108 — FEAT-APPIMAGE-GUI-WITH-GTK-01 (#33)

**Tamanho:** L | **Status:** PENDING

**Entrega:** refactor AppImage de `python-appimage` (CLI only) para `appimagetool` + GTK runtime portátil bundlado.

### 109 — FEAT-BLUETOOTH-CONNECTION-01 (promoção)

**Tamanho:** S (validação) | **Status:** PROTOCOL_READY → MERGED

**Entrega:** rodar pareamento BT real + validar `transport=bt` + lightbar + triggers. Promover sprint em `docs/process/sprints/`.

### 110 — VALIDATION-V3-MOUSE-TECLADO-01

**Tamanho:** S | **Status:** PROTOCOL_READY

**Entrega:** rodar aba Mouse e Teclado fim-a-fim com hardware e jogo real. Documentar limitações de cursor em Wayland (compositor controla).

---

## Wave V3.3 — Sprints históricas pendentes (SPRINT_ORDER.md)

### 111 — CHORE-CI-REPUBLISH-TAGS-01 (PROTOCOL_READY)

Re-publicar v2.0.0 e v2.1.0 com artifacts no GitHub. Requer execução humana via `gh release create`.

### 112 — HARDWARE-VALIDATION-PROTOCOL-01 (PROTOCOL_READY)

Checklist 21 itens. Já existe spec; rodar.

### 113 — FEAT-GITHUB-PROJECT-VISIBILITY-01 (PROTOCOL_READY)

Governança + social-preview PNG + badges. Requer `gh` CLI humano.

### 114 — FEAT-FIRMWARE-UPDATE-PHASE1-01 (PROTOCOL_READY)

Research DFU. Documento existe; promoção requer execução em hardware.

### 115 — CHORE-CI-COSMIC-MATRIX-01

**Tamanho:** S | **Modelo:** sonnet | **Status:** PENDING

**Entrega:** adicionar matrix CI com `ubuntu-24.04` + `XDG_CURRENT_DESKTOP=COSMIC` (mock) no `release.yml` para validar testes COSMIC-aware.

---

## Wave V3.4 — COSMIC nativo (forward-looking)

### 116 — FEAT-COSMIC-APPLET-RUST-01

**Tamanho:** XL | **Status:** PENDING (futuro)

ADR-014 Camada 3. Crate Rust `cosmic-applet-hefesto-dualsense4unix` para integração nativa com cosmic-panel. Fora de escopo v3.1.

### 117 — FEAT-COSMIC-NOTIFICATIONS-01

**Tamanho:** S | **Status:** PENDING

Emitir notificações `org.freedesktop.Notifications` em eventos canônicos (controle conectado, bateria <15%, perfil trocado). Funciona em qualquer DE; COSMIC respeita spec.

### 118 — FEAT-COSMIC-GLOBAL-SHORTCUTS-01

**Tamanho:** M | **Status:** PENDING

Integração com `cosmic-settings` para registrar atalhos globais (alternativa ao combo HID PS+D-pad, opt-in).

### 119 — FEAT-COSMIC-PANEL-WIDGET-01

**Tamanho:** L | **Status:** PENDING (depende 116)

Widget de painel COSMIC (não confundir com tray) mostrando bateria + perfil ativo. Implementado via libcosmic.

---

## Ordem de execução recomendada

```
P0 BLOQUEADORES (executar imediatamente):
  101 → 102 → 105       (re-portar wlr, fix install.sh, doc-update)
       ↓
  103                   (validação COSMIC real — hardware do mantenedor)
       ↓
  104                   (tray fallback se 103 detectar problema)

P1 PÓS-COSMIC (depois das P0):
  106 (CHECKLIST hardware) — pode rodar em paralelo a 107/109
  109 (BT validation) — em paralelo a 106
  107 (#32 GUI quit) — investigação
  110 (Mouse/Teclado validation)

P2 BACKLOG:
  108 (AppImage GUI)
  111–114 (PROTOCOL_READY → MERGED)
  115 (CI matrix COSMIC)

P3 FUTURO:
  116–119 (COSMIC nativo — depois de v3.1.0 estabilizar)
```

---

## Critérios de release v3.1.0

Para tag `v3.1.0` (COSMIC hardening):

- [ ] 101–105 MERGED
- [ ] 106 executada (CHECKLIST_VALIDACAO_v3.md preenchido)
- [ ] 109 executada se hardware BT disponível
- [ ] CHANGELOG entry `[3.1.0]` com seção "COSMIC compatibility restored"
- [ ] Pytest verde (target: 1345+ tests)
- [ ] Ruff + mypy strict verdes
- [ ] `./run.sh --smoke` USB verde em COSMIC real
- [ ] Smoke `.deb` install funciona em `ubuntu-24.04` (CI)

---

## Princípio de execução (deste agente)

1. **Documentar primeiro:** cada sprint executada gera entry em `CHANGELOG.md` `[Unreleased]`.
2. **Validação contínua:** após cada sprint, rodar `pytest tests/unit -q` + `ruff check` antes de commit.
3. **Smoke real:** sprints que tocam runtime (daemon, GUI) rodam `./run.sh --smoke` antes de fechar.
4. **Commits atômicos:** 1 sprint = 1 commit (ou 1 série coesa). Mensagem PT-BR sem acento → `feat(cosmic): restaurar WlrctlBackend portado para hefesto_dualsense4unix (BUG-COSMIC-WLR-BACKEND-REGRESSION-01)`.
5. **Anti-regressão:** sprint que descobre bug colateral abre nova sprint em vez de inline-fix (regra L5 AI.md).
6. **PR para release:** v3.1.0 sai em PR único `release/v3.1.0` listando 101–106 fechadas.

---

*"O dobro de sprints na metade do tempo entrega mais do que o dobro do que sprints magras em sequência longa." — SPRINT_ORDER.md, mantida.*
