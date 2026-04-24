# SESSION_RESTORE — estado canônico para recuperação pós-crash

> **Leitura obrigatória** ao iniciar nova sessão se encontrar `git status` não-trivial, memórias conflitantes, ou dúvida sobre onde paramos.
>
> Atualizar este arquivo ao final de cada sessão não-trivial. Uma linha no topo de "Última atualização" + seção "Onde paramos".

---

## Última atualização: 2026-04-24 (v2.4.1 PUBLICADA — auditoria V2.3 + fixes COSMIC/Flatpak)

## Onde paramos

1. **v2.4.1 publicada** em 2026-04-24 via workflow run `24874826763` (3m24s, todos os 6 jobs verdes). Tag = commit `d9c11de`. 5 assets `isDraft:false`: `.whl`, `.tar.gz`, `.AppImage`, `.deb`, `.flatpak`. URL: <https://github.com/AndreBFarias/releases/tag/v2.4.1>.
2. **v2.4.0 também publicada** (`6bb777c`, run `24874197415`, 3m26s) — release anterior que precisou de um commit de fix (`a6419ec`) para passar o CI antes da cadeia completa funcionar. Assets antigos ainda disponíveis.
3. **Estado git:** HEAD = `d9c11de` em `origin/main` (sincronizado). Tags `v2.4.0` e `v2.4.1` publicadas. Working tree limpo.
4. **26 commits desde v2.3.0** (`e5384ab`) distribuídos em 2 waves:
   - **Wave V2.3 follow-up (sprints 85-86):** `AUDIT-V23-FORENSIC-01` (86) gerou relatório em `docs/process/audits/2026-04-24-audit-v23-forensic.md` com 26 achados + 14 sprints-filhas. `BUG-TEST-POLL-LOOP-UINPUT-TIMING-01` (85) fix inline na v2.4.1 (flaky em CI loaded).
   - **Wave V2.4 (sprints 87-100):** 14 `AUDIT-FINDING-*` executadas em sequência em ~2h30 com executor-sprint. Destaques: security (path traversal, PID recycling), bugs funcionais (UDP PlayerLED/MicLED, apply_draft rumble, mic_led reset), refactors (ipc_server 843→316 LOC split em 4 módulos, evdev_reader -55 LOC, ipc_bridge cov 29%→92%), cobertura (63%→71% total).
   - **Wave V2.4 complementar (fixes colaterais):** `BUG-FLATPAK-DEPS-01` (deps Python completas + GNOME Platform 47), `BUG-COSMIC-PORTAL-UNSUPPORTED-01` (graceful degradation), `BUG-SINGLE-INSTANCE-EBADF-01` (double close fd + mock testes fork), `BUG-COSMIC-WLR-BACKEND-01` (WlrctlBackend + install.sh auto).
5. **Indicadores:** pytest **1307 passed + 8 skipped** (era 1143+5 na v2.3.0, +164 testes), coverage **71%** (era 63%), ruff clean, mypy zero em **112 files** (era 108), smoke USB/BT verdes. 3 módulos novos (`ipc_handlers.py`, `ipc_draft_applier.py`, `ipc_rumble_policy.py`, `wlr_toplevel.py`).
6. **Automação COSMIC entregue:**
   - `src/hefesto/integrations/window_backends/wlr_toplevel.py`: `WlrctlBackend` via protocolo `wlr-foreign-toplevel-management-unstable-v1`. Cobre COSMIC, Sway, Hyprland, niri, river.
   - `src/hefesto/integrations/window_detect.py`: `_WaylandCascadeBackend` (portal → wlrctl → None).
   - `install.sh`: detecta `XDG_CURRENT_DESKTOP=*COSMIC*`, oferece `apt install wlrctl` + `GDK_BACKEND=x11` (auto sob `--yes` ou `--force-xwayland`).
   - `packaging/debian/control`: `Recommends: python3-uinput, wlrctl`.
7. **Pendências para próxima sessão (prioridades, sem spec ainda):**
   - **Validar v2.4.1 em Pop!_OS COSMIC real** (S) — reinstalar via `sudo apt install ./hefesto_2.4.1_amd64.deb` ou `./install.sh --yes --force-xwayland`, confirmar comportamento real do autoswitch, log do daemon. Resultado dessa validação define se segue para opção (2) ou (3) abaixo.
   - **FEAT-WLR-TOPLEVEL-PYWAYLAND-01** (L) — reimplementar WlrctlBackend usando `pywayland` + `wayland-protocols` em vez de subprocess. Elimina dep externa, funciona no flatpak sandbox.
   - **FEAT-FLATPAK-WLRCTL-BUNDLED-01** (S) — incluir `wlrctl` como módulo do manifesto flatpak (build meson+ninja). Alternativa mais simples se (2) for overkill.
   - **CHORE-TOUCHPAD-COSMIC-VALIDATION-01** (XS) — validar `TouchpadReader` em COSMIC nativo via `evtest`.
   - Outras (backlog V2.x+): onboarding wizard, rumble-per-profile override, i18n, presets import/export. Ver `docs/process/SPRINT_ORDER.md` seção "Wave V2.5" para a lista completa com justificativas.

---

## Roadmap v2.2.1 — ordem canônica de execução

Escolha do usuário em 2026-04-23: v2.2.0 encerrada, seguir para v2.2.1 com 4 prioridades selecionadas (bugs packaging, fix glyphs, infra venv, polish perfis).

| # | Sprint | Status | Esforço | Justificativa da posição |
|---|---|---|---|---|
| 0 | Alinhar SPRINT_ORDER.md | DONE 2026-04-23 | 5 min | Pré-requisito processual |
| 1 | **BUG-APPIMAGE-VERSION-NAME-01** | PENDING | 0.25 it | Isolado, zero risco; `build_appimage.sh` lê pyproject.toml |
| 2 | **BUG-DEB-PYDANTIC-V2-UBUNTU-22-01** | PENDING | 0.5 it | Packaging: control declara `python3-pydantic (>= 2.0)`, README docs workaround, smoke job `ubuntu-24.04` |
| 3 | **INFRA-VENV-PYGOBJECT-01** | PENDING | 0.5 it | DX: `dev-setup.sh` instala PyGObject; desbloqueia `test_status_actions_reconnect.py` e valid visual |
| 4 | **BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-02** | SPEC ESCRITA 2026-04-23 | XS | Fix canônico: whitelist ADR-011 + teste regressão com fixture de glyphs + logging `--verbose` |
| 5 | **UI-PROFILES-RADIO-GROUP-REDESIGN-01** | PENDING | 1 it | H1 do UI-PROFILES-LAYOUT-POLISH-01; exige valid visual (pré-req #3) |
| 6 | **UI-PROFILES-RIGHT-PANEL-REBALANCE-01** | PENDING | 1 it | H5; mesma condição #5 |
| 7 | **Release v2.2.1** | FUTURO | 15 min | Bump pyproject, CHANGELOG, tag, `gh workflow run release.yml -f tag=v2.2.1` |

**Total estimado:** ~3.25 iterações + release. Viável em 2-3 sessões.

**Sprints #1-4 são seguras para `/sprint-ciclo` automático** (nenhuma toca UI; zero validação visual GUI).

**Sprints #5-6 exigem validação visual** — só rodar após #3 (INFRA-VENV-PYGOBJECT) concluir e `./run.sh --gui` funcionar localmente.

---

## Firmware 70.2 MERGED — aba Firmware implementada (2026-04-23)

Sprint `FEAT-FIRMWARE-UPDATE-GUI-01` (ordem 70.2) materializou a opção A+UI da decisão arquitetural:

- **Backend** `src/hefesto/integrations/firmware_updater.py` (230 linhas): wrapper subprocess de `dualsensectl` (check/info/apply). 5 exceções tipadas. Parser tolerante. Timeouts controlados.
- **Mixin** `src/hefesto/app/actions/firmware_actions.py` (300 linhas): FirmwareActionsMixin com thread worker via `_get_executor()` + callbacks `GLib.idle_add`. Tradução de erros em PT-BR. Confirmação modal antes de aplicar.
- **UI** nova page em `main.glade`: banner de risco MAIÚSCULO, frame versão atual, frame aplicar (entry + browse + apply + progress), status label.
- **Wire-up** `src/hefesto/app/app.py`: herança + `install_firmware_tab()` no bootstrap.
- **Testes** `tests/unit/test_firmware_updater.py`: 17 testes (is_available, parse, get_info, apply validation, apply fluxo com progress_callback).
- Gates: mypy zero em 107 arquivos (+2), ruff limpo, pytest 1046/1046.

Requer `dualsensectl` instalado no sistema do usuário — se ausente, aba mostra mensagem guiada e desabilita botões.

## Firmware 69 — research CONCLUÍDA com achado crítico (2026-04-23)

### Achado game-changer durante pesquisa desta sessão

**`nowrep/dualsensectl` merged firmware update em 2026-02-19** (PR #53 de `deadYokai`). O comando `dualsensectl update firmware.bin` funciona hoje em Linux puro, sem Wine. Protocolo completo (feature reports `0x20` + `0xF4` + `0xF5`, blob `950272 bytes`, CDN Sony `fwupdater.dl.playstation.net`) documentado em `docs/research/firmware-dualsense-2026-04-survey.md` §0.

### Impacto nos specs 69/70

- **PHASE2 (69):** de **BLOCKED-ON-HARDWARE** → **RESEARCH-DONE-VIA-UPSTREAM**. Reescopar para 0.5 iteração documental (consolidar survey + código upstream em doc final); ou marcar diretamente como MERGED.
- **PHASE3 (70):** de **BLOCKED-ON-PHASE-2** → **AGUARDA DECISÃO ARQUITETURAL**. 4 opções listadas no survey §0.5:
  - **A (recomendação provisória):** wrapper subprocess Hefesto → dualsensectl. 1-2 iterações.
  - **B:** porte Python nativo (`src/hefesto/firmware/`). 3-5 iterações.
  - **C:** fwupd/LVFS. Dependente de Sony publicar no LVFS — sem prazo.
  - **D:** não implementar; README aponta dualsensectl.

### Decisão pendente do dono

Antes de reescrever PHASE3, sugerido sprint nova `FEAT-FIRMWARE-UPDATE-PHASE3-DECISION-01` para formalizar escolha entre A/B/C/D.

### Documentação completa da pesquisa

- `docs/research/firmware-update-protocol.md` — PHASE1 original (304 linhas, 2026-04-23).
- `docs/research/firmware-dualsense-2026-04-survey.md` — survey 2026-04-23 com achado upstream (492 linhas).

---

## Itens fora do ciclo v2.2.1 (adiados ou aguardando humano)

### Aguardam ação humana
- **CHORE-CI-REPUBLISH-TAGS-01** (PROTOCOL_READY): `gh workflow run release.yml -f tag=v2.0.0` + `v2.1.0` para re-publicar artifacts das tags históricas. Fazer quando v2.2.1 estiver estável.
- **FEAT-GITHUB-PROJECT-VISIBILITY-01** (PROTOCOL_READY): `gh repo edit --description ... --add-topic ...` + upload social preview via web UI. Docs em `docs/history/gh-repo-config.md`.

### Adiados para v2.3
- **FEAT-KEYBOARD-PERSISTENCE-01** (59.2): campo `ProfileConfig.key_bindings` + mapper A-06.
- **FEAT-KEYBOARD-UI-01** (59.3): aba "Mouse e Teclado" com TreeView CRUD + L3/R3 teclado virtual.

### Blocked
- **FEAT-FIRMWARE-UPDATE-PHASE2-01** (69): hardware.
- **FEAT-FIRMWARE-UPDATE-PHASE3-01** (70): depende de 69.

---

## Armadilhas ativas nesta época

- **A-12 PARCIALMENTE RESOLVIDA (PyGObject ausente no `.venv`):** `dev-setup.sh` valida e imprime instrução acionável; instalação ainda é manual via `--with-tray`. OK conhecido.
- **A-06 ampliada na V2.4 (mic_led):** agora cobre também "campo ausente em *Config mas aplicado pelo apply com default regride estado runtime". Registrado no BRIEF.
- **Pop!_OS COSMIC alpha sem portal `GetActiveWindow`:** fix em camadas entregue na v2.4.1 — WaylandPortalBackend degrada graceful após 3 falhas; WlrctlBackend cobre via wlr-foreign-toplevel; install.sh automatiza wlrctl+XWayland. **Validação em ambiente COSMIC real ainda pendente** (item #1 da próxima sessão).
- **`wlrctl` não está em todos os repos apt:** Ubuntu 24.04+ sim (universe); Pop!_OS 22.04 provavelmente não. Fallback XWayland cobre o caso.
- **Flatpak sandbox não enxerga `wlrctl` do host:** `WlrctlBackend` retorna None dentro do sandbox, cai no fallback XWayland se `GDK_BACKEND=x11` estiver no atalho. Fix definitivo = sprint FEAT-WLR-TOPLEVEL-PYWAYLAND-01 ou FEAT-FLATPAK-WLRCTL-BUNDLED-01.

---

## Checklist para a próxima sessão

Se você é a assistente entrando agora, faça nesta ordem:

1. `git status` — confirmar working tree limpo; HEAD deve ser `d9c11de` ou mais novo.
2. `git log --oneline v2.4.1..HEAD` — deve ser vazio (nenhum commit pós-release) OU ser só novos que a sessão anterior fez.
3. Ler este arquivo (você está lendo).
4. Ler `docs/process/SPRINT_ORDER.md` seção **"Wave V2.5 — sugestões para próxima sessão"** (linha ~430) para ver as 8 sugestões priorizadas.
5. Ler `VALIDATOR_BRIEF.md` seção [PROCESS] Lições L-21-1 a L-21-7 + sub-checklist, e [CORE] Armadilhas A-01..A-12 (A-06 foi ampliada na V2.4 para incluir "campo ausente no schema mas aplicado pelo apply").
6. `bash scripts/dev-setup.sh` se `.venv/bin/pytest` não funcionar.
7. **Perguntar ao usuário qual sprint V2.5 ele quer**. Default recomendado: começar pela validação manual do release v2.4.1 em COSMIC (item #1) se ele tiver ambiente COSMIC, ou por `FEAT-FLATPAK-WLRCTL-BUNDLED-01` / `FEAT-WLR-TOPLEVEL-PYWAYLAND-01` se ele preferir fechar essa lacuna primeiro.
8. Usar `/planejar-sprint <tema>` para gerar spec formal antes de executar — nenhuma das 8 sugestões V2.5 tem spec escrito ainda.

---

## Como atualizar este arquivo

Ao final de uma sessão não-trivial:

1. Alterar **"Última atualização"** para hoje.
2. Editar **"Onde paramos"** em até 5 linhas (diff real de estado, não narrativa).
3. Mover sprints do roadmap entre PENDING/DONE/IN_PROGRESS conforme progresso.
4. Adicionar armadilha nova em "Armadilhas ativas" se descobrir.
5. Commit com mensagem `docs: atualizar SESSION_RESTORE após <sessão>`.

Quando v2.2.1 for lançada, este arquivo pivota para v2.3: mudar "Próximo alvo" e zerar roadmap.
