# SESSION_RESTORE — estado canônico para recuperação pós-crash

> **Leitura obrigatória** ao iniciar nova sessão se encontrar `git status` não-trivial, memórias conflitantes, ou dúvida sobre onde paramos.
>
> Atualizar este arquivo ao final de cada sessão não-trivial. Uma linha no topo de "Última atualização" + seção "Onde paramos".

---

## Última atualização: 2026-04-24 (v2.3.0 PUBLICADA — keyboard feature completa, 2º release 100% automático)

## Onde paramos

1. **v2.3.0 publicada no GitHub** em 2026-04-24 via workflow run `24869314981` (automático). Tag = commit `e5384ab`. 5 assets com `isDraft: false`: `.whl`, `.tar.gz`, `.AppImage`, `.deb`, `.flatpak`. **Segundo release 100% automático consecutivo** — pipeline `release.yml` passou em todos os jobs de primeira (build/deb/appimage/flatpak/deb-install-smoke Noble/github-release).
2. **Estado git:** HEAD = `e5384ab` em `origin/main` (sincronizado) + tag `v2.3.0` pushada. Working tree limpo.
3. **5 commits desde v2.2.2** (`b12e28e`):
   - `7e49648` sprint **80 BUG-CI-ACENTUACAO-REGRESSION-01** — 6 violações reais (spec dizia 10, a v2.2.2 reescreveu release.yml baixando a contagem)
   - `6e90f05` sprint **59.2 FEAT-KEYBOARD-PERSISTENCE-01** — `Profile.key_bindings` + mapper A-06 + 9 JSONs + 10 testes
   - `517a59e` sprint **59.3 Fase B+D** — tokens virtuais `__OPEN_OSK__`/`__CLOSE_OSK__` + `_OSKController` (onboard/wvkbd) + `TouchpadReader` mesclado em dispatch → KEY_BACKSPACE/ENTER/DELETE + 17 testes + conftest autouse HEFESTO_FAKE=1
   - `ba104f9` sprint **59.3 Fase E** — `InputActionsMixin` (subclasse de MouseActionsMixin) + aba "Mouse e Teclado" + TreeView CRUD + DraftConfig.key_bindings round-trip + 10 testes + validação visual
   - `e5384ab` release v2.3.0 bump
4. **Marco keyboard feature completo:** tripé planejado desde v2.2.0 entregue (persistência + UI + integrações OSK/touchpad). Aba "Mouse e Teclado" navegável em `/tmp/hefesto_gui_kbd_*.png`; screenshot canônico em `docs/process/screenshots/FEAT-KEYBOARD-UI-01-depois.png` (sha256 `eb0feb060284c510cf1fb1b33b0dafd9286633896eccb9006439383a13b7a9d9`).
5. **Gates finais:** pytest 1138 passed + 5 skipped, ruff clean, mypy zero em 108 files, validar-acentuacao exit 0, smoke USB/BT verdes.
6. **Pendências da próxima sessão (escolhas do usuário):**
   - **AUDIT-V23-FORENSIC-01** (L, ready) — auditoria externa arquivo-por-arquivo sem viés de quem implementou, buscando bugs/órfãos/lógica frágil/otimizações. Deve **gerar sprints novas** (não fix direto). Próxima sessão prioritária por pedido do usuário em 2026-04-24.
   - **BUG-TEST-POLL-LOOP-UINPUT-TIMING-01** (XS, ready) — 4 testes flaky em dev local com /dev/uinput (CI passa). Fix conhecido: `keyboard_emulation_enabled=False` nos 5 DaemonConfig de `test_poll_loop_evdev_cache.py`.
   - **CHORE-CI-REPUBLISH-TAGS-01** (PROTOCOL_READY) — aguarda ação humana para re-publicar v2.0.0/v2.1.0.
   - **FEAT-GITHUB-PROJECT-VISIBILITY-01** (PROTOCOL_READY) — governança GitHub aguarda humano.

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

- **A-12 (PyGObject ausente no `.venv`):** `test_status_actions_reconnect.py` e `./run.sh --gui` falham sem intervenção. Workaround: `bash scripts/dev-setup.sh` recria venv com PyGObject. Fix canônico em INFRA-VENV-PYGOBJECT-01 (roadmap #3).
- **Glyph strip bug (GLYPHS-01):** reproduzido 2x (V2.1 e V2.2 pós-release). Causa raiz não isolada; disparo em contexto de execução paralela/orquestrada. Fix canônico em GLYPHS-02 (roadmap #4). Blindagem recomendada: **nunca rodar `scripts/validar-acentuacao.py --fix` sem review manual do diff** até GLYPHS-02 MERGED.

---

## Checklist para a próxima sessão

Se você é a assistente entrando agora, faça nesta ordem:

1. `git status` — confirmar working tree limpo.
2. `git log --oneline origin/main..HEAD` — confirmar zero commits locais não-pushed.
3. Ler este arquivo (você está lendo).
4. Ler o **topo** de `docs/process/SPRINT_ORDER.md` para confirmar que a ordem canônica ainda bate com esta.
5. Ler `VALIDATOR_BRIEF.md` seção [PROCESS] Lições L-21-* e [CORE] Armadilhas A-01..A-12.
6. `ls -lat ~/.claude/projects/-home-andrefarias-Desenvolvimento-Hefesto-DualSense-Unix/*.jsonl | head -3` — identificar session anterior se precisar ler últimos eventos.
7. Rodar `bash scripts/dev-setup.sh` se `.venv/bin/pytest` não funciona.
8. Perguntar ao usuário antes de começar qualquer sprint do roadmap (confirma se a ordem ainda vale).

---

## Como atualizar este arquivo

Ao final de uma sessão não-trivial:

1. Alterar **"Última atualização"** para hoje.
2. Editar **"Onde paramos"** em até 5 linhas (diff real de estado, não narrativa).
3. Mover sprints do roadmap entre PENDING/DONE/IN_PROGRESS conforme progresso.
4. Adicionar armadilha nova em "Armadilhas ativas" se descobrir.
5. Commit com mensagem `docs: atualizar SESSION_RESTORE após <sessão>`.

Quando v2.2.1 for lançada, este arquivo pivota para v2.3: mudar "Próximo alvo" e zerar roadmap.
