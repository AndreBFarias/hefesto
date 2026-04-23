# SESSION_RESTORE — estado canônico para recuperação pós-crash

> **Leitura obrigatória** ao iniciar nova sessão se encontrar `git status` não-trivial, memórias conflitantes, ou dúvida sobre onde paramos.
>
> Atualizar este arquivo ao final de cada sessão não-trivial. Uma linha no topo de "Última atualização" + seção "Onde paramos".

---

## Última atualização: 2026-04-23 (pós-restauração v2.2.0 + decisão v2.2.1)

## Onde paramos

1. **v2.2.0 publicada** no GitHub com 5 assets (whl, tar.gz, AppImage, deb, flatpak). Tag `f6ca6a8` no remote.
2. **Sessão anterior (`92996300`) crashou** após commit `e6c0e29` (2 sprints colaterais documentando bugs do release). Regressão de glyph strip em 25 arquivos corrigida nesta sessão (`d244106`).
3. **Estado git:** HEAD = `d244106` em `origin/main` (sincronizado). Working tree limpo pós-restore.
4. **Próximo alvo:** **release v2.2.1 (patch)** com 6 sprints escolhidas pelo usuário (ver § Roadmap).
5. **Keyboard (59.2/59.3)** adiado para v2.3.0. **Firmware 69/70** research iniciado nesta sessão (survey web); captura PHASE2 real aguarda hardware.

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

## Firmware 69/70 — research iniciado 2026-04-23

- **Research bibliográfico prévio:** `docs/research/firmware-update-protocol.md` (304 linhas, fase PHASE1).
- **Survey atualizado (em progresso ou concluído):** `docs/research/firmware-dualsense-2026-04-survey.md` — disparado nesta sessão via agente de web search.
- **Captura real (PHASE2):** BLOCKED-ON-HARDWARE. Aguarda PC + VM Win + DualSense + cabo USB-C + conta PSN.
- **Implementação CLI (PHASE3):** BLOCKED-ON-PHASE-2.

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
