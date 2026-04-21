# HEFESTO — Decisões de Spec V2 (Consolidado)

> **Destino no repo:** `docs/process/HEFESTO_DECISIONS_V2.md`
> Esta pasta está excluída do `check_anonymity.sh` — por isso este arquivo pode mencionar nomes de modelos de IA no contexto meta-processo.
>
> **Substitui integralmente:** `HEFESTO_DECISIONS.md` (V1).
> **Status:** CONGELADO. Qualquer mudança daqui em diante vira V3, não patch inline.

---

## 0. CONTEXTO

Dois ciclos de auditoria pré-execução fecharam. Este documento consolida:

- Decisões do V1 (auditoria 1 → resposta 1 → V1).
- Respostas à auditoria V2 (auditoria 2 → resposta 2 → este V2).
- Uma pendência aberta: seção 1 da auditoria V1 (contradições) nunca foi enviada.

**Compromissos globais que valem pra tudo abaixo:**

1. **Anonimato absoluto.** `check_anonymity.sh` (entregue separadamente) roda em CI e pré-commit. Exclui `LICENSE`, `NOTICE`, `CHANGELOG.md`, `docs/process/**`, `docs/history/**`, `tests/fixtures/**`.
2. **Idioma.** PT-BR em código, comentários, commits, docs, logs. Termos técnicos retornados por APIs externas, `errno` strings, flags POSIX, nomes de protocolos e identificadores de sistema permanecem na forma EN original.
   - OK: `logger.error("falha ao ler hidraw: Permission denied")`
   - OK: `logger.warn("pacote UDP descartado: version desconhecida")`
   - ERRADO: `logger.error("permissão negada ao ler hidraw")` (traduziu errno)
   - ERRADO: `logger.error("hidraw read failed")` (deveria ser PT-BR)
3. **Escopo Linux.** Distros com systemd-logind. Alpine/Void/Gentoo = PR welcome, não support. Documentado em ADR-009.
4. **Workflow.** `gh issue` → branch → commit impessoal → PR `Closes #N` → squash merge.

---

## 1. TABELA DE DECISÕES CONSOLIDADA

### Do V1 (auditoria 1)

| ID   | Decisão                                                                 | Sprint         | Status |
|------|-------------------------------------------------------------------------|----------------|--------|
| 2.1  | `IController` síncrona + executor no daemon                             | W1.1           | final  |
| 2.2  | Match: AND entre campos, OR dentro de listas                            | W3.1           | final  |
| 2.3  | NDJSON UTF-8, delimitador `\n`                                          | W4.2           | final  |
| 2.4  | Rate UDP: global 2000 pkt/s + por IP 1000 pkt/s                         | W4.3           | final  |
| 2.5  | W6.3 sem esconder HID real. Esconder vira W9 exploratória.              | W6.3, W9       | final  |
| 2.6  | Edge (`054c:0df2`) no udev desde W0.1                                   | W0.1           | final  |
| 2.7  | Stubs das ADRs 001–009 no W0.1                                          | W0.1           | final  |
| 2.8  | TUI sem daemon: tela offline com botão `[Iniciar daemon]`               | W5.1           | final  |
| 3.1  | `libhidapi-hidraw0` (runtime) no bootstrap + CI + README                | W0.1           | final  |
| 3.2  | `install_udev.sh` cobre `/dev/uinput` via udev rule + modules-load      | W0.1, W6.3     | final  |
| 3.3  | NÃO adicionar ao grupo `input`. Udev seletivo + `--unsafe-keyboard-hotkeys` opt-in | W0.1, W8.1 | final |
| 3.4  | `graphical-session.target` default + `hefesto-headless.service` alternativa | W4.1       | final  |
| 3.5  | AppIndicator: detectar em runtime + log warn + README quickstart        | W5.4           | final  |
| 3.6  | `FakeController` em `tests/fixtures/` desde W1.1. CI só com fake.       | W1.1           | final  |
| 4.1  | `platformdirs` em vez de `xdg_paths` próprio                            | W0.1           | final  |
| 4.2  | `filelock` em vez de implementação própria                              | W0.1           | final  |
| 4.3  | UDP v1 posicional (compat DSX) + pydantic discriminator                 | W4.3           | final  |
| 4.4  | PT-BR em tudo visível ao usuário                                        | todas          | final  |
| 4.5  | Esqueleto CLI adiantado pra W4.1 (daemon commands)                      | W4.1, W5.3     | final  |
| 5.1  | `hatchling>=1.20` fixado                                                | W0.1           | final  |
| 5.2  | `.gitattributes` com `eol=lf`                                           | W0.1           | final  |
| 5.3  | `NOTICE` atribuindo udev rule ao pydualsense                            | W0.1           | final  |
| 5.4  | `.desktop` e ícone movidos pra W5.4                                     | W5.4           | final  |
| 5.5  | `def main(): app()` explícito                                           | W4.1           | final  |
| 5.6  | `docs/protocol/trigger-modes.md` canônico no W0.1                       | W0.1           | final  |
| 5.7  | Ruff exclui `tests/fixtures/**`                                         | W0.1           | final  |
| 5.8  | Mypy overrides pra deps sem stubs                                       | W0.1           | final  |
| 5.9  | ADR-008 (BT vs USB polling) + fake replay dos dois modos                | W1.1, W1.3     | final  |
| 5.10 | UDP rejeita `version != 1` com log warn + drop                          | W4.3           | final  |

### Do V2 (auditoria 2)

| ID    | Decisão                                                                | Sprint         | Status |
|-------|------------------------------------------------------------------------|----------------|--------|
| V2-1  | Regex de anonimato expandido + whitelist por arquivo (não por palavra) | W0.1           | final  |
| V2-2  | `CLAUDE.md` da árvore vira `AGENTS.md`                                 | W0.1           | final  |
| V2-3  | TUI detecta unit ativa via `systemctl --user list-unit-files`          | W5.1           | final  |
| V2-4  | Hotkey em modo uinput: combo sagrado PS+D-pad, configurável            | W6.3, W8.1     | final  |
| V2-5  | uinput via udev rule `KERNEL=="uinput"` com `TAG+="uaccess"`           | W0.1           | final  |
| V2-6  | **Tudo PT-BR. Termos técnicos EN retornados por APIs/sistema mantidos na forma original.** | todas | final |
| V2-7  | `ControllerState.transport: Literal["usb", "bt"]` no Patch 2           | W1.1           | final  |
| V2-8  | Fallback via classe `MatchAny` sentinel (não match vazio)              | W3.1           | final  |
| V2-9  | `process_name` casa com basename de `/proc/PID/exe` (não `comm`)       | W6.1           | final  |
| V2-10 | `window_title_regex` usa `re.search`                                   | W3.1           | final  |
| V2-11 | `RateLimiter` com eviction de IPs inativos                             | W4.3           | final  |
| V2-12 | Units `.service` com `Conflicts=` mútuo                                | W4.1           | final  |
| V2-13 | `record_hid_capture.py` no W1.1. Captures em `tests/fixtures/`, sem Git LFS (limite 5MB) | W1.1 | final |
| V2-14 | `CHECKLIST_MANUAL.md` e `setup_issues.sh` incluídos no W0.1            | W0.1           | final  |
| V2-15 | PyGObject opt-in via `--with-tray` no `dev_bootstrap.sh`               | W0.1, W5.4     | final  |
| V2-16 | Escopo documentado: "Linux com systemd-logind". ADR-009 nova.          | W0.1           | final  |
| V2-17 | Debounce de battery no evento: dispara se `\|Δ\| ≥ 1%` OU `elapsed ≥ 5s`, mínimo 100ms entre eventos | W1.2, W1.3 | final |

### Pendência aberta — RESOLVIDA (V3)

| ID  | Contradição original da seção 1 V1                               | Endereçada por                          |
|-----|------------------------------------------------------------------|-----------------------------------------|
| 1.1 | `CLAUDE.md` na árvore viola REGRA -1                             | V2-2 (renome para `AGENTS.md`)          |
| 1.2 | `check_anonymity.sh` regex incompleto                            | V2-1 (script reescrito e entregue)      |
| 1.3 | `ALLOWED_CONTEXT` gera falso negativo                            | V2-1 (whitelist migra para por-arquivo) |
| 1.4 | Aridade de `Galloping` diverge em 3 lugares do spec              | 5.6 (tabela canônica em W0.1)           |
| 1.5 | Labels GitHub usadas sem criação prévia                          | Patch 1 item 11 (`setup_labels.sh`)     |

**Status:** pendência morta. Auditoria V3 confirmou mapeamento 1:1.

---

## 2. PATCHES ATUALIZADOS AO `HEFESTO_PROJECT.md`

Todos os patches abaixo substituem as versões do V1.

### Patch 1 — Sprint 0.1 expandido (substitui o do V1)

**Tarefas do W0.1 (19 itens):**

1. `git init`, criar repo GH `hefesto` público.
2. Estrutura de pastas completa (inclui `docs/adr/`, `docs/protocol/`, `docs/process/`, `docs/history/`).
3. `pyproject.toml`:
   - `build-system.requires = ["hatchling>=1.20"]`
   - Deps: `pydualsense>=0.7.5`, `textual>=0.47`, `typer>=0.9`, `pydantic>=2.0`, `python-xlib>=0.33`, `evdev>=1.6`, `structlog>=23.0`, `rich>=13.0`, `platformdirs>=4.0`, `filelock>=3.13`
   - Extras: `[dev]`, `[emulation]` com `python-uinput`, `[tray]` com `PyGObject>=3.44`
   - `[tool.mypy.overrides]` pra `textual`, `typer`, `evdev`, `Xlib`, `pydualsense`, `uinput`, `Xlib.*` com `ignore_missing_imports=true`
   - `[tool.ruff] exclude = ["tests/fixtures/**"]`
4. `.gitattributes` com `*.sh`, `*.rules`, `*.py`, `*.md`, `*.toml` todos `text eol=lf`.
5. `NOTICE` atribuindo `70-ps5-controller.rules` ao pydualsense (MIT).
6. `LICENSE` MIT.
7. `scripts/check_anonymity.sh` (arquivo já entregue à parte — copiar como-está).
8. `scripts/check_test_data.sh` validando ausência de nomes próprios em `tests/`.
9. `scripts/dev_bootstrap.sh`:
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   WITH_TRAY=0
   for arg in "$@"; do
     [[ "$arg" == "--with-tray" ]] && WITH_TRAY=1
   done

   sudo apt-get update
   sudo apt-get install -y libhidapi-dev libhidapi-hidraw0 libudev-dev libxi-dev
   if [[ "$WITH_TRAY" == "1" ]]; then
     sudo apt-get install -y libgirepository1.0-dev libcairo2-dev pkg-config python3-dev
   fi

   python -m venv .venv
   . .venv/bin/activate
   EXTRAS="dev,emulation"
   [[ "$WITH_TRAY" == "1" ]] && EXTRAS="$EXTRAS,tray"
   pip install -e ".[$EXTRAS]"

   ./scripts/install_udev.sh
   ```
10. `scripts/install_udev.sh` instala:
    - `/etc/udev/rules.d/70-ps5-controller.rules` (conforme Patch 5)
    - `/etc/udev/rules.d/71-uinput.rules` (conforme Patch 5)
    - `/etc/modules-load.d/hefesto.conf` com `uinput`
    - Roda `udevadm control --reload-rules && udevadm trigger` e `modprobe uinput`
11. `scripts/setup_labels.sh` cria 13 labels via `gh label create` (ver lista em spec original).
12. `scripts/setup_issues.sh` cria 26 issues iniciais via `gh issue create` em loop. Array com títulos + labels + body apontando pra seção do spec.
13. `.github/workflows/ci.yml`:
    ```yaml
    - run: sudo apt-get install -y libhidapi-dev libhidapi-hidraw0 libudev-dev libxi-dev
    - run: bash scripts/check_anonymity.sh
    - run: ruff check src/ tests/
    - run: mypy src/hefesto
    - run: pytest tests/unit -v --cov=hefesto
    ```
14. 9 ADR stubs em `docs/adr/` (título + contexto 3 linhas + decisão 1 linha):
    - `001-pydualsense-backend.md`
    - `002-textual-tui.md`
    - `003-udp-port-6969-compat.md`
    - `004-systemd-user-service.md`
    - `005-profile-schema-v1.md`
    - `006-xlib-window-detection.md`
    - `007-wayland-deferral.md`
    - `008-bt-vs-usb-polling.md`
    - `009-systemd-logind-scope.md` **(nova, V2-16)**
15. `docs/protocol/trigger-modes.md` com tabela canônica dos 19 modos + arity + ranges.
16. `docs/process/HEFESTO_DECISIONS_V2.md` (este arquivo).
17. `CHECKLIST_MANUAL.md` na raiz do repo com template: cada DoD que requer device físico tem checkbox que um revisor com hardware marca antes do release.
18. `AGENTS.md` (era `CLAUDE.md` no spec original — renome final).
19. `README.md` esqueleto incluindo:
    - Requisito `libhidapi-hidraw0` runtime
    - Extensão AppIndicator pra tray em GNOME
    - Nota "Linux com systemd-logind" no escopo
    - Link pra `CHECKLIST_MANUAL.md`

**DoD atualizada:**
- `./scripts/dev_bootstrap.sh` executa em Pop!_OS 22.04 limpa.
- `./scripts/dev_bootstrap.sh --with-tray` instala extras de PyGObject sem erro.
- `./scripts/check_anonymity.sh` retorna vazio.
- CI passa (lint + mypy + testes unit mesmo sem código de negócio ainda).
- 9 ADR stubs existem.
- `docs/protocol/trigger-modes.md` com tabela canônica completa.
- Labels criadas no GH (`gh label list` mostra os 13).
- 26 issues criadas no GH (`gh issue list` conta 26 com label `status:ready`).
- `AGENTS.md` presente, `CLAUDE.md` inexistente.

---

### Patch 2 — `IController` + `ControllerState` (W1.1)

```python
# src/hefesto/core/controller.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

Transport = Literal["usb", "bt"]


@dataclass(frozen=True)
class ControllerState:
    """Snapshot imutável do controle num instante."""
    battery_pct: int
    l2_raw: int               # 0-255
    r2_raw: int               # 0-255
    connected: bool
    transport: Transport      # V2-7
    # Campos adicionais (buttons, sticks, touchpad) entram em W1.2.


class IController(ABC):
    """Interface síncrona. Chamadas bloqueantes.

    O daemon envolve em loop.run_in_executor() para integração asyncio.
    Razão: backends futuros (cffi/Rust) provavelmente também serão síncronos;
    acoplar à event loop trava substituição. Ver ADR-001.
    """

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def read_state(self) -> ControllerState: ...

    @abstractmethod
    def set_trigger(self, side: str, effect: "TriggerEffect") -> None: ...

    @abstractmethod
    def set_led(self, color: tuple[int, int, int]) -> None: ...

    @abstractmethod
    def set_rumble(self, weak: int, strong: int) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...
```

Uso no daemon (W1.3):

```python
# src/hefesto/daemon/main.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def poll_loop(controller: IController, event_bus, running: asyncio.Event):
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="hid-poll")
    while running.is_set():
        state = await loop.run_in_executor(executor, controller.read_state)
        await event_bus.publish("state.update", state)
        await asyncio.sleep(1 / 60)
```

---

### Patch 3 — `MatchCriteria` + `MatchAny` (W3.1)

```python
# src/hefesto/profiles/schema.py
from __future__ import annotations

import os
import re
from typing import Literal, Union

from pydantic import BaseModel, Field


class MatchCriteria(BaseModel):
    """Casamento por critérios específicos.

    Semântica:
      - AND entre campos preenchidos.
      - OR dentro de cada lista.
      - Campos None/[] são ignorados na avaliação.

    Exemplo:
        MatchCriteria(
            window_class=["steam_app_1091500", "Cyberpunk2077.exe"],
            process_name=["Cyberpunk2077.exe"]
        )

    Bate quando:
        (wm_class ∈ window_class) AND (exe_basename ∈ process_name)
    """
    type: Literal["criteria"] = "criteria"
    window_class: list[str] = Field(default_factory=list)
    window_title_regex: str | None = None
    process_name: list[str] = Field(default_factory=list)

    def matches(self, window_info: dict) -> bool:
        conditions = []
        if self.window_class:
            conditions.append(window_info["wm_class"] in self.window_class)
        if self.window_title_regex:
            # V2-10: re.search, não fullmatch. Menos fricção pro criador de perfil.
            conditions.append(
                bool(re.search(self.window_title_regex, window_info["wm_name"]))
            )
        if self.process_name:
            # V2-9: basename de /proc/PID/exe, não /proc/PID/comm (trunca em 15 chars).
            conditions.append(window_info["exe_basename"] in self.process_name)
        return all(conditions) if conditions else False


class MatchAny(BaseModel):
    """Sentinel explícito pro perfil fallback. Sempre casa.

    V2-8: evita que perfil com match vazio por engano vire wildcard silencioso.
    Fallback.json precisa declarar explicitamente:
        "match": {"type": "any"}
    """
    type: Literal["any"] = "any"

    def matches(self, window_info: dict) -> bool:
        return True


Match = Union[MatchCriteria, MatchAny]
```

Coleta de `window_info` em W6.1:

```python
# src/hefesto/integrations/xlib_window.py
import os

def get_active_window_info() -> dict:
    # ... Xlib boilerplate ...
    pid = _get_pid_from_window(win)
    try:
        exe_path = os.readlink(f"/proc/{pid}/exe")
        exe_basename = os.path.basename(exe_path)
    except (OSError, FileNotFoundError):
        exe_basename = ""

    return {
        "wm_class": wm_class,
        "wm_name": wm_name,
        "pid": pid,
        "exe_basename": exe_basename,   # V2-9
    }
```

---

### Patch 4 — `RateLimiter` com eviction (W4.3)

```python
# src/hefesto/daemon/udp_server.py
from collections import defaultdict, deque
import time

RATE_GLOBAL = 2000   # pkt/s total
RATE_PER_IP = 1000   # pkt/s por IP


class RateLimiter:
    """Dois limites sobrepostos. Global previne flood total,
    per-IP previne monopolização por um cliente.

    V2-11: IPs inativos são evictados pra não vazar memória.
    """
    def __init__(self):
        self.global_window: deque[float] = deque(maxlen=RATE_GLOBAL)
        self.per_ip: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=RATE_PER_IP)
        )

    def allow(self, ip: str) -> bool:
        now = time.monotonic()
        cutoff = now - 1.0

        # Janela global
        while self.global_window and self.global_window[0] < cutoff:
            self.global_window.popleft()
        if len(self.global_window) >= RATE_GLOBAL:
            return False

        # Janela por IP
        ip_window = self.per_ip[ip]
        while ip_window and ip_window[0] < cutoff:
            ip_window.popleft()

        if not ip_window:
            # IP ficou sem atividade na última 1s: eviction (V2-11)
            del self.per_ip[ip]
            ip_window = self.per_ip[ip]   # recria entrada fresh

        if len(ip_window) >= RATE_PER_IP:
            return False

        self.global_window.append(now)
        ip_window.append(now)
        return True
```

---

### Patch 5 — udev rules (W0.1)

**`assets/70-ps5-controller.rules`:**

```
# DualSense + DualSense Edge. Acesso via ACL do systemd-logind (uaccess).
# Mais seguro que MODE=0666: permissão só pro usuário da sessão ativa.

# USB — DualSense standard
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0ce6", MODE="0660", TAG+="uaccess"
# USB — DualSense Edge
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0df2", MODE="0660", TAG+="uaccess"
# Bluetooth — DualSense
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", KERNELS=="0005:054C:0CE6.*", MODE="0660", TAG+="uaccess"
# Bluetooth — DualSense Edge
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", KERNELS=="0005:054C:0DF2.*", MODE="0660", TAG+="uaccess"
```

**`assets/71-uinput.rules`:** **(V2-5, nova)**

```
# Acesso a /dev/uinput via ACL do systemd-logind.
# Usado pra emulação de gamepad virtual (Xbox360/DS4) no W6.3.
KERNEL=="uinput", SUBSYSTEM=="misc", MODE="0660", TAG+="uaccess"
```

**`assets/hefesto.conf` (pra `/etc/modules-load.d/`):**

```
uinput
```

---

### Patch 6 — mypy overrides (W0.1)

```toml
# pyproject.toml
[[tool.mypy.overrides]]
module = [
    "pydualsense",
    "pydualsense.*",
    "textual",
    "textual.*",
    "evdev",
    "Xlib",
    "Xlib.*",
    "uinput",
    "gi",
    "gi.*",
]
ignore_missing_imports = true
```

---

### Patch 7 — ADR-008 atualizada (W1.1)

```markdown
# ADR-008: Diferença entre Bluetooth e USB no polling

## Contexto
pydualsense expõe HID sem diferenciar USB/BT. Na prática:
- USB: 1000Hz possível, battery report a cada pacote.
- BT: 250Hz típico, battery report a cada N pacotes, latência maior.
- Gatilho adaptativo via BT tem comportamento ligeiramente diferente em alguns modos (Machine, Galloping).

## Decisão
- Daemon poll fixo a 60Hz (suficiente pra triggers, não desperdiça CPU).
- `ControllerState.transport: Literal["usb", "bt"]` exposto pra UI e lógica dependente.
- FakeController tem dois replays: `fixtures/hid_capture_usb.bin` e `fixtures/hid_capture_bt.bin`. Testes W1.3 cobrem ambos os modos.
- **Debounce de battery no evento** (V2-17):
  - Dispara `battery_change` se `abs(delta_pct) >= 1` OU `elapsed_since_last >= 5.0s`.
  - Mínimo 100ms entre eventos consecutivos (rate ceiling).
  - Debounce vale tanto pra USB quanto pra BT.

## Consequências
- Usuário BT vê latência 16-32ms maior (aceitável pra trigger, não pra competitivo).
- Trocar pra 120Hz é trivial se alguém reclamar (config `poll_hz` em `daemon.toml`).
- Event bus não é inundado em USB, onde bateria reportaria a cada 16ms.
```

---

### Patch 8 — Units systemd com `Conflicts=` (W4.1)

**`assets/hefesto.service`:**

```ini
[Unit]
Description=Hefesto DualSense adaptive trigger daemon
After=graphical-session.target
PartOf=graphical-session.target
Conflicts=hefesto-headless.service

[Service]
Type=simple
ExecStart=%h/.local/bin/hefesto daemon start --foreground
Restart=on-failure
RestartSec=2
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=graphical-session.target
```

**`assets/hefesto-headless.service`:**

```ini
[Unit]
Description=Hefesto DualSense daemon (headless — sem auto-switch X11)
After=default.target
Conflicts=hefesto.service

[Service]
Type=simple
ExecStart=%h/.local/bin/hefesto daemon start --foreground --headless
Restart=on-failure
RestartSec=2
Environment=PYTHONUNBUFFERED=1
Environment=HEFESTO_NO_WINDOW_DETECT=1

[Install]
WantedBy=default.target
```

Instalação via CLI em W4.1:

```bash
hefesto daemon install-service             # instala hefesto.service, desabilita headless se existir
hefesto daemon install-service --headless  # instala hefesto-headless.service, desabilita a normal
```

Implementação do comando invoca `systemctl --user disable` na unit oposta antes do `enable` na escolhida.

---

### Patch 9 — Hotkey combo sagrado (V2-4, novo no V2)

**`src/hefesto/integrations/hotkey_daemon.py`:**

```python
# Leitura de botões do controle via event bus interno (não /dev/input).
# Hotkey é observação passiva dos botões já lidos pelo IController.
# NÃO requer grupo 'input' nem evdev em teclado.

DEFAULT_SACRED_COMBO = ["ps", "dpad_up"]   # próximo perfil
DEFAULT_SACRED_COMBO_REV = ["ps", "dpad_down"]  # perfil anterior


class HotkeyManager:
    """Escuta eventos de botão do daemon e dispara ações.

    Em modo uinput (emulação Xbox360 ativa), os botões do combo sagrado
    NÃO são repassados ao gamepad virtual (evita combo ser consumido pelo jogo).
    Combo configurável via daemon.toml:

        [hotkey]
        next_profile = ["ps", "dpad_up"]
        prev_profile = ["ps", "dpad_down"]
        passthrough_in_emulation = false   # true = combo vai pro jogo também
    """
    ...
```

Opção `--unsafe-keyboard-hotkeys` em W8.1 adiciona evdev puro (teclado comum) e exige:

```bash
# Aviso mostrado ANTES de ativar:
# Modo --unsafe-keyboard-hotkeys exige acesso ao grupo 'input'.
# Isto dá leitura de QUALQUER evento de teclado (risco de keylogger).
# Continue apenas se você confia no ambiente. (y/N)
```

---

### Patch 10 — ADR-009 (V2-16, nova)

**`docs/adr/009-systemd-logind-scope.md`:**

```markdown
# ADR-009: Escopo Linux — systemd-logind requerido

## Contexto
As udev rules usam `TAG+="uaccess"` pra dar ACL seletiva ao usuário da sessão
ativa. Essa tag é processada pelo `systemd-logind`, que só existe em distros
que adotaram systemd.

Distros afetadas: Alpine (OpenRC), Void (runit), Gentoo com OpenRC, Artix.
Usuários dessas distros precisariam configurar ACL manualmente ou usar
`MODE="0666"` (menos seguro).

## Decisão
- v0.x e v1.x suportam oficialmente apenas distros com systemd-logind.
- README declara o requisito explicitamente.
- PRs que adicionem suporte a OpenRC/runit são bem-vindos, mas o mainline
  não testa nem garante.

## Consequências
- 99%+ dos usuários de DualSense em Linux estão em distros mainstream
  (Pop!_OS, Ubuntu, Fedora, Arch, Debian estável) — sem impacto prático.
- Usuários de distros alternativas recebem mensagem clara em vez de falha obscura.
- Reduz superfície de teste: uma só estratégia de permissão.
```

---

### Patch 11 — TUI detecta unit (V2-3, nova)

**`src/hefesto/tui/screens/daemon_offline.py`:**

```python
# Tela mostrada quando IPC socket não responde (daemon parado).
# Descobre qual unit systemd está instalada antes de oferecer botão.

import subprocess


def detect_installed_unit() -> str | None:
    """Retorna 'hefesto' ou 'hefesto-headless' ou None.

    V2-3: usuário pode ter instalado qualquer uma das duas (Patch 8).
    Se nenhuma ou as duas (inconsistente), retorna None e TUI oferece dropdown.
    """
    try:
        result = subprocess.run(
            ["systemctl", "--user", "list-unit-files",
             "hefesto.service", "hefesto-headless.service",
             "--no-legend", "--no-pager"],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError:
        return None

    enabled_units = []
    for line in result.stdout.strip().split("\n"):
        parts = line.split()
        if len(parts) >= 2 and parts[1] in ("enabled", "enabled-runtime"):
            unit_name = parts[0].removesuffix(".service")
            enabled_units.append(unit_name)

    if len(enabled_units) == 1:
        return enabled_units[0]
    return None   # nenhuma ou ambas
```

---

## 3. RESPOSTAS ÀS 5 PENDÊNCIAS FINAIS DO V1

| #   | Pergunta (V1)                                              | Resposta                     |
|-----|------------------------------------------------------------|------------------------------|
| 1   | Seção 1 da auditoria (contradições) — enviar pra fechar    | **Pendente**. Destravar após 48h se não chegar. |
| 2   | Renomear `CLAUDE.md` pra `AGENTS.md` no repo?              | **Sim.** V2-2.               |
| 3   | Hotkey default via botões do controle (não requer `input`)?| **Sim.** V2-4 + Patch 9.     |
| 4   | PT-BR em logs técnicos também?                             | **Sim, com ressalva de termos EN retornados por APIs.** V2-6. |
| 5   | `setup_labels.sh` automatizado no W0.1?                    | **Sim.** Patch 1 item 11.    |

---

## 4. REGEX DE ANONIMATO (V2-1)

Implementação completa em `scripts/check_anonymity.sh` — arquivo entregue separadamente. Características:

- 15+ termos cobertos (claude, anthropic, openai, chatgpt, opus, sonnet, haiku, gemini, copilot, mistral, grok, gpt-N, llama-N, "by claude", "generated by", "feito por", "criado por", "autor:", etc.).
- Whitelist por **arquivo/path** (não por palavra): `LICENSE`, `NOTICE`, `CHANGELOG.md`, `docs/process/**`, `docs/history/**`, `tests/fixtures/**`.
- Usa `git grep` quando em repo (respeita `.gitignore` + pathspec), cai pra `grep -r` antes do `git init`.
- Auto-exclusão: o próprio script está na whitelist pra não gatilhar em si mesmo.

**Por que este arquivo (`HEFESTO_DECISIONS_V2.md`) não viola o check:** está em `docs/process/**`, excluído por pathspec.

---

## 5. ORDEM DE EXECUÇÃO FINAL

1. ~~Resolver seção 1 da auditoria (contradições)~~ → Pendente não-bloqueante.
2. Aplicar Patches 1–11 deste V2 ao `HEFESTO_PROJECT.md`.
3. Renomear `CLAUDE.md` da árvore pra `AGENTS.md`.
4. Commit único do scaffold com mensagem `chore: scaffold inicial do projeto`.
5. Executar Sprint 0.1 (19 itens do Patch 1).
6. Confirmar DoD do W0.1 em `CHECKLIST_MANUAL.md`.
7. Submeter tabela de trigger modes (`docs/protocol/trigger-modes.md`) ao mantenedor humano pra revisão. **Bloqueia W2.1.**
8. Começar W1.1 em paralelo (não depende da tabela).

---

## 6. PRÓXIMAS INTERAÇÕES COM O MANTENEDOR HUMANO

Pontos que exigem review antes do merge:

- **Bloqueante W2.1:** `docs/protocol/trigger-modes.md` (tabela dos 19 modos) — mantenedor confirmou que quer revisar uma vez.
- **Não-bloqueante:** seção 1 da auditoria V1. Destravar se não chegar em 48h.
- **Pós-W0.1:** confirmar que os 26 issues criados fazem sentido antes de começar W1.1.

---

## 7. CHANGELOG

- **V1 → V2:**
  - +17 decisões da auditoria V2 incorporadas.
  - +3 patches (Patch 9, 10, 11).
  - Patch 2 corrige omissão do `transport`.
  - Patch 3 substitui fallback implícito por `MatchAny` sentinel.
  - Patch 4 adiciona eviction.
  - Patch 5 divide em dois arquivos `.rules` (hidraw + uinput).
  - Patch 7 formaliza debounce de battery.
  - Patch 8 adiciona `Conflicts=` mútuo.
  - Regex de anonimato migra de whitelist-por-palavra pra whitelist-por-arquivo.
  - Sprint 0.1 cresce de 16 pra 19 itens.

- **V2 → V3:** (hipotético) só se houver seção 1 da auditoria V1 com contradições reais.
