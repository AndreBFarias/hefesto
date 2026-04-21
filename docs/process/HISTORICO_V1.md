# HISTORICO_V1.md — Jornada da V1.0.0

> Documento de processo: o que foi feito, por que, como. Referência para contribuidores entenderem o arco da release.
> **Período:** 2026-04-20 (v0.1.0 publicada) → 2026-04-21 (v1.0.0 publicada).
> **Método:** sprints orquestradas em worktrees isoladas, executores Opus/Sonnet em paralelo, cherry-pick ordenado no `main`.

---

## 1. Estado inicial (v0.1.0)

Release 0.1.0 publicada 2026-04-20 entregou os Waves W0-W8 do `HEFESTO_PROJECT.md`:

- Core HID híbrido (pydualsense output + evdev input).
- 19 trigger factories.
- 8 métodos JSON-RPC (IPC Unix socket).
- UDP compat DSX porta 6969.
- Perfis pydantic + autoswitch X11.
- CLI typer, TUI Textual, GUI GTK3 (7 fases).
- Tray Ayatana + close-to-tray.
- Systemd user service + install.sh.
- 289 testes, 9 ADRs, 5 discoveries documentadas.

Último commit da 0.1.0: `fe4cd89` (merge PR #67 HEFESTO-GUI fase 8).

---

## 2. Descobertas que dispararam a onda V1.0.0

Sessão de revisão em 2026-04-21 identificou:

1. **Regressão no working-tree** (não-committada): strip de glyphs Unicode de estado (BLACK CIRCLE, WHITE CIRCLE, BLACK/WHITE VERTICAL RECTANGLE) interpretou erroneamente "zero emojis" como "zero não-ASCII". Testes do `BatteryMeter` foram rebaixados para `assert == ""`, escondendo a regressão.
2. **Socket IPC com `unlink()` cego**: dois daemons (`hefesto.service` systemd + `./run.sh --smoke`) compartilhavam o mesmo path e se sabotavam.
3. **AssertionError no `udp_server.connection_made`** a cada startup: `isinstance` contra `asyncio.DatagramTransport` falha em Python 3.10 com `_SelectorDatagramTransport`.
4. **GUI congela** com daemon lento/offline: `asyncio.run()` síncrono a 20 Hz na thread GTK.
5. **Ícone antigo** (chama laranja) ainda em uso; novo ícone (martelo + circuito) disponível mas não carregado.
6. **Dualidade confusa** `hefesto.service` / `hefesto-headless.service` — dropdown da aba Daemon mostrava unit não instalada.
7. **Strings inconsistentes**: minúsculas no header, acentuação ausente em algumas labels.
8. **USB autosuspend do kernel** derrubava o DualSense durante polling (descoberto em projeto irmão `fusectl`).

---

## 3. Sprints executadas na onda V1.0.0

12 sprints em duas subondas. Cada sprint tem spec em `docs/process/sprints/<ID>.md`.

### Subonda A — fundação correta

| Sprint | Commit | Efeito |
|---|---|---|
| UX-HEADER-01 | `e67cf31` | Glyphs Unicode preservados; docs trocam HEAVY CHECK MARK/CROSS MARK por `OK:`/`ERRADO:` |
| BUG-UDP-01 | `54731b6` | Assert ruidoso removido; journal limpo |
| BUG-IPC-01 | `656148b` | Probe de socket vivo + isolamento smoke via `HEFESTO_IPC_SOCKET_NAME` |
| UX-RECONNECT-01 | `8533f2e` | Máquina 3 estados (`Online`/`Reconectando`/`Offline`) + botão Reiniciar Daemon |

### Integração pós-subonda A

Commit `e7bd6da`: desabilitar IPC/UDP/autoswitch nos 6 `DaemonConfig` dos testes de lifecycle (que quebraram ao aplicar BUG-IPC-01 contra daemon de produção ativo). Whitelist `VALIDATOR_BRIEF.md` no `check_anonymity.sh`.

### Subonda B — USB power + empacotamento

| Sprint | Commit | Efeito |
|---|---|---|
| USB-POWER-01 | `297587f` | Regra udev `72-ps5-controller-autosuspend.rules` (trazido do fusectl). `power/control=on`, `autosuspend_delay_ms=-1` |
| ADR-010 a 013 + install.sh | `378e158` | 4 ADRs novos; install.sh orquestra deps+venv+udev+desktop+systemd numa passada |
| Ícone novo | `4c0581e` | `assets/appimage/Hefesto.png` substituído pelo design martelo+circuito; cache hicolor populado em 9 resoluções |

### Subonda C — polish + banner + refactor

| Sprint | Commit | Efeito |
|---|---|---|
| UX-BANNER-01 | `0c548d1` | Banner com logo 64×64, wordmark "Hefesto" bold xx-large, subtitle pequeno |
| SIMPLIFY-UNIT-01 | `33fcf8f` | Remoção de `hefesto-headless.service`; dropdown vira label fixo |
| POLISH-CAPS-01 | `f35d0f2` | Title Case consistente em toda GUI; botões traduzidos para PT-BR; window title `Hefesto - DSX para Unix` |
| BUG-FREEZE-01 | `2afa8c3` | IPC via ThreadPoolExecutor + callbacks GLib.idle_add; timeout 250ms no connect; 20 Hz → 10 Hz |
| FEAT-MOUSE-01 | `d462696` | Aba Mouse com toggle, sliders, mapeamento; Cross/L2=BTN_LEFT, Triangle/R2=BTN_RIGHT, R3=BTN_MIDDLE, D-pad=setas, LS=movimento, RS=scroll |
| Integração pós-merge | `2ebdbc5` | `_tick_reconnect_state` async; Title Case em todos renderers; testes atualizados |
| Release v1.0.0 | `5e01796` | Bump `pyproject.toml` + `__init__.py` 0.1.0 → 1.0.0; CHANGELOG V1; tag `v1.0.0` |

---

## 4. Método empírico: o que funcionou

### Orquestração em worktrees paralelas

Cada sprint recebeu:
- Um spec em `docs/process/sprints/<ID>.md` (escrito antes do executor).
- Um executor `executor-sprint` em `isolation="worktree"`, contexto isolado.
- Proof-of-work obrigatório: pytest + lint + anonimato + visual (quando UI).

Pico de paralelismo: 5 executores simultâneos (UX-BANNER + SIMPLIFY + FEAT-MOUSE + POLISH + BUG-FREEZE). Merge ordenado no `main` via `git cherry-pick` resolvendo conflitos manualmente.

### Aprendizados

1. **Worktrees partem do HEAD no momento do dispatch**, não do commit que o orquestrador acabou de criar. Isso causa commit_base divergente (`fe4cd89` em vez de meu `835964f`). Cherry-pick resolve porque só aplica o delta.

2. **Conflitos em `main.glade` são frequentes** quando várias sprints mexem na GUI. Estratégia: dividir regiões no spec (banner no topo, dropdown na aba Daemon, aba Mouse no final do Notebook) para minimizar overlap.

3. **`FEAT-MOUSE-01` travou no primeiro dispatch** tentando validar com daemon ativo (watchdog stall 600s). Retry com escopo enxuto de proof-of-work (unit tests + captura estática, 45s limite) completou em ~13min.

4. **Sprints-novas nascem durante execução**: `BUG-ANON-01`, `CHORE-ACENTO-01`, `CHORE-FAKEPATH-01` foram criadas pelos próprios executores quando encontraram achados colaterais (meta-regra 9.7). Zero débito inline.

5. **Decisão de adiar vs retry**: FEAT-MOUSE-01 foi refeita com sucesso; sprints onde a causa-raiz é ambiental (ex.: socket de produção bloqueando teste) merecem adiamento em vez de retry imediato.

### Aprendizados de conteúdo

6. **Glyphs de estado não são emojis**: formalizado em ADR-011. BLACK CIRCLE (U+25CF), WHITE CIRCLE (U+25CB), BLOCK ELEMENTS (U+2580-259F), BOX DRAWING (U+2500-257F) são UI textual funcional. Emoji_Presentation (U+2700+ coloridos, U+1F000+) é o que a regra proíbe.

7. **`fusectl` foi referência ouro**: projeto irmão do autor já havia enfrentado a mesma gotcha do USB autosuspend no Pop!_OS. Importei a udev rule quase literal (correção semântica: `SUBSYSTEM=="usb"` em vez de `hidraw`). Eu fui injusto inicialmente com o fusectl — retratado no ADR-013.

8. **Soberania de subsistema (meta-regra 9.3)**: `IpcServer.stop()` registra `st_ino` no `start()`; só deleta o socket se o inode bater. Se outro daemon reciclou o path, apenas loga `ipc_socket_inode_divergente_skip_unlink`. Correção que vai além do spec original.

---

## 5. Métricas finais V1.0.0

| Métrica | Valor |
|---|---|
| Commits sobre a 0.1.0 | 8 |
| Sprints fechadas nesta onda | 12 |
| Sprints-novas criadas (backlog) | 2 (CHORE-ACENTO-01, CHORE-FAKEPATH-01, BUG-ANON-01) |
| ADRs novos | 4 (010 a 013) |
| Testes unitários | 289 → **335** (+46) |
| Armadilhas catalogadas no BRIEF | A-01 a A-06 |
| Discoveries novas em `docs/process/discoveries/` | 0 (incorporadas em ADRs) |
| Tamanho do CHANGELOG V1 | 30 linhas de highlights + 40 de detalhes |

---

## 6. Publicação

- **Tag:** `v1.0.0` push em 2026-04-21.
- **Remote:** `git@github.com-personal:AndreBFarias/hefesto.git`.
- **Workflows:**
  - `CI` (lint + mypy + pytest matrix 3.10/3.11/3.12) em execução.
  - `Release` (build wheel+sdist → AppImage → GitHub release com 3 artifacts) em execução.
- **PyPI:** opt-in via `vars.PYPI_PUBLISH=true`; não acionado nesta release.

---

## 7. O que vem em seguida

`docs/process/SPRINT_ORDER.md` lista 17 sprints categorizadas em 3 waves:
- **V1.1** — 13 sprints de bugs + features pequenas + dívida técnica.
- **V1.2** — 4 sprints de plataforma (COSMIC/Wayland, Flatpak, BT hotplug, docs).
- **V2.0** — 3 sprints arquiteturais (refactor lifecycle, métricas, plugin system).

Ordem, paralelismo recomendado e modelo sugerido (Opus/Sonnet) definidos.

---

*"A forja não revela o ferreiro. Só a espada."* — linha final do `HEFESTO_PROJECT.md`, ADR-000 do projeto em essência.
