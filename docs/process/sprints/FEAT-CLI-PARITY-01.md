# FEAT-CLI-PARITY-01 — Paridade CLI com features novas da GUI

**Tipo:** feat (CLI).
**Wave:** V1.1.
**Estimativa:** 1 iteração.
**Dependências:** FEAT-LED-BRIGHTNESS-01 e FEAT-MOUSE-01 mergeadas no `main`.

---

**Tracking:** issue [#79](https://github.com/AndreBFarias/hefesto/issues/79) — fechada por PR com `Closes #79` no body.

## Contexto

`hefesto` CLI (typer) expõe subcomandos `status`, `battery`, `led`, `profile`, `trigger`, `daemon`, `emulate`. Com features novas da GUI (luminosidade LED, emulação mouse, botão reiniciar daemon), a CLI precisa de paridade para scripts/headless users que não abrem a GUI.

## Decisão

Adicionar/estender subcomandos:

```bash
# Luminosidade
hefesto led --brightness 50                      # 50%
hefesto led --color '#ff8800' --brightness 80    # cor + brightness

# Mouse
hefesto mouse on  [--speed 6] [--scroll-speed 1]
hefesto mouse off
hefesto mouse status                             # enabled=true, speed=6...

# Daemon restart (irmão de start/stop)
hefesto daemon restart                           # systemctl user restart hefesto.service

# Perfil: aplicar draft
hefesto profile apply --file draft.json          # aplica JSON sem salvar
hefesto profile save <nome> --from-active         # snapshot do perfil ativo para novo nome
```

Tudo via IPC — reaproveita handlers do daemon, não duplica lógica.

## Critérios de aceite

- [ ] `src/hefesto/cli/cmd_led.py`: flag `--brightness INT` (0-100), validação.
- [ ] `src/hefesto/cli/cmd_mouse.py` (NOVO): subcomandos `on`, `off`, `status`.
- [ ] `src/hefesto/cli/cmd_daemon.py`: `restart` wraps `systemctl --user restart`.
- [ ] `src/hefesto/cli/cmd_profile.py`: `apply --file`, `save <nome> --from-active`.
- [ ] Testes unitários `tests/unit/test_cli_*.py` cobrindo os novos comandos com mocks de IPC.
- [ ] `docs/usage/cli.md` atualizado com os novos comandos.
- [ ] Tab completion via typer (já existe) pega os novos subcomandos automaticamente.

## Arquivos tocados (previsão)

- `src/hefesto/cli/cmd_led.py`
- `src/hefesto/cli/cmd_mouse.py` (novo)
- `src/hefesto/cli/cmd_daemon.py`
- `src/hefesto/cli/cmd_profile.py`
- `src/hefesto/cli/app.py` (registrar mouse app)
- `tests/unit/test_cli_led_brightness.py` (novo)
- `tests/unit/test_cli_mouse.py` (novo)
- `tests/unit/test_cli_profile_apply.py` (novo)
- `docs/usage/cli.md`

## Fora de escopo

- Rearquitetura da CLI (continua typer).
- Interactive mode (`hefesto repl`).
- Suporte a múltiplos controles via CLI (V2).

## Notas

- Erros de IPC devem mostrar mensagem clara ao usuário (não traceback).
- `hefesto mouse status` retorna JSON se `--json` flag presente (scriptabilidade).
