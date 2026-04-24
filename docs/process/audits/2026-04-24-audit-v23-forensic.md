# Auditoria externa pós-v2.3.0 — relatório

**Sprint:** AUDIT-V23-FORENSIC-01
**Data:** 2026-04-24
**Auditor:** revisor externo (sessão nova — sem contexto das sprints V2.3).
**Método:** conforme spec `docs/process/sprints/AUDIT-V23-FORENSIC-01.md`, apoiado em `README.md` e `VALIDATOR_BRIEF.md`. Não foi lido `MEMORY.md`, `CHANGELOG.md`, `SESSION_RESTORE.md`, `HEFESTO_DECISIONS_V*.md`, nem specs prévias de `docs/process/sprints/`.

---

## Resumo executivo

Base auditada: 18.016 LOC de produção em 106 arquivos Python + 17.250 LOC de testes em 86 arquivos + 19 scripts + 4 arquivos de packaging debian + 3 workflows GitHub Actions. Tag `v2.3.0` (commit `e5384ab`), HEAD `79a216f` (pré-flight da auditoria).

**Baseline de tooling:**
- `.venv/bin/ruff check src tests` → `All checks passed!`
- `.venv/bin/mypy src/hefesto` → `Success: no issues found in 108 source files`
- `.venv/bin/pytest tests/unit --cov=src/hefesto -q` → **1143 passed, 5 skipped em 18.45s; coverage total 63%.**
- `vulture` ausente no venv; coverage foi o único sinal objetivo de dead code detectável automaticamente.

Descobertas:

| Severidade | Quantidade | Sprints novas |
|---|---:|---:|
| Bloqueante | 0 | 0 |
| Alto | 6 | 6 |
| Médio | 9 | 5 |
| Baixo | 7 | 1 (checklist) |
| Cosmético | 4 | 0 |
| **Total** | **26 achados** | **12 sprints-filhas** |

A base é **sólida** em higiene estática — ruff e mypy passam limpos, sem `# type: ignore` gratuito, zero uso de `eval`, zero `exec` de código dinâmico, `subprocess` em todo lugar com argv-list (sem `shell=True`). Isso por si é um achado positivo: elimina categorias inteiras de débito trivial e direciona auditor para lógica de negócio.

Os 6 achados "alto" concentram-se em:
1. Protocolo UDP (compat DSX) com 3 instruções sendo **silenciosamente no-op** no handler, apesar de documentadas no schema.
2. **Duplicação tripla** da mesma lógica de multiplicador de política de rumble espalhada por 3 módulos.
3. **Path traversal** via IPC `profile.switch` por falta de sanitização antes do `Path.__truediv__`.
4. **mic_led resetando a False** em cada `profile.switch` por falta do campo em `LedsConfig`.
5. **API paralela dead** (`KeyboardSubsystem` classe) que é testada mas nunca cabeada no `Daemon`.
6. **`profile.apply_draft`** ignora a política de rumble — caminho IPC de draft bypassa a escala economia/balanceado/max/auto.

Base de teste tem ratio 0.95 LOC-test : LOC-src, mas distribuição é bimodal: daemon/ + core/ + profiles/ cobertos ≥80%, GUI/actions zerado em 5 arquivos (~708 LOC).

---

## Saídas de ferramentas (evidência literal)

### ruff
```
$ .venv/bin/ruff check src tests
All checks passed!
```

### mypy
```
$ .venv/bin/mypy src/hefesto
Success: no issues found in 108 source files
```

### pytest + cov (extrato — módulos <70%)
```
$ .venv/bin/pytest tests/unit --cov=src/hefesto --cov-report=term-missing -q
...
1143 passed, 5 skipped in 18.45s
TOTAL                                                         8708   3245    63%
```

Coverage por módulo com ≤70% (ordem crescente):

| Módulo | Stmts | Miss | Cov |
|---|---:|---:|---:|
| `app/actions/emulation_actions.py` | 86 | 86 | 0% |
| `app/actions/firmware_actions.py` | 178 | 178 | 0% |
| `app/actions/rumble_actions.py` | 171 | 171 | 0% |
| `app/actions/trigger_specs.py` | 50 | 50 | 0% |
| `app/actions/triggers_actions.py` | 223 | 223 | 0% |
| `app/main.py` | 19 | 19 | 0% |
| `app/theme.py` | 25 | 25 | 0% |
| `app/tray.py` | 132 | 132 | 0% |
| `cli/cmd_tray.py` | 59 | 59 | 0% |
| `daemon/main.py` | 32 | 32 | 0% |
| `__main__.py` | 3 | 3 | 0% |
| `app/app.py` | 173 | 163 | 6% |
| `app/gui_dialogs.py` | 63 | 53 | 16% |
| `integrations/window_backends/wayland_portal.py` | 85 | 67 | 21% |
| `app/actions/mouse_actions.py` | 111 | 88 | 21% |
| `app/actions/lightbar_actions.py` | 189 | 144 | 24% |
| `integrations/window_backends/xlib.py` | 68 | 52 | 24% |
| `gui/widgets/stick_preview_gtk.py` | 80 | 61 | 24% |
| `app/ipc_bridge.py` | 137 | 97 | 29% |
| `cli/cmd_emulate.py` | 40 | 29 | 28% |
| `cli/cmd_plugin.py` | 49 | 35 | 29% |
| `app/gui_prefs.py` | 31 | 19 | 39% |
| `gui/widgets/button_glyph.py` | 84 | 50 | 40% |
| `daemon/subsystems/mouse.py` | 66 | 31 | 53% |
| `utils/single_instance.py` | 154 | 70 | 55% |
| `daemon/subsystems/keyboard.py` | 168 | 67 | 60% |

### padrões varridos por grep

- `shell=True`: encontrado apenas em comentários dizendo "NUNCA usa shell=True" — nenhum uso real.
- Dynamic code execution (`eval(...)` ou `exec(...)` em módulo Python): **0 ocorrências** em `src/`.
- TODO/FIXME/XXX em código de produção: 0 em `src/` (exceto docstring mencionando token virtual `__XXX__`).
- Handlers largos (`except ... Exception`): 123 ocorrências na base — universalmente sem `exc_info=True`. Detalhe em achado 15.
- Em `src/hefesto/app/actions/*.py` sozinho: 16 `except Exception`.

---

## Achados

### 1. [bug-funcional] UDP PlayerLED, MicLED e TriggerThreshold são silenciosamente no-op

- **Arquivo:** `src/hefesto/daemon/udp_server.py:217-238`
- **Severidade:** alto
- **Evidência:**
  ```python
  def _do_player_led(self, params: list[Any]) -> None:
      # Placeholder: backend ainda não expõe player LED API.
      # Gravamos no store para a TUI/perfis refletirem.
      if len(params) < 2:
          raise ValueError("PlayerLED precisa [idx, bitmask]")
      _idx, bitmask = params[:2]
      self.store.bump(f"udp.player_led.{int(bitmask)}")   # <-- só bump

  def _do_mic_led(self, params: list[Any]) -> None:
      if not params:
          raise ValueError("MicLED precisa [state]")
      state = bool(params[0])
      self.store.bump(f"udp.mic_led.{int(state)}")        # <-- só bump

  def _do_trigger_threshold(self, params: list[Any]) -> None:
      if len(params) < 2:
          raise ValueError("TriggerThreshold precisa [side, value]")
      side_raw, value = params[0], int(params[1])
      side = str(side_raw).lower()
      if side not in ("left", "right"):
          raise ValueError(f"TriggerThreshold side invalido: {side_raw}")
      self.store.bump(f"udp.trigger_threshold.{side}.{value}")  # <-- só bump
  ```
- **Análise:** O docstring do módulo no topo (linhas 11-20) declara os 6 tipos suportados. O backend `PyDualSenseController` já implementa `set_player_leds` (`backend_pydualsense.py:160`) e `set_mic_led` (`:149`); os 2 comentários no código ainda dizem "backend ainda não expõe" — **informação desatualizada**. Jogos DSX compatíveis (Cyberpunk, Forza) que enviem `PlayerLED` ou `MicLED` por UDP têm seus comandos contabilizados no `store.counters` e nunca propagados ao hardware. `TriggerThreshold` é ambíguo (o schema não define semântica), mas os outros dois são bug funcional claro.
- **Recomendação:** em `_do_player_led`, chamar `self.controller.set_player_leds(bits)` após decodificar bitmask em tuple[bool]×5. Em `_do_mic_led`, chamar `self.controller.set_mic_led(state)`. Para `_do_trigger_threshold`, decidir em sprint de produto se o campo é ignorado oficialmente ou implementado.
- **Sprint nova:** AUDIT-FINDING-UDP-PLACEHOLDER-HANDLERS-01

### 2. [bug-funcional] `profile.apply_draft` bypassa política de rumble

- **Arquivo:** `src/hefesto/daemon/ipc_server.py:644-661` vs `:433-454`
- **Severidade:** alto
- **Evidência:**
  ```python
  # _handle_rumble_set (linhas 433-454) — aplica política:
  eff_weak, eff_strong = _apply_rumble_policy(self.daemon, weak, strong)
  self.controller.set_rumble(weak=eff_weak, strong=eff_strong)

  # _handle_profile_apply_draft, seção rumble (linhas 649-658) — NÃO aplica:
  weak = max(0, min(255, weak))
  strong = max(0, min(255, strong))
  ...
  self.controller.set_rumble(weak=weak, strong=strong)   # <-- bruto
  ```
- **Análise:** A política global (`economia` 0.3×, `balanceado` 0.7×, `max` 1.0×, `auto` dinâmico, `custom` user-defined) é aplicada em `rumble.set` mas ignorada em `profile.apply_draft`. GUI → aba Rumble → "Aplicar perfil" envia draft e o daemon pula a escala. Resultado: slider "Economia" no perfil não atenua se o caminho de chegada for draft.
- **Recomendação:** na seção rumble do `_handle_profile_apply_draft`, trocar a chamada direta por `_apply_rumble_policy(self.daemon, weak, strong)` e usar os valores escalados no `set_rumble`.
- **Sprint nova:** AUDIT-FINDING-IPC-DRAFT-RUMBLE-POLICY-01

### 3. [bug-funcional] `apply_led_settings` reseta `mic_led` a cada profile switch

- **Arquivo:** `src/hefesto/core/led_control.py:83-102` + `src/hefesto/profiles/schema.py:119-142` + `src/hefesto/profiles/manager.py:130-147`
- **Severidade:** alto
- **Evidência:** `LedsConfig` não tem campo `mic_led`:
  ```python
  class LedsConfig(BaseModel):
      model_config = ConfigDict(extra="forbid")
      lightbar: tuple[int, int, int] = (0, 0, 0)
      player_leds: list[bool] = Field(default_factory=lambda: [False] * 5)
      lightbar_brightness: float = Field(default=1.0, ge=0.0, le=1.0)
  ```
  `_to_led_settings` não passa `mic_led`, então recai no default `False`:
  ```python
  return LedSettings(
      lightbar=leds.lightbar,
      brightness_level=float(leds.lightbar_brightness),
      player_leds=player_leds_tuple,
      # mic_led ausente -> default False em LedSettings
  )
  ```
  `apply_led_settings` sempre invoca `set_mic_led`:
  ```python
  def apply_led_settings(controller: IController, settings: LedSettings) -> None:
      effective = settings.apply_brightness(settings.brightness_level)
      controller.set_led(effective.lightbar)
      controller.set_mic_led(settings.mic_led)   # <-- sempre False em profile switch
      controller.set_player_leds(settings.player_leds)
  ```
- **Análise:** Usuário muta mic via hardware (botão físico) ou via IPC → mic LED vermelho aceso. AutoSwitch ou user chama `profile.switch` → `_to_led_settings` produz `LedSettings(mic_led=False)` → `set_mic_led(False)` apaga. Regressão silenciosa em cada troca de perfil. O `VALIDATOR_BRIEF.md` armadilha **A-06** foi escrita para o caso "campo novo em `*Config` precisa sprint-par de profile-apply", mas aqui é o inverso: o **campo nunca entrou no schema** e o `apply_led_settings` passa `False` sem condicional. A-06 está **incompleta** para mic_led.
- **Recomendação:** três opções possíveis:
  (a) adicionar `mic_led: bool = False` a `LedsConfig`, propagar em `_to_led_settings`, e populá-lo em `_build_profile_from_editor` (GUI);
  (b) não aplicar `set_mic_led` no `apply_led_settings` quando `mic_led` não for explícito — em vez disso, mover a chamada para um path separado (`apply_mic_led`) invocado só por sprints de produto;
  (c) deixar mic_led como estado runtime puro, nunca persistido em perfil, e remover a chamada do `apply_led_settings`.
  Opção (c) casa melhor com a semântica "mic_led é estado do botão, não config estética".
- **Sprint nova:** AUDIT-FINDING-PROFILE-MIC-LED-RESET-01

### 4. [segurança] Path traversal possível via IPC `profile.switch`

- **Arquivo:** `src/hefesto/profiles/loader.py:42-44, 53-88` + `src/hefesto/daemon/ipc_server.py:270-278`
- **Severidade:** alto
- **Evidência:** Handler IPC valida apenas "não vazio":
  ```python
  async def _handle_profile_switch(self, params: dict[str, Any]) -> dict[str, Any]:
      name = params.get("name")
      if not isinstance(name, str) or not name:
          raise ValueError("profile.switch exige 'name' string")
      profile = self.profile_manager.activate(name)   # <-- passa direto
  ```
  `ProfileManager.activate` → `load_profile(name)` → constrói caminho com `Path.__truediv__`:
  ```python
  def load_profile(identifier: str) -> Profile:
      directory = profiles_dir(ensure=True)
      direct = directory / f"{identifier}.json"
      if direct.exists():
          return _read_profile(direct)
      ...
  ```
  `pathlib.Path` documenta: `Path("/home/x") / "/etc/passwd"` → `PosixPath('/etc/passwd')`. E `Path("/home/x") / "../../etc/passwd"` → `PosixPath('/home/x/../../etc/passwd')` que `.exists()` normaliza. O filename é `f"{identifier}.json"`, então o target é `/<foo>/<identifier>.json` — identifier pode começar com `/` (escape absoluto) ou `..` (escape relativo).
- **Análise:** Socket IPC é `$XDG_RUNTIME_DIR/hefesto/hefesto.sock` com `0o600` (linha `ipc_server.py:128`), então só processos do mesmo UID conectam. **Risco real baixo** (atacante já tem UID do user). Mas: (1) `_json_rpc_error(req_id, CODE_INTERNAL, str(exc))` em `_dispatch:262` retorna a exceção literal — pydantic `ValidationError` em arquivo arbitrário leaks path + conteúdo parcial; (2) princípio de defesa em profundidade sugere validar nome no boundary. Validação de `Profile.name` no schema (linha 181-190) rejeita `/` e `..`, mas isso é para `name` dentro do JSON — não aplicado a `identifier` passado para `load_profile`.
- **Recomendação:** adicionar sanitização no `load_profile` antes do `Path.__truediv__`: rejeitar identifier com `/`, `\`, `..`, ou caracteres nulos. Alternativa mais simples: usar `path.resolve().is_relative_to(directory)` após o concat e rejeitar se escape. Também normalizar `CODE_INTERNAL` response para não vazar `str(exc)` bruto.
- **Sprint nova:** AUDIT-FINDING-PROFILE-PATH-TRAVERSAL-01

### 5. [duplicação] Lógica de multiplicador de política de rumble triplicada

- **Arquivo:** `src/hefesto/core/rumble.py:51-110`, `src/hefesto/daemon/subsystems/rumble.py:34-78`, `src/hefesto/daemon/ipc_server.py:765-816`
- **Severidade:** alto
- **Evidência:** duas funções quase idênticas:
  ```python
  # core/rumble.py — _effective_mult
  if policy == "custom":
      mult = float(config.rumble_policy_custom_mult)
      return mult, last_auto_mult, last_auto_change_at
  if policy in RUMBLE_POLICY_MULT:
      mult = RUMBLE_POLICY_MULT[policy]
      return mult, last_auto_mult, last_auto_change_at
  if policy == "auto":
      if battery_pct > 50: target = 1.0
      elif battery_pct >= 20: target = 0.7
      else: target = 0.3
      ...

  # daemon/subsystems/rumble.py — _effective_mult_inline
  if policy in RUMBLE_POLICY_MULT:
      return RUMBLE_POLICY_MULT[policy], last_auto_mult, last_auto_change_at
  if policy == "custom":
      mult = float(config.rumble_policy_custom_mult)
      return mult, last_auto_mult, last_auto_change_at
  if policy == "auto":
      ...
  ```
  E o `_apply_rumble_policy` em `ipc_server.py:777` importa `_effective_mult` direto — provando que a "razão" (evitar import circular) alegada no comentário da versão inline **já caiu**:
  ```python
  from hefesto.core.rumble import _effective_mult
  from hefesto.daemon.lifecycle import AUTO_DEBOUNCE_SEC
  ```
- **Análise:** As duas implementações diferem sutilmente: `core/rumble.py` registra `logger.warning("rumble_policy_desconhecida")` no fallback; `subsystems/rumble.py` não loga. Ordem dos ifs é trocada. Drift ativo — próxima vez que política mudar, ambas precisam ser atualizadas em sincronia e testes verificam ambas. Também em `ipc_server.py:809-812` lê/escreve campos privados `rumble_engine._last_auto_mult` por fora, violando encapsulamento.
- **Recomendação:** deletar `_effective_mult_inline` de `daemon/subsystems/rumble.py`; em `reassert_rumble` importar `_effective_mult` do core. Extrair o write-back em `RumbleEngine.update_auto_state(mult, change_at)` método público em vez de acessar `_last_auto_*` externamente.
- **Sprint nova:** AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01

### 6. [dead-code/débito-paralelo] `KeyboardSubsystem` existe, é testada, mas nunca cabeada

- **Arquivo:** `src/hefesto/daemon/subsystems/keyboard.py:129-164`
- **Severidade:** alto
- **Evidência:** a classe é completa:
  ```python
  class KeyboardSubsystem:
      name = "keyboard"
      _device: Any = None
      async def start(self, ctx: DaemonContext) -> None: ...
      async def stop(self) -> None: ...
      def is_enabled(self, config: DaemonConfig) -> bool: ...
  ```
  Mas o wire-up real no `Daemon` usa as funções top-level (mesma file, linhas 167 e 229):
  ```python
  def start_keyboard_emulation(daemon: Any) -> bool: ...
  def stop_keyboard_emulation(daemon: Any) -> None: ...
  ```
  E `lifecycle.py:248-258` só chama as funções top-level. Grep confirma — `KeyboardSubsystem` só aparece em `__all__` e no teste `tests/unit/test_keyboard_wire_up.py`. Nenhum código de produção instancia a classe.
- **Análise:** duas APIs paralelas implementam a mesma feature com mecânicas diferentes. Se no futuro alguém mover a integração para a API de `Subsystem` protocol (via `PluginsSubsystem` registry), a classe vai entrar ativa e o comportamento pode divergir silenciosamente. O teste `test_keyboard_wire_up.py` confirma o comportamento da classe isolada, não da cadeia integrada. Classe é **casca sem efeito**.
- **Recomendação:** decidir um caminho — ou (a) migrar o wire-up real para `KeyboardSubsystem` (via registry) e deletar `start/stop_keyboard_emulation`; ou (b) deletar `KeyboardSubsystem` e seus testes, mantendo só as funções top-level. Opção (b) é menos risco — remover é mais fácil que integrar.
- **Sprint nova:** AUDIT-FINDING-KEYBOARD-SUBSYSTEM-DEAD-01

### 7. [dead-code] `profiles/autoswitch.py::start_autoswitch` e `_noop` nunca são chamados

- **Arquivo:** `src/hefesto/profiles/autoswitch.py:120-135` (start_autoswitch) e `:138-142` (_noop)
- **Severidade:** médio
- **Evidência:**
  ```bash
  $ grep -rn "profiles.autoswitch import\|from hefesto.profiles.autoswitch" src/ tests/
  (vazio — ninguém importa start_autoswitch nem _noop)
  ```
  O wire-up real vai por `src/hefesto/daemon/subsystems/autoswitch.py::start_autoswitch` (nome colidente, assinatura diferente). A função em `profiles/autoswitch.py` tem signature `(manager: ProfileManager, window_reader)` e a em `daemon/subsystems/autoswitch.py` tem `(daemon: Any)` — quem usa o módulo via lifecycle importa do subsystems.
- **Análise:** `AutoSwitcher` classe em `profiles/autoswitch.py` é usada (instanciada por `daemon/subsystems/autoswitch.py:start_autoswitch`). Mas a função `start_autoswitch` local + o helper `_noop` são lixo semântico. Cobertura 85%, o gap de 15% aponta justamente para estas funções.
- **Recomendação:** deletar `profiles/autoswitch.py::start_autoswitch` e `_noop`. Remover do `__all__`. 22 linhas de código morto.
- **Sprint nova:** AUDIT-FINDING-DEAD-CODE-01 (agrupada)

### 8. [duplicação] `TouchpadReader` e `EvdevReader` compartilham ~100 LOC de loop+reconnect

- **Arquivo:** `src/hefesto/core/evdev_reader.py:153-208` vs `:392-450`
- **Severidade:** médio
- **Evidência:** ambos têm o mesmo padrão:
  ```python
  # EvdevReader._run:
  backoff = 0.5
  while not self._stop_flag.is_set():
      path = self._device_path or find_dualsense_evdev()
      if path is None:
          ...; backoff = min(backoff * 2, 5.0); continue
      try: dev = InputDevice(str(path))
      except Exception as exc:
          logger.warning("evdev_open_failed", ...); ...
          self._device_path = None; ...; continue
      ...
      try:
          for event in dev.read_loop():
              ...
      except OSError as exc:
          logger.warning("evdev_read_lost", ...); self._reset_buttons_on_disconnect()
          self._device_path = None
      except Exception as exc:
          logger.warning("evdev_read_loop_error", err=str(exc)); self._reset_buttons_on_disconnect()
      finally:
          with contextlib.suppress(Exception): dev.close()
      if not self._stop_flag.is_set(): time.sleep(0.1)
  ```
  `TouchpadReader._run` repete ~90% idêntico com substituições mecânicas (`find_dualsense_touchpad_evdev`, `touchpad_reader_*` event names, `_reset_on_disconnect`).
- **Análise:** Próximo leitor de evdev que surgir (IMU? gyro? haptic feedback?) vai copiar o mesmo padrão pela terceira vez. Extrair `_EvdevLoopBase` com hooks `_find_device()`, `_on_event()`, `_on_disconnect()` mata a duplicação.
- **Recomendação:** introduzir classe base `_EvdevReconnectLoop` em `core/evdev_reader.py` e reutilizar em ambos readers. Preservar retrocompatibilidade dos nomes exportados.
- **Sprint nova:** AUDIT-FINDING-EVDEV-READER-BASE-CLASS-01

### 9. [anti-pattern] `app/ipc_bridge.py` tem 13 wrappers idênticos `try: _run_call(...); return True; except Exception: return False`

- **Arquivo:** `src/hefesto/app/ipc_bridge.py:142-282`
- **Severidade:** médio
- **Evidência:** 13 funções públicas (`profile_switch`, `trigger_set`, `led_set`, `rumble_set`, `rumble_stop`, `rumble_passthrough`, `rumble_policy_set`, `rumble_policy_custom`, `player_leds_set`, `mouse_emulation_set`, `apply_draft`, `profile_list` parcial, `daemon_status_basic`) seguem o padrão:
  ```python
  def X(...) -> bool:
      try:
          _run_call(...)
          return True
      except Exception:
          return False
  ```
  Sem log. Sem distinção entre "daemon offline" e "validation error" e "timeout". GUI recebe `False` sem saber.
- **Análise:** anti-pattern sistêmico. Se o daemon está online mas rejeita o payload (erro de validação do pydantic — ex.: `brightness` fora de [0,1]), a GUI vê `False` idêntico ao caso "socket FileNotFoundError". UX degrada. Quando o user reclama "aplicar não funciona", não há trilha no log do daemon nem no da GUI.
- **Recomendação:** extrair helper `_safe_call(method, params, timeout) -> tuple[bool, Any | None]` que captura só `(FileNotFoundError, ConnectionError, IpcError, OSError)` e loga `debug` para esses; deixa outras exceções subirem. Os 13 wrappers viram 2 linhas cada usando o helper.
- **Sprint nova:** AUDIT-FINDING-IPC-BRIDGE-BARE-EXCEPT-01

### 10. [segurança] `single_instance` pode matar PID reciclado de processo alheio

- **Arquivo:** `src/hefesto/utils/single_instance.py:87-113, 125-133`
- **Severidade:** médio
- **Evidência:**
  ```python
  predecessor = _read_existing_pid(path)
  if predecessor is not None and predecessor != os.getpid():
      if is_alive(predecessor):
          logger.info("single_instance_takeover_iniciado", ...)
          _terminate_predecessor(predecessor)    # <-- SIGTERM ao PID
  ```
  `is_alive(pid)` apenas confirma "processo com esse PID existe e é sinalizável pelo user". Se o daemon Hefesto crashou e o kernel reciclou o PID para outro processo do mesmo UID (ex.: `firefox`, `python script pessoal`), `is_alive` retorna True e `SIGTERM` vai para o processo errado.
- **Análise:** PID recycling em Linux moderno é improvável em janela curta (pid_max default 4M no kernel ≥5), mas **não impossível**. Sistema sob fork bomb ou com pid_max baixo (2^15 antigo) tem janela maior. O spawn/kill é disparado por udev + systemd (A-11 documentada). Princípio de defesa em profundidade: confirmar que PID é hefesto antes de matar.
- **Recomendação:** antes de `_terminate_predecessor`, verificar `/proc/<pid>/comm` (Linux) ou `/proc/<pid>/cmdline` contém `hefesto` / `hefesto.app.main` / `hefesto daemon`. Se não bater, tratar pid file como órfão (log warning, apagar file, prosseguir com lock acquire sem matar).
- **Sprint nova:** AUDIT-FINDING-SINGLE-INSTANCE-PID-RECYCLE-01

### 11. [perf] `WaylandPortalBackend` cria `ThreadPoolExecutor` + `asyncio.run` por chamada

- **Arquivo:** `src/hefesto/integrations/window_backends/wayland_portal.py:56-89`
- **Severidade:** médio
- **Evidência:**
  ```python
  def _try_dbus_fast(handle_token: str) -> WindowInfo | None:
      ...
      def _run() -> WindowInfo | None:
          async def _async() -> WindowInfo | None:
              ...
          return asyncio.run(_async())   # <-- cria+destroi loop por call

      with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:  # <-- cria pool por call
          future = pool.submit(_run)
          ...
  ```
- **Análise:** `get_active_window_info` é chamado pelo `AutoSwitcher` a 2 Hz quando compositor é Wayland puro. Cada tick cria um `ThreadPoolExecutor` descartável + uma thread worker + um event loop novo (`asyncio.run` cria loop + registra SIGINT handler + tear-down). Overhead ~5-10 ms por chamada em sistema ocupado; para 2 Hz é absorvível, mas sinal de alerta se frequência subir. Em pior cenário (compositor lento), o timeout de 2s multiplica por 2Hz = pool em estado pendente.
- **Recomendação:** migrar para um thread de longa vida com queue; ou usar `jeepney` síncrono direto na thread do autoswitch (bloqueia, mas o poll interval já é 500 ms). Ou aceitar o overhead e adicionar cache/dedup.
- **Sprint nova:** AUDIT-FINDING-WAYLAND-PORTAL-PERF-01

### 12. [cobertura] 11 módulos em 0% cov, 708 LOC zerados

- **Arquivo:** ver tabela em "Saídas de ferramentas"
- **Severidade:** médio
- **Evidência:** coverage reports 0% em 11 módulos, incluindo `app/actions/rumble_actions.py` 171 LOC, `app/actions/triggers_actions.py` 223 LOC, `app/actions/firmware_actions.py` 178 LOC, `app/tray.py` 132 LOC, `app/actions/emulation_actions.py` 86 LOC. Entry points (`app/main.py` 19, `daemon/main.py` 32, `__main__.py` 3) sem cobertura é esperado. Mas actions representam lógica de UI — ~708 LOC sem rede de testes.
- **Análise:** A regra do projeto (README) diz "1036 unit tests" (stale — são 1143 agora). Soma em branches bateu 63% total. Actions são testadas via GUI real, mas nada previne regressão em headless/CI. Spec V2.3 adicionou `test_input_actions.py` com `_FakeMixin` como padrão — é o template para estender cobertura.
- **Recomendação:** aplicar o padrão `_FakeMixin` para criar testes unitários para cada action module grande, priorizando `rumble_actions.py` e `triggers_actions.py` (onde ambiguidade de estado é mais custosa).
- **Sprint nova:** AUDIT-FINDING-COVERAGE-ACTIONS-ZERO-01

### 13. [complexidade] `ipc_server.py` 843 LOC excede limite do projeto (800)

- **Arquivo:** `src/hefesto/daemon/ipc_server.py` (843 LOC)
- **Severidade:** médio
- **Evidência:** `VALIDATOR_BRIEF.md` seção "Padrões de código" declara `Limite: 800 linhas por arquivo (exceto configs/registries/testes)`. `ipc_server.py` é handler dispatcher, não config. Além disso, o método `_handle_profile_apply_draft` sozinho tem ~120 LOC (linhas 565-685) com 4 seções paralelas (leds/triggers/rumble/mouse) cada uma envolvida em try/except.
- **Análise:** Tamanho absoluto como proxy imperfeito, mas nesta base específica é violação de contrato autodeclarado. Split natural: `ipc_server.py` (start/stop/probe/dispatch) + `ipc_handlers.py` (handlers). `_handle_profile_apply_draft` pode virar classe `DraftApplier` com um método por seção.
- **Recomendação:** split estrutural em 2 ou 3 arquivos; extrair `_apply_rumble_policy` e constantes para novo arquivo ou mover para `core/rumble.py` (ver achado 5).
- **Sprint nova:** AUDIT-FINDING-IPC-SERVER-SPLIT-01

### 14. [teste-design] `_FakeMixin` com `__get__` dinâmico mascara bugs no mixin

- **Arquivo:** `tests/unit/test_input_actions.py:48-90`
- **Severidade:** médio
- **Evidência:**
  ```python
  class _FakeMixin:
      def __init__(self) -> None:
          self.draft = DraftConfig.default()
          self._key_bindings_store = _FakeListStore()
          self._toasts: list[str] = []
      def _get(self, _key: str) -> Any:
          return None  # TreeView/widgets indisponíveis nos testes unit
      def _toast_input(self, msg: str) -> None:
          self._toasts.append(msg)

  def _build_mixin() -> Any:
      instance = _FakeMixin()
      for name in (...):
          setattr(
              instance,
              name,
              InputActionsMixin.__dict__[name].__get__(instance, type(instance)),
          )
      return instance
  ```
- **Análise:** O padrão usa descriptor protocol (`__get__`) para bind métodos do mixin a um objeto sem herdar GTK. Funciona para métodos que interagem via `self._get(...)` (retornando `None`), `self.draft`, `self._toasts`. **Problemas:** (a) métodos que dependem de outros do mixin pelo nome (chamadas `self._outro_metodo`) esperando outros mixins no MRO — aqui explodem com AttributeError só no path específico, passam silenciosamente em outros; (b) tests cobrem "happy path quando widget é None" — não testam path feliz com widget real; (c) o `_FakeListStore` não implementa toda API de `Gtk.ListStore` (ex.: `iter_children`, `append` com iter pai). Discrepâncias são invisíveis.
- **Recomendação:** manter `_FakeMixin` como teste **de unidade pura** (é isso que ele é), mas **acrescentar** testes de integração com GTK real marcados `@pytest.mark.skipif(not GTK_AVAILABLE)`. O spec V2.3 já fez `pytest.importorskip("gi")`, o que é bom — mas importa o mixin e executa só na ausência de widgets.
- **Sprint nova:** agrupada em AUDIT-FINDING-COVERAGE-ACTIONS-ZERO-01

### 15. [anti-pattern] 123+ handlers `except ... Exception` sem `exc_info=True`

- **Arquivo:** varredura `grep -rn "except.*Exception.*:" src/hefesto | wc -l` → 123
- **Severidade:** médio
- **Evidência:** padrão universal na base:
  ```python
  try:
      ...
  except Exception as exc:
      logger.warning("algo_failed", err=str(exc))  # sem traceback
  ```
  Amostra: `backend_pydualsense.py:63, 91, 117`, `keyboard.py:96, 109, 146`, `keyboard.py:267, 273`, `rumble.py:201`, `udp_server.py:194`, `ipc_server.py:218`, `profiles/loader.py:80-81`, `ipc_bridge.py` 13×, `app/actions/*` 16×.
- **Análise:** A mensagem preserva `err=str(exc)` mas o traceback (linha exata, stack) só aparece com `exc_info=True` (structlog) ou `logger.exception(...)` (stdlib). Quando bug real ocorre, debug fica cego — precisa reproduzir local. A auditoria contabilizou 123 ocorrências em produção; é débito sistêmico, não só ponto-a-ponto.
- **Recomendação:** checklist de 10-15 handlers críticos (poll loop, apply_led_settings chamador, IPC dispatch, shutdown) recebem `exc_info=True`. Os cosméticos (find_dualsense_evdev ao iterar devices) podem continuar como `debug`. Regra dorvante: se o except está num path que manda log `warning` ou `error`, **incluir traceback**.
- **Sprint nova:** AUDIT-FINDING-LOG-EXC-INFO-01 (checklist agrupado, inclui também achado 16, 17, 18, 20)

### 16. [anti-pattern] `except ... Exception: pass` silencioso em `backend_pydualsense.py` e find_dualsense*

- **Arquivo:** `src/hefesto/core/backend_pydualsense.py:91-92, 117-118` e `src/hefesto/core/evdev_reader.py:67-68, 323-324`
- **Severidade:** baixo
- **Evidência:**
  ```python
  # backend_pydualsense.py
  try:
      if bool(getattr(ds.state, "micBtn", False)):
          buttons.add("mic_btn")
  except Exception:  # defensivo: state pode estar cru no primeiro tick
      pass

  # evdev_reader.py (find_dualsense_evdev + find_dualsense_touchpad_evdev)
  for path in list_devices():
      try:
          dev = InputDevice(path)
          ...
      except Exception:
          continue
  ```
- **Análise:** Silêncio absoluto. Se `ds.state` subir exception novo (ex.: `RuntimeError` por BUS_ERROR em USB unplug), nunca saberemos. Em `find_*`, se um device evdev tem permissão negada, pulamos sem log. OK como fallback, não OK como única trilha.
- **Recomendação:** capturar `AttributeError` (ou o específico esperado) em vez de `Exception` genérico; ou log `debug` antes do `pass`/`continue`.
- **Sprint nova:** agrupada em AUDIT-FINDING-LOG-EXC-INFO-01

### 17. [tipo fraco] `connect_with_retry` backoff fixo, sem limite

- **Arquivo:** `src/hefesto/daemon/connection.py:18-32`
- **Severidade:** baixo
- **Evidência:**
  ```python
  async def connect_with_retry(daemon: Any) -> None:
      backoff = daemon.config.reconnect_backoff_sec
      while True:
          try:
              await daemon._run_blocking(daemon.controller.connect)
              ...
              return
          except Exception as exc:
              logger.warning("controller_connect_failed", err=str(exc))
              if not daemon.config.auto_reconnect:
                  raise
              await asyncio.sleep(backoff)
  ```
- **Análise:** `backoff` é lido do config e nunca cresce. Se controle ficar desplugado por 1h, daemon tenta reconectar 1800 vezes com 2s sleep — CPU baixa mas log spam e bateria de máquina host comprometida. Também: `while True` sem sanity exit se stop signal chega durante `asyncio.sleep(backoff)` — o `stop_event` não é inspecionado aqui.
- **Recomendação:** backoff exponencial com teto; e/ou checar `daemon._stop_event.is_set()` dentro do sleep via `asyncio.wait_for`.
- **Sprint nova:** NENHUMA (Edit pronto após AUDIT-FINDING-LOG-EXC-INFO-01)

### 18. [anti-pattern] `_compute_mult` e `_apply_rumble_policy` silenciam leitura de state com `except Exception: pass`

- **Arquivo:** `src/hefesto/core/rumble.py:201`, `src/hefesto/daemon/subsystems/rumble.py:104`, `src/hefesto/daemon/ipc_server.py:789-790`
- **Severidade:** baixo
- **Evidência:**
  ```python
  # rumble.py::_compute_mult
  with contextlib.suppress(AttributeError, TypeError, ValueError):
      battery_pct = int(self._state_ref.battery_pct)

  # subsystems/rumble.py::reassert_rumble
  try:
      snap = daemon.store.snapshot()
      ...
  except Exception:
      pass

  # ipc_server.py::_apply_rumble_policy
  if store is not None:
      try:
          snap = store.snapshot()
          ctrl = snap.controller
          if ctrl is not None and ctrl.battery_pct is not None:
              battery_pct = int(ctrl.battery_pct)
      except Exception:
          pass
  ```
- **Análise:** Três locais silenciam o mesmo erro. Se store.snapshot() levanta (nunca deveria — é in-memory), `battery_pct` fica em 50 hardcoded. Modo `auto` passa a rodar sem saber a bateria real. Sem log, sem métrica de recurso.
- **Recomendação:** logger.debug de 1 linha no handler de exception com o motivo.
- **Sprint nova:** agrupada em AUDIT-FINDING-LOG-EXC-INFO-01

### 19. [silencioso] UDP não clampa RGB — IPC clampa

- **Arquivo:** `src/hefesto/daemon/udp_server.py:211-215` vs `src/hefesto/daemon/ipc_server.py:327-329`
- **Severidade:** baixo
- **Evidência:**
  ```python
  # UDP — sem validação de range:
  def _do_rgb_update(self, params: list[Any]) -> None:
      if len(params) < 4:
          raise ValueError("RGBUpdate precisa [idx, r, g, b]")
      _idx, r, g, b = params[:4]
      self.controller.set_led((int(r), int(g), int(b)))  # <-- sem clamp

  # IPC — valida:
  for idx, v in enumerate(rgb):
      if not isinstance(v, int) or not (0 <= v <= 255):
          raise ValueError(f"led.set: rgb[{idx}] fora de byte")
  ```
- **Análise:** UDP aceita RGB arbitrário. Passa direto ao backend — pydualsense internal clamp pode ou não proteger. Inconsistência de semântica entre IPC (rigoroso) e UDP (permissivo).
- **Recomendação:** clampar `(0, min(255, int(v)))` no UDP `_do_rgb_update`. Inconsistência silenciosa vira bug quando o backend mudar.
- **Sprint nova:** NENHUMA (Edit pronto; será incluído na sprint AUDIT-FINDING-UDP-PLACEHOLDER-HANDLERS-01)

### 20. [defensivo questionável] `is_connected` default `True` se attr ausente

- **Arquivo:** `src/hefesto/core/backend_pydualsense.py:75`
- **Severidade:** baixo
- **Evidência:**
  ```python
  def is_connected(self) -> bool:
      if self._ds is None:
          return False
      return bool(getattr(self._ds, "connected", True))
  ```
- **Análise:** Se o pydualsense remover `connected` em versão futura, default reporta `True` (conectado). Seguro seria default `False` — conservador.
- **Recomendação:** mudar default para `False` e acrescentar log debug.
- **Sprint nova:** NENHUMA (Edit pronto quando alguém pegar AUDIT-FINDING-LOG-EXC-INFO-01)

### 21. [código-morto] Sentinels no dicionário `_PARES` de `validar-acentuacao.py`

- **Arquivo:** `scripts/validar-acentuacao.py:319, 376, 380, 381`
- **Severidade:** cosmético
- **Evidência:**
  ```python
  _par("m" + "enor", "menor"),  # sentinel — menor já é correto, não adicionar
  _par("depo" + "is", "depois"),  # já correto; não altera
  _par("categor" + "ia", "categoria"),  # correta em minúscula; mantém
  _par("prior" + "idade", "prioridade"),  # já correta sem acento
  ```
  O loop de dedup (linha 389) rejeita pares onde `errada == correta` → essas 4 entradas viram no-ops. Servem só de "doc-in-code" para impedir futuros contributors de tentar adicioná-las.
- **Análise:** redundância pedagógica. Funciona. Um `# NOT_WORDS = ["menor", "depois", ...]` teria o mesmo efeito sem confundir o leitor.
- **Recomendação:** remover ou converter em set explícito com comentário explicativo.
- **Sprint nova:** NENHUMA (Edit pronto)

### 22. [code-smell] `_deliver` em `core/events.py` usa nested `contextlib.suppress`

- **Arquivo:** `src/hefesto/core/events.py:105-123`
- **Severidade:** cosmético
- **Evidência:**
  ```python
  def _deliver(self, sub: _Subscriber, topic: str, payload: Any) -> None:
      try:
          sub.queue.put_nowait(payload)
          sub.overflow_logged = False
          return
      except asyncio.QueueFull:
          pass
      with contextlib.suppress(asyncio.QueueEmpty):
          sub.queue.get_nowait()
          with contextlib.suppress(asyncio.QueueFull):
              sub.queue.put_nowait(payload)
      if not sub.overflow_logged: ...
  ```
- **Análise:** defesa contra race que não existe — o design single-threaded asyncio garante que put/get não interleaveiam. Pattern é defensivo corretamente, mas o duplo-suppress sinaliza ou que o autor subestimou o design (over-defensive) ou que a função pode ser chamada de threads (documentation diz que não). Vale um comentário explicativo.
- **Recomendação:** adicionar comentário de 1 linha explicando por que o duplo-suppress, OU simplificar se a single-thread garantia é real.
- **Sprint nova:** NENHUMA

### 23. [teste gap] `trigger_effects.py` coverage 99% — 2 linhas de raise-path não exercitadas

- **Arquivo:** `src/hefesto/core/trigger_effects.py:136, 251`
- **Severidade:** cosmético
- **Evidência:** linhas 136 (`raise ValueError("galloping: end ({end}) deve ser > start ({start})")`) e 251 (`raise ValueError(f"multi_position_vibration: precisa 10 strengths, recebeu {len(strengths)}")`) são só as assertivas de validação sem teste.
- **Recomendação:** acrescentar 2 testes `pytest.raises(ValueError, match=...)` em `test_trigger_effects.py` ou similar.
- **Sprint nova:** NENHUMA

### 24. [teste gap] Cov 60% em `keyboard.py`, 55% em `single_instance.py`, 53% em `subsystems/mouse.py`

- **Arquivo:** ver tabela em "Saídas de ferramentas"
- **Severidade:** baixo
- **Evidência:** `daemon/subsystems/keyboard.py` 168 stmts, 67 miss (60%), `utils/single_instance.py` 154 stmts, 70 miss (55%), `daemon/subsystems/mouse.py` 66 stmts, 31 miss (53%). Linhas missing concentram-se em branches de erro (onboard/wvkbd missing, pid reciclado, mouse unplug). Críticos demais para 53-60% de cobertura.
- **Recomendação:** sub-sprint separada cobrindo os 3 módulos com branches faltantes. `single_instance` é especialmente crítico (segurança).
- **Sprint nova:** agrupada em AUDIT-FINDING-COVERAGE-ACTIONS-ZERO-01

### 25. [processo/meta] `VALIDATOR_BRIEF.md` armadilha A-06 precisa ampliação para mic_led

- **Arquivo:** `VALIDATOR_BRIEF.md` seção "A-06" (linhas 126-131)
- **Severidade:** processo (meta)
- **Evidência:** A-06 descreve "Campo novo em `LedsConfig`/`TriggersConfig`/`RumbleConfig` precisa sprint-par de profile-apply". Foi marcada RESOLVIDA para `lightbar_brightness` e `player_leds`. Mas achado 3 (mic_led) mostra caso inverso: **campo que nunca entrou em LedsConfig mas cujo default é aplicado ao hardware**. A armadilha não cobre esse caso.
- **Recomendação:** após AUDIT-FINDING-PROFILE-MIC-LED-RESET-01, atualizar A-06 com variante: "Campo ausente em `*Config` mas aplicado pelo apply_led_settings com default pode regredir estado runtime". Alternativamente, reescrever A-06 para o princípio mais amplo: "toda chamada em `apply_*_settings` precisa ou vir de um campo persistido ou ser condicional a flag `is_present`".
- **Sprint nova:** incluída em AUDIT-FINDING-PROFILE-MIC-LED-RESET-01 (edit do BRIEF no final)

### 26. [processo/meta] README reporta "1036 unit tests" — count atual é 1143

- **Arquivo:** `README.md:8`
- **Severidade:** cosmético
- **Evidência:**
  ```markdown
  [![Testes](https://img.shields.io/badge/testes-1036%20unit-brightgreen.svg)](tests/unit/)
  ```
  pytest atual: `1143 passed, 5 skipped`. Diff: +107 testes (provavelmente keyboard V2.3).
- **Recomendação:** badge estático em README drift. Idealmente automatizado via workflow que edita o badge no bump de versão. Por ora, atualizar para 1143.
- **Sprint nova:** NENHUMA (Edit pronto)

---

## Processo (meta)

- **Ruff e mypy limpos em 18k LOC é notável.** É o resultado de CI strict + pre-commit hooks (VALIDATOR_BRIEF seção "Contratos de runtime"). Disciplina visível.
- **Coverage de 63% é enganosamente baixo** — concentração em actions/ GUI que têm teste difícil em headless. Backend coverage (core/ + daemon/ + profiles/) bate >80% amplamente. A solução é padrão `_FakeMixin` aplicado mais largamente, não teste GUI real em CI.
- **Duplicação entre `daemon/subsystems/` e `core/`** ocorre em rumble e ocorreu em autoswitch. O princípio "import circular evitado" é invocado mas o próprio ipc_server.py quebra o princípio importando `_effective_mult` do core. Padrão documentado na origem se mantém mesmo quando a razão técnica evapora — sinal clássico de acoplamento conceitual que precisa ser revisado na arquitetura.
- **13 lições empíricas (L-21-1 até L-21-7 + sub-checklist)** mostram maturidade do processo. Auditoria não contradiz nenhuma — reforça L-21-3 (ler o código antes do spec) via achados 3, 6, 7 onde o código estava claramente derivando de narrativa sem grep atual.

---

## Fixes inline aplicados

Nenhum. A auditoria é estritamente diagnóstica. Todos os fixes (mesmo triviais) foram deferred para sprints-filhas conforme protocolo 9.7. Única exceção autorizada (typo trivial em comentário/string) não foi necessária.

---

## Índice de sprints-filhas geradas

| # | ID | Origem (achados) | Severidade | Porte estimado |
|---|---|---|---|---|
| 1 | `AUDIT-FINDING-UDP-PLACEHOLDER-HANDLERS-01` | 1, 19 | alto | S |
| 2 | `AUDIT-FINDING-IPC-DRAFT-RUMBLE-POLICY-01` | 2 | alto | XS |
| 3 | `AUDIT-FINDING-PROFILE-MIC-LED-RESET-01` | 3, 25 | alto | M |
| 4 | `AUDIT-FINDING-PROFILE-PATH-TRAVERSAL-01` | 4 | alto | S |
| 5 | `AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01` | 5 | alto | M |
| 6 | `AUDIT-FINDING-KEYBOARD-SUBSYSTEM-DEAD-01` | 6 | alto | XS |
| 7 | `AUDIT-FINDING-DEAD-CODE-01` | 7, 21 | médio | XS |
| 8 | `AUDIT-FINDING-EVDEV-READER-BASE-CLASS-01` | 8 | médio | M |
| 9 | `AUDIT-FINDING-IPC-BRIDGE-BARE-EXCEPT-01` | 9 | médio | S |
| 10 | `AUDIT-FINDING-SINGLE-INSTANCE-PID-RECYCLE-01` | 10 | médio | S |
| 11 | `AUDIT-FINDING-WAYLAND-PORTAL-PERF-01` | 11 | médio | S |
| 12 | `AUDIT-FINDING-COVERAGE-ACTIONS-ZERO-01` | 12, 14, 24 | médio | L |
| 13 | `AUDIT-FINDING-IPC-SERVER-SPLIT-01` | 13 | médio | L |
| 14 | `AUDIT-FINDING-LOG-EXC-INFO-01` | 15, 16, 17, 18, 20 | baixo | M (checklist) |

Ordem sugerida de execução (em `SPRINT_ORDER.md` wave V2.4):
1. Altos primeiro (`UDP-PLACEHOLDER-HANDLERS`, `PROFILE-MIC-LED-RESET`, `IPC-DRAFT-RUMBLE-POLICY`, `PROFILE-PATH-TRAVERSAL`, `RUMBLE-POLICY-DEDUP`, `KEYBOARD-SUBSYSTEM-DEAD`).
2. Médios em seguida (`DEAD-CODE`, `EVDEV-READER-BASE-CLASS`, `IPC-BRIDGE-BARE-EXCEPT`, `SINGLE-INSTANCE-PID-RECYCLE`, `WAYLAND-PORTAL-PERF`, `COVERAGE-ACTIONS-ZERO`, `IPC-SERVER-SPLIT`).
3. Baixos (`LOG-EXC-INFO` — checklist de 10-15 pontos).

Achados 17, 19, 20, 21, 22, 23, 26 não geram sprint — são edits prontos que qualquer executor faz em passagem futura (autorização implícita no protocolo 9.7 dado a trivialidade).

---

*"A forja não revela o ferreiro. Só a espada. Mas a auditoria mede a espada."*
