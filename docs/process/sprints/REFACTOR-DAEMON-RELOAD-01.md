# REFACTOR-DAEMON-RELOAD-01 — Hot-reload seguro do HotkeyManager em `daemon.reload`

**Tipo:** refactor (dívida técnica).
**Wave:** V1.2.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma (mas pré-req para config hot-swap de perfil via IPC).

---

**Tracking:** issue a criar. Origem: armadilha **A-08** em `VALIDATOR_BRIEF.md`.

## Contexto

Armadilha A-08 do BRIEF:

> `_start_hotkey_manager` captura `action = self.config.ps_button_action` e `command = self.config.ps_button_command` em closure, fora da função interna `_on_ps_solo`. Se `daemon.reload` futuramente substituir `self.config = NewConfig(...)`, a closure continua apontando pros valores antigos. Bug latente.

Hoje não há `daemon.reload` implementado, mas assim que implementarmos, o HotkeyManager não reage a mudanças de config.

## Decisão

1. `_on_ps_solo` lê `self.config.ps_button_action` **dentro** da função — não em closure.
2. Novo método `Daemon.reload_config(new_config: DaemonConfig)` que:
   - Salva o novo config em `self.config`.
   - Rebuilda `_hotkey_manager` via `_stop_hotkey_manager()` + `_start_hotkey_manager()` para garantir observadores frescos.
   - Se `mouse_emulation_enabled` mudou, chama `set_mouse_emulation(new_config.mouse_emulation_enabled, ...)`.
   - Se `rumble_policy` mudou, já é pego automaticamente via `RumbleEngine._effective_mult` (ref compartilhada) — sem trabalho extra.
3. Handler IPC novo `daemon.reload {config_overrides: {...}}` que chama `reload_config`.

### Snippet chave

```python
# src/hefesto/daemon/lifecycle.py
def _start_hotkey_manager(self) -> None:
    def _on_ps_solo() -> None:
        # Ler cfg de `self.config` em runtime — NÃO em closure.
        cfg = self.config
        if cfg.ps_button_action == "none":
            return
        if cfg.ps_button_action == "steam":
            from hefesto.integrations.steam_launcher import open_or_focus_steam
            open_or_focus_steam()
        elif cfg.ps_button_action == "custom":
            command = cfg.ps_button_command
            if not command:
                logger.warning("hotkey_ps_solo_custom_sem_comando")
                return
            ...

    self._hotkey_manager = HotkeyManager(on_ps_solo=_on_ps_solo)
    logger.info("hotkey_manager_started", ps_button_action=self.config.ps_button_action)


def _stop_hotkey_manager(self) -> None:
    self._hotkey_manager = None


def reload_config(self, new_config: DaemonConfig) -> None:
    old = self.config
    self.config = new_config

    # Rebuild hotkey se mudou algo relevante (paranoia: rebuild sempre).
    self._stop_hotkey_manager()
    self._start_hotkey_manager()

    # Mouse
    if old.mouse_emulation_enabled != new_config.mouse_emulation_enabled:
        self.set_mouse_emulation(
            new_config.mouse_emulation_enabled,
            speed=new_config.mouse_speed,
            scroll_speed=new_config.mouse_scroll_speed,
        )

    logger.info("daemon_config_reloaded",
                keys_changed=[k for k in new_config.__dict__ if getattr(old, k, None) != getattr(new_config, k)])
```

Handler IPC:

```python
# src/hefesto/daemon/ipc_server.py
async def _handle_daemon_reload(self, params: dict) -> dict:
    overrides = params.get("config_overrides", {})
    new_cfg = replace(self.daemon.config, **overrides)
    self.daemon.reload_config(new_cfg)
    return {"status": "ok", "config": asdict(new_cfg)}
```

## Critérios de aceite

- [ ] `src/hefesto/daemon/lifecycle.py`: `_on_ps_solo` lê `self.config` em runtime; método `reload_config(new_config)` implementado.
- [ ] `src/hefesto/daemon/ipc_server.py`: handler `daemon.reload` + registro em `self._handlers`.
- [ ] Teste `tests/unit/test_daemon_reload.py`:
  - `reload_config({"ps_button_action": "none"})` → `_on_ps_solo` não abre Steam mesmo se PS solo dispara.
  - `reload_config({"mouse_emulation_enabled": True})` → `_mouse_device` vivo após reload.
  - IPC `daemon.reload` retorna config atualizado.
- [ ] Smoke USB + BT verdes.

## Arquivos tocados

- `src/hefesto/daemon/lifecycle.py`
- `src/hefesto/daemon/ipc_server.py`
- `tests/unit/test_daemon_reload.py` (novo)

## Notas para o executor

- `replace(dataclass_instance, **kwargs)` é da `dataclasses` stdlib — aceita override parcial.
- **Pegada rápida**: `reload_config` deve ser **rápido** (<100ms). Rebuildando `HotkeyManager` é barato (só troca uma instância Python); mouse device pode levar 50ms.
- Ao rebuildar hotkey durante um "hold" de PS+dpad_up (usuário com combo pressionado no momento do reload), o novo manager perde o estado — usuário precisa soltar e pressionar de novo. Documentar.
- Atualizar comentário no BRIEF A-08 marcando como resolvido.
