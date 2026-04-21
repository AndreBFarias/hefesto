# FEAT-HOTKEY-STEAM-01 — Botão PS abre a Steam

**Tipo:** feat.
**Wave:** V1.1.
**Estimativa:** 1 iteração.
**Dependências:** `HotkeyManager` existe (W8.1).

---

**Tracking:** issue [#71](https://github.com/AndreBFarias/hefesto/issues/71) — fechada por PR com `Closes #71` no body.

## Contexto

Botão PS (home) no DualSense hoje faz parte do combo sagrado (`PS + D-pad` para trocar perfil). Usuário quer: **PS isolado, pressionado+solto sem combo**, abre a Steam se ela não estiver rodando OU traz Steam para foreground se já estiver rodando. Replica o comportamento do botão Xbox no Xbox Game Bar / Steam Input.

Política de timing: o combo sagrado já usa buffer 150ms (V3-2). Se PS é pressionado e em 150ms não chega D-pad, repassa como evento isolado. Aproveitar esse repasse para disparar o abrir-Steam.

## Decisão

Estender `HotkeyManager` (ou componente irmão) com handler `on_ps_solo_pressed()`:
1. Se `pgrep -x steam` retorna PID → `wmctrl -a "Steam"` para focus.
2. Senão → `subprocess.Popen(["steam"], start_new_session=True, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)`.
3. Log: `ps_button_action_steam`.
4. Nunca bloqueia o daemon — tudo em thread worker.

Configurável via `daemon.toml`:
```toml
[hotkey.ps_button]
action = "steam"  # ou "none", ou "custom_command"
custom_command = []
```

## Critérios de aceite

- [ ] `src/hefesto/integrations/hotkey_manager.py` (ou `hotkey_evdev.py`): novo método `on_ps_solo_pressed()` ativado quando o buffer de combo expira sem segundo botão. Ver V3-2 sobre buffer 150ms.
- [ ] Helper `_open_steam()`: detecta via `shutil.which("steam")` e `pgrep -x steam`; usa `wmctrl` se rodando, senão spawn. Nunca levanta — log on failure.
- [ ] Config `DaemonConfig.ps_button_action: Literal["steam", "none", "custom"] = "steam"` + `ps_button_command: list[str] = []`.
- [ ] Teste `tests/unit/test_hotkey_ps_button.py`: mock `pgrep` + mock `Popen`; confirma que "steam" spawn é tentado em ausência de processo, e `wmctrl` é chamado quando processo existe.
- [ ] Documentação em `docs/usage/hotkeys.md` (novo ou existente) descrevendo o comportamento.

## Proof-of-work runtime

- DualSense plugado, daemon ativo.
- Steam fechada → pressionar PS (solo) → Steam abre em ~2s.
- Steam aberta em background → pressionar PS → Steam vem para foreground.
- Pressionar PS + D-pad cima em 100ms → troca perfil (não abre Steam — combo tem prioridade).

## Fora de escopo

- Custom commands editáveis via GUI (V2).
- Disparar launchers alternativos (Heroic, Lutris) — criar sprint própria.

## Notas

- `wmctrl -a "Steam"` é grep case-insensitive por título; pode pegar janelas de overlay. Melhor: `wmctrl -lx` + filtrar `steam.Steam` no WM_CLASS.
- Se `steam` binário não existir no PATH, logar warning na primeira tentativa e nunca tentar de novo até reinício.
