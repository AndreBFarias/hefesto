# AUDIT-FINDING-WAYLAND-PORTAL-PERF-01 — Migrar `WaylandPortalBackend` para thread de longa vida

**Origem:** achado 11 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** S (≤3h). **Severidade:** médio.
**Tracking:** label `type:performance`, `ai-task`, `status:ready`.

## Contexto

`src/hefesto/integrations/window_backends/wayland_portal.py:56-89` cria `ThreadPoolExecutor(max_workers=1)` + `asyncio.run(_async())` a cada chamada de `get_active_window_info`. O `AutoSwitcher` chama 2 Hz em compositor Wayland puro. Overhead: ~5-10ms por chamada (criação/tear-down de loop + thread). Aceitável em escala atual, mas sinal de alerta.

## Objetivo

Duas opções:

**(a)** Usar `jeepney` síncrono direto na thread do autoswitch (já bloqueia a 500ms — o overhead de asyncio.run não é necessário). Eliminar o wrapper ThreadPoolExecutor.

**(b)** Se `dbus-fast` é preferido, criar uma thread de longa vida no `WaylandPortalBackend.__init__` com queue de requests — cada chamada enfileira e aguarda result. Loop asyncio reutilizável.

Recomendação: **(a)** — mais simples, menos concorrência, mesmo throughput em 2 Hz.

## Critérios de aceite

- [ ] `_try_dbus_fast` removido OU refatorado para thread persistente (se opção b).
- [ ] `_try_jeepney` continua funcional com timeout explícito adicionado (`conn.send_and_get_reply(msg, timeout=2.0)` se suportado pelo jeepney, ou wrapper com threading.Timer).
- [ ] Nenhum `ThreadPoolExecutor` novo por chamada de `get_active_window_info`.
- [ ] Teste em `tests/unit/test_window_backends.py`: confirma que o backend não cria threads/loops novos em múltiplas chamadas (mock jeepney/dbus_fast).
- [ ] Cov de `integrations/window_backends/wayland_portal.py` sobe de 21% para ≥60%.
- [ ] Suite completa segue verde; ruff + mypy limpos.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
.venv/bin/pytest tests/unit/test_window_backends.py -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/pytest tests/unit --cov=src/hefesto/integrations/window_backends/wayland_portal.py --cov-report=term-missing -q
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
# Runtime (opcional, só em Wayland puro):
# HEFESTO_WAYLAND=1 python3 -c "
# from hefesto.integrations.window_backends.wayland_portal import WaylandPortalBackend
# b = WaylandPortalBackend()
# import time; t0 = time.monotonic()
# for _ in range(10): b.get_active_window_info()
# print('10 chamadas em', (time.monotonic()-t0)*1000, 'ms')
# "
# Esperado: < 100ms para 10 chamadas (< 10ms por call)
```

## Fora de escopo

- Suporte a compositors que não expõem `org.freedesktop.portal.Window` — GNOME 46+ / COSMIC 1.0+ é o target.
- Cache de resultado entre chamadas (desktop não muda de janela em < 100ms usually) — sprint futura de otimização maior.
- Migrar para `aiofd`+epoll nativo — overkill para este caso.
