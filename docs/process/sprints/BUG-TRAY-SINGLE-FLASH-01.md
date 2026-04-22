# BUG-TRAY-SINGLE-FLASH-01 — GUI abre e fecha imediatamente ao plugar o DualSense

**Tipo:** fix (UX crítico).
**Wave:** V1.1 — fase 5 (pós BUG-MULTI-INSTANCE-01).
**Estimativa:** 1 iteração.
**Dependências:** BUG-MULTI-INSTANCE-01 (já mergeado — depende do módulo `single_instance`).

---

**Tracking:** issue a criar (referência: issue #68 família). Body deve fechar a issue nova via `Closes #<N>`.

## Sintoma (reportado pelo usuário em 2026-04-22)

> Ao conectar depois de instalar eu vejo no tray que o programa tenta abrir mas é fechado imediatamente.

Hefesto-GUI aparece no tray ~200ms, depois desaparece. O daemon continua rodando — só a janela da GUI some.

## Diagnóstico

Após BUG-MULTI-INSTANCE-01 (2026-04-22), `HefestoApp.__init__` faz `acquire_or_takeover("gui")` — modelo "última vence": nova invocação manda SIGTERM na anterior. O problema:

1. Usuário pluga o DualSense. udev rule `73-ps5-controller-hotplug.rules` dispara `hefesto-gui-hotplug.service` (unit oneshot) que executa `~/.local/bin/hefesto-gui`.
2. `hefesto-gui` faz `setsid nohup ./run.sh &` — **duas vezes** em <200ms porque o udev ADD dispara uma vez pro subsystem `usb` e outra pra `hidraw`/filhos.
3. GUI1 sobe, registra `gui.pid`.
4. GUI2 sobe 100ms depois, detecta GUI1 no lock, manda SIGTERM — GUI1 morre.
5. Efeito visual: "abriu e fechou".

A unit `hefesto-gui-hotplug.service` tinha um guard `pgrep -f 'hefesto.app.main'` (antes de BUG-MULTI-INSTANCE-01), mas é race-prone: dois eventos udev em <100ms pulam o guard.

Confirmar cadeia com:

```bash
journalctl --user -u hefesto-gui-hotplug.service --since "10 min ago" --no-pager
```

## Decisão

Mudar o modelo de single-instance **APENAS para a GUI** para **"primeira vence, nova traz a existente ao foco"** (decisão do usuário em 2026-04-22).

Motivo: a GUI é presentacional; "matar a anterior" só faz sentido se o usuário EXPLICITAMENTE pediu outra GUI (não via race de udev). Para daemon, "última vence" continua porque corrige o bug original (duas instâncias disputando hardware).

### API nova em `single_instance.py`

```python
def acquire_or_bring_to_front(name: str, bring_to_front_cb: Callable[[int], None]) -> int | None:
    """Modelo 'primeira vence'.

    Se predecessor vivo, chama `bring_to_front_cb(predecessor_pid)` e retorna None
    (caller deve sair com exit 0). Se predecessor morto ou ausente, adquire o lock
    normalmente e retorna `os.getpid()`.
    """
```

`HefestoApp` passa callback que localiza a janela via `xdotool search --pid <pid>` (X11) ou `wmctrl -lxp | grep <pid>` e ativa via `xdotool windowactivate` / `wmctrl -ia`. Se não encontra janela (processo sem X), fallback pra SIGUSR1 (trata-se de pedido de "show window" — a GUI escuta SIGUSR1 e faz `self.show_window()`).

Daemon continua usando `acquire_or_takeover`.

## Critérios de aceite

- [ ] `src/hefesto/utils/single_instance.py`: adicionar `acquire_or_bring_to_front(name, bring_to_front_cb)`. `acquire_or_takeover` preservado intacto (daemon ainda usa).
- [ ] `src/hefesto/app/app.py`: `HefestoApp.__init__` substitui `acquire_or_takeover("gui")` por:
  ```python
  pid = acquire_or_bring_to_front("gui", bring_to_front_cb=_activate_window_by_pid)
  if pid is None:
      sys.exit(0)  # trouxe anterior ao foco, sai limpo
  ```
- [ ] `src/hefesto/app/app.py`: nova função `_activate_window_by_pid(predecessor_pid: int) -> None` usa `subprocess.run(["xdotool", "search", "--pid", str(pid)])` → pega WID → `windowactivate`. Fallback SIGUSR1 via `os.kill(pid, SIGUSR1)`.
- [ ] `src/hefesto/app/app.py`: `HefestoApp.__init__` instala handler SIGUSR1 que chama `GLib.idle_add(self.show_window)` — permite "trazer ao foco" quando xdotool não achar.
- [ ] `assets/hefesto-gui-hotplug.service:10`: **remover** o guard `pgrep -f` (virou redundante). ExecStart vira:
  ```
  ExecStart=%h/.local/bin/hefesto-gui
  ```
  O próprio launcher delega pro `acquire_or_bring_to_front` — se houve race, a 2ª invocação simplesmente traz a 1ª ao foco.
- [ ] Teste `tests/unit/test_single_instance.py`: novo `test_bring_to_front_chama_callback` — primeiro fork adquire; segundo detecta, chama callback com pid do 1º, **não manda SIGTERM**, retorna None.
- [ ] Proof-of-work runtime:
  ```bash
  .venv/bin/python -m hefesto.app.main &
  GUI1=$!
  sleep 3
  .venv/bin/python -m hefesto.app.main &
  GUI2=$!
  sleep 3
  # Esperado: GUI1 ainda vivo, GUI2 morreu (exit 0)
  kill -0 $GUI1 && echo "GUI1 OK"
  kill -0 $GUI2 2>/dev/null && echo "FALHA GUI2 vivo" || echo "GUI2 saiu limpo"
  ```

## Arquivos tocados (previsão)

- `src/hefesto/utils/single_instance.py` (+ função + callback type)
- `src/hefesto/app/app.py` (+ `_activate_window_by_pid`, + SIGUSR1 handler)
- `assets/hefesto-gui-hotplug.service` (remover guard pgrep)
- `tests/unit/test_single_instance.py` (+ teste `bring_to_front`)

## Proof-of-work visual

1. Tray já mostra Hefesto.
2. Clicar no ícone do Hefesto no menu de aplicativos duas vezes rapidamente. Esperado: janela existente vem pro foco, não surge uma 2ª.
3. Fechar janela (X — close-to-tray). Clicar no ícone do menu novamente. Esperado: janela reaparece (via SIGUSR1 handler).
4. Desplugar e replugar o DualSense. Esperado: janela aparece UMA vez e fica aberta (ou reaparece em foco se já estava aberta).
5. Screenshot + sha256 após cada passo.

## Notas para o executor

- `xdotool search --pid <pid>` pode retornar múltiplos WIDs (janela principal + tray). Filtrar pelo primeiro com título contendo "Hefesto".
- Fallback SIGUSR1 é necessário porque Wayland puro não responde a xdotool. Em Wayland a detecção de janela é por portal XDG (V1.2 — FEAT-COSMIC-WAYLAND-01).
- **Não remover `acquire_or_takeover`** — daemon continua usando.
- Se o predecessor está vivo mas "zumbi" (ex.: processo travado no GTK main loop), SIGUSR1 pode não responder. Nesse caso, após 2s sem resposta, executar takeover como fallback. Parametrizar: `acquire_or_bring_to_front(name, cb, fallback_takeover_after_sec=2.0)`.

## Armadilha candidata A-11 (proposta)

> A-11: race de udev ADD disparando unit oneshot 2x em <200ms. Guard `pgrep` insuficiente. Fix canônico: single-instance via flock (módulo `single_instance`) em vez de guard external.
