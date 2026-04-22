# BUG-DAEMON-STATUS-MISMATCH-01 — Painel Daemon mostra "failed" com daemon vivo

**Tipo:** fix (UX / clareza).
**Wave:** V1.1 — fase 5.
**Estimativa:** 1 iteração.
**Dependências:** BUG-MULTI-INSTANCE-01 (depende do pid file produzido por `single_instance`).

---

**Tracking:** issue a criar.

## Sintoma (reportado em 2026-04-22)

> fala que não iniciou o autostart ou daemon tá confuso. Fora isso na aba de status fala que o daemon tá online

Captura evidencia:
- Header do topo: `● Conectado Via USB` (verde) — IPC respondeu, daemon vivo.
- Aba Daemon: `Status: ● failed (auto-start: enabled)` — systemd diz que a unit falhou.

A aba Daemon mostra o estado **da unit systemd** (`systemctl --user is-active`), que pode estar em `failed` porque o daemon foi iniciado **fora do systemd** (ex.: via CLI `hefesto daemon start --foreground`, ou via takeover por outra GUI). Não há mentira — os dois estados são verdadeiros, mas a apresentação é confusa.

## Diagnóstico

`src/hefesto/app/actions/daemon_actions.py:238-248` (`_refresh_daemon_view`) consulta `systemctl --user is-active` e escreve o label. Não consulta IPC nem pid file. Resultado: usuário vê "failed" mesmo com IPC funcionando perfeitamente.

O bug **é cosmético** (não quebra funcionalidade), mas mina confiança. Precisamos apresentar os 3 estados possíveis de forma clara:

| systemd | IPC/pid | Apresentação correta |
|---|---|---|
| `active` | vivo | `● Online (gerenciado pelo systemd)` verde |
| `inactive` ou `failed` | vivo | `● Online (processo avulso, sem systemd)` amarelo — indica que o daemon está rodando mas fora do auto-restart |
| `active` | morto | `● Iniciando...` amarelo — transitório |
| `inactive` ou `failed` | morto | `○ Offline` vermelho |
| `active` | vivo E unit auto-start habilitado | `● Online (systemd + auto-start)` verde |

## Decisão

Refatorar `_refresh_daemon_view` em `daemon_actions.py` para consultar **3 fontes**:

1. `systemctl --user is-active hefesto.service` → `systemd_active: bool`.
2. `systemctl --user is-enabled hefesto.service` → `systemd_enabled: bool`.
3. `hefesto.utils.single_instance.is_alive(pid_from_file)` → `process_alive: bool`.

E pintar o label com a matriz acima. Mensagem explícita em PT-BR, sem jargão `is-active`.

## Critérios de aceite

- [ ] `src/hefesto/app/actions/daemon_actions.py`:
  - Método novo `_daemon_status() -> Literal["online_systemd", "online_avulso", "iniciando", "offline"]`.
  - `_refresh_daemon_view` usa `_daemon_status()` + label amigável em PT-BR.
  - Cores: verde (online_systemd), amarelo (online_avulso, iniciando), vermelho (offline).
  - Tooltip no label explica o que cada estado significa (hover).
- [ ] Switch `Auto-start` (daemon_autostart_switch) reflete `systemd_enabled` sempre (independente de vivo/morto). Continua funcionando: toggle chama `systemctl --user enable|disable` em thread worker.
- [ ] `Status: ● Online (processo avulso)` oferece botão secundário "Migrar para systemd" que roda `systemctl --user start hefesto.service` **após** enviar SIGTERM ao processo avulso via pid file (reutiliza takeover).
- [ ] Teste `tests/unit/test_daemon_status_matrix.py`: monkeypatch `_systemctl_oneline` + `is_alive` + `pid_file.read_text` cobre as 4 combinações principais.
- [ ] Proof-of-work runtime:
  ```bash
  # Cenário 1: systemd + vivo
  systemctl --user start hefesto.service
  # GUI deve mostrar "Online (systemd + auto-start)" ou "(systemd)"

  # Cenário 2: avulso
  systemctl --user stop hefesto.service
  .venv/bin/hefesto daemon start --foreground &
  # GUI deve mostrar "Online (processo avulso)"

  # Cenário 3: offline
  systemctl --user stop hefesto.service
  pkill hefesto
  # GUI deve mostrar "Offline"
  ```

## Arquivos tocados

- `src/hefesto/app/actions/daemon_actions.py`
- `src/hefesto/gui/main.glade` (+ botão "Migrar para systemd")
- `tests/unit/test_daemon_status_matrix.py` (novo)

## Notas para o executor

- `_daemon_status()` consulta IPC via `daemon.status` com timeout 1s. Se IPC timeout, assume `process_alive=False`.
- Label no header do topo (`●/○ Conectado Via USB`) é **outra coisa**: reflete `ControllerState.connected` (hardware), não estado do daemon. Não confundir.
- "Migrar para systemd" só aparece se `online_avulso`. Se já é `online_systemd`, oculto.
- Pid file path: `runtime_dir() / "daemon.pid"`. Usar helpers de `single_instance.is_alive`.
