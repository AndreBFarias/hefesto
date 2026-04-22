# REFACTOR-HOTKEY-EVDEV-01 — Deduplicar `_evdev.snapshot()` por tick

**Tipo:** refactor (dívida técnica).
**Wave:** V1.1 — fase 5.
**Estimativa:** XS (30min).
**Dependências:** nenhuma.

---

**Tracking:** issue a criar. Origem: armadilha **A-09** em `VALIDATOR_BRIEF.md`.

## Contexto

`src/hefesto/daemon/lifecycle.py` hoje tem **2 consumidores** de `_evdev.snapshot()` por tick:

- `:191-197` (hotkey manager lê `buttons_pressed`).
- `:347-355` (mouse emulation lê `buttons_pressed`).

Cada snapshot custa ~0.3ms (syscall de ioctl + parse). A 60Hz com mouse ON + hotkey = **120 snapshots/s** → ~36ms/s só em evdev. Barato, mas multiplica a cada novo subsystem (FEAT-HOTKEY-MIC-01 vai adicionar o 3º consumidor).

## Decisão

Extrair `_evdev_snapshot_cached` no `_poll_loop` que lê 1x por tick e passa via parâmetro pros consumidores.

```python
async def _poll_loop(self) -> None:
    while not self._is_stopping():
        tick_started = loop.time()
        state = await self._run_blocking(self.controller.read_state)

        # Single snapshot per tick — reusado pelos subsystems.
        buttons_pressed = self._evdev_buttons_once()

        self.store.update_controller_state(state)
        self.bus.publish(EventTopic.STATE_UPDATE, state)
        self.store.bump("poll.tick")

        if self._mouse_device is not None:
            self._dispatch_mouse_emulation(state, buttons_pressed)

        if self._hotkey_manager is not None:
            self._hotkey_manager.observe(buttons_pressed, now=tick_started)

        ...

def _evdev_buttons_once(self) -> frozenset[str]:
    """Snapshot dos botões físicos via evdev — cached-per-tick."""
    evdev = getattr(self.controller, "_evdev", None)
    if evdev is None or not evdev.is_available():
        return frozenset()
    try:
        return frozenset(evdev.snapshot().buttons_pressed)
    except Exception as exc:
        logger.debug("evdev_snapshot_falhou", err=str(exc))
        return frozenset()
```

Assinatura de `_dispatch_mouse_emulation` muda para aceitar `buttons_pressed: frozenset[str]` em vez de recuperar sozinha.

## Critérios de aceite

- [ ] `src/hefesto/daemon/lifecycle.py`:
  - Método novo `_evdev_buttons_once() -> frozenset[str]`.
  - `_poll_loop` chama 1x e passa.
  - `_dispatch_mouse_emulation(state, buttons_pressed)`.
  - Remove a lógica duplicada de ler snapshot dentro de `_dispatch_mouse_emulation` e do consumer de hotkey.
- [ ] Teste `tests/unit/test_poll_loop_evdev_cache.py`: fake controller com `_evdev` mock. Roda 10 ticks. Confirma que `snapshot()` foi chamado exatamente 10 vezes (não 20).
- [ ] Smoke USB + BT continuam verdes (`poll.tick >= 50`).

## Arquivos tocados

- `src/hefesto/daemon/lifecycle.py`
- `tests/unit/test_poll_loop_evdev_cache.py` (novo)

## Notas para o executor

- Cuidado com ordem: `buttons_pressed` é usado DEPOIS de `read_state` mas os subsystems assumem estado congruente. Como `_evdev.snapshot()` é um canal **independente** de `controller.read_state`, pode haver leve skew (até um frame). Aceitável — é assim hoje também.
- Se futuramente adicionar 4º+ consumidor (ex.: botão Mic via #90), basta receber `buttons_pressed` como argumento.
- Atualizar comentário no `VALIDATOR_BRIEF.md` A-09 marcando como **resolvido** na coluna de status.

## Armadilha correlacionada

- Resolve A-09 formalmente.
- Não introduz A-11 nova (se surgir algo, documentar).
