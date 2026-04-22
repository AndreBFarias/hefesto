# Jornada: o caso do cursor que voava

**Data:** 2026-04-22.
**Sprint:** BUG-MULTI-INSTANCE-01.
**Autor:** sessão Claude a serviço do projeto Hefesto.

---

## 1. O sintoma

Usuário instalou v1.0.0 (`install.sh` + `uninstall.sh` + `install.sh` de novo pra polir UX), plugou o DualSense, abriu a GUI. Aba Mouse com toggle **desligado**: cursor não se move (esperado).

Ligou o toggle. Cursor começa a voar diagonalmente pela tela, sem estímulo do stick. Usuário tenta matar o processo `hefesto` no monitor do sistema — some um, outro nasce com PID novo. Repete 5+ vezes, sempre aparece PID diferente. Sem conseguir conter, reinicia o PC.

Ao religar, abre monitor antes de tudo, filtra "hefesto", e observa o mesmo padrão: PIDs renascendo cada vez que mata um.

## 2. Por que o cursor voava

Investigação mostrou **duas fontes de geração de uinput** rodando concorrentes. O daemon Hefesto tem:

```python
# src/hefesto/daemon/lifecycle.py
def _start_mouse_emulation(self) -> bool:
    if self._mouse_device is not None:
        return True  # idempotência DENTRO do mesmo processo
    ...
    self._mouse_device = UinputMouseDevice(...)
    self._mouse_device.start()
```

A idempotência é **local ao processo**. Duas instâncias do daemon vivas → dois `UinputMouseDevice` virtuais criados → o kernel vê 2 dispositivos "Hefesto Virtual Mouse+Keyboard", cada um recebendo `dispatch(state)` a 60Hz.

Como ambos leem o mesmo estado bruto do DualSense via evdev (`/dev/input/event24`) e ambos aplicam escala `mouse_speed` + direção do stick, o cursor recebe REL_X e REL_Y **em dobro**. Com stick mesmo em repouso e pequeno drift (LY=123, RY=127 em vez de 128), o drift amplificado duplamente move o cursor continuamente.

## 3. Por que os PIDs renasciam

Cinco fontes de spawn sem mutex:

1. **`install.sh` passo 6** executava `systemctl --user restart hefesto.service`. A unit tinha `Restart=on-failure RestartSec=2` e `WantedBy=graphical-session.target` — permanentemente enabled.
2. **`install.sh` passo 7** copiava e habilitava `hefesto-gui-hotplug.service` (oneshot), ativada em cada login gráfico e em cada `ACTION=="add"` do USB DualSense via udev rule.
3. **A própria GUI** (`HefestoApp.show` → `ensure_daemon_running`) chamava `systemctl --user start hefesto.service` no bootstrap (sprint BUG-DAEMON-AUTOSTART-01). Proteção local: contador `<=2` tentativas. Global: zero.
4. **`~/.local/bin/hefesto-gui`** fazia `setsid nohup ./run.sh &` sem checar se outra GUI estava viva.
5. **Unit hotplug-gui**: `ExecStart=/bin/sh -c "pgrep -f 'hefesto.app.main' >/dev/null || %h/.local/bin/hefesto-gui"`. O guard `pgrep` é race-prone — dois eventos udev em <100ms pulam.

Efeito conjunto: matar um processo com `kill -TERM` no monitor era suficiente pro systemd respawnar em até 2s via `Restart=on-failure`. Se o usuário plugou/replugou o DSX no processo, udev dispara novo hotplug. A sensação de "aparece outro PID" era literal.

## 4. A solução

Modelo **"última vence"** via `fcntl.flock` em pid files + SIGTERM(2s)→SIGKILL no predecessor. Detalhes:

```python
# src/hefesto/utils/single_instance.py

def acquire_or_takeover(name: str) -> int:
    path = runtime_dir() / f"{name}.pid"
    predecessor = _read_existing_pid(path)
    if predecessor is not None and predecessor != os.getpid():
        if is_alive(predecessor):
            _terminate_predecessor(predecessor)  # SIGTERM 2s → SIGKILL
        # pid órfão sobrescreve sem matar

    fd = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # com retry 2s se EWOULDBLOCK
    os.ftruncate(fd, 0)
    os.write(fd, f"{os.getpid()}\n".encode("ascii"))
    _HELD_LOCKS[name] = fd  # impede GC
    return os.getpid()
```

Wire-up mínimo:

```python
# src/hefesto/daemon/main.py
from hefesto.utils.single_instance import acquire_or_takeover
acquire_or_takeover("daemon")   # antes de build_controller

# src/hefesto/app/app.py:HefestoApp.__init__
acquire_or_takeover("gui")
```

Hardening da unit systemd:

```ini
[Unit]
StartLimitIntervalSec=30
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=2
SuccessExitStatus=143 SIGTERM   # takeover não dispara respawn
```

`install.sh` passos 6-7 viram opt-in com default **NÃO**. Flags `--enable-autostart`, `--enable-hotplug-gui`.

`HefestoApp.quit_app` encerra daemon junto:

```python
subprocess.run(
    ["systemctl", "--user", "stop", "hefesto.service"],
    capture_output=True, timeout=5, check=False,
)
Gtk.main_quit()
```

`uninstall.sh` faz `pkill -TERM → pkill -KILL` residual.

## 5. A prova

Teste runtime com hardware real (em 2026-04-22):

```
D1=28035 vivo → pid file 28035
D2=28066 sobe → single_instance_takeover_iniciado predecessor_pid=28035
                → single_instance_predecessor_saiu_sigterm (em 50ms)
                → pid file 28066
                → D2 reanexa /dev/input/event24
D1 morto (SuccessExitStatus=143 impede respawn)

Mouse toggle ligado:
  1 único "Hefesto Virtual Mouse+Keyboard" no sistema
  Cursor delta em 2.5s com stick parado: 0, 0
  Bug resolvido.
```

Suite de testes: **412 passed, 4 skipped**. Armadilhas catalogadas: **A-10** (múltiplas instâncias) e **A-11** (race udev ADD) no `VALIDATOR_BRIEF.md`.

## 6. Lições

1. **Idempotência local não protege contra instâncias paralelas.** Toda vez que um subsistema toca recurso exclusivo (uinput, hidraw, UDP bind, socket IPC), precisa de mutex entre processos — não só dentro do processo.
2. **`Restart=on-failure` é facão sem punho.** Sem `SuccessExitStatus` cobrindo SIGTERM, qualquer mecanismo de shutdown limpo vira respawn involuntário. Sem `StartLimitBurst`, loops infinitos. A unit da v1.0 tinha só `Restart=on-failure RestartSec=2`.
3. **udev `ACTION=="add"` dispara múltiplas vezes por plug.** USB physical + hidraw + input são subsystems diferentes, cada um gera ADD. Guard por `pgrep` é inadequado. Resolver via lock no processo filho, não na unit.
4. **Opt-in > opt-out em software que toca hardware compartilhado.** Default do install.sh v1.0 ligava tudo automaticamente. Um usuário que nem queria auto-start foi forçado a múltiplos pontos de spawn. Default silencioso evita pegadinha.
5. **"Sair" do tray deve significar sair de tudo.** Usuário clica Sair esperando fechar. Se o daemon continua vivo em background, é invasivo.

## 7. Arquivo resultante

- `src/hefesto/utils/single_instance.py` (novo, ~180 linhas).
- `src/hefesto/daemon/main.py` (+2 linhas).
- `src/hefesto/app/app.py` (+ takeover, + quit_app com stop).
- `src/hefesto/app/actions/daemon_actions.py` (+ `_daemon_pid_alive`).
- `src/hefesto/daemon/service_install.py` (+ `enable: bool = False`).
- `src/hefesto/cli/app.py` (+ `--enable` flag).
- `assets/hefesto.service` (hardening).
- `install.sh` (opt-in passos 6-7).
- `uninstall.sh` (pkill residual).
- `VALIDATOR_BRIEF.md` (armadilhas A-10, A-11).
- `tests/unit/test_single_instance.py` (novo, 6 testes).
- `tests/unit/test_quit_app_stops_daemon.py` (novo, 4 testes).
- `tests/unit/test_service_install.py` (atualizado).

## 8. Ramificações

O feedback subsequente do usuário na mesma sessão (2026-04-22 tarde) gerou **22 novas specs de sprint** em `docs/process/sprints/` — de polish UI (tema Drácula, SVGs originais, rodapé global) a features (Player LEDs reais, presets de trigger, política de rumble com modo Auto), a plataformas (`.deb`, pesquisa de firmware updater). `SPRINT_ORDER.md` agrupa em 3 waves com ordem paralelizável.

Um dos achados dessa onda — **"GUI abre e fecha imediatamente ao plugar"** — decorre diretamente da escolha "última vence" pra GUI. Sprint **BUG-TRAY-SINGLE-FLASH-01** reverte pra **"primeira vence"** só na GUI (daemon continua "última vence"). Nova função `acquire_or_bring_to_front(name, cb)` com callback que traz janela existente ao foco via xdotool/SIGUSR1.

---

*Relato preservado conforme meta-regra 9.6 (evidência empírica antes de fix) e meta-regra 9.8 (validação runtime-real obrigatória para sprints que tocam daemon).*
