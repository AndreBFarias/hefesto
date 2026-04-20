# HEFESTO — Decisões de Spec V3 (Deltas sobre V2)

> **Destino no repo:** `docs/process/HEFESTO_DECISIONS_V3.md`
> **Substitui:** nada. **Complementa:** `HEFESTO_DECISIONS_V2.md`.
> **Status:** CONGELADO. Se houver V4, é sobre descobertas de execução, não revisão de spec.

Regras globais (`~/.config/zsh/AI.md` v4.0 + `~/.claude/CLAUDE.md` com meta-regras 9.6–9.8 e validação visual 13–14) aplicam-se por padrão e não são re-declaradas.

---

## 1. STATUS DA PENDÊNCIA ABERTA DO V2

**RESOLVIDA.** Mapeamento 1:1 de cada item da seção 1 V1 contra decisões posteriores confirmado:

| 1.1 | 1.2 | 1.3 | 1.4 | 1.5 |
|-----|-----|-----|-----|-----|
| V2-2 | V2-1 | V2-1 | 5.6 | Patch 1 item 11 |

V2 atualizado. Pendência morta.

---

## 2. DELTAS DE CORREÇÃO SOBRE OS PATCHES DO V2

### V3-1 — Substitui Patch 4 V2 (RateLimiter com `_sweep`)

O `del` + re-acesso via `defaultdict` do V2 não liberava memória. Versão corrigida:

```python
# src/hefesto/daemon/udp_server.py
from collections import deque
import time

RATE_GLOBAL = 2000
RATE_PER_IP = 1000


class RateLimiter:
    """Dois limites sobrepostos: global protege servidor, per-IP protege fairness.

    IPs inativos são removidos por _sweep periódico (no máximo 1x/s), impedindo
    vazamento de memória quando muitos IPs aparecem uma vez e somem.
    """

    def __init__(self) -> None:
        self.global_window: deque[float] = deque(maxlen=RATE_GLOBAL)
        self.per_ip: dict[str, deque[float]] = {}
        self._last_sweep: float = 0.0

    def _sweep(self, now: float) -> None:
        if now - self._last_sweep < 1.0:
            return
        cutoff = now - 1.0
        self.per_ip = {
            ip: wnd for ip, wnd in self.per_ip.items()
            if wnd and wnd[-1] >= cutoff
        }
        self._last_sweep = now

    def allow(self, ip: str) -> bool:
        now = time.monotonic()
        cutoff = now - 1.0
        self._sweep(now)

        while self.global_window and self.global_window[0] < cutoff:
            self.global_window.popleft()
        if len(self.global_window) >= RATE_GLOBAL:
            return False

        ip_window = self.per_ip.setdefault(ip, deque(maxlen=RATE_PER_IP))
        while ip_window and ip_window[0] < cutoff:
            ip_window.popleft()
        if len(ip_window) >= RATE_PER_IP:
            return False

        self.global_window.append(now)
        ip_window.append(now)
        return True
```

### V3-2 — Complementa Patch 9 V2 (buffer de 150ms configurável)

Combo sagrado precisa de política de timing documentada:

```python
# daemon.toml default
# [hotkey]
# buffer_ms = 150
# next_profile = ["ps", "dpad_up"]
# prev_profile = ["ps", "dpad_down"]
# passthrough_in_emulation = false

HOTKEY_BUFFER_MS_DEFAULT = 150

# Política: PS sempre bufferizado por buffer_ms. Se chegar segundo botão do combo
# nesse intervalo → consome combo, não repassa ao uinput. Se expirar sem completar
# → repassa PS atrasado ao uinput. Custo: overlay Steam abre com ~150ms de delay
# mas troca de perfil funciona de forma confiável.
```

### V3-3 — Complementa Patch 11 V2 (`detect_installed_unit` defensivo)

```python
def detect_installed_unit() -> str | None:
    """Retorna 'hefesto', 'hefesto-headless' ou None."""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "list-unit-files",
             "hefesto.service", "hefesto-headless.service",
             "--no-pager", "--plain"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    stdout = result.stdout.strip()
    if not stdout:
        return None

    enabled_units: list[str] = []
    for line in stdout.split("\n"):
        parts = line.split()
        if len(parts) >= 2 and parts[1] in ("enabled", "enabled-runtime"):
            enabled_units.append(parts[0].removesuffix(".service"))

    return enabled_units[0] if len(enabled_units) == 1 else None
```

---

## 3. DELTAS DE DOMÍNIO HEFESTO

### V3-4 — Semântica `docs/process/` vs `docs/history/`

Documentar em `AGENTS.md`:

- **`docs/process/`** — artefatos vivos do processo de design: `HEFESTO_DECISIONS_V2.md`, `HEFESTO_DECISIONS_V3.md`, `ROADMAP.md`, `DUVIDAS_*.md` atuais.
- **`docs/history/`** — arquivo morto: auditorias antigas, RFCs rejeitadas, versões anteriores de decisões que foram substituídas (V1 vai pra cá).

Ambas excluídas do `check_anonymity.sh`. Diferença é temporal/operacional.

### V3-5 — Gate de 5MB nos HID captures no CI

Adicionar ao `.github/workflows/ci.yml` no job `lint-test`:

```yaml
- name: Verificar tamanho de HID captures
  run: |
    OVERSIZE=$(find tests/fixtures -name "*.bin" -size +5M 2>/dev/null)
    if [[ -n "$OVERSIZE" ]]; then
      echo "ERRO: captures excedem 5MB:"
      echo "$OVERSIZE"
      exit 1
    fi
```

### V3-6 — `wm_class` usa segundo elemento da tupla Xlib

Documentado no W6.1:

> Xlib retorna `wm_class` como tupla `(instance, class)`. Usamos sempre o segundo elemento (`class`), mais estável entre distros. Exceção conhecida: alguns apps Qt/GTK têm instance e class idênticos (`firefox`, `firefox`), outros divergem (`steam`, `Steam`). Quando divergem, matcher vê `Steam`. Perfis devem listar o valor de `class` — sugerir `xprop WM_CLASS` na documentação de criação de perfis.

### V3-7 — Teste de regressão do `check_anonymity.sh` (divergência V2)

**Decisão corrigida:** usar pytest + subprocess em vez de `bats-core`.

Justificativa:
- Zero deps novas (pytest já está em `[dev]`).
- CI não precisa de `apt install bats-core`.
- `tmp_path` auto-cleanup é mais limpo que setup/teardown manual do bats.
- Testes de falso-positivo ficam mais legíveis em Python.

**Arquivo canônico:** `tests/unit/test_check_anonymity.py` (copiar o entregue durante a auditoria V3, cobre 17 casos: 7 detecção positiva, 5 whitelist, 4 falso-positivo, 1 auto-exclusão, 2 modo git).

### V3-8 — `record_hid_capture.py` com YAML descritor determinístico

```bash
python scripts/record_hid_capture.py \
    --transport usb \
    --duration 30 \
    --script captures/script_default.yaml \
    --output tests/fixtures/hid_capture_usb.bin
```

`captures/script_default.yaml` (versionado) lista a sequência canônica:

```yaml
version: 1
transport_assert: usb    # falha se device reportar bt
steps:
  - wait: 0.5
  - press: ["r2"]
  - hold: 1.0
  - release: ["r2"]
  - press: ["l2"]
  - hold: 1.0
  - release: ["l2"]
  - stick: {side: left, x: 0.5, y: 0.0}
  - wait: 0.5
  - stick: {side: left, x: 0.0, y: 0.0}
  - battery_read: true
  # ...
```

Captures gerados em devices diferentes passam a ser byte-comparáveis para as partes determinísticas do protocolo (setpoints, comandos).

---

## 4. ATUALIZAÇÕES NO PATCH 1 (W0.1)

Com V3-5, V3-7 e V3-8 incorporados, o Patch 1 cresce de 19 para **22 itens**:

**Adicionar após o item 19 do V2:**

20. `tests/unit/test_check_anonymity.py` (pytest, do anexo V3).
21. Job `lint-test` no CI inclui gate de 5MB (V3-5).
22. `scripts/record_hid_capture.py` + `captures/script_default.yaml` stub (V3-8).

---

## 5. CHANGELOG

- **V2 → V3:**
  - Pendência 1.1 fechada retroativamente.
  - Patch 4 substituído por versão com `_sweep` (bug real no original).
  - Patch 9 ganha `buffer_ms` configurável.
  - Patch 11 ganha `--plain` e tratamento de stdout vazio.
  - 5 deltas de domínio adicionados (V3-4 a V3-8).
  - Sprint 0.1 cresce para 22 itens.
  - Teste de regressão do check_anonymity migra de bats para pytest.
