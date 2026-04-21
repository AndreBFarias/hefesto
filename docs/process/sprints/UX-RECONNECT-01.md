# UX-RECONNECT-01 — Reconnect automático da GUI + feedback "tentando reconectar"

**Tipo:** feat (UX, melhoria).
**Wave:** fora de wave (correção de promessa "daemon sempre online").
**Estimativa:** 1 iteração de executor.
**Dependências:** **BUG-IPC-01 e UX-HEADER-01 devem estar mergeados antes.** Esta sprint estende os markups restaurados pela UX-HEADER-01 e confia na detecção de socket vivo da BUG-IPC-01 para evitar flicker.

---

## Contexto

Pedido direto do usuário em 2026-04-21: "o daemon sempre deve ficar online ao abrir o app". Hoje, quando a GUI abre e o daemon não está pronto (ex.: socket recém-deletado, systemd reiniciando, controle desconectado), o header mostra apenas "daemon offline" em vermelho, sem sinal de esperança. O usuário não sabe se basta esperar, se precisa clicar em algo, se deve reiniciar o serviço.

O objetivo da sprint é transformar a GUI em **cliente IPC resiliente**:

1. Polling IPC em background a cada **2s**. Se `daemon.state_full` responde, header mostra "conectado"; se falha, mostra "tentando reconectar…" durante 6s antes de desistir e mostrar "daemon offline".
2. Botão **"reiniciar daemon"** na aba Daemon, executando `systemctl --user restart hefesto.service` via subprocess. Útil quando o socket morreu e o systemd ainda não detectou.
3. Estado visual do header — três fases:
   - **Conectado:** `● conectado via <transport>` (verde, U+25CF).
   - **Tentando reconectar:** `◐ tentando reconectar...` (amarelo/laranja, U+25D0 CIRCLE WITH LEFT HALF BLACK — intermediário semântico).
   - **Offline persistente:** `○ daemon offline` (vermelho, U+25CB).

---

## Arquitetura do polling

A GUI GTK3 roda em thread principal GLib. Polling usa `GLib.timeout_add_seconds(2, callback)` que já está presente em outras partes da GUI. A chamada IPC passa por `hefesto.app.ipc_bridge.daemon_state_full()` (síncrona, já existe).

Estados rastreados em `StatusActionsMixin`:
- `_consecutive_failures: int` — incrementa a cada `None` retornado, zera em sucesso.
- `_reconnect_threshold: int = 3` — 3 falhas consecutivas (= 6s) antes de passar de "reconectando" para "offline".

Transição de estado (máquina simples):

```
INITIAL / ONLINE → (IPC fail) → RECONNECTING (1..3 tentativas) → (falha persistente) → OFFLINE
OFFLINE → (IPC ok) → ONLINE
RECONNECTING → (IPC ok) → ONLINE
```

---

## Critérios de aceite

- [ ] `src/hefesto/app/actions/status_actions.py` — adicionar `_reconnect_state: str` (um de `"online"`, `"reconnecting"`, `"offline"`) e `_consecutive_failures: int`. Método novo `_update_reconnect_state(state_full: dict | None)` muda o estado e chama o renderer apropriado.
- [ ] Três renderers:
  - `_render_online(state)` — já existe (restaurado pela UX-HEADER-01), mantido.
  - `_render_reconnecting()` — novo: `'<span foreground="#d90">◐ tentando reconectar...</span>'`.
  - `_render_offline()` — já existe, chamado somente após `_consecutive_failures >= 3`.
- [ ] `src/hefesto/app/app.py` ou `main.py` — registrar `GLib.timeout_add_seconds(2, self._poll_daemon_tick)` no `_on_activate` / `__init__`. O tick chama `ipc_bridge.daemon_state_full()` e delega para `StatusActionsMixin._update_reconnect_state`.
- [ ] `src/hefesto/app/actions/daemon_actions.py` — adicionar botão **"reiniciar daemon"** na aba Daemon. Handler roda `subprocess.run(["systemctl", "--user", "restart", "hefesto.service"], timeout=10)`. Trata `CalledProcessError` (service não instalado) e `FileNotFoundError` (systemd ausente) com `logger.error` + `Gtk.MessageDialog` informativo. O botão fica **desabilitado** se `detect_installed_unit()` retornar `None`.
- [ ] `src/hefesto/gui/main.glade` — adicionar o botão na aba Daemon (label "Reiniciar daemon", id `btn_restart_daemon`). Se `main.glade` for editado por Cambalache, registrar no diff apenas o nó novo.
- [ ] Unit test em `tests/unit/test_status_actions_reconnect.py` (novo): cobre máquina de estado (INITIAL→ONLINE, ONLINE→RECONNECTING→OFFLINE, RECONNECTING→ONLINE).
- [ ] Proof-of-work visual: captura de três estados (online, reconnecting, offline) com sha256sum. Estado "reconnecting" induzido por `systemctl --user stop hefesto.service` enquanto a GUI está aberta.
- [ ] Todos os testes unitários verdes (≥291 após BUG-IPC-01 já mergeado).
- [ ] `./scripts/check_anonymity.sh` verde.

---

## Proof-of-work esperado

```bash
# 1. Daemon ON → GUI abre mostrando "● conectado via <transport>"
systemctl --user start hefesto.service
sleep 2
.venv/bin/python -m hefesto.app.main &
sleep 4
WID=$(xdotool search --name "Hefesto v" | head -1)
TS=$(date +%Y%m%dT%H%M%S)
import -window "$WID" "/tmp/hefesto_ux_reconnect_online_${TS}.png"
sha256sum "/tmp/hefesto_ux_reconnect_online_${TS}.png"

# 2. Daemon para → GUI mostra "◐ tentando reconectar..."
systemctl --user stop hefesto.service
sleep 3   # dentro do threshold (3 ticks x 2s = 6s)
TS=$(date +%Y%m%dT%H%M%S)
import -window "$WID" "/tmp/hefesto_ux_reconnect_tentando_${TS}.png"
sha256sum "/tmp/hefesto_ux_reconnect_tentando_${TS}.png"

# 3. Após threshold → GUI mostra "○ daemon offline"
sleep 6
TS=$(date +%Y%m%dT%H%M%S)
import -window "$WID" "/tmp/hefesto_ux_reconnect_offline_${TS}.png"
sha256sum "/tmp/hefesto_ux_reconnect_offline_${TS}.png"

# 4. Botão Reiniciar daemon (aba Daemon)
xdotool key --window "$WID" ctrl+6   # vai para aba Daemon
# click no botão (coord depende do glade) → daemon volta → estado ONLINE após 2s
systemctl --user is-active hefesto.service   # esperado: active
TS=$(date +%Y%m%dT%H%M%S)
import -window "$WID" "/tmp/hefesto_ux_reconnect_restored_${TS}.png"
sha256sum "/tmp/hefesto_ux_reconnect_restored_${TS}.png"

pkill -f hefesto.app.main

# 5. Unit + lint
.venv/bin/pytest tests/unit -q
./scripts/check_anonymity.sh
.venv/bin/ruff check src/ tests/
```

**Aritmética esperada:**
- 4 PNGs `online`, `tentando`, `offline`, `restored` com sha256 distintos.
- Máquina de estado: ao desligar daemon, 1ª a 3ª tick (0-6s) mostram `◐ tentando reconectar...`. Na 4ª tick (~8s), troca para `○ daemon offline`. Ao religar daemon (via botão ou externo), primeira tick pós-restart volta para `● conectado via <transport>`.
- Testes: 289+ (BUG-IPC-01) + 1 novo = ≥292 passing.

---

## Arquivos tocados (previsão)

- `src/hefesto/app/actions/status_actions.py` — máquina de estado + renderer reconnecting.
- `src/hefesto/app/actions/daemon_actions.py` — handler do botão restart.
- `src/hefesto/app/app.py` (ou `main.py`, onde estão os signals) — registro do `GLib.timeout_add_seconds`.
- `src/hefesto/gui/main.glade` — botão "Reiniciar daemon" na aba Daemon.
- `tests/unit/test_status_actions_reconnect.py` — novo.

---

## Fora de escopo

- Notificações de sistema (libnotify) quando o daemon reconecta — feature futura.
- Histórico de estados (log na aba Daemon) — feature futura.
- Auto-start do service se nunca foi instalado — já é responsabilidade do `install.sh`.
- Polling em frequência alta (>0.5Hz) — desnecessário, custa CPU e acorda HID em sleep.

---

## Notas para o executor

- Se `detect_installed_unit()` em `src/hefesto/daemon/lifecycle.py` (ou onde vive hoje) retornar `None`, o botão fica desabilitado com tooltip "serviço hefesto.service não instalado — rode install.sh".
- O caractere `◐` (U+25D0) é Geometric Shape (não emoji) — preservável via `VALIDATOR_BRIEF.md` A-04.
- `subprocess.run([...], timeout=10)` — passar args como lista, nunca `shell=True`.
- Se descobrir que `GLib.timeout_add_seconds` já está sendo usado para outro poll, reaproveitar a timer e compor o tick, não criar segunda timer.
