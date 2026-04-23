# VALIDATOR_BRIEF.md — Hefesto-DualSense_Unix

Referência canônica para validador-sprint. Invariantes, contratos de runtime, armadilhas conhecidas e padrões do projeto. Atualizar quando uma sprint descobre algo novo.

---

## [CORE] Identidade do projeto

- **Nome:** Hefesto — port PT-BR do DualSenseX (Paliverse) para Linux.
- **Raiz:** `/home/andrefarias/Desenvolvimento/Hefesto-DualSense_Unix`.
- **Tipo:** `daemon+cli+tui+gui` (Python 3.10+). Capacidades visuais: `gui` (GTK3) + `tui` (Textual).
- **Branch principal:** `main`.
- **Stack:** Python 3.10, pydualsense, textual, typer, pydantic v2, python-xlib, evdev, structlog, PyGObject (GTK3), python-uinput (extra).
- **Entry points:** `hefesto` (CLI), `hefesto-gui` (GTK3), `python -m hefesto`.

---

## [CORE] Hierarquia de regras (em conflito, obedecer nesta ordem)

1. `~/.config/zsh/AI.md` v4.0 — regras universais.
2. `~/.claude/CLAUDE.md` — extensões: meta-regras 9.6–9.8, validação visual 13–14, ciclo de sprint §15.
3. `docs/process/HEFESTO_DECISIONS_V2.md` — patches 1–11 consolidados.
4. `docs/process/HEFESTO_DECISIONS_V3.md` — deltas V3-1 a V3-8.
5. `docs/process/HEFESTO_PROJECT.md` — visão do produto, 8 waves, 26 sprints.
6. `AGENTS.md` — protocolo do repo (anonimato, idioma, estrutura `docs/`).

---

## [CORE] Contratos de runtime

Executor que chegar em sessão nova sem `.venv/bin/pytest` acessível DEVE rodar `bash scripts/dev-setup.sh` antes de qualquer gate. Execução cega é violação de L-21-4.

Toda sprint runtime obriga execução destes comandos como proof-of-work:

```bash
# Preparação de ambiente (idempotente; rápido se .venv/ viva)
bash scripts/dev-setup.sh

# Smoke USB (2s) — FakeController
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke

# Smoke BT (2s) — FakeController
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt

# Testes unitários
.venv/bin/pytest tests/unit -v --no-header -q

# Lint + types
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto

# Anonimato (obrigatório pré-commit)
./scripts/check_anonymity.sh
```

Esperado no smoke: `poll.tick >= 50` em 2s a 30Hz; `battery.change.emitted >= 1`; sem traceback no stderr.

---

## [CORE] Capacidades visuais aplicáveis

Projeto tem **GUI (GTK3)** e **TUI (Textual)**. Sprints que tocam `src/hefesto/app/**`, `src/hefesto/tui/**`, `src/hefesto/gui/*.glade`, CSS/QSS ou templates obrigam captura visual via skill `validacao-visual`.

Pipeline canônico (preferir nesta ordem):

1. **CLI X11** (pré-autorizado em settings.json): `scrot`, `import`, `xdotool`, `wmctrl`, `ffmpeg`, `sha256sum`.
2. **claude-in-chrome MCP** — só se a sprint for validada via navegador.
3. **playwright MCP** — apps dev locais.

Para GUI GTK3, comando canônico:
```bash
.venv/bin/python -m hefesto.app.main &
sleep 3
WID=$(xdotool search --name "Hefesto v" | head -1)
TS=$(date +%Y%m%dT%H%M%S)
xdotool windowactivate "$WID" && sleep 0.4
import -window "$WID" "/tmp/hefesto_gui_<area>_${TS}.png"
sha256sum "/tmp/hefesto_gui_<area>_${TS}.png"
```

Proof-of-work visual obriga: PNG absoluto + sha256 + descrição multimodal (3-5 linhas cobrindo elementos, acentuação PT-BR, contraste, comparação antes/depois).

---

## [CORE] Invariantes de arquitetura

- **IPC socket path:** `$XDG_RUNTIME_DIR/hefesto/hefesto.sock` via `hefesto.utils.xdg_paths.ipc_socket_path()`. Cliente e servidor usam o mesmo ponto de verdade.
- **UDP compat DSX:** `127.0.0.1:6969`, JSON schema em `docs/protocol/udp-schema.md`.
- **JSON-RPC 2.0** em NDJSON UTF-8 sobre Unix socket. 10 métodos canônicos: `profile.switch`, `profile.list`, `trigger.set`, `trigger.reset`, `led.set`, `rumble.set`, `daemon.status`, `daemon.state_full`, `controller.list`, `daemon.reload`.
- **Perfil fallback** (`fallback.json`) tem `priority: -1000` e matcher universal. Autoswitch cai nele quando nenhum outro bate.
- **PT-BR obrigatório** em código, comentários, docs, commits, logs `INFO`+. EN preservado em `errno`, flags POSIX, identificadores de protocolo.
- **Acentuação PT-BR obrigatória** — todo arquivo tocado pela sprint passa por varredura de acentuação periférica. Não aceitar `funcao`, `validacao`, `comunicacao`, `configuracao`, `descricao`, etc.
- **Zero emojis gráficos** (Emoji_Presentation block: U+1F000+, U+2600+ coloridos). **Glyphs Unicode de estado** (U+25CF BLACK CIRCLE, U+25CB WHITE CIRCLE, U+25AE/AF block elements, box drawing) **são permitidos e devem ser preservados** — fazem parte da UI textual funcional.
- **Limite de request IPC:** `MAX_PAYLOAD_BYTES = 32_768` em `src/hefesto/daemon/ipc_server.py`. Requests maiores são rejeitados com erro JSON-RPC `-32600`. Ajuste defensivo (HARDEN-IPC-PAYLOAD-LIMIT-01).

---

## [CORE] Armadilhas conhecidas (atualizar quando sprint descobrir nova)

### A-01: `IpcServer.start()` / `stop()` com `unlink()` cego — **RESOLVIDA**
Local original: `src/hefesto/daemon/ipc_server.py:79-80` e `:94-95`.
Risco: dois processos daemon compartilhando o mesmo socket_path se destroem mutuamente. Reproduzido 2026-04-21: daemon systemd em execução teve seu socket apagado por `./run.sh --smoke`, deixando a GUI órfã mostrando "daemon offline" apesar de `systemctl is-active = active`.
Fix aplicado: método `_probe_socket_and_cleanup()` em `src/hefesto/daemon/ipc_server.py:126-157`. Antes de qualquer `unlink`, tenta `socket.connect` com timeout 100ms; se conexão aceita, levanta `SocketInUseError` (não apaga); só remove arquivo órfão de socket morto. Chamado em `start()` linha 116. Auditado em AUDIT-V2-COMPLETE-01 (2026-04-23).

### A-02: `udp_server.py` AssertionError a cada startup — **RESOLVIDA**
Local original: `src/hefesto/daemon/udp_server.py:106`.
Código antigo: `assert isinstance(transport, asyncio.DatagramTransport)`. Em Python 3.10, o objeto real `_SelectorDatagramTransport` não passa o isinstance check para a classe pública `asyncio.DatagramTransport`. Traceback no journal a cada startup.
Fix aplicado: `src/hefesto/daemon/udp_server.py:112`. Assert removido; atribuição direta com `# type: ignore[assignment]` e comentário referenciando `BUG-UDP-01 / A-02`. Auditado em AUDIT-V2-COMPLETE-01 (2026-04-23).

### A-03: Smoke compartilha socket path com daemon de produção — **RESOLVIDA (indireto)**
Local: `run.sh:52-78` + `src/hefesto/utils/xdg_paths.py:52-53`.
Risco original: decorre de A-01; smoke poderia destruir socket de daemon vivo.
Status: risco concreto de destruição mútua está fechado pela resolução de A-01 — probe ativo impede apagar socket em uso. Isolamento via env `HEFESTO_IPC_SOCKET_NAME` não foi implementado (opcional, não mais crítico). Auditado em AUDIT-V2-COMPLETE-01 (2026-04-23).

### A-04: Diff working-tree 2026-04-21 removeu glyphs Unicode de estado
Local: `src/hefesto/app/actions/{status,daemon,emulation}_actions.py`, `src/hefesto/tui/widgets/__init__.py`, `tests/unit/test_tui_widgets.py`, `docs/process/HEFESTO_PROJECT.md`, `docs/process/HEFESTO_DECISIONS_V2.md`.
Risco: interpretação errada de "zero emojis" strippou BLACK/WHITE CIRCLE (U+25CF/U+25CB) dos markups Pango, zerou `BatteryMeter._icon_for_level` (retorna `""` para todos os níveis) e adaptou o teste para esconder a regressão (viola meta-regras 9.2 e 9.6). Docs perderam `HEAVY CHECK MARK` / `CROSS MARK` sem substituição por texto.
Fix canônico: reverter os `*_actions.py` e `tui/widgets/__init__.py` ao HEAD~0 pré-diff; nos docs, substituir por texto "OK" / "ERRADO". **RESOLVIDA** pela sprint UX-HEADER-01 em 2026-04-21.

### A-05: USB autosuspend derruba DualSense durante polling
Local: kernel Linux com `CONFIG_USB_RUNTIME_PM=y` (default Pop!_OS/Ubuntu/Fedora).
Risco: suspende device USB inativo após ~2s. Gamepad em polling HID a 60-120 Hz perde conexão transiente; hidraw devolve `ENODEV`; daemon entra em reconnect loop; GUI mostra "daemon offline" ou "tentando reconectar" com controle fisicamente ligado.
Fix canônico: aplicar `assets/72-ps5-controller-autosuspend.rules` via `install_udev.sh`. Regra força `power/control=on` e `power/autosuspend_delay_ms=-1` para `054c:0ce6` e `054c:0df2` no subsystem=usb. Ver sprint USB-POWER-01. Trazido de projeto irmão (desbloqueador Switch) onde a gotcha foi primeiro documentada.

### A-06: Campo novo em `LedsConfig`/`TriggersConfig`/`RumbleConfig` precisa sprint-par de profile-apply
Local: `src/hefesto/profiles/manager.py:85-93` (`_to_led_settings`) e `apply()` :62-70.
Risco: sprint adiciona campo ao pydantic schema e aos 4 JSONs de `assets/profiles_default/`, mas `_to_led_settings()` (ou equivalente para triggers/rumble) só lê um subconjunto fixo de campos. Campo novo vira letra morta no autoswitch/profile.switch. Detectado em FEAT-LED-BRIGHTNESS-01 (2026-04-21): `lightbar_brightness` chegou ao schema, JSON e GUI, mas `_to_led_settings` não propagou ao `LedSettings` → RGB bruto foi ao hardware ignorando perfil.
Fix canônico: toda spec que adiciona campo a `*Config` DEVE incluir na lista de critérios a alteração do mapper correspondente (`_to_led_settings`, `build_from_name`, etc.) e teste de integração `test_profile_manager.py` que valide propagação ao controller via mock. Planejador-sprint passa a considerar "profile-apply propagation" item obrigatório.
**RESOLVIDA para `lightbar_brightness`** (FEAT-LED-BRIGHTNESS-02 + FEAT-LED-BRIGHTNESS-03, 2026-04-22): `_to_led_settings` agora propaga `lightbar_brightness` → `LedSettings.brightness_level`; `apply_led_settings` escala RGB antes de enviar ao hardware; handler GUI usa `_pending_brightness` transiente; `_build_profile_from_editor` inclui brightness no JSON salvo; `_refresh_lightbar_from_state` sincroniza slider com guard anti-loop. Testes: `test_apply_propaga_brightness`, `test_apply_brightness_maximo_nao_escala`, `tests/unit/test_lightbar_persist.py` (7 testes).
**RESOLVIDA para `player_leds`** (BUG-PLAYER-LEDS-APPLY-01, 2026-04-23): `_to_led_settings` já propagava para `LedSettings.player_leds` desde FEAT-PLAYER-LEDS-APPLY-01, porém `apply_led_settings` só chamava `set_led` e `set_mic_led` — `set_player_leds` ficou fora. Fix: `apply_led_settings` agora invoca `controller.set_player_leds(settings.player_leds)` ao final. Sintoma antes do fix: perfil com `player_leds` definido no JSON aparecia marcado na GUI mas o hardware mantinha configuração antiga (os 5 LEDs nunca refletiam o perfil carregado). Testes: `test_apply_propaga_player_leds_ao_controller`, `test_apply_propaga_player_leds_todos_apagados`, `test_activate_propaga_player_leds` em `tests/unit/test_profile_manager.py`; 4 testes de propagação em `TestApplyLedSettings` cobrindo os 4 cenários canônicos (todos on/off, padrão alternado, default). Também adicionado botão "Aplicar LEDs" dedicado no glade (`player_leds_apply`) + handler `on_player_leds_apply` para reemitir bitmask atual sob demanda.

### A-07: Wire-up de novo subsistema do Daemon precisa 3 pontos sincronizados
Local: `src/hefesto/daemon/lifecycle.py` — `run()`, `_poll_loop()`, `_shutdown()`.
Risco: sprint adiciona novo subsystem (HotkeyManager, MouseDevice, AutoSwitcher) mas esquece de um dos 3 pontos canônicos. Detectado em FEAT-HOTKEY-STEAM-01 iter.1: `_on_ps_solo` foi definido no HotkeyManager, testes do manager isolado passaram, mas `Daemon` nunca instanciou o manager nem chamou `observe()` no poll loop — hotkey morreu antes de existir em produção.
Fix canônico: toda sprint de subsystem novo DEVE ter seção "wire-up no Daemon" nos critérios de aceite listando (1) slot no dataclass `Daemon`, (2) método `_start_<subsys>()` chamado em `run()` antes do `await self._stop_event.wait()`, (3) consumo no `_poll_loop()` se aplicável, (4) zeragem no `_shutdown()`. Teste obrigatório: `test_start_<subsys>_instancia_e_executa_callback` que construa `Daemon` com config real e dispare o callback, provando que a instância é alcançável via `daemon._<subsys>`.

### A-08: Closure em `_start_<subsys>` captura `config` por alias — reload quebra silenciosamente
Local: `src/hefesto/daemon/lifecycle.py:269-270` (padrão) — `action = self.config.ps_button_action; command = self.config.ps_button_command`.
Risco: `daemon.reload` futuro substitui `self.config = NewConfig(...)`, mas closures já capturadas continuam apontando para os valores antigos. Bug latente: `action="steam"` no disco, mas hotkey ainda dispara o custom antigo.
Fix canônico: capturar `cfg = self.config` no outer e ler `cfg.field` **dentro** da closure, não fora. Mesmo assim, se reload faz `self.config = novo`, ainda quebra — melhor resolver via hot-reload do HotkeyManager (`_stop_hotkey_manager() + _start_hotkey_manager()`) quando IPC `daemon.reload` existir. Registrar no planejamento de V1.2 `daemon.reload`.
**RESOLVIDA** pela sprint REFACTOR-DAEMON-RELOAD-01 (2026-04-22): `_on_ps_solo` lê `self.config` em runtime (não em closure); método `reload_config(new_config)` implementado — substitui `self.config`, rebuilda HotkeyManager via `_stop_hotkey_manager + _start_hotkey_manager`, reage se `mouse_emulation_enabled` mudou; handler IPC `daemon.reload` implementado com validação de campos desconhecidos e retorno do novo config serializado. Testes: `tests/unit/test_daemon_reload.py` (10 cenários).

### A-09: Múltiplos consumidores de `_evdev.snapshot()` por tick — **RESOLVIDA**
Local original: `src/hefesto/daemon/lifecycle.py:176-181` (hotkey) e `:328-332` (mouse).
Risco: cada subsystem novo que precisa ler botões físicos via evdev snapshot duplica o custo por tick. Antes: 2 consumidores → 2 snapshots/tick (120/s a 60Hz quando ambos ativos).
Fix aplicado (REFACTOR-HOTKEY-EVDEV-01, 2026-04-22): método `_evdev_buttons_once() -> frozenset[str]` extraído em `Daemon`. Chamado 1× em `_poll_loop` antes dos consumidores; resultado injetado via parâmetro em `_dispatch_mouse_emulation(state, buttons_pressed)` e passado diretamente a `_hotkey_manager.observe(buttons_pressed, now=tick_started)`. Teste: `tests/unit/test_poll_loop_evdev_cache.py` (5 cenários) confirma exatamente 1 snapshot/tick com 0, 1 ou 2 consumidores ativos. Novos consumidores (FEAT-HOTKEY-MIC-01 etc.) devem receber `buttons_pressed` como parâmetro — não relendo evdev internamente.

### A-12: PyGObject ausente no `.venv` sem `--with-tray`
Local: `scripts/dev_bootstrap.sh`, `run.sh`, `scripts/dev-setup.sh`.
Risco: `.venv/bin/python -m hefesto.app.main` falha com `ModuleNotFoundError: No module named 'gi'` quando bootstrap rodou sem `--with-tray`. O `run.sh` contorna invocando `/usr/bin/python3` que tem `python3-gi` do sistema, mas validação visual via `.venv` quebra. Detectado em BUG-GUI-DAEMON-STATUS-INITIAL-01 (2026-04-23): executor precisou injetar `PYTHONPATH` apontando para `/usr/lib/python3/dist-packages` para reproduzir o bug.
Fix canônico (sprint INFRA-VENV-PYGOBJECT-01): `dev-setup.sh` valida `gi` importável pelo `.venv/bin/python` e, quando ausente, imprime instrução literal (`bash scripts/dev_bootstrap.sh --with-tray` ou `apt install python3-gi libgirepository-1.0-dev + pip install -e ".[tray]"`). README menciona a decisão opt-in.

### A-11: Race de udev ADD disparando unit oneshot 2x em <200ms
Local: `assets/73-ps5-controller-hotplug.rules` + `assets/hefesto-gui-hotplug.service`.
Risco: o plug USB do DualSense gera múltiplos eventos `ACTION=="add"` em <200ms (interface USB + filhos hidraw). Guard `pgrep -f hefesto.app.main` na unit oneshot é race-prone — dois eventos em paralelo entram antes do 1º processo ser visível. Resultado: 2 GUIs sobem; a 2ª (takeover "última vence" do single_instance) mata a 1ª → efeito visual de "tray abre e fecha". Reportado em 2026-04-22 pelo usuário após instalar v1.0.0 + BUG-MULTI-INSTANCE-01.
Fix canônico (sprint BUG-TRAY-SINGLE-FLASH-01): remover guard `pgrep`; `HefestoApp.__init__` usa novo `acquire_or_bring_to_front("gui", ...)` (modelo "primeira vence") em vez de `acquire_or_takeover`. Predecessor vivo é trazido ao foco via `xdotool windowactivate` ou SIGUSR1 handler; nova GUI sai com rc 0. Daemon continua com `acquire_or_takeover` porque ali "última vence" é desejado.

### A-10: Múltiplas instâncias de daemon/GUI concorrendo por hardware
Local: `src/hefesto/daemon/main.py` (run_daemon), `src/hefesto/app/app.py` (HefestoApp.__init__), `install.sh` (passos 6-7), `assets/hefesto.service` + `assets/hefesto-gui-hotplug.service` + udev rule 73.
Risco: cinco fontes independentes de spawn sem mutex (install.sh restart + hotplug unit + udev ADD + launcher GUI + ensure_daemon_running da GUI) geram 2+ daemons concorrentes. Cada daemon cria seu próprio `UinputMouseDevice` e ambos emitem REL_X/REL_Y → cursor "voando" ao ativar o toggle Mouse. Matar processo via monitor não basta — `Restart=on-failure RestartSec=2` respawna em ≤2s, dando sensação de "PID novo aparece cada vez". Reportado pelo usuário em 2026-04-22 após rodar install/uninstall.
Fix canônico (sprint BUG-MULTI-INSTANCE-01, 2026-04-22):
  - `src/hefesto/utils/single_instance.py`: `acquire_or_takeover(name)` via `fcntl.flock` em `$XDG_RUNTIME_DIR/hefesto/<name>.pid`. Modelo "última vence" — envia `SIGTERM` ao predecessor (grace 2s, poll 50ms), escala `SIGKILL` se necessário.
  - `run_daemon` e `HefestoApp.__init__` chamam `acquire_or_takeover("daemon")` e `acquire_or_takeover("gui")` no topo.
  - `assets/hefesto.service`: `SuccessExitStatus=143 SIGTERM` (takeover não dispara respawn) + `StartLimitIntervalSec=30 StartLimitBurst=3` em `[Unit]`.
  - `install.sh` passos 6-7 viram opt-in (default NÃO). Flags `--enable-autostart`, `--enable-hotplug-gui`.
  - `HefestoApp.quit_app`: chama `systemctl --user stop hefesto.service` antes de `Gtk.main_quit()` — "Sair" do tray encerra GUI + daemon.
  - `ensure_daemon_running`: antes de disparar `systemctl start`, verifica pid file via `is_alive()` para não duplicar spawn.
  - `uninstall.sh`: após systemctl stop+disable, `pkill -TERM` em `hefesto\.app\.main` e `hefesto daemon start` com grace 2s + `pkill -KILL` residual.

---

## [PROCESS] Lições acumuladas por ciclo

Regras de metodologia descobertas durante sprints anteriores. Planejador/executor/validador leem esta seção como trilho permanente. Auditor de release revisa: lições violadas geram achado.

### L-21-1: Spec com gate massivo exige dry-run ANTES do spec
Origem: CHORE-ACENTUACAO-STRICT-HOOK-01 (V2.1). Sprint previu 3-10 falsos-positivos; explodiu em 267. Regra: quando sprint instala gate novo (pre-commit, CI check, linter), rodar o dry-run contra a base inteira **antes** de escrever o spec e dimensionar whitelist/correção em massa com número real, não estimativa. Se dry-run excede 10 ocorrências, spec inclui mini-commit "chore: <tema> pré-existente" como etapa separada.

### L-21-2: Bug vira sprint só após reprodução em árvore limpa
Origem: BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01 (V2.1). Spec foi escrito com base em diff sujo do working tree, sem `git stash` + teste isolado. Quando testado em HEAD limpo, não reproduziu. Regra: antes de abrir spec de bug, rodar `git stash && git checkout <HEAD>` e anexar ao spec o diff do comando-bug executado em árvore limpa. Se não reproduziu, sprint é **investigativa**, não de fix.

### L-21-3: Ler o código-chave ANTES de escrever spec
Origem: PROFILE-DISPLAY-NAME-01 → SUPERSEDED por PROFILE-SLUG-SEPARATION-01 (V2.1). Planejador assumiu que `Profile.name` era ASCII e escreveu spec de `display_name`; `Profile.name` já era acentuado e o problema era oposto (filename colidindo com defaults). Regra: todo spec que toca um módulo lista em "Contexto" os trechos lidos (arquivo:linha) que confirmam a premissa. Sem leitura, planejador não pode escrever sobre o módulo.

### L-21-4: Toda sessão nova valida `.venv` antes de rodar sprints
Origem: AUDIT-V2-COMPLETE-01 (V2.1). Auditor rodou sem `.venv/` pronto e confiou em "último baseline verde". Débito silencioso. Regra: primeiro passo de executor em sessão nova é `bash scripts/dev-setup.sh` (ou `pip install -e ".[dev]" + .venv/bin/pytest --collect-only`). Execução cega é violação.

### L-21-5: Paralelo de subagents só com pool <50% usado
Origem: sessão release V2.1 (V2.1). 4 subagents em paralelo com pool ~80% usado: 2 foram rate-limited, zero ganho de velocidade. Regra: antes de disparar N subagents, estimar tokens/minuto ativos (sessão + agents em voo). Se pool >50%, serializar. Paralelo de 3+ só em pool fresco (<30%).

### L-21-6: "Protocolo escrito" ≠ "Executado"
Origem: HARDWARE-VALIDATION-PROTOCOL-01, FEAT-FIRMWARE-UPDATE-PHASE1-01 (V2.1). Sprints marcadas MERGED sem execução humana dos 21 itens / metodologia. Regra: sprint cujo entregável é **apenas** documento/protocolo/checklist ganha status `PROTOCOL_READY` (não MERGED) até registro formal de ≥1 execução humana. Release notes diferenciam sprints MERGED (código executado) de PROTOCOL_READY (doc pronto).

---

## [CORE] Padrões de código

- `from __future__ import annotations` em arquivos novos.
- Logging via `structlog` sempre: `from hefesto.utils.logging_config import get_logger; logger = get_logger(__name__)`. Nunca `print()`.
- Paths via `pathlib.Path` + `hefesto.utils.xdg_paths`. Nunca hardcoded absolutos.
- Testes unitários em `tests/unit/`, um arquivo por módulo. Padrão de nome: `test_<modulo>.py`.
- Limite: 800 linhas por arquivo (exceto configs/registries/testes).
- Docstrings curtas em PT-BR.

---

## [CORE] Protocolo anti-débito (meta-regra 9.7)

Achado colateral → **Edit-pronto** OU **sprint-nova com ID**. Nunca "issue depois", "TODO", "seria bom revisar", "pré-existente fora escopo". Executor-sprint que encontrar achado colateral auto-dispatcha `planejador-sprint` para gerar sprint nova com ID próprio.

---

## [CORE] Canônicos pós-fix

Após cada sprint de correção, atualizar este brief:
- Se nova armadilha foi descoberta → adicionar em `[CORE] Armadilhas conhecidas`.
- Se contrato de runtime mudou → atualizar comandos em `[CORE] Contratos de runtime`.
- Se invariante foi quebrada intencionalmente → registrar em `docs/process/discoveries/`.

---

*"A forja não revela o ferreiro. Só a espada."*

---

**Rodapé de enriquecimento**

- 2026-04-21T21:15Z — modo VALIDATE — validação FEAT-LED-BRIGHTNESS-01. Adicionada armadilha A-06 (campo novo de perfil exige sprint-par em `_to_led_settings`/mappers). Detectada na revisão: `lightbar_brightness` salvo em schema e 4 JSONs mas ignorado no `ProfileManager.apply()`. Sprints-filhas abertas: FEAT-LED-BRIGHTNESS-02 (profile-apply propaga brightness) e FEAT-LED-BRIGHTNESS-03 (handler GUI persiste valor no state).
- 2026-04-22T00:25Z — modo VALIDATE — validação FEAT-HOTKEY-STEAM-01 iter.2/3. APROVADO_COM_RESSALVAS. Iter.1 falhou por wire-up ausente no Daemon (só manager isolado, sem instância). Iter.2 corrigiu: `_hotkey_manager` slot no dataclass, `_start_hotkey_manager()` chamado em `run()`, `observe()` chamado em `_poll_loop` lendo `_evdev.snapshot().buttons_pressed`, zerado em `_shutdown()`. Adicionadas 3 armadilhas: A-07 (wire-up de subsystem precisa 3 pontos sincronizados), A-08 (closure captura config por alias quebra reload), A-09 (snapshot evdev duplicado por tick). Ressalvas: ramo `action="custom"` com `command=[]` é silenciado sem log (IMPORTANTE, Edit pronto); sprint nova REFACTOR-HOTKEY-EVDEV-01 proposta para deduplicar snapshot.
- 2026-04-22T — sprints FEAT-LED-BRIGHTNESS-02 + FEAT-LED-BRIGHTNESS-03 executadas (consolidadas). `lightbar_brightness` agora propaga end-to-end: schema → `_to_led_settings` → `LedSettings.brightness_level` → `apply_led_settings` (escala RGB) → hardware. GUI: `_pending_brightness` transiente, guard `_refresh_guard` em `on_lightbar_brightness_changed`, `_refresh_lightbar_from_state` sincroniza slider do state_full, `_build_profile_from_editor` inclui brightness no perfil salvo. Armadilha A-06 marcada como RESOLVIDA para brightness. 450 testes (4 skipped por hardware). Smoke USB+BT verdes.
- 2026-04-22T — sprint BUG-MULTI-INSTANCE-01 executada. Usuário reportou cursor "voando" ao ativar toggle Mouse + PIDs renascendo ao matar processo. Raiz: 5 fontes de spawn sem mutex. Fix: módulo `single_instance` (flock + SIGTERM→SIGKILL "última vence"), wire-up em `run_daemon` e `HefestoApp.__init__`, unit hardening (SuccessExitStatus=143, StartLimit 3/30s), install.sh opt-in (prompts default N), quit_app para daemon via systemctl stop, uninstall.sh com pkill residual. Armadilha A-10 adicionada. Testes: `test_single_instance.py` (6) + `test_quit_app_stops_daemon.py` (4). Proof-of-work runtime pendente de hardware real conectado.
- 2026-04-22T — sprint REFACTOR-HOTKEY-EVDEV-01 executada.
- 2026-04-23T — sprint BUG-PLAYER-LEDS-APPLY-01 executada. Usuário reportou "LEDs do jogador não possuem botão de aplicar e não funcionam quando eu deixo marcado". Diagnóstico: H1 PARCIAL (faltava botão dedicado), H2 OK (handler IPC `led.player_set` funcional), H3 CONFIRMADO BUG (`apply_led_settings` não propagava `player_leds` ao controller — armadilha A-06 latente), H4 OK (backend pydualsense usa `PlayerID(bitmask)`). Fix: (1) `apply_led_settings` chama `controller.set_player_leds(settings.player_leds)`; (2) botão "Aplicar LEDs" adicionado em `main.glade`; (3) handler `on_player_leds_apply` em `lightbar_actions.py`; (4) registro em `app.py`. Testes: +7 (998 passed). Validação runtime: IPC `led.player_set` OK contra daemon systemd real com USB conectado; proof-of-work end-to-end com FakeController confirmando cadeia `ProfileManager.apply → apply_led_settings → set_player_leds`. A-06 marcada RESOLVIDA também para player_leds.
- 2026-04-22T — sprint REFACTOR-DAEMON-RELOAD-01 executada. Armadilha A-08 RESOLVIDA. `_on_ps_solo` lê `self.config` em runtime. `reload_config(new_config)` implementado em `Daemon`: salva config, rebuilda HotkeyManager, reage a mouse_emulation_enabled se mudou. Handler IPC `daemon.reload` implementado com override parcial via `dataclasses.replace`, validação de campos desconhecidos, retorno do novo config via `asdict`. `test_ipc_server.py::test_daemon_reload` adaptado para nova semântica (sem daemon -> erro limpo). 10 novos testes em `tests/unit/test_daemon_reload.py`. Suite: 782 passed. Smoke USB+BT verdes. Deduplicação de `_evdev.snapshot()` por tick em `lifecycle.py`. Método `_evdev_buttons_once()` extraído; `_poll_loop` chama 1× e injeta `buttons_pressed` nos consumidores via parâmetro. `_dispatch_mouse_emulation` recebe `buttons_pressed: frozenset[str]` em vez de reler evdev internamente. Armadilha A-09 marcada RESOLVIDA. Teste: `tests/unit/test_poll_loop_evdev_cache.py` (5 cenários) — confirma 1 snapshot/tick independente de número de consumidores ativos.
