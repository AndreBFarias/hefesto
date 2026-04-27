# CLUSTER-IPC-STATE-PROFILE-01 — daemon.state_full ao vivo + persistência de profile.switch + lock manual no autoswitch

**Tipo:** cluster de fix (3 bugs relacionados — Bug A crítico, Bugs B e C de UX).
**Branch:** `rebrand/dualsense4unix` (continuação; PR #103).
**Estimativa:** 1 iteração de executor com 3 commits self-contained + 1 commit de testes consolidados (4 commits no PR).
**Dependências:** nenhuma. Atinge árvore atual em `rebrand/dualsense4unix` HEAD.

---

## Contexto

Três bugs reportados em runtime real (USB, hardware OK, daemon systemd ativo) compartilham a mesma área de código (`daemon/ipc_handlers.py` + `profiles/autoswitch.py` + `profiles/manager.py`) e o mesmo conceito (sincronização runtime/disco/IPC do estado de perfil + estado do controle). Atacar separados forçaria 2-3 PRs do mesmo arquivo com merge conflicts. Cluster faz sentido.

Lido na exploração (lição L-21-3):

- `src/hefesto_dualsense4unix/daemon/ipc_handlers.py:175-231` — `_handle_daemon_state_full`. Lê `snap = self.store.snapshot()` e usa `snap.controller.raw_lx/raw_ly/l2_raw/r2_raw`. Para `buttons`, abre snapshot independente em `self.controller._evdev` (linhas 187-194). Não compartilha com o que `_poll_loop` armazena.
- `src/hefesto_dualsense4unix/daemon/ipc_handlers.py:46-54` — `_handle_profile_switch`. Chama `self.profile_manager.activate(name)` que internamente persiste via `save_last_profile()` (cadeia `manager.activate → save_last_profile → ~/.config/hefesto-dualsense4unix/session.json`). NÃO chama `_write_active_marker` (esse é o `active_profile.txt` da CLI).
- `src/hefesto_dualsense4unix/profiles/manager.py:58-68` — `ProfileManager.activate` já chama `save_last_profile(profile.name)` (linha 67) — `session.json` é o canônico.
- `src/hefesto_dualsense4unix/utils/session.py:29-43` — `save_last_profile` grava `~/.config/hefesto-dualsense4unix/session.json` com chave `last_profile`.
- `src/hefesto_dualsense4unix/daemon/connection.py:70-90` — `restore_last_profile()` lê `load_last_profile()` (session.json) na conexão. Esse é o canônico que daemon respeita no boot.
- `src/hefesto_dualsense4unix/cli/cmd_profile.py:294-308` — `_write_active_marker / read_active_marker` usam `active_profile.txt`. Esse marker NÃO é lido pelo daemon — só pela CLI (`profile current` em :222).
- `src/hefesto_dualsense4unix/profiles/autoswitch.py:51-103` — `AutoSwitcher.run` faz poll a 2Hz; `_activate` respeita `store.manual_trigger_active` (BUG-MOUSE-TRIGGERS-01) mas NÃO respeita lock manual de `profile.switch` por usuário.
- `src/hefesto_dualsense4unix/daemon/state_store.py:79-96` — `mark_manual_trigger_active / clear_manual_trigger_active` já existem como precedente. Padrão a replicar.
- `src/hefesto_dualsense4unix/daemon/lifecycle.py:381-449` — `_poll_loop`. Linha 414 grava `state` no store. Linha 425 chama `_dispatch_mouse_emulation(state, buttons_pressed)` com `state` LIVE. Confirma: dispatch_mouse usa `state` direto da chamada `controller.read_state()`, IPC handler usa `store.snapshot()` (que é populado pelo mesmo state via `update_controller_state(state)`).

**Reanálise crítica das hipóteses do reporter:**

- **Bug A:** sticks=128, l2/r2=0 é o snapshot **default neutro** de `ControllerState` (`controller.py:65-68`). Indica que `store._controller_state` ainda está em algum default OU que está sendo atualizado mas com valores neutros (evdev não conectou). O `controller._evdev.is_available()` retornar `False` faz `read_state()` cair no fallback pydualsense (`backend_pydualsense.py:153-177`), que com `hid_playstation` ativo "os valores não atualizam" (comentário literal do código, linha 153). Hipótese forte: **evdev_reader não conectou no startup do daemon, então o ramo primário (`_evdev.is_available()`) retorna False e o fallback retorna estado estagnado**. O dispatch_mouse "funciona" porque mesmo no fallback degenerado os sticks às vezes mudam (depende do path code) — OU porque o usuário viu cursor mexer em outro contexto. Verificar empiricamente é parte da sprint.
- **Bug B:** `manager.activate()` JÁ persiste via `save_last_profile()` → `session.json`. Daemon JÁ restaura via `restore_last_profile()` na conexão. Premissa do reporter ("não escreve `active_profile.txt`") é **tecnicamente correta** porém tangencial — o `active_profile.txt` é legado da CLI, não é o canônico do daemon. **O sintoma reportado ("perfil volta ao anterior na próxima sessão") é cascata de Bug C**: autoswitch reativa em <1s o perfil que casa por wm_class, então `session.json` acaba salvando o autoswitch em vez da escolha manual. Bug B real é **alinhar `active_profile.txt` com `session.json`** (ambos refletindo a verdade) ou aposentar `active_profile.txt`.
- **Bug C:** confirmado pela leitura de `autoswitch.py:91-103`. `_activate` respeita `manual_trigger_active` mas não tem flag para `manual_profile_switch`. Fix proposto pelo reporter (lock temporário 30s) é alinhado com o precedente `manual_trigger_active`.

---

## Justificativa de cluster

Os 3 bugs compartilham:
- `daemon/ipc_handlers.py` (Bug A reescreve `_handle_daemon_state_full`; Bug B pode ajustar `_handle_profile_switch` para também atualizar `active_profile.txt` por simetria).
- `daemon/state_store.py` (Bug C adiciona `manual_profile_lock_until` análogo a `manual_trigger_active`).
- `profiles/autoswitch.py` (Bug C consulta o lock).
- `daemon/lifecycle.py` (Bug A pode precisar expor último `state` LIVE — não só via store).
- Conceito comum: como state e profile sincronizam runtime/disco/IPC.

Atacar separados forçaria 2-3 PRs no mesmo arquivo com merge conflicts. Cluster é o caminho com menor débito.

Lição L-21-7 não se aplica (sem dependência de pacote externo nova).

---

## Escopo (touches autorizados)

### Arquivos a modificar

- `src/hefesto_dualsense4unix/daemon/ipc_handlers.py` — Bug A (`_handle_daemon_state_full` lê `state` LIVE) e Bug B (`_handle_profile_switch` aciona lock + sincroniza `active_profile.txt` com `session.json`).
- `src/hefesto_dualsense4unix/daemon/state_store.py` — Bug C: novos métodos `mark_manual_profile_lock(until: float)` / `manual_profile_lock_active(now: float) -> bool` + campo `_manual_profile_lock_until: float`.
- `src/hefesto_dualsense4unix/profiles/autoswitch.py` — Bug C: `_activate` consulta `store.manual_profile_lock_active(now)` antes de aplicar (logo após o check de `manual_trigger_active`).
- `src/hefesto_dualsense4unix/daemon/lifecycle.py` — Bug A: novo slot `_last_state: ControllerState | None = None` em `Daemon`, atualizado em `_poll_loop` logo após `read_state` (1 linha).
- `src/hefesto_dualsense4unix/cli/cmd_profile.py` — Bug B: ajuste mínimo se necessário (provavelmente nenhum — CLI já chama `_activate_via_ipc_or_fallback` que escreve marker).

### Arquivos a criar

- `tests/unit/test_ipc_state_full_live.py` — Bug A (3-5 cenários: fresh state via store, fresh state via daemon._last_state, buttons via state.buttons_pressed em vez de evdev independente, fallback gracioso quando store vazio).
- `tests/unit/test_ipc_profile_switch_persist.py` — Bug B (2-3 cenários: profile.switch grava session.json via manager.activate, profile.switch também grava active_profile.txt para paridade CLI/IPC, timeout não corrompe arquivo).
- `tests/unit/test_autoswitch_manual_lock.py` — Bug C (4-5 cenários: manual lock bloqueia _activate, lock expira após N segundos, profile.switch IPC seta o lock, store API isolada).

### Arquivos NÃO a tocar (invariantes do BRIEF)

- `src/hefesto_dualsense4unix/daemon/ipc_server.py` — não tocar dispatcher; só o mixin de handlers.
- `src/hefesto_dualsense4unix/utils/session.py` — `save_last_profile` é canônico, não mudar.
- `src/hefesto_dualsense4unix/profiles/manager.py:58-68` — `ProfileManager.activate` já faz `save_last_profile`. Não duplicar no handler IPC.
- Nenhum dos 4 JSONs em `assets/profiles_default/` — escopo de schema fechado.
- Nenhum CSS, glade, Pango markup — não há toque visual.
- Glyphs Unicode de estado (U+25CF, U+25CB) — preservar (armadilha A-04).

---

## Critérios de aceite

### Bug A — `daemon.state_full` ao vivo

1. `_handle_daemon_state_full` retorna `lx, ly, l2_raw, r2_raw, buttons` refletindo o **último tick do `_poll_loop`** quando hardware está conectado e usuário aciona qualquer input.
2. `buttons` é populado a partir de `state.buttons_pressed` (que já consolida evdev + HID-raw `mic_btn` em `backend_pydualsense.py:140-152`), não a partir de uma chamada independente a `controller._evdev.snapshot()` no async loop. Isso elimina divergência poll-loop/IPC e remove um snapshot evdev redundante por chamada IPC (alinhado com armadilha A-09 resolvida).
3. Quando `_poll_loop` ainda não rodou nenhum tick (boot, antes da conexão), o handler retorna o snapshot do `store` (que pode estar `None` ou neutro) sem levantar — fallback equivalente ao atual.
4. Diagnóstico complementar: se `store.controller_state` está em valores neutros (`raw_lx=128, raw_ly=128, l2_raw=0, r2_raw=0` E `buttons=frozenset()`) por ≥3 ticks consecutivos com `controller.is_connected() == True`, logar `state_stale_warning` (1× por minuto, com contadores) — ajuda a diagnosticar evdev_reader não conectado em campo.
5. Não quebra `_handle_daemon_status` (parente direto).

### Bug B — `profile.switch` paridade de persistência

6. `_handle_profile_switch` continua chamando `manager.activate(name)` (que persiste `session.json` — canônico). Adicionalmente, escreve `active_profile.txt` via mesma helper que a CLI usa (`_write_active_marker`) para paridade de marker.
7. A escrita de `active_profile.txt` é best-effort: falha (disco cheio, permissão) loga warning mas NÃO falha o IPC. `session.json` é a fonte de verdade.
8. Se `manager.activate` levantar (perfil inválido), `active_profile.txt` NÃO é tocado (atomicidade do conjunto).
9. Documentação inline (docstring de `_handle_profile_switch`) registra: "session.json é canônico para daemon restore; active_profile.txt é marker secundário para CLI legacy. Ambos atualizados em `profile.switch`."

### Bug C — autoswitch respeita lock manual

10. Novo campo `StateStore._manual_profile_lock_until: float = 0.0` (timestamp absoluto de `loop.time()` ou `time.monotonic()`; escolher um e ser consistente).
11. Novo método `StateStore.mark_manual_profile_lock(until: float) -> None` adquire o lock; `manual_profile_lock_active(now: float) -> bool` retorna `now < self._manual_profile_lock_until`.
12. Constante `MANUAL_PROFILE_LOCK_SEC = 30.0` em `state_store.py` (top-level, exportada). Sprint não introduz config — valor canônico fixo.
13. `_handle_profile_switch` calcula `until = time.monotonic() + MANUAL_PROFILE_LOCK_SEC` e chama `store.mark_manual_profile_lock(until)` antes de retornar (após o `manager.activate` ter sucesso).
14. `AutoSwitcher._activate` consulta `self.store.manual_profile_lock_active(loop.time())` (ou `time.monotonic()` — alinhar) e, se ativo, faz no-op com log `autoswitch_suppressed_by_manual_profile_lock` (separado do log existente para `manual_trigger_active`).
15. Após o lock expirar, autoswitch volta a operar normalmente (próximo tick do `AutoSwitcher.run`).
16. Lock é renovado em cada `profile.switch` IPC (escolha mais recente vence). Não acumula.
17. Lock NÃO é setado por: autoswitch interno (recursão evitada), `daemon.reload`, restore_last_profile no boot. SÓ é setado pelo handler `profile.switch` IPC (entrada manual do usuário via tray/CLI/GUI).

### Quality gates universais

18. Todos os 998+ testes unitários pré-existentes continuam passando (baseline a confirmar com `.venv/bin/pytest tests/unit --collect-only -q | tail -1` antes do executor começar — lição L-21-2).
19. Smoke USB+BT verdes (FakeController; ver Contratos de runtime do BRIEF).
20. Lint (ruff) + types (mypy) verdes nos arquivos modificados.
21. Acentuação PT-BR varrida em todos os arquivos modificados (varredura periférica do BRIEF). Padrões a procurar: `funcao`, `validacao`, `comunicacao`, `configuracao`, `descricao`, `aplicacao`, `direcao`, `ativacao`, `criacao`, `restauracao`, `transicao`.
22. `./scripts/check_anonymity.sh` verde.

---

## Invariantes a preservar

- **Soberania de subsistema (meta-regra 9.3):** sprint não toca socket de daemon vivo; nenhum write em `~/.config/` que o usuário não tenha solicitado via IPC.
- **A-09 (evdev snapshot dedup):** Bug A REMOVE um consumidor de `evdev.snapshot()` (linha 187-194 do handler atual) — o handler passa a usar `state.buttons_pressed`. Alinha com a regra de "1 snapshot/tick" introduzida em REFACTOR-HOTKEY-EVDEV-01.
- **A-07 (wire-up de subsystem):** Bug A adiciona slot `_last_state` em `Daemon` (lifecycle.py). Mas isso é apenas um cache de leitura — não é subsystem novo, não exige `_start_*` / `_shutdown` / wire em 3 pontos. Suficiente: declarar slot, atualizar em `_poll_loop` 1 linha, ler em `_handle_daemon_state_full`.
- **A-08 (closure captura config):** N/A — não há closure nova capturando config.
- **PT-BR + zero emojis:** docstrings e logs em PT-BR; identificadores de protocolo (`profile.switch`, `daemon.state_full`) preservados em EN.
- **Logging via `structlog`:** novo log `state_stale_warning` e `autoswitch_suppressed_by_manual_profile_lock` via `logger.info` / `logger.warning`.

---

## Plano de implementação

### Commit 1 — Bug A (daemon.state_full ao vivo)

1. Em `src/hefesto_dualsense4unix/daemon/lifecycle.py`:
   - Adicionar slot `_last_state: ControllerState | None = None` no dataclass `Daemon` (próximo aos outros slots `_*`, ordem-aritmética não importa por ser dataclass com defaults).
   - No `_poll_loop`, logo após `self.store.update_controller_state(state)` (linha ~414), adicionar `self._last_state = state` (1 linha).
   - Em `_shutdown` (procurar bloco existente), adicionar `self._last_state = None`.
2. Em `src/hefesto_dualsense4unix/daemon/ipc_handlers.py`, reescrever `_handle_daemon_state_full` (linhas 175-231):
   - Tentar `state = getattr(self.daemon, "_last_state", None)` primeiro. Fallback: `state = self.store.controller_state` (compat com testes que injetam store sem daemon).
   - Substituir o bloco try/except do evdev (linhas 187-194) por `buttons = sorted(state.buttons_pressed) if state else []`.
   - Mapear: `lx = state.raw_lx if state else 128` (etc) — mesmo padrão atual mas via `state` em vez de `snap.controller`.
   - Manter o resto do retorno (`mouse_emulation`, `rumble_policy`, `counters`) intacto.
   - Adicionar contador de stale: se `state and self.controller.is_connected() and state.raw_lx == 128 and state.raw_ly == 128 and state.l2_raw == 0 and state.r2_raw == 0 and not state.buttons_pressed`, incrementar `self.store.bump("state_full.stale_neutral")`. Quando passar de 3 (configurável via constante local `STALE_WARN_THRESHOLD = 3`), logar 1× warning `state_stale_neutral_warning` com `state_full_calls` no extra. Threshold é por chamadas IPC, não por ticks (mais simples; aceitável).

### Commit 2 — Bug B (profile.switch paridade de persistência)

1. Em `src/hefesto_dualsense4unix/daemon/ipc_handlers.py`:
   - Em `_handle_profile_switch` (linhas 46-54), após `profile = self.profile_manager.activate(name)`, adicionar bloco try/except que chama o helper de marker da CLI:
     ```python
     try:
         from hefesto_dualsense4unix.cli.cmd_profile import _write_active_marker
         _write_active_marker(profile.name)
     except Exception as exc:
         logger.warning("active_marker_write_failed", profile=profile.name, err=str(exc))
     ```
   - Atualizar docstring do handler explicando paridade `session.json` (canônico daemon) + `active_profile.txt` (marker CLI legado).
2. Avaliar mover `_write_active_marker` para `hefesto_dualsense4unix/utils/session.py` como `save_active_marker(name)` para evitar import de `cli.*` no daemon (cli.* deveria depender do daemon, não o contrário). Decisão do executor: se import circular não acontecer, manter; se acontecer, mover. Adicionar 1 linha em `__all__` se mover.

### Commit 3 — Bug C (autoswitch respeita lock manual de profile.switch)

1. Em `src/hefesto_dualsense4unix/daemon/state_store.py`:
   - Top-level: constante `MANUAL_PROFILE_LOCK_SEC: float = 30.0`.
   - Adicionar campo `self._manual_profile_lock_until: float = 0.0` no `__init__`.
   - Novo método `mark_manual_profile_lock(self, until: float) -> None` (com `self._lock`).
   - Novo método `manual_profile_lock_active(self, now: float) -> bool` (retorna `now < self._manual_profile_lock_until`).
   - Atualizar `__all__` com `MANUAL_PROFILE_LOCK_SEC`.
2. Em `src/hefesto_dualsense4unix/daemon/ipc_handlers.py` `_handle_profile_switch` (continuação do commit 2):
   - Após o `_write_active_marker`, adicionar:
     ```python
     import time
     until = time.monotonic() + MANUAL_PROFILE_LOCK_SEC
     self.store.mark_manual_profile_lock(until)
     ```
   - Importar `MANUAL_PROFILE_LOCK_SEC` do state_store.
3. Em `src/hefesto_dualsense4unix/profiles/autoswitch.py`:
   - Em `_activate` (linha 91), depois do check de `manual_trigger_active` (linhas 97-103), adicionar:
     ```python
     import time
     if self.store is not None and self.store.manual_profile_lock_active(time.monotonic()):
         logger.info(
             "autoswitch_suppressed_by_manual_profile_lock",
             candidate=name,
             wm_class=info.get("wm_class", ""),
         )
         return
     ```

### Commit 4 — Testes consolidados

1. `tests/unit/test_ipc_state_full_live.py` — 3-5 cenários cobrindo critérios 1-5.
2. `tests/unit/test_ipc_profile_switch_persist.py` — 2-3 cenários cobrindo critérios 6-9.
3. `tests/unit/test_autoswitch_manual_lock.py` — 4-5 cenários cobrindo critérios 10-17. Usar `monkeypatch` para `time.monotonic` quando preciso (precedente: `tests/unit/test_subsystem_autoswitch.py`).

---

## Aritmética estimada (validação L-21-1 + L-21-3)

Sem meta de redução de LOC. Estimativa de delta:

| Arquivo | LOC atual | Delta esperado | LOC pós-sprint |
|---|---:|---:|---:|
| `daemon/ipc_handlers.py` | 446 | +12 (Bug A reescreve em ~−5; Bug B+C adicionam ~+17) | ~458 |
| `daemon/state_store.py` | 135 | +20 (Bug C: 1 const + 1 campo + 2 métodos + lock) | ~155 |
| `profiles/autoswitch.py` | 125 | +10 (Bug C: import + bloco de check) | ~135 |
| `daemon/lifecycle.py` | 495 | +3 (slot + write em poll + reset em shutdown) | ~498 |

Limite de 800 linhas por arquivo respeitado em todos. Nenhum arquivo cruza 800.

Testes novos: ~150-200L distribuídos em 3 arquivos (~50-70L cada).

Baseline de testes pré-sprint: rodar `.venv/bin/pytest tests/unit --collect-only -q | tail -1` para fixar `BASELINE = N`. FAIL_AFTER esperado: 0. PASS_AFTER esperado: `BASELINE + 12 a 18` (3 arquivos novos × 4-6 testes).

---

## Proof-of-work esperado

### Diff final
- 4 commits self-contained no PR #103, mensagens em PT-BR.

### Runtime real (do BRIEF "Contratos de runtime")

```bash
# 0. Setup (idempotente)
bash scripts/dev-setup.sh

# 1. Smoke FakeController USB+BT
HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=usb HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke
HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=bt  HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke --bt

# 2. Suíte unitária
.venv/bin/pytest tests/unit -v --no-header -q

# 3. Testes específicos da sprint
.venv/bin/pytest tests/unit/test_ipc_state_full_live.py tests/unit/test_ipc_profile_switch_persist.py tests/unit/test_autoswitch_manual_lock.py -v

# 4. Lint + types
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto_dualsense4unix

# 5. Anonimato
./scripts/check_anonymity.sh
```

### Runtime real com hardware (USB DualSense conectado)

```bash
# Setup: hardware DualSense via USB conectado, daemon ativo
systemctl --user restart hefesto-dualsense4unix.service && sleep 3

# Bug A — state_full retorna dados ao vivo
# (usuário aperta e segura CROSS, mexe stick esquerdo)
.venv/bin/python -c "
import asyncio
from hefesto_dualsense4unix.cli.ipc_client import IpcClient
async def main():
    async with IpcClient.connect(timeout=2) as c:
        st = await c.call('daemon.state_full')
        print('buttons:', st.get('buttons'))
        print('lx:', st.get('lx'))
        print('ly:', st.get('ly'))
        print('l2_raw:', st.get('l2_raw'))
asyncio.run(main())
"
# Esperado: buttons inclui 'cross' enquanto usuário segura X; lx/ly mudam quando stick mexe; l2_raw>0 ao puxar L2.

# Bug B — profile.switch persiste ambos session.json e active_profile.txt
.venv/bin/python -c "
import asyncio
from hefesto_dualsense4unix.cli.ipc_client import IpcClient
async def main():
    async with IpcClient.connect(timeout=2) as c:
        await c.call('profile.switch', {'name': 'shooter'})
asyncio.run(main())
"
sleep 1
cat ~/.config/hefesto-dualsense4unix/active_profile.txt    # esperado: shooter
python -c "import json; print(json.load(open('$HOME/.config/hefesto-dualsense4unix/session.json'))['last_profile'])"  # esperado: shooter

# Bug C — autoswitch respeita lock manual por 30s
# (usuário precisa estar em janela cuja regra ativa "browser" — ex: Firefox aberto e focado)
.venv/bin/hefesto-dualsense4unix profile activate shooter
sleep 5
.venv/bin/hefesto-dualsense4unix status | grep active_profile
# Esperado: shooter (lock ainda ativo, autoswitch respeita)

sleep 30
# Após lock expirar:
.venv/bin/hefesto-dualsense4unix status | grep active_profile
# Esperado: browser (autoswitch volta a operar normalmente)
```

### Validação visual
N/A — sem toque em GUI/TUI/CSS/Pango. Sem captura PNG necessária.

### Acentuação periférica
Varredura nos 4 arquivos modificados + 3 arquivos novos:

```bash
rg -n "funcao|validacao|comunicacao|configuracao|descricao|aplicacao|direcao|ativacao|criacao|restauracao|transicao" src/hefesto_dualsense4unix/daemon/ipc_handlers.py src/hefesto_dualsense4unix/daemon/state_store.py src/hefesto_dualsense4unix/profiles/autoswitch.py src/hefesto_dualsense4unix/daemon/lifecycle.py tests/unit/test_ipc_state_full_live.py tests/unit/test_ipc_profile_switch_persist.py tests/unit/test_autoswitch_manual_lock.py
```
Resultado esperado: 0 hits.

### Hipótese verificada (lição L-21-3)

Identificadores citados confirmados via grep antes do spec:
- `_handle_daemon_state_full` em `ipc_handlers.py:175` — confirmado.
- `_handle_profile_switch` em `ipc_handlers.py:46` — confirmado.
- `manager.activate` em `manager.py:58` — confirmado.
- `save_last_profile` em `session.py:29` — confirmado.
- `_write_active_marker` em `cmd_profile.py:294` — confirmado.
- `manual_trigger_active` flag em `state_store.py:79` — confirmado (precedente para o lock).
- `AutoSwitcher._activate` em `autoswitch.py:91` — confirmado.
- `_poll_loop` + `update_controller_state` em `lifecycle.py:381,414` — confirmado.
- `_dispatch_mouse_emulation` recebe `state` LIVE em `lifecycle.py:425` — confirmado.

---

## Riscos e não-objetivos

### Riscos

1. **Bug A pode revelar problema mais profundo de evdev_reader.** Se em runtime real o teste mostrar `state.buttons_pressed = frozenset()` mesmo com botão pressionado, a raiz não está no handler IPC mas em `EvdevReader.start()` falhando silenciosamente. Nesse caso, o executor abre sprint nova `BUG-EVDEV-READER-NOT-CONNECTED-01` (achado colateral; protocolo anti-débito 9.7) e o critério 4 (log `state_stale_warning`) ajuda a diagnosticar. A sprint atual ainda fecha o gap arquitetural — IPC handler passa a refletir o que o poll loop vê.
2. **Lock de 30s pode atrapalhar usuários que querem autoswitch agressivo.** Tradeoff aceito: 30s é curto o suficiente para não frustrar, longo o suficiente para a UX "ativei manualmente, ele respeitou". Reabrir como sprint nova se feedback de campo pedir. Não introduzir config nesta sprint (escopo fechado).
3. **`active_profile.txt` ainda diverge se usuário edita à mão.** Não escopo desta sprint resolver — é caso patológico, não bug.
4. **Renovar lock em todo `profile.switch` (critério 16) pode mascarar autoswitch loops.** Mitigação: lock SÓ é setado por handler IPC (entrada externa); autoswitch interno chama `manager.activate` direto (não passa pelo handler), portanto não auto-renova (critério 17).

### Não-objetivos

- Aposentar `active_profile.txt` (sprint à parte se desejar).
- Tornar `MANUAL_PROFILE_LOCK_SEC` configurável via `DaemonConfig` (sprint à parte se feedback pedir).
- Refatorar `_handle_daemon_state_full` para retornar dataclass tipado em vez de `dict` (escopo de schema, sprint à parte).
- Resolver evdev_reader não conectando — se descoberto, abre sprint nova.

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-Dualsense4Unix/VALIDATOR_BRIEF.md`
- Precedente armadilha A-09 (evdev snapshot dedup): justifica Bug A consumir `state.buttons_pressed` em vez de chamar `_evdev.snapshot()` direto.
- Precedente BUG-MOUSE-TRIGGERS-01: pattern `mark_manual_trigger_active / clear_manual_trigger_active` reaplicado para `manual_profile_lock`.
- Precedente FEAT-PERSIST-SESSION-01: `save_last_profile` em `session.json` é o canônico do daemon.
- PR alvo: #103 (rebrand/dualsense4unix).

---

*"Três bugs num arquivo só viram um cluster ou três PRs em conflito. Esse cluster é o caminho com menor débito."*
