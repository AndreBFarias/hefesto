# FEAT-BLUETOOTH-CONNECTION-01 — Conexão funcional via Bluetooth (input + output + hotplug)

**Status:** **MERGED** em 2026-05-16 (sessão V3.1). Validado em hardware real
(DualSense A0:FA:9C:C3:11:F0 pareado + USB unplugged + daemon `transport=bt` +
lightbar magenta + profile activate fps via BT + evdev event2 + touchpad
event4 OK). Proof-of-work em `CHECKLIST_VALIDACAO_v3.md` seção "#29 — Bluetooth
(MERGED 2026-05-16)".

**Tipo:** feat (gap de feature reportada pelo usuário 2026-04-27).
**Wave:** fora de wave — pedido direto: "uma parada que deixamos de implementar é o funcionamento via conexão não por fio, mas via Bluetooth".
**Branch:** `rebrand/dualsense4unix`. PR #103.
**Estimativa:** 1 iteração de executor + 1 ciclo de validação runtime real.
**Dependências:** nenhuma; consolida peças já dispersas (regra 74 existente, backend transport-aware, ConnectionType.BT em pydualsense).

---

## Contexto

Investigação preliminar (planejador, 2026-04-27) demonstrou que a base do código **já é transport-agnostic** — o que falta é wire-up de instalação, documentação e validação runtime real:

1. **`src/hefesto_dualsense4unix/core/backend_pydualsense.py:263-269`** — `_detect_transport()` lê `pydualsense.conType` (USB ou BT) corretamente. Backend já distingue.
2. **`.venv/lib/python3.10/site-packages/pydualsense/pydualsense.py:143-169`** — `determineConnectionType()` decide pelo length do report (64 = USB, 78 = BT). `prepareReport()` usa `OUTPUT_REPORT_USB=0x02` (linha 515) ou `OUTPUT_REPORT_BT=0x31` (linha 577). Lightbar, triggers, rumble, mic LED e player LEDs já são despachados corretamente.
3. **`src/hefesto_dualsense4unix/core/evdev_reader.py:43-69`** — `find_dualsense_evdev()` filtra por VID `0x054C` + PID `{0x0CE6, 0x0DF2}` sem distinguir bus. Kernel `hid_playstation` expõe o mesmo evdev em USB ou BT — input via evdev funciona idêntico.
4. **`src/hefesto_dualsense4unix/daemon/connection.py:101-163`** — `reconnect_loop()` é agnóstico de transport; só chama `controller.connect()` com backoff 5s offline / 30s online.
5. **`src/hefesto_dualsense4unix/testing/fake_controller.py:65-73`** — `FakeController` aceita `transport: Transport = "usb" | "bt"`; `run.sh --smoke --bt` já existe e roda no CI.
6. **`assets/70-ps5-controller.rules:9-11`** — JÁ inclui linhas BT para hidraw uaccess (`KERNELS=="0005:054C:0CE6.*"` e `0DF2.*`). Permissão de leitura/escrita em `/dev/hidrawN` BT funciona.
7. **`assets/74-ps5-controller-hotplug-bt.rules`** — JÁ existe (FEAT-HOTPLUG-BT-01 catalogado em `docs/process/CHECKLIST_HARDWARE_V2.md:108-113`), mas **nunca foi formalizado em sprint** e **nunca foi validado em hardware real** (item 8 do checklist permanece com checkbox vazio).
8. **`scripts/install_udev.sh:14`** — JÁ copia `74-ps5-controller-hotplug-bt.rules` para `/etc/udev/rules.d/`.

### Lacunas reais identificadas

- **L1:** `install.sh:179-194` faz check de presença de `70-73` mas **não verifica** `74`. Se as 4 canônicas existirem, pula `install_udev.sh` e a regra 74 nunca chega ao sistema. Texto descritivo lista "Quatro regras" — precisa virar cinco.
- **L2:** README e docs não têm seção de pareamento BT (`bluetoothctl pair <MAC>` + `bluetoothctl trust + connect`). Usuário sem familiaridade com BT no Linux fica preso.
- **L3:** Item 8 do `CHECKLIST_HARDWARE_V2.md` ainda é PROTOCOL_READY (lição L-21-6) — não foi executado contra hardware BT real. Sprint precisa fechar com captura de log demonstrando `transport=bt` em `daemon.status` runtime.
- **L4:** Spec dedicado FEAT-HOTPLUG-BT-01 nunca foi escrito. A regra 74 entrou ao repo direto. Sem spec, validador não tem rastro do "porquê" e qualquer regressão futura perde contexto.
- **L5:** Não há aviso/guia para autosuspend BT (equivalente do A-05 USB). Em alguns adaptadores BT/CSR, `bluetoothd` ou `hci_uart` aplicam power save que pode causar latência transiente. Documentar como nota — não bloquear feature.

---

## Hipóteses verificadas vs descartadas

| Hipótese | Status | Evidência |
|---|---|---|
| H1: pydualsense não suporta BT | **FALSA** | linha 167 retorna `ConnectionType.BT`; linha 577 monta `outReport` BT |
| H2: evdev não enxerga BT | **FALSA** | filtro VID/PID em `find_dualsense_evdev`; kernel `hid_playstation` cobre ambos buses |
| H3: existe filtro `transport=="usb"` ignorando BT | **FALSA** | `rg "transport.*usb" src/` retornou zero filtros funcionais (apenas defaults e log fields) |
| H4: write em hidraw BT requer CRC ou packet diferente | **FALSA** | pydualsense já calcula CRC em `prepareReport` BT (linha 577+) |
| H5: regra hidraw 70 não cobre BT | **FALSA** | linhas 9-11 do `70-ps5-controller.rules` cobrem `KERNELS=="0005:054C:..."` |
| H6: instalador não instala regra 74 | **VERDADEIRA** | `install.sh:179-194` lista só 70-73 |
| H7: docs faltam guia de pareamento | **VERDADEIRA** | grep `bluetoothctl` em `README.md` retornou zero |
| H8: validação runtime BT nunca foi executada em hardware | **VERDADEIRA** | item 8 `CHECKLIST_HARDWARE_V2.md` `[ ]` vazio |

**Conclusão:** sprint vira **CHORE-VERIFY-BT + DOC-BT + INSTALLER-FIX** — não precisa tocar em código de runtime do daemon nem do backend.

---

## Escopo (touches autorizados)

### Arquivos a modificar

- `install.sh` — adicionar verificação de `/etc/udev/rules.d/74-ps5-controller-hotplug-bt.rules` no check do passo 3/9 (linha 179-185); ajustar o texto descritivo de "Quatro regras" para "Cinco regras" e listar a 74 com one-liner.
- `README.md` — adicionar seção curta "Conexão via Bluetooth" no fluxo de uso, com comandos canônicos: `bluetoothctl scan on`, `pair <MAC>`, `trust <MAC>`, `connect <MAC>`. Se README não tem fluxo de uso de hardware ainda, criar subseção.
- `docs/process/CHECKLIST_HARDWARE_V2.md` — atualizar item 8 (Hotplug BT) com sub-itens detalhados: detecção `daemon.status` retornando `transport=bt`, lightbar funcional via BT, triggers funcionais via BT, rumble funcional via BT, perfil ativo preservado em desligar/religar.

### Arquivos a criar

- `docs/process/sprints/FEAT-BLUETOOTH-CONNECTION-01.md` — este arquivo.
- `docs/process/sprints/FEAT-HOTPLUG-BT-01.md` — formalizar retroativamente o spec da regra 74 (paridade documental com USB-POWER-01 etc.). Conteúdo: histórico, comando `udevadm info -a /dev/hidrawN | grep KERNELS` para verificar match, sintaxe de wildcard `.*`, fallback se KERNELS difere por kernel.

### Arquivos NÃO a tocar

- `src/hefesto_dualsense4unix/core/backend_pydualsense.py` — funcional e transport-aware. Tocar = risco de regressão sem causa.
- `src/hefesto_dualsense4unix/core/evdev_reader.py` — `find_dualsense_evdev` já cobre BT.
- `src/hefesto_dualsense4unix/daemon/connection.py` — `reconnect_loop` já é agnóstico.
- `src/hefesto_dualsense4unix/testing/fake_controller.py` — modo BT já presente.
- `assets/74-ps5-controller-hotplug-bt.rules` — conteúdo final, só falta wire-up no installer.
- `assets/70-ps5-controller.rules` — já cobre BT.
- `scripts/install_udev.sh` — já copia regra 74.

---

## Critérios de aceite

1. `install.sh` passo 3/9 verifica também `/etc/udev/rules.d/74-ps5-controller-hotplug-bt.rules` na lógica de `need_udev`. Texto descritivo lista cinco regras.
2. `README.md` tem seção "Conexão via Bluetooth" com bloco de comandos `bluetoothctl` validado contra Pop!_OS / Ubuntu (PT-BR puro, acentuação correta).
3. `docs/process/sprints/FEAT-HOTPLUG-BT-01.md` criado com paridade ao formato `USB-POWER-01.md` (causa-raiz, patch aplicado, verificação, fora de escopo).
4. `docs/process/CHECKLIST_HARDWARE_V2.md` item 8 expandido com sub-itens (≥4 checks: status transport, lightbar, triggers, rumble, perfil preservado).
5. Proof-of-work runtime real (executor com hardware BT pareado): captura `hefesto-dualsense4unix status` mostrando `transport=bt` + log do daemon `controller_connected transport=bt` + screenshot da GUI com header ` Conectado Via BT`.
6. Smoke BT contínuo verde: `HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=bt HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke --bt` (já passa hoje; serve como regression guard).
7. Suite unit verde sem novos arquivos de teste obrigatórios — sprint não introduz código novo de runtime.
8. `./scripts/check_anonymity.sh` verde.
9. Acentuação periférica varrida em todos os arquivos modificados.

---

## Invariantes a preservar

- BRIEF `[CORE] Invariantes de arquitetura` — PT-BR obrigatório, zero emojis gráficos, glyphs Unicode de estado preservados (``, ``).
- BRIEF A-05 (USB autosuspend) — não confundir com BT. Se for citar power management BT, abrir nota separada; **não** estender a regra 72 para BT (BT não tem `power/control` em USB subsystem).
- BRIEF A-10 (multi-instância) — daemon hotplug BT NÃO deve gerar segunda instância. A unit `hefesto-gui-hotplug.service` já usa `acquire_or_bring_to_front("gui")` (BUG-TRAY-SINGLE-FLASH-01). Confirmar em runtime real que parear BT com GUI já aberta apenas traz ao foco, não duplica.
- BRIEF A-11 (race udev ADD duplo) — kernel BT pode emitir múltiplos `ACTION=="add"` no SUBSYSTEM=="hidraw" durante negociação L2CAP. O guard único é `acquire_or_bring_to_front` na GUI; não adicionar `pgrep` na unit.
- Lição L-21-6 — entregável de doc/protocolo precisa de validação humana real registrada no sprint; sem isso, status = `PROTOCOL_READY`, não `MERGED`.
- Lição L-21-3 — premissas sobre hidraw BT precisam ser validadas com `udevadm info -a /dev/hidrawN` em hardware real antes de virar texto canônico.

---

## Plano de implementação

### Etapa A — installer (5-10 linhas)

1. Editar `install.sh:179-185`. Adicionar `&& [[ -f /etc/udev/rules.d/74-ps5-controller-hotplug-bt.rules ]]` ao bloco condicional de `need_udev`.
2. Editar `install.sh:189-193`. Trocar "Quatro regras" por "Cinco regras"; adicionar linha `74-ps5-controller-hotplug-bt.rules    abre a GUI ao parear o controle via BT`.
3. Não tocar `scripts/install_udev.sh` — já copia a 74.

### Etapa B — README (15-30 linhas)

1. Localizar seção de uso/instalação no README. Se não existe subseção "Conexão", criar.
2. Adicionar bloco PT-BR com comandos `bluetoothctl`:
   ```bash
   bluetoothctl
   # dentro do prompt:
   power on
   agent on
   default-agent
   scan on
   # apertar e segurar PS + Create no controle até a luz piscar rapido
   # aguardar entrada "Wireless Controller" com MAC
   pair <MAC>
   trust <MAC>
   connect <MAC>
   exit
   ```
3. Frase final: "Após pareado, o daemon detecta automaticamente em ≤ 5 s; a GUI é trazida ao foco pela regra udev 74."

### Etapa C — sprint retroativa FEAT-HOTPLUG-BT-01 (60-100 linhas)

1. Criar `docs/process/sprints/FEAT-HOTPLUG-BT-01.md` no formato canônico (espelhando `USB-POWER-01.md`):
   - **Causa-raiz:** udev USB rule não dispara em BT (kernel não cria SUBSYSTEM=usb event para hidraw L2CAP).
   - **Patch aplicado:** arquivo `assets/74-ps5-controller-hotplug-bt.rules` (já no repo); diff de `install_udev.sh` (já em produção).
   - **Verificação manual:** `udevadm info -a /dev/hidrawN | grep KERNELS` deve mostrar `0005:054C:0CE6.*` ou `0DF2.*`.
   - **Por que SUBSYSTEM=hidraw e não bluetooth:** o kernel `hid_playstation` cria o nó hidraw como ponto unificado independente do bus; a unit precisa bater no momento em que o nó está pronto para escrita, e isso só acontece no add do hidraw.
   - **Fora de escopo:** power management BT (separado).

### Etapa D — CHECKLIST_HARDWARE_V2 item 8 expandido

Substituir conteúdo atual do item 8 por sub-checklist:

```markdown
## Item 8 — Hotplug BT (FEAT-HOTPLUG-BT-01) + Conexão BT funcional (FEAT-BLUETOOTH-CONNECTION-01)

### 8.1 — Pareamento inicial
- [ ] `bluetoothctl pair <MAC>` completa sem erro.
- [ ] `bluetoothctl connect <MAC>` retorna "Connection successful".
- [ ] `lsusb | grep 0ce6` deve estar VAZIO (nenhuma USB ativa).
- [ ] `bluetoothctl devices Connected` lista o controle.

### 8.2 — Detecção pelo daemon
- [ ] `hefesto-dualsense4unix status` retorna `connected=True transport=bt battery_pct=<num>`.
- [ ] Log do daemon (`journalctl --user -u hefesto-dualsense4unix.service`) tem `controller_connected transport=bt`.

### 8.3 — Output funcional via BT
- [ ] `hefesto-dualsense4unix led --color "#FF00FF"` — lightbar fica magenta no controle.
- [ ] `hefesto-dualsense4unix profile activate shooter` — gatilhos endurecem (rigid em L2/R2).
- [ ] `hefesto-dualsense4unix profile activate aventura` — multi-position L2 + R2 com 4-5 zonas (cf. item 10).
- [ ] Rumble curto via algum perfil que dispara — motores vibram.

### 8.4 — Hotplug GUI
- [ ] Com daemon parado e GUI fechada: parear BT → GUI abre via regra 74. **Validação visual obrigatória** (skill `validacao-visual` + PNG + sha256).
- [ ] Com GUI aberta: parear BT novamente → janela existente vai ao foco, NÃO duplica (cobre A-10 + A-11 sob hidraw bus).

### 8.5 — Resiliência
- [ ] Desligar controle (PS por 10 s), aguardar 5 s, religar/reconectar.
    - Esperado: `reconnect_loop` detecta em ≤ 5 s; perfil ativo preservado; header GUI volta verde.
    - Critério de falha: reconexão não acontece; perfil volta para `fallback`; cursor errático (regressão BUG-MULTI-INSTANCE-01).
```

### Etapa E — Proof-of-work runtime real

Executor com hardware BT pareado roda esta sequência e anexa logs ao spec:

```bash
# pré
bluetoothctl devices Connected | grep -i "wireless\|dualsense" || echo "PAREAR PRIMEIRO"
lsusb | grep 0ce6 && echo "FALHA: USB ainda conectado, desplugue para teste BT puro"

# install com regra 74
sudo bash scripts/install_udev.sh
ls /etc/udev/rules.d/ | grep 74

# daemon
systemctl --user restart hefesto-dualsense4unix.service
sleep 5
hefesto-dualsense4unix status > /tmp/hefesto_bt_status.txt
journalctl --user -u hefesto-dualsense4unix.service --since "10 seconds ago" \
    | grep -E "controller_connected|transport" > /tmp/hefesto_bt_log.txt

# output BT
hefesto-dualsense4unix led --color "#FF00FF"
sleep 1
hefesto-dualsense4unix profile activate shooter

# GUI hotplug (se houver bench físico para parear durante teste)
.venv/bin/python -m hefesto_dualsense4unix.app.main &
sleep 4
WID=$(xdotool search --name "Hefesto - Dualsense4Unix v" | head -1)
TS=$(date +%Y%m%dT%H%M%S)
xdotool windowactivate "$WID" && sleep 0.4
import -window "$WID" "/tmp/hefesto_bt_gui_${TS}.png"
sha256sum "/tmp/hefesto_bt_gui_${TS}.png"

# anexar logs e PNG ao FEAT-BLUETOOTH-CONNECTION-01.md
```

Esperado em `/tmp/hefesto_bt_status.txt`:
```
connected   = True
transport   = bt
battery_pct = <num>
```

Esperado em `/tmp/hefesto_bt_log.txt`:
```
... controller_connected transport=bt ...
```

Esperado em `/tmp/hefesto_bt_gui_*.png`: header GUI mostra ` Conectado Via BT` (verde, U+25CF).

---

## Aritmética estimada

| Arquivo | Δ linhas | Direção |
|---|---|---|
| `install.sh` | +6 a +8 | adição (verificação + texto) |
| `README.md` | +20 a +30 | adição (seção BT) |
| `docs/process/CHECKLIST_HARDWARE_V2.md` | +25 a +35 | substituição de item 8 (de 6L para ~35L) |
| `docs/process/sprints/FEAT-HOTPLUG-BT-01.md` | ~80 | criação (retroativo) |
| `docs/process/sprints/FEAT-BLUETOOTH-CONNECTION-01.md` | este arquivo | criação |

**Sem código de runtime alterado** — zero risco de regressão de testes unit.
**Touches periféricos:** apenas docs + 1 arquivo bash (install.sh).

---

## Testes

Sem novos testes unitários necessários. A cobertura runtime existente é:

- `tests/unit/test_fake_controller_capture_loader.py` — valida `transport=bt` em FakeController loader.
- Smoke `./run.sh --smoke --bt` — exercita `transport=bt` end-to-end (já no contrato de runtime do BRIEF).
- `tests/unit/test_evdev_reader.py` — valida `find_dualsense_evdev` por VID/PID (cobre BT implícito).

Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER = 0`. Suite total: ≥998 testes (BRIEF rodapé 2026-04-23).

---

## Proof-of-work esperado

- Diff final do `install.sh`, `README.md`, `CHECKLIST_HARDWARE_V2.md` e dois arquivos novos.
- Runtime sintético (sem hardware):
  ```bash
  bash scripts/dev-setup.sh
  HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=bt HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke --bt
  HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=usb HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke
  .venv/bin/pytest tests/unit -v --no-header -q
  .venv/bin/ruff check src/ tests/
  .venv/bin/mypy src/hefesto_dualsense4unix
  ./scripts/check_anonymity.sh
  ```
- Runtime real (executor com hardware BT pareado): comandos da Etapa E acima, com `/tmp/hefesto_bt_status.txt`, `/tmp/hefesto_bt_log.txt` e `/tmp/hefesto_bt_gui_*.png` (sha256) anexados ao spec final.
- Validação visual da GUI com transport=bt no header (skill `validacao-visual`).
- Hipótese verificada: `rg "transport.*usb"` em `src/` retorna zero filtros funcionais (já confirmado pelo planejador, repetir como gate antes de fechar sprint).
- Acentuação periférica varrida em todos arquivos tocados.

### Status final esperado

- Se executor consegue hardware BT real: `MERGED` (lição L-21-6 satisfeita).
- Se executor não consegue hardware BT no ciclo: `PROTOCOL_READY` — código + docs entregues, runtime real aguardando bench. Status separado evita falso positivo de release.

---

## Riscos e não-objetivos

### Não-objetivos

- **Não** implementar power management BT (autosuspend BT equivalente A-05). Se aparecer desconexão transiente em BT, abrir sprint `BT-POWER-01` separada.
- **Não** estender regra 72 (autosuspend USB) para BT — semântica diferente.
- **Não** criar UI dedicada de pareamento BT na GUI (fora de escopo; usuário usa `bluetoothctl` direto). Se for pedido futuro: sprint `UI-BT-PAIRING-01`.
- **Não** mexer no backend pydualsense — funcional via teste empírico (ConnectionType.BT path).

### Riscos

- **R1:** `KERNELS=="0005:054C:0CE6.*"` pode não bater em todos os kernels — `udevadm info` é a salvaguarda. Se em hardware real do executor o KERNELS for `0005:054C:0CE6.0001` mas em outro kernel for `0005:054C:0CE6.0010`, o `.*` cobre. Se o formato mudar radicalmente (ex.: `0005:054C:0CE6_<hash>`), abrir sprint de fallback.
- **R2:** Múltiplos `ACTION=="add"` em hidraw BT durante negociação L2CAP — coberto por A-11 + `acquire_or_bring_to_front`. Validar em runtime real.
- **R3:** Adaptador BT do usuário com firmware antigo pode não negociar HID corretamente — fora de escopo do projeto; documentar como troubleshoot.

### Achado colateral (protocolo anti-débito)

Se executor descobrir durante runtime real:
- **Latência > 50ms em BT** → sprint nova `PERF-BT-LATENCY-01`.
- **Reconnect_loop não detecta BT desligado** → sprint nova `BUG-RECONNECT-BT-01`.
- **Bug em prepareReport BT do pydualsense** → sprint nova `UPSTREAM-PYDUALSENSE-BT-01` (eventualmente upstream).

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-Dualsense4Unix/VALIDATOR_BRIEF.md`
- Precedente histórico (formato): `docs/process/sprints/USB-POWER-01.md`, `docs/process/sprints/UX-RECONNECT-01.md`.
- Catálogo: `docs/process/CHECKLIST_HARDWARE_V2.md` item 8 (FEAT-HOTPLUG-BT-01).
- Asset existente: `assets/74-ps5-controller-hotplug-bt.rules`.
- Lições aplicadas: L-21-3 (ler código antes do spec — feito), L-21-6 (PROTOCOL_READY vs MERGED — explicitado), L-21-7 (premissa empírica — `udevadm info` na verificação).
- pydualsense reference: `.venv/lib/python3.10/site-packages/pydualsense/pydualsense.py:143-169` (`determineConnectionType`), `:504-636` (`prepareReport` USB/BT branches).

---

*"O ferro frio resiste ao martelo. O ferro quente cede. A diferença é só a brasa." — sobre por que esta sprint é leve: a forja já está acesa.*
