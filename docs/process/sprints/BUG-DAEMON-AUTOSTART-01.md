# BUG-DAEMON-AUTOSTART-01 — Daemon não inicia automaticamente ao abrir a GUI

**Tipo:** fix (UX crítico).
**Wave:** V1.1.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** issue [#68](https://github.com/AndreBFarias/hefesto/issues/68) — fechada por PR com `Closes #68` no body.

## Sintoma

Usuário abre a GUI (via launcher ou menu de aplicativos) — header mostra "○ Daemon Offline". Precisa clicar manualmente no botão "Reiniciar Daemon" na aba Daemon para subir. Espera razoável: daemon deve estar ativo antes mesmo da janela aparecer (ou subir no ato).

## Diagnóstico provável

A unit `hefesto.service` é `WantedBy=graphical-session.target`. Em ambientes GNOME/Pop!_OS, `graphical-session.target` ativa ao login. Portanto o daemon deveria estar ativo desde o início da sessão. Hipóteses:

1. Unit não está `enabled` após o `install.sh` — `systemctl --user enable hefesto.service` pode não estar rodando.
2. Unit falha no primeiro boot por socket-resto (armadilha A-01), fica em `failed`, `Restart=on-failure` dá até 3 tentativas e para.
3. `After=graphical-session.target` ordena mas não garante ativação paralela.

Segundo vetor: a GUI, ao abrir, pode tentar conectar no IPC e falhar (daemon morto), mostrar offline, mas não DISPARAR o start do daemon. Solução adicional: no bootstrap da GUI, se `detect_installed_unit() is not None` e `systemctl is-active hefesto.service != active`, disparar `systemctl --user start hefesto.service` em thread worker (silencioso, 5s timeout). Se falhar, fallback para estado OFFLINE padrão.

## Critérios de aceite

- [ ] `scripts/install_udev.sh` e `install.sh` confirmam `systemctl --user enable hefesto.service` no final.
- [ ] `src/hefesto/app/app.py` no bootstrap (`run()` antes do `show()`) chama helper novo `ensure_daemon_running()` em thread worker via `_get_executor()`:
  - Verifica `detect_installed_unit()`; se `None`, não faz nada (usuário sem service instalado).
  - Chama `systemctl --user is-active hefesto.service`; se não `active`, dispara `systemctl --user start hefesto.service` com timeout 5s.
  - Nunca bloqueia a thread GTK; falha silenciosa com `logger.warning`.
- [ ] Teste manual: fechar GUI, `systemctl --user stop hefesto.service`, reabrir GUI. Header deve mostrar "Tentando Reconectar" inicialmente e migrar para "Conectado Via USB" em até 5s sem intervenção.
- [ ] `assets/hefesto.service` mantém `After=graphical-session.target` e ganha também `Wants=hefesto.service` ou equivalente para encorajar auto-start.
- [ ] `.venv/bin/pytest tests/unit -q` verde.

## Proof-of-work

```bash
systemctl --user stop hefesto.service
.venv/bin/python -m hefesto.app.main &
sleep 6
systemctl --user is-active hefesto.service   # esperado: active
# Header da GUI deve estar verde (● Conectado Via USB)
```

## Arquivos tocados (previsão)

- `src/hefesto/app/app.py` (ensure_daemon_running no bootstrap)
- `src/hefesto/app/actions/daemon_actions.py` (helper reutiliza função)
- `install.sh` (garantir enable)

## Notas para o executor

- Não causar loop: se o `start` falhar 2x seguidas no bootstrap, parar de tentar até a próxima abertura da GUI.
- Preservar idempotência — reabrir várias vezes não deve enfileirar comandos systemctl.
