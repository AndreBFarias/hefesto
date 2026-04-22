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

Toda sprint runtime obriga execução destes comandos como proof-of-work:

```bash
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

---

## [CORE] Armadilhas conhecidas (atualizar quando sprint descobrir nova)

### A-01: `IpcServer.start()` / `stop()` com `unlink()` cego
Local: `src/hefesto/daemon/ipc_server.py:79-80` e `:94-95`.
Risco: dois processos daemon compartilhando o mesmo socket_path se destroem mutuamente. Reproduzido 2026-04-21: daemon systemd em execução teve seu socket apagado por `./run.sh --smoke`, deixando a GUI órfã mostrando "daemon offline" apesar de `systemctl is-active = active`.
Fix canônico: antes de `unlink()`, tentar conectar temporariamente; só deletar se falhar (socket morto).

### A-02: `udp_server.py:106` AssertionError a cada startup
Local: `src/hefesto/daemon/udp_server.py:106`.
Código: `assert isinstance(transport, asyncio.DatagramTransport)`. Em Python 3.10, o objeto real `_SelectorDatagramTransport` não passa o isinstance check para a classe pública `asyncio.DatagramTransport`. Traceback no journal a cada startup; não impede o listen, mas polui logs de produção.
Fix canônico: remover o assert ou trocar por `if transport is None: ...`.

### A-03: Smoke compartilha socket path com daemon de produção
Local: `run.sh:52-78` + `src/hefesto/utils/xdg_paths.py:52-53`.
Risco: decorre de A-01. Smoke deveria usar socket isolado (ex.: nome parametrizável via env `HEFESTO_IPC_SOCKET_NAME`).

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
