# HEFESTO — Decisões de Spec (Pós-Auditoria)

> Respostas consolidadas às dúvidas levantadas na auditoria pré-execução.
> Este arquivo vira `DOUBTS_RESOLVED.md` no repo depois do `git init`.
> Alterações aqui listadas devem ser aplicadas ao `HEFESTO_PROJECT.md` como parte do Sprint 0.1.

**Nota:** seção 1 (Contradições) da auditoria não foi incluída no review. Pendente.

---

## TABELA DE DECISÕES

| ID   | Decisão                                                                  | Sprint afetada |
|------|--------------------------------------------------------------------------|----------------|
| 2.1  | `IController` síncrona + executor no daemon                              | W1.1           |
| 2.2  | Match: AND entre campos, OR dentro de listas                             | W3.1           |
| 2.3  | NDJSON UTF-8, delimitador `\n`                                           | W4.2           |
| 2.4  | Rate UDP: global 2000 pkt/s + por IP 1000 pkt/s                          | W4.3           |
| 2.5  | W6.3 sem esconder HID real. Esconder vira W9 exploratória.               | W6.3, W9       |
| 2.6  | Edge (`054c:0df2`) no udev desde W0.1                                    | W0.1           |
| 2.7  | Stubs das ADRs 001–008 no W0.1                                           | W0.1           |
| 2.8  | TUI sem daemon: tela offline com botão `[Iniciar daemon]`                | W5.1           |
| 3.1  | `libhidapi-hidraw0` (runtime) no bootstrap + CI + README                 | W0.1           |
| 3.2  | `install_udev.sh` cobre `/dev/uinput` + `modules-load.d/hefesto.conf`    | W0.1, W6.3     |
| 3.3  | NÃO adicionar ao grupo `input`. Udev seletivo + `--unsafe-keyboard-hotkeys` opt-in | W0.1, W8.1 |
| 3.4  | `graphical-session.target` default + `hefesto-headless.service` alternativa | W4.1        |
| 3.5  | AppIndicator: detectar em runtime + log warn + README quickstart         | W5.4           |
| 3.6  | `FakeController` em `tests/fixtures/` desde W1.1. CI só com fake.        | W1.1           |
| 4.1  | `platformdirs` em vez de `xdg_paths` próprio                             | W0.1           |
| 4.2  | `filelock` em vez de implementação própria                               | W0.1           |
| 4.3  | UDP v1 posicional (compat DSX) + pydantic discriminator                  | W4.3           |
| 4.4  | PT-BR em tudo visível ao usuário                                         | todas          |
| 4.5  | Esqueleto CLI adiantado pra W4.1 (daemon commands)                       | W4.1, W5.3     |
| 5.1  | `hatchling>=1.20` fixado                                                 | W0.1           |
| 5.2  | `.gitattributes` com `eol=lf`                                            | W0.1           |
| 5.3  | `NOTICE` atribuindo udev rule ao pydualsense                             | W0.1           |
| 5.4  | `.desktop` e ícone movidos pra W5.4                                      | W5.4           |
| 5.5  | `def main(): app()` explícito                                            | W4.1           |
| 5.6  | `docs/protocol/trigger-modes.md` canônico no W0.1                        | W0.1           |
| 5.7  | Ruff exclui `tests/fixtures/**`                                          | W0.1           |
| 5.8  | Mypy overrides pra deps sem stubs                                        | W0.1           |
| 5.9  | ADR-008 (BT vs USB polling) + fake replay dos dois modos                 | W1.1, W1.3     |
| 5.10 | UDP rejeita `version != 1` com log warn + drop                           | W4.3           |

---

## PATCHES NO SPEC ORIGINAL

### Patch 1 — Sprint 0.1 (substituir conteúdo atual por esta versão expandida)

**Tarefas do Sprint 0.1 passam a ser:**

1. `git init`, criar repo GH `hefesto` público.
2. Estrutura de pastas (inclui `docs/adr/` com 8 stubs e `docs/protocol/trigger-modes.md` populado).
3. `pyproject.toml` com:
   - `build-system.requires = ["hatchling>=1.20"]`
   - Deps incluem `platformdirs>=4.0`, `filelock>=3.13`.
   - `[tool.mypy.overrides]` pra `textual`, `typer`, `evdev`, `Xlib`, `pydualsense`, `pydualsense.*` com `ignore_missing_imports=true`.
   - `[tool.ruff] exclude = ["tests/fixtures/**"]`.
4. `.gitattributes` padrão Python + `*.sh`, `*.rules`, `*.py` com `text eol=lf`.
5. `NOTICE` atribuindo `70-ps5-controller.rules` ao pydualsense (MIT).
6. `LICENSE` MIT.
7. `scripts/check_anonymity.sh` com grep + lista de palavras proibidas.
8. `scripts/check_test_data.sh` validando ausência de nomes próprios em `tests/`.
9. `scripts/dev_bootstrap.sh`:
   ```bash
   sudo apt-get install -y libhidapi-dev libhidapi-hidraw0 libudev-dev libxi-dev
   python -m venv .venv
   . .venv/bin/activate
   pip install -e ".[dev,emulation]"
   ./scripts/install_udev.sh
   ```
10. `scripts/install_udev.sh` instala:
    - `/etc/udev/rules.d/70-ps5-controller.rules` (VID/PID `054c:0ce6` + `054c:0df2`)
    - `/etc/modules-load.d/hefesto.conf` com `uinput`
    - Regra ACL pra `/dev/uinput` grupo do usuário ou acesso via `setfacl`
11. `scripts/setup_labels.sh` cria labels GH via `gh label create` (13 labels do spec).
12. `.github/workflows/ci.yml` inclui:
    ```yaml
    - run: sudo apt-get install -y libhidapi-dev libhidapi-hidraw0 libudev-dev libxi-dev
    ```
13. 8 ADR stubs em `docs/adr/` (titulo + contexto 3 linhas + decisão 1 linha):
    - `001-pydualsense-backend.md`
    - `002-textual-tui.md`
    - `003-udp-port-6969-compat.md`
    - `004-systemd-user-service.md`
    - `005-profile-schema-v1.md`
    - `006-xlib-window-detection.md`
    - `007-wayland-deferral.md`
    - `008-bt-vs-usb-polling.md` **(nova, de 5.9)**
14. `docs/protocol/trigger-modes.md` com tabela canônica dos 19 modos + arity + ranges extraídos do README Paliverse.
15. `README.md` esqueleto mencionando requisito de `libhidapi-hidraw0` e extensão AppIndicator pra tray.
16. `DOUBTS_RESOLVED.md` (este arquivo) commitado no W0.1.

**Definition of Done atualizada:**
- `./scripts/dev_bootstrap.sh` executa em Pop!_OS 22.04 limpa.
- `./scripts/check_anonymity.sh` retorna vazio.
- CI passa (lint + mypy + testes unit mesmo sem código de negócio).
- 8 ADR stubs existem.
- `docs/protocol/trigger-modes.md` tem a tabela completa.
- Labels criadas no GH.

---

### Patch 2 — Interface `IController` sync (W1.1)

Spec original não definia. Substituir por:

```python
# src/hefesto/core/controller.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass(frozen=True)
class ControllerState:
    battery_pct: int
    l2_raw: int  # 0-255
    r2_raw: int
    connected: bool
    # ... buttons, sticks

class IController(ABC):
    """Interface síncrona. Chamadas bloqueantes.
    Daemon envolve em loop.run_in_executor() para integração asyncio."""

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def read_state(self) -> ControllerState: ...

    @abstractmethod
    def set_trigger(self, side: str, effect: TriggerEffect) -> None: ...

    @abstractmethod
    def set_led(self, color: tuple[int, int, int]) -> None: ...

    @abstractmethod
    def set_rumble(self, weak: int, strong: int) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...
```

Uso no daemon:

```python
# src/hefesto/daemon/main.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def poll_loop(controller: IController):
    loop = asyncio.get_running_loop()
    while running:
        state = await loop.run_in_executor(
            executor, controller.read_state
        )
        await event_bus.publish("state.update", state)
        await asyncio.sleep(1/60)
```

---

### Patch 3 — Schema de match (W3.1)

```python
# src/hefesto/profiles/schema.py
from pydantic import BaseModel, Field

class MatchCriteria(BaseModel):
    """AND entre campos preenchidos. OR dentro de cada lista.

    Exemplo:
        MatchCriteria(
            window_class=["steam_app_1091500", "Cyberpunk2077.exe"],
            process_name=["Cyberpunk2077.exe"]
        )

    Bate quando: (wm_class ∈ window_class) AND (proc ∈ process_name).
    Campos ausentes (None/[]) são ignorados na regra.
    """
    window_class: list[str] = Field(default_factory=list)
    window_title_regex: str | None = None
    process_name: list[str] = Field(default_factory=list)

    def matches(self, window_info: dict) -> bool:
        conditions = []
        if self.window_class:
            conditions.append(window_info["wm_class"] in self.window_class)
        if self.window_title_regex:
            conditions.append(bool(re.search(self.window_title_regex, window_info["wm_name"])))
        if self.process_name:
            conditions.append(window_info["exe_name"] in self.process_name)
        return all(conditions) if conditions else False
```

---

### Patch 4 — Rate limit UDP (W4.3)

```python
# src/hefesto/daemon/udp_server.py
from collections import defaultdict, deque
import time

RATE_GLOBAL = 2000  # pkt/s total
RATE_PER_IP = 1000  # pkt/s por IP

class RateLimiter:
    def __init__(self):
        self.global_window: deque[float] = deque(maxlen=RATE_GLOBAL)
        self.per_ip: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=RATE_PER_IP)
        )

    def allow(self, ip: str) -> bool:
        now = time.monotonic()
        cutoff = now - 1.0

        # limpa janelas expiradas preguiçosamente
        while self.global_window and self.global_window[0] < cutoff:
            self.global_window.popleft()
        if len(self.global_window) >= RATE_GLOBAL:
            return False

        ip_window = self.per_ip[ip]
        while ip_window and ip_window[0] < cutoff:
            ip_window.popleft()
        if len(ip_window) >= RATE_PER_IP:
            return False

        self.global_window.append(now)
        ip_window.append(now)
        return True
```

---

### Patch 5 — Udev rules ampliada (W0.1)

```
# /etc/udev/rules.d/70-ps5-controller.rules
# DualSense + DualSense Edge. Acesso sem root via hidraw.

# USB — DualSense standard
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0ce6", MODE="0660", TAG+="uaccess"
# USB — DualSense Edge
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0df2", MODE="0660", TAG+="uaccess"
# Bluetooth — DualSense
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", KERNELS=="0005:054C:0CE6.*", MODE="0660", TAG+="uaccess"
# Bluetooth — DualSense Edge
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", KERNELS=="0005:054C:0DF2.*", MODE="0660", TAG+="uaccess"
```

`TAG+="uaccess"` usa ACL do systemd-logind e dá permissão só pra usuário logado na sessão ativa. Mais seguro que `MODE="0666"`.

---

### Patch 6 — Mypy overrides (W0.1)

Adicionar ao `pyproject.toml`:

```toml
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
]
ignore_missing_imports = true
```

---

### Patch 7 — Nova ADR-008 (BT vs USB polling)

```markdown
# ADR-008: Diferença entre Bluetooth e USB no polling

## Contexto
pydualsense expõe HID sem diferenciar USB/BT. Mas:
- USB: 1000Hz polling possível, battery report a cada pacote.
- BT: 250Hz típico, battery report a cada N pacotes, latência maior.
- Gatilho adaptativo via BT tem comportamento ligeiramente diferente em alguns modos (Machine, Galloping).

## Decisão
- Daemon poll fixo a 60Hz (suficiente pra triggers, não desperdiça CPU).
- Battery report com debounce de 5s pra evitar spam via USB.
- `ControllerState` marca `transport: Literal["usb", "bt"]` pra UI exibir.
- FakeController tem dois replays: `fixtures/hid_capture_usb.bin` e `fixtures/hid_capture_bt.bin`. Testes W1.3 cobrem ambos.

## Consequências
- Usuário BT vê latência 16-32ms maior (aceitável pra trigger, não pra competitivo).
- Trocar pra 120Hz é trivial se alguém reclamar (config `poll_hz`).
```

---

### Patch 8 — Headless service (W4.1)

`assets/hefesto-headless.service`:

```ini
[Unit]
Description=Hefesto DualSense daemon (headless mode)
After=default.target

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

Flag `--headless` / env `HEFESTO_NO_WINDOW_DETECT=1` desliga o auto-switch X11 (sem DISPLAY não funcionaria mesmo). Perfil ativo fica manual via CLI.

---

## ORDEM DE EXECUÇÃO ATUALIZADA

1. Resolver seção 1 da auditoria (contradições) — pendente.
2. Aplicar patches 1-8 acima ao `HEFESTO_PROJECT.md`.
3. Renomear `CLAUDE.md` do projeto pra `AGENTS.md` ou `CONTRIBUTING_AI.md` (regra -1 de anonimato vale pro próprio nome do arquivo).
4. Executar Sprint 0.1 expandido.
5. Abrir 26 issues via `scripts/setup_issues.sh` (criado em W0.1).
6. Começar W1.1.

---

## PENDÊNCIAS PRA VOCÊ CONFIRMAR

- [ ] Seção 1 da auditoria (contradições) — enviar pra fechar o loop.
- [ ] Confirma renomear `CLAUDE.md` pra `AGENTS.md` no repo?
- [ ] Confirma que hotkey default é via botões do controle (não requer grupo `input`)?
- [ ] Confirma PT-BR em logs técnicos também (não só UI)?
- [ ] Confirma que quer `setup_labels.sh` automatizado no W0.1 ou prefere criar labels manualmente no GH UI?

Sem essas 5, sigo com as recomendações listadas (default = sim/sim/sim/sim/automatizado).
