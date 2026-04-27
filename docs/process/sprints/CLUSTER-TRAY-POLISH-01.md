# CLUSTER-TRAY-POLISH-01 — três bugs do tray (quit limpo + zumbi "(carregando)" + underscore mnemonic)

**Tipo:** bug-fix (cluster).
**Wave:** V2.2.x — pós-rebrand.
**Branch:** `rebrand/dualsense4unix`. PR alvo: #103.
**Estimativa:** 1 iteração (cluster de 3 sub-frentes em um único spec por afinidade de arquivos: `app/tray.py` e `app/app.py`).
**Dependências:** nenhuma.

---

**Tracking:** label `type:bug`, `area:gui`, `area:tray`, `status:ready`.

## Contexto

Cluster ataca **três defeitos do tray do GTK3 reportados em runtime real (2026-04-27)** num único spec porque dois deles tocam o mesmo arquivo (`app/tray.py`) e o terceiro toca um arquivo adjacente (`app/app.py`). Atacar em PRs separados gera 2-3 conflitos de merge na mesma região.

Trechos lidos que confirmam a premissa:
- `src/hefesto_dualsense4unix/app/app.py:261-295` — `quit_app` chama `Gtk.main_quit()` antes do cleanup; `_shutdown_backend` roda numa thread `daemon=True` e só faz `tray.stop()` + `systemctl --user stop hefesto-dualsense4unix.service`. Não tenta matar daemon avulso (não-systemd).
- `src/hefesto_dualsense4unix/app/tray.py:81-86` — submenu "Perfis" recebe placeholder `Gtk.MenuItem(label="(carregando)")` na inicialização e adiciona ao `_profiles_submenu` direto. Esse item NÃO entra em `_profile_menu_items`.
- `src/hefesto_dualsense4unix/app/tray.py:119-144` — `_render_profiles` itera `for item in self._profile_menu_items: self._profiles_submenu.remove(item)`. Como o placeholder de inicialização não está em `_profile_menu_items`, ele nunca é removido.
- `src/hefesto_dualsense4unix/app/tray.py:137` — `Gtk.MenuItem(label=label)` cria item com `use_underline=True` (default GTK3). Resultado: `meu_perfil` vira `meu__perfil` (escape de mnemonic) ou abre atalho oculto.
- `src/hefesto_dualsense4unix/utils/single_instance.py:60-78` — `_pid_file("daemon")` resolve para `runtime_dir() / "daemon.pid"`. `is_alive(pid)` cobre `ProcessLookupError → False`, `PermissionError → True` (defensivo). `_is_hefesto_dualsense4unix_process(pid)` confere `/proc/<pid>/comm` ou `cmdline` contra marker `"hefesto"` antes de matar — protege contra recycle de PID.
- `src/hefesto_dualsense4unix/utils/xdg_paths.py:40-47` — `runtime_dir(ensure=False)` retorna `Path("$XDG_RUNTIME_DIR/hefesto-dualsense4unix")` (com fallback documentado).
- `tests/unit/test_quit_app_stops_daemon.py:1-153` — 5 testes existentes do `quit_app`: validam systemctl call, fallback a FileNotFoundError, tray.stop, TimeoutExpired, ordem `Gtk.main_quit` antes do cleanup. Reusar `_InstantThread` e `_make_quit_stub`.

### Bug A — TRAY-QUIT-CLEAN-01

GUI sobe (manualmente ou via hotplug). Daemon roda **fora do systemd** (caso comum em dev: `nohup ~/.local/bin/hefesto-dualsense4unix daemon start --foreground &` ou execução direta). User clica "Sair" no tray. `_shutdown_backend` chama `systemctl --user stop hefesto-dualsense4unix.service` — no-op porque a unit não está rodando. GUI morre. Daemon avulso continua vivo em background, sem janela visível, segurando socket IPC, evdev, uinput, hidraw.

Reproduzido 2026-04-27: GUI subiu, daemon avulso PID 188004 iniciado por shell, click em "Sair" → GUI morreu, `pgrep -af hefesto` ainda lista 188004 ativo.

Causa raiz: `_shutdown_backend` só conhece o caminho via systemctl, ignora o pid file canônico (`$XDG_RUNTIME_DIR/hefesto-dualsense4unix/daemon.pid`) que `acquire_or_takeover("daemon")` cria em `daemon/main.py:41` independente de quem subiu o daemon.

### Bug B — TRAY-LOADING-ZOMBIE-01

Submenu "Perfis" do tray exibe item desabilitado `(carregando)` permanentemente, mesmo após perfis terem sido populados. Confirmado por dbusmenu introspection (2026-04-27):

```
id=5 label='Perfis' enabled=True
  id=6 label='(carregando)' enabled=0   <- nunca removido
  id=139 label='André' enabled=True
  id=140 label='audiophile' enabled=True
  id=141 label='fallback' enabled=True
  id=142 label='meu__perfil' enabled=True
  ...
```

Causa raiz: o placeholder é adicionado ao `_profiles_submenu` em `tray.py:83-85` durante `start()`, antes do primeiro `_render_profiles`. Mas o loop de remoção em `_render_profiles:122-123` itera apenas `_profile_menu_items` — a lista que `_render_profiles` mesmo gerencia. O placeholder de inicialização ficou fora dessa lista; é órfão.

### Bug C — TRAY-UNDERSCORE-MNEMONIC-01

Perfil chamado `meu_perfil` aparece no menu como `meu__perfil`. Confirmado por dbusmenu introspection acima (`id=142 label='meu__perfil'`).

Causa raiz: `Gtk.MenuItem(label=label)` na linha 137 herda `use_underline=True` por default GTK3. Quando uma label tem `_`, GTK3 interpreta o caractere seguinte como mnemonic atalho (Alt+letter). Dependendo da versão / aparência, o `_` pode ser exibido sublinhado ou (no caso atual, via dbusmenu rendering) escapado para `__`. O usuário vê algo errado de qualquer forma. Solução canônica: `set_use_underline(False)` desliga o feature — perfis não precisam de atalho.

## Escopo (touches autorizados)

**Arquivos a modificar:**
- `src/hefesto_dualsense4unix/app/app.py` — `_shutdown_backend` e `quit_app` (Bug A).
- `src/hefesto_dualsense4unix/app/tray.py` — eliminar placeholder de inicialização e setar `use_underline=False` em itens de perfil (Bugs B e C).
- `tests/unit/test_quit_app_stops_daemon.py` — adicionar testes para o pid-file fallback do Bug A.
- `tests/unit/test_tray.py` — adicionar testes para Bugs B e C (renderização de perfis, ausência do placeholder zumbi, `use_underline=False`).

**Arquivos a criar:** nenhum — extensão de testes existentes preferível a arquivo novo.

**Arquivos NÃO a tocar:**
- `src/hefesto_dualsense4unix/integrations/tray.py` — `TrayController` em `integrations` é canal D-Bus separado (`probe_gi_availability` apenas). Bugs estão no `AppTray` em `app/tray.py`.
- `src/hefesto_dualsense4unix/utils/single_instance.py` — `is_alive`, `_is_hefesto_dualsense4unix_process`, `_pid_file` são canônicos e reusáveis. Importar; não modificar.
- `src/hefesto_dualsense4unix/utils/xdg_paths.py` — `runtime_dir` já exposto. Não tocar.
- `assets/hefesto-dualsense4unix.service`, `install.sh`, `uninstall.sh` — fora de escopo.
- `src/hefesto_dualsense4unix/daemon/main.py` — daemon side já cria `daemon.pid` via `acquire_or_takeover`. Lado consumidor (GUI) é que faltava ler.

## Acceptance criteria

### Bug A — TRAY-QUIT-CLEAN-01

1. `_shutdown_backend` em `app/app.py` continua chamando `systemctl --user stop hefesto-dualsense4unix.service` (cobre daemon-systemd-managed). Comportamento e testes existentes (`test_quit_app_chama_systemctl_stop`, `test_quit_app_sobrevive_a_systemctl_ausente`, `test_quit_app_para_tray`, `test_quit_app_sobrevive_a_timeout`, `test_quit_app_main_quit_antes_do_cleanup`) permanecem verdes.
2. Após o systemctl stop, `_shutdown_backend` lê o pid file `runtime_dir() / "daemon.pid"`. Se ausente ou ilegível, segue silenciosamente.
3. Se PID legível e `is_alive(pid)` é True E `_is_hefesto_dualsense4unix_process(pid)` confirma marker — envia `os.kill(pid, signal.SIGTERM)`. Espera até 3s em loop poll de 100ms checando `is_alive`. Se ainda vivo após 3s, envia `os.kill(pid, signal.SIGKILL)`.
4. Se `os.kill` levanta `ProcessLookupError` (daemon morreu durante a janela), trata silenciosamente. `PermissionError` é log warning + segue.
5. Se PID corresponde a processo NÃO-Hefesto (recycle), aborta sem matar — log warning `quit_app_pid_recycle_detectado`. Reusa `_is_hefesto_dualsense4unix_process` de `single_instance.py`.
6. Operação é **idempotente**: se daemon já foi morto pelo systemctl stop (caso systemd-managed), o `is_alive(pid_lido)` retorna False → nenhum kill é enviado, função retorna em silêncio.
7. Ordem das ações em `_shutdown_backend`: (a) `tray.stop()`; (b) `systemctl stop`; (c) ler pid file e SIGTERM/SIGKILL fallback. Logs informativos PT-BR a cada etapa.
8. `Gtk.main_quit()` continua sendo chamado **antes** do `_shutdown_backend` (em `quit_app`) — invariante já testado em `test_quit_app_main_quit_antes_do_cleanup`.
9. Reproduzir o cenário runtime-real e confirmar daemon avulso morto (proof-of-work seção dedicada).

### Bug B — TRAY-LOADING-ZOMBIE-01

10. Em `tray.py:start()` (~linhas 81-86), o placeholder `Gtk.MenuItem(label="(carregando)")` é **adicionado a `_profile_menu_items`** quando criado, OU é removido no início de `_render_profiles` antes do loop de populate, OU é simplesmente eliminado e substituído por chamada explícita a `_render_profiles([])` que via critério 11 produz "(nenhum perfil)" temporariamente.
11. Recomendado (alternativa preferida): **remover o placeholder de inicialização**. Em vez disso, chamar `self._render_profiles([])` antes do `_tick_refresh()` em `start()`, deixando `_render_profiles` controlar 100% do conteúdo do submenu via `_profile_menu_items`.
12. Após `_render_profiles(profiles_reais)`, a árvore dbusmenu do submenu "Perfis" não contém nenhum item com label `(carregando)`.
13. Teste novo (`test_tray.py`): instanciar `AppTray` com fake gi, chamar `start()` + `_render_profiles([{"name": "X", "active": True}])`, validar que `_profiles_submenu.append` foi chamado **apenas** com itens em `_profile_menu_items` (sem ghost) e que nenhum item criado tem label `"(carregando)"` permanente após o render.

### Bug C — TRAY-UNDERSCORE-MNEMONIC-01

14. Em `_render_profiles` linha 137, após `item = Gtk.MenuItem(label=label)`, chamar `item.set_use_underline(False)` antes do `connect`.
15. Aplicar a mesma chamada no item `(nenhum perfil)` (linha 127) por consistência — ele não tem `_` hoje, mas o reflexo defensivo evita regressão futura se o texto mudar.
16. Não aplicar em `_status_item` (linha 71) nem em `show` (linha 75) nem em `quit_item` (linha 91): labels conhecidas, sem `_`, e mnemonic explícito em "Sair" / "Abrir painel" pode ser desejável no futuro.
17. Teste novo (`test_tray.py`): após `_render_profiles([{"name": "meu_perfil", "active": False}])`, confirmar que `set_use_underline(False)` foi chamado no item correspondente.
18. Runtime real: dbusmenu introspection após o fix mostra `label='meu_perfil'` (sem `__` duplo).

### Frente comum

19. Gates canônicos verdes:
    - `bash scripts/dev-setup.sh` (preparo).
    - `.venv/bin/pytest tests/unit -v --no-header -q`.
    - `.venv/bin/ruff check src/ tests/`.
    - `.venv/bin/mypy src/hefesto_dualsense4unix`.
    - `./scripts/check_anonymity.sh`.
20. Smoke USB e BT verdes (FakeController) — não regrediu nada do daemon:
    - `HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=usb HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke`.
    - `HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=bt  HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke --bt`.
21. Acentuação periférica (`á é í ó ú â ê ô ã õ à ç`) em toda string e log adicionados — nenhum `funcao`, `acao`, `nao`, `informacao`, `validacao`, `aplicacao`.

## Invariantes a preservar

- **PT-BR obrigatório** em mensagens, logs e comentários novos (`[CORE] Identidade do projeto`).
- **Acentuação correta** em qualquer string/log adicionado.
- **Zero emojis gráficos**. Glyphs de estado (U+25CF, U+25CB, etc.) permitidos mas inaplicáveis aqui.
- **Ordem `Gtk.main_quit` ANTES do cleanup** (`quit_app:267-273` docstring) — testada em `test_quit_app_main_quit_antes_do_cleanup`. NÃO inverter.
- **Thread `daemon=True`** do `_shutdown_backend` — não trocar para `daemon=False` (docstring linha 280-281 explica que cleanup pode travar em D-Bus sem StatusNotifierWatcher robusto). O timeout de 3s no SIGTERM-poll é o teto; SIGKILL imediato após.
- **A-10 (BRIEF)** — `acquire_or_takeover("daemon")` é a fonte canônica do pid file. NÃO criar pid file paralelo no GUI.
- **A-12 (BRIEF)** — GUI roda com `--system-site-packages` para PyGObject; nada muda aqui mas testes que mockam `gi` precisam continuar funcionando (vide pattern em `test_tray.py:55-79`).
- **Reuso de helpers**: importar `is_alive` e `_is_hefesto_dualsense4unix_process` de `single_instance.py`. NÃO duplicar a heurística de markers.
- **Idempotência** do `_shutdown_backend`: rodar 2x consecutivos não pode mandar SIGKILL para PID 0 nem para processo aleatório.
- **`logger.warning` / `logger.info` via structlog** (`utils.logging_config`). Nunca `print()`.
- **Não adicionar `subprocess` calls síncronas adicionais com timeout >3s**: o cleanup tem orçamento de ~8s total (5s systemctl + 3s SIGTERM poll) e roda em thread daemon — encerrar mesmo que trave.
- **`_profile_menu_items` é a única fonte de verdade** do submenu Perfis após o fix. Qualquer item adicionado via `_profiles_submenu.append` que não esteja em `_profile_menu_items` é anti-padrão (lição aprendida do Bug B).

## Plano de implementação

### 1. `app/app.py` — fix Bug A

a. Adicionar imports no topo se ausentes: `signal` (já presente linha 15), `os` (já presente linha 14). Importar dois helpers e o path:
```python
from hefesto_dualsense4unix.utils.single_instance import is_alive, _is_hefesto_dualsense4unix_process
from hefesto_dualsense4unix.utils.xdg_paths import runtime_dir
```
Como `_is_hefesto_dualsense4unix_process` começa com `_` (privado), reexportar via __all__ pode ser exigido por lint. Alternativa: re-expor em `single_instance.py` removendo o underscore (renomear para `is_hefesto_dualsense4unix_process`) — preferível, atualiza referências internas no mesmo módulo e evita import de privado entre pacotes. Verificar com `rg "_is_hefesto_dualsense4unix_process"` antes para listar callers e renomear todos.

b. Em `_shutdown_backend` (linha 279-295), após o try/except de `subprocess.run`, adicionar bloco:
```python
# Fallback: daemon avulso (não-systemd) sobrevive ao stop acima.
# Le pid canônico criado por acquire_or_takeover("daemon").
pid_path = runtime_dir() / "daemon.pid"
try:
    raw = pid_path.read_text(encoding="ascii").strip()
    pid = int(raw)
except (FileNotFoundError, OSError, ValueError):
    return

if pid <= 0 or not is_alive(pid):
    return

if not is_hefesto_dualsense4unix_process(pid):
    logger.warning("quit_app_pid_recycle_detectado", pid=pid)
    return

try:
    os.kill(pid, signal.SIGTERM)
except ProcessLookupError:
    return
except PermissionError as exc:
    logger.warning("quit_app_sigterm_perm", pid=pid, erro=str(exc))
    return

# Espera grace 3s polling 100ms.
import time
deadline = time.monotonic() + 3.0
while time.monotonic() < deadline:
    if not is_alive(pid):
        logger.info("quit_app_daemon_avulso_encerrado", pid=pid)
        return
    time.sleep(0.1)

try:
    os.kill(pid, signal.SIGKILL)
    logger.warning("quit_app_daemon_avulso_sigkill", pid=pid)
except ProcessLookupError:
    pass
```

c. Confirmar que `time` está importado (não está hoje — adicionar `import time` no bloco de stdlib no topo).

d. Acentuação: `encerrado`, `recycle detectado`, `não-systemd`. Logs como structlog kwargs (snake_case ASCII), só value-strings em PT-BR.

### 2. `app/tray.py` — fix Bug B

a. Em `start()`, **remover** as linhas 83-85 (criação e append do placeholder). Substituir por:
```python
self._profiles_item.set_submenu(self._profiles_submenu)
self._menu.append(self._profiles_item)
# ...resto do start permanece...

# Logo antes de GLib.timeout_add_seconds (linha ~98):
self._render_profiles([])  # popula com "(nenhum perfil)" via path canônico
```
Isso garante que o submenu nasce com um único item desabilitado `(nenhum perfil)` controlado por `_profile_menu_items`. O primeiro `_tick_refresh()` (linha 99) então remove esse item e popula com perfis reais.

b. Como `_render_profiles([])` chama `self._profiles_submenu.show_all()`, o submenu já fica visível antes do tick — sem zumbi.

c. Atenção: `_render_profiles` em :144 chama `show_all()`. O `_menu.show_all()` de `:95` cobre todo o menu — chamada extra é segura.

### 3. `app/tray.py` — fix Bug C

a. Na linha 127 (criação de "(nenhum perfil)") inserir antes do `append`:
```python
item.set_use_underline(False)
```

b. Na linha 137 (criação dos itens de perfil) inserir antes do `connect`:
```python
item.set_use_underline(False)
```

### 4. Testes — `tests/unit/test_quit_app_stops_daemon.py`

a. Adicionar testes (4-5 cenários) reusando `_InstantThread` e `_make_quit_stub`:
- `test_quit_app_mata_daemon_avulso_via_pid_file` — monkeypatch `runtime_dir` para tmp, escreve pid 12345 com fake `is_alive=True` e `is_hefesto_dualsense4unix_process=True`, mock `os.kill`, valida chamada SIGTERM.
- `test_quit_app_pid_file_ausente_continua` — pid file não existe, função retorna sem erro.
- `test_quit_app_pid_recycle_aborta_kill` — pid vivo mas `is_hefesto_dualsense4unix_process` retorna False → nenhum `os.kill` enviado.
- `test_quit_app_pid_morto_apos_systemctl_stop` — `is_alive(pid)` retorna False (caso systemd-managed) → nenhum kill, função retorna em silêncio (idempotência).
- `test_quit_app_sigkill_apos_grace` — primeiro check `is_alive=True` por toda janela, valida que `os.kill(pid, SIGKILL)` foi chamado após o loop.
- Para acelerar grace: monkeypatch `time.monotonic` ou `time.sleep` para zero.

### 5. Testes — `tests/unit/test_tray.py`

a. Adicionar bloco `test_tray_apptray_*` reusando `_setup_fake_gi`. Como `AppTray` depende de `gi.repository.Gtk` e `AyatanaAppIndicator3`, mocks já existem no fixture.

b. Cenários:
- `test_apptray_render_profiles_remove_placeholder_inicial` — chama `start()` (que agora chama `_render_profiles([])` em vez de adicionar placeholder cru), depois `_render_profiles([{"name": "X"}])`, confirma que nenhum `MenuItem` criado tem label `"(carregando)"`.
- `test_apptray_render_profiles_aplica_use_underline_false` — chama `_render_profiles([{"name": "meu_perfil", "active": False}])`, valida que `set_use_underline(False)` foi chamado no item criado para `meu_perfil`.
- `test_apptray_render_perfil_vazio_aplica_use_underline_false` — `_render_profiles([])`, valida `set_use_underline(False)` em "(nenhum perfil)".

## Aritmética estimada

- `app/app.py`: baseline 422L. Adicionar bloco de pid-file fallback em `_shutdown_backend` ~30L + `import time` 1L = +31L → projetado **~453L**. Limite 800L (`[CORE] Padrões de código`) — folga 347L.
- `app/tray.py`: baseline 181L. Bug B remove 3L (placeholder), adiciona 1L (`_render_profiles([])` no start). Bug C adiciona 2L (`set_use_underline(False)` em 2 lugares). Saldo +0L. Projetado **~181L**. Limite 800L — folga 619L.
- `tests/unit/test_quit_app_stops_daemon.py`: baseline 153L. Adicionar 5 testes × ~25L cada = +125L → projetado **~278L**.
- `tests/unit/test_tray.py`: baseline 129L. Adicionar 3 testes × ~30L cada = +90L → projetado **~219L**.
- `src/hefesto_dualsense4unix/utils/single_instance.py`: rename `_is_hefesto_dualsense4unix_process` → `is_hefesto_dualsense4unix_process` (1 linha de def + atualizar todos callers no mesmo arquivo, ~3 ocorrências). Saldo neutro. Conferir via `rg "_is_hefesto_dualsense4unix_process"` antes do refactor (lição L-21-3) para garantir nenhum caller externo está afetado; se houver caller fora do módulo, atualizar também.

Total de linhas projetadas adicionadas: ~245L. Sem nenhum arquivo aproximando-se do limite 800L.

## Testes

**Adicionados:**
- `test_quit_app_stops_daemon.py`: 5 testes novos para o pid-file fallback (Bug A).
- `test_tray.py`: 3 testes novos para placeholder e use_underline (Bugs B e C).

**Baseline:** verde antes do início. Suite atual ≈ 998 passed (vide rodapé do BRIEF, BUG-PLAYER-LEDS-APPLY-01 2026-04-23 cita 998).

**FAIL_BEFORE = 0**, esperado **FAIL_AFTER = 0**. Suite total esperada após sprint ≈ 1006 passed.

## Proof-of-work esperado

### Diff final
- `git diff rebrand/dualsense4unix~1..HEAD -- src/hefesto_dualsense4unix/app/app.py src/hefesto_dualsense4unix/app/tray.py src/hefesto_dualsense4unix/utils/single_instance.py tests/unit/test_quit_app_stops_daemon.py tests/unit/test_tray.py`

### Runtime real
```bash
# Preparo
bash scripts/dev-setup.sh

# Smoke USB (2s) — FakeController, sem hardware
HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=usb \
  HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke

# Smoke BT (2s)
HEFESTO_DUALSENSE4UNIX_FAKE=1 HEFESTO_DUALSENSE4UNIX_FAKE_TRANSPORT=bt \
  HEFESTO_DUALSENSE4UNIX_SMOKE_DURATION=2.0 ./run.sh --smoke --bt

# Unit
.venv/bin/pytest tests/unit -v --no-header -q

# Lint + types
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto_dualsense4unix

# Anonimato
./scripts/check_anonymity.sh
```

### Bug A — proof runtime real (daemon avulso encerra junto com GUI)
```bash
# Setup: parar systemd unit, subir daemon avulso por shell
systemctl --user stop hefesto-dualsense4unix.service
nohup ~/.local/bin/hefesto-dualsense4unix daemon start --foreground >/tmp/test_daemon.log 2>&1 &
sleep 3

# Confirmar PID avulso
DAEMON_PID=$(cat "$XDG_RUNTIME_DIR/hefesto-dualsense4unix/daemon.pid")
echo "daemon avulso pid=$DAEMON_PID"
ps -p "$DAEMON_PID" -o pid,comm,args

# Subir GUI (separado, não via hotplug)
DISPLAY=:1 nohup ~/.local/bin/hefesto-dualsense4unix-gui >/tmp/test_gui.log 2>&1 &
sleep 4

# Disparar "Sair" via dbusmenu
.venv/bin/python <<'PY'
import dbus
bus = dbus.SessionBus()
watcher = bus.get_object('org.kde.StatusNotifierWatcher', '/StatusNotifierWatcher')
items = dbus.Interface(watcher, 'org.freedesktop.DBus.Properties').Get(
    'org.kde.StatusNotifierWatcher', 'RegisteredStatusNotifierItems')
hef = next(str(i) for i in items if 'hefesto' in str(i))
proxy = bus.get_object(
    hef.split('/')[0],
    '/org/ayatana/NotificationItem/hefesto_dualsense4unix/Menu')
menu = dbus.Interface(proxy, 'com.canonical.dbusmenu')
_, layout = menu.GetLayout(0, -1, dbus.Array([], signature='s'))
def find(item, label):
    iid, props, kids = item
    if label.lower() in str(props.get('label', '')).lower():
        return iid
    for k in kids:
        r = find(k, label)
        if r:
            return r
sair_id = find(layout, 'Sair')
menu.Event(dbus.Int32(sair_id), 'clicked', dbus.String(''), dbus.UInt32(0))
PY

sleep 6
# Esperado vazio
pgrep -af "hefesto" | grep -v grep || echo "limpo"

# Confirmação positiva
test ! -e "/proc/$DAEMON_PID" && echo "daemon avulso $DAEMON_PID encerrado"
```

### Bug B — proof runtime real (placeholder some)
```bash
# GUI rodando (mesma sessão acima ou nova)
.venv/bin/python <<'PY'
import dbus
bus = dbus.SessionBus()
watcher = bus.get_object('org.kde.StatusNotifierWatcher', '/StatusNotifierWatcher')
items = dbus.Interface(watcher, 'org.freedesktop.DBus.Properties').Get(
    'org.kde.StatusNotifierWatcher', 'RegisteredStatusNotifierItems')
hef = next(str(i) for i in items if 'hefesto' in str(i))
proxy = bus.get_object(
    hef.split('/')[0],
    '/org/ayatana/NotificationItem/hefesto_dualsense4unix/Menu')
menu = dbus.Interface(proxy, 'com.canonical.dbusmenu')
_, layout = menu.GetLayout(0, -1, dbus.Array([], signature='s'))
def walk(item, depth=0):
    iid, props, kids = item
    label = str(props.get('label', ''))
    print(f"{'  '*depth}id={iid} label={label!r}")
    for k in kids:
        walk(k, depth + 1)
walk(layout)
PY

# Esperado: nenhum item com label '(carregando)' no submenu Perfis.
```

### Bug C — proof runtime real (sem underscore duplicado)
- Mesma introspection acima. Esperado: o item para `meu_perfil` aparece como `label='meu_perfil'` (não `'meu__perfil'`).
- Pré-requisito: existir um perfil chamado `meu_perfil` em `~/.config/hefesto-dualsense4unix/profiles/` para o run real. Se ausente, criar:
```bash
cp ~/.config/hefesto-dualsense4unix/profiles/fallback.json \
   ~/.config/hefesto-dualsense4unix/profiles/meu_perfil.json
# Editar "name": "meu_perfil"
```

### Validação visual (skill `validacao-visual`)
- Não estritamente obrigatória (mudança não muda layout do glade), mas **recomendada**: após fix, capturar tray menu aberto via `import -window root` e descrever os 3 estados (placeholder some, perfis sem `__`, "Sair" encerra tudo). Subordinado ao BRIEF `[CORE] Capacidades visuais aplicáveis`. Se executor pular, justificar no proof-of-work.

```bash
.venv/bin/python -m hefesto_dualsense4unix.app.main &
sleep 3
TS=$(date +%Y%m%dT%H%M%S)
# tray icon: capturar painel completo (nem todos os DEs permitem screenshot só do menu)
import -window root "/tmp/hefesto_tray_polish_${TS}.png"
sha256sum "/tmp/hefesto_tray_polish_${TS}.png"
```

### Acentuação periférica
```bash
# Em todos os arquivos modificados:
for f in src/hefesto_dualsense4unix/app/app.py \
         src/hefesto_dualsense4unix/app/tray.py \
         src/hefesto_dualsense4unix/utils/single_instance.py \
         tests/unit/test_quit_app_stops_daemon.py \
         tests/unit/test_tray.py; do
  rg -n "funcao|acao|nao\b|informacao|validacao|aplicacao|configuracao|descricao" "$f" || echo "  $f: ok"
done
```

### Hipótese verificada (lição L-21-3 / 4)
```bash
# Confirmar que identificadores citados existem antes do executor começar:
rg -n "def _shutdown_backend|def quit_app|def _render_profiles|def _is_hefesto_dualsense4unix_process|def is_alive|_pid_file|runtime_dir" \
  src/hefesto_dualsense4unix/app/app.py \
  src/hefesto_dualsense4unix/app/tray.py \
  src/hefesto_dualsense4unix/utils/single_instance.py \
  src/hefesto_dualsense4unix/utils/xdg_paths.py
```

## Riscos e não-objetivos

- **Risco residual A (Bug A):** se `daemon.pid` foi escrito por uma instância antiga e a flock foi perdida sem limpeza (corner case), GUI poderia tentar matar PID alheio. Mitigado por `is_hefesto_dualsense4unix_process` (heurística inclusiva via `/proc/<pid>/comm` + cmdline). Reportado em AUDIT-FINDING-SINGLE-INSTANCE-PID-RECYCLE-01 — esse cluster usa a mesma defesa.
- **Risco residual B (Bug A):** se o daemon avulso está em estado uninterruptible (`D` state, espera I/O hidraw bloqueante), SIGTERM pode não entregar e SIGKILL é necessário. Plano contempla: 3s grace + SIGKILL.
- **Não-objetivo:** não consolidar `quit_app` para usar `acquire_or_takeover("daemon")` da GUI (tomaria o lock e mataria o daemon — comportamento mais agressivo, fora do escopo "Sair limpo"). O fix atual usa o pid file só pra LER, não pra adquirir.
- **Não-objetivo:** não converter `_shutdown_backend` para `async`. A thread daemon síncrona é o contrato vigente (linha 277 docstring).
- **Não-objetivo:** não unificar `_profile_menu_items` e o submenu inteiro num só model (`Gio.Menu`). Refactor maior, fora desse cluster.
- **Achado colateral antecipado:** o rename `_is_hefesto_dualsense4unix_process` → `is_hefesto_dualsense4unix_process` em `single_instance.py` é mexida em código compartilhado. Se o executor encontrar caller externo ao módulo durante o `rg` da Plano §1.a, atualizar todos os call sites no mesmo commit. Se caller for em arquivo NÃO relacionado ao tray (ex: módulo daemon), registrar como nota no commit message — não dispatchar sprint nova (mexida é trivial).

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-Dualsense4Unix/VALIDATOR_BRIEF.md`
  - Armadilha A-10 (multi-instance + pid file canônico) — base do fix Bug A.
  - Lição L-21-3 (ler código-chave antes do spec) — aplicada via `rg` confirmando símbolos.
  - Lição L-21-4 (validar `.venv` em sessão nova) — proof-of-work começa com `dev-setup.sh`.
- Precedente histórico:
  - `BUG-MULTI-INSTANCE-01` (2026-04-22) — introduziu `single_instance` e `quit_app` chamando systemctl. Bug A é a continuação natural (cobrir caso não-systemd).
  - `BUG-TRAY-SINGLE-FLASH-01` — primeiro precedente de fix em `app/tray.py`.
  - `AUDIT-FINDING-SINGLE-INSTANCE-PID-RECYCLE-01` — origem da defesa via `/proc/<pid>/comm`.
- PR alvo: #103 (`rebrand/dualsense4unix`).
