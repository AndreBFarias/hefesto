# FEAT-COSMIC-WAYLAND-01 — Compatibilidade com COSMIC (Wayland) do Pop!_OS

**Tipo:** feat (plataforma).
**Wave:** V1.1 ou V1.2.
**Estimativa:** 2-3 iterações (Wayland é território novo).
**Dependências:** nenhuma.

---

**Tracking:** issue [#80](https://github.com/AndreBFarias/hefesto/issues/80) — fechada por PR com `Closes #80` no body.

## Contexto

Pop!_OS 24.04 traz o **COSMIC DE** (System76, Wayland-nativo). ADR-007 já fala em deferir Wayland, mas o desembarque do COSMIC em produção exige revisitar. Pontos do Hefesto que quebram em Wayland:

1. **Detecção de janela ativa** (`src/hefesto/integrations/xlib_window.py`): depende de `python-xlib` + `DISPLAY`. Em Wayland puro, não há X display; autoswitch cai em fallback silencioso (`fallback.json`).
2. **Validação visual** (`scrot`, `import`, `xdotool`, `wmctrl`): todas X11-only. Em COSMIC puro, usar `grim` (screenshot Wayland) + `wlrctl` / `ydotool` para input; ou via portal XDG (D-Bus).
3. **AppIndicator Ayatana**: funciona em Wayland com XWayland; COSMIC tem API de panel própria (cosmic-applet) — sprint futura para integração nativa.
4. **Hotkey global**: `/dev/input/event*` funciona independente de Wayland/X11 — OK.
5. **uinput mouse/keyboard**: funciona em Wayland — OK (evdev nível kernel).

## Decisão em camadas

### Camada 1 (mínima): detecção + fallback documentado

- `src/hefesto/integrations/xlib_window.py` detecta `os.environ.get("WAYLAND_DISPLAY")` primeiro; se Wayland, tentar portal D-Bus `org.freedesktop.portal.Window` (disponível no COSMIC 1.0+).
- Se nem X nem portal disponíveis: `get_active_window_info()` retorna `None`; `AutoSwitcher` entra em modo silencioso (usa `fallback.json` + respeita escolha manual via CLI/GUI).
- Log `autoswitch_compositor_unsupported` no boot.

### Camada 2 (portal XDG para janela ativa)

- Implementar cliente Python do portal `org.freedesktop.portal.Window` (via `dbus-fast` ou `pydbus`).
- Retorna `wm_class` / `pid` / `app_id` no formato esperado por `ProfileManager.select_for_window()`.
- Teste manual no COSMIC: abrir Firefox, Steam, Terminal — perfil troca corretamente.

### Camada 3 (COSMIC-native panel applet, futuro)

- Criar crate Rust `cosmic-applet-hefesto` que se comunica com daemon via Unix socket — fora do escopo desta sprint.

## Critérios de aceite

- [ ] `src/hefesto/integrations/xlib_window.py` renomeado para `src/hefesto/integrations/window_detect.py` com factory que escolhe backend (`XlibBackend` | `WaylandPortalBackend` | `NullBackend`).
- [ ] `WaylandPortalBackend` implementa via D-Bus portal; testado em COSMIC 1.0 Pop!_OS 24.04.
- [ ] `NullBackend` é fallback quando nenhum dos dois disponível; `AutoSwitcher` respeita.
- [ ] Skill `validacao-visual` ganha tentativa nova: `grim` + `wlr-randr` para COSMIC (via `settings.json` permissões) além do pipeline X11 atual.
- [ ] Teste unitário `tests/unit/test_window_detect_factory.py`: mock `os.environ` para X11, Wayland, ambos, nenhum — factory retorna backend certo.
- [ ] `docs/adr/014-cosmic-wayland-support.md` (novo ADR substituindo/complementando 007).
- [ ] `docs/usage/cosmic.md` (novo): guia de uso no COSMIC.

## Proof-of-work

- Booting COSMIC Pop!_OS 24.04.
- `./run.sh --daemon --fake` em background.
- GUI abre via `hefesto-gui`; janela aparece (XWayland por enquanto OK).
- Abrir Firefox → daemon loga `profile_autoswitch from_=fallback to=navegacao wm_class=firefox`.
- Captura visual via `grim $(slurp)` + descrição multimodal.

## Arquivos tocados (previsão)

- `src/hefesto/integrations/window_detect.py` (novo ou refactor de xlib_window.py)
- `src/hefesto/integrations/window_backends/xlib.py`
- `src/hefesto/integrations/window_backends/wayland_portal.py`
- `src/hefesto/integrations/window_backends/null.py`
- `docs/adr/014-cosmic-wayland-support.md` (novo)
- `docs/usage/cosmic.md` (novo)
- `tests/unit/test_window_detect_factory.py` (novo)

## Fora de escopo

- Applet nativo COSMIC em Rust.
- Suporte Hyprland / Sway específico (teste comunidade).
- Substituir toda pipeline visual de validação (X11 fica como fallback).

## Notas

- `WAYLAND_DISPLAY` presente + `DISPLAY` também: ambiente XWayland — X backend funciona, preferir X por compatibilidade.
- `WAYLAND_DISPLAY` sem `DISPLAY`: Wayland puro, usar portal.
- Portal `org.freedesktop.portal.Window.GetActiveWindow` só foi introduzido recentemente; COSMIC 1.0+ tem, GNOME 46+ também.
