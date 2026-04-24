# SPRINT_ORDER.md — Roadmap de execução do Hefesto

> Ordem recomendada de execução das sprints pendentes, agrupadas por wave/fase.
> Cada sprint tem spec em `docs/process/sprints/<ID>.md` e issue correspondente no GitHub.

**Status de main:** `v2.0.0` publicada em 2026-04-23. 42 sprints entregues em 3 waves (v1.0 → v1.1 → v1.2 → v2.0) em ~48h corridas. Próximos objetivos: backlog V2.x (PPA Launchpad, OpenTelemetry, i18n, onboarding wizard, sandbox forte de plugins).

Todas as sprints marcadas MERGED abaixo foram entregues — spec original preservada por auditoria.

---

## Legenda

- **[BUG]** correção de UX quebrado (reportado pelo usuário).
- **[FEAT]** feature nova.
- **[UI]** polish visual ou tema.
- **[CHORE]** dívida técnica ou docs.
- **[REFACTOR]** limpeza arquitetural.
- **[RESEARCH]** pesquisa experimental.
- **[RELEASE]** marco de publicação.
- **=>** pode rodar em paralelo com a sprint acima.

### Status de sprint

- **PENDING** — spec escrito, ainda não executado.
- **IN_PROGRESS** — executor em voo.
- **PROTOCOL_READY** — entregável é apenas documento/protocolo/checklist; código não foi executado. Requer ≥1 execução humana registrada para virar MERGED. Operacionaliza lição L-21-6.
- **MERGED** — código (ou, no caso de sprints só-doc, protocolo com ≥1 execução humana) entregue e validado. Release notes contam MERGED vs. PROTOCOL_READY separadamente.

---

## Wave V1.1 — Estabilidade + UX polido

Objetivo: fechar buracos reportados pelo usuário, polir a GUI, deixar o Hefesto apresentável pra terceiros.

### Fase 1 — Bugs críticos (concluída)

| Ordem | Sprint | Status |
|---|---|---|
| 1 | [BUG] **BUG-DAEMON-AUTOSTART-01** (#68) | MERGED 2026-04-22 |
| 2 | [BUG] **BUG-MOUSE-TRIGGERS-01** (#69) | MERGED 2026-04-22 |

### Fase 2 — Features pequenas (concluída)

| Ordem | Sprint | Status |
|---|---|---|
| 3 | [FEAT] **FEAT-LED-BRIGHTNESS-01** (#70) | MERGED 2026-04-22 |
| 3=> | [FEAT] **FEAT-HOTKEY-STEAM-01** (#71) | MERGED 2026-04-22 |
| 3=> | [FEAT] **FEAT-MOUSE-02** (#87) | MERGED 2026-04-22 |

### Fase 3 — Fundamentos do daemon (concluída)

| Ordem | Sprint | Status |
|---|---|---|
| 4 | [FEAT] **FEAT-HOTPLUG-GUI-01** (#75) | MERGED 2026-04-22 |
| 4=> | [FEAT] **FEAT-CLI-PARITY-01** (#79) | MERGED 2026-04-22 |
| 5 | [CHORE] **CHORE-FAKEPATH-01** (#76) | MERGED 2026-04-22 |
| 5=> | [CHORE] **CHORE-CI-SMOKE-01** (#78) | MERGED 2026-04-22 |
| 5=> | [CHORE] **CHORE-ACENTO-01** (#77) | MERGED 2026-04-22 |
| 6 | [FEAT] **FEAT-PERSIST-SESSION-01** | DIRECT TO MAIN 2026-04-22 |

### Fase 4 — Estabilidade de processo (concluída)

| Ordem | Sprint | Status |
|---|---|---|
| 7 | [BUG] **BUG-MULTI-INSTANCE-01** (single-instance takeover + opt-in autostart) | DIRECT TO MAIN 2026-04-22 |

### Fase 5 — Fixes P0 pós-usuario-real (MERGED 2026-04-22)

Ordem sequencial porque bugs podem interagir entre si.

| Ordem | Sprint | Porte | Modelo sugerido |
|---|---|---|---|
| 8 | [BUG] **BUG-TRAY-SINGLE-FLASH-01** — GUI abre e fecha ao plugar (virar "primeira vence") | S | sonnet |
| 9 | [BUG] **BUG-DAEMON-STATUS-MISMATCH-01** — painel Daemon confuso | S | sonnet |
| 10 | [BUG] **BUG-RUMBLE-APPLY-IGNORED-01** — "Aplicar rumble" não persiste | S | sonnet |
| 11 | [FEAT] **FEAT-PLAYER-LEDS-APPLY-01** — envio real dos Player LEDs | M | opus (HID direto) |
| 12 | [FEAT] **FEAT-LED-BRIGHTNESS-02** — propagação brightness no ProfileManager | XS | sonnet |
| 13 | [FEAT] **FEAT-LED-BRIGHTNESS-03** — persist handler GUI do brightness | XS | sonnet |
| 14 | [REFACTOR] **REFACTOR-HOTKEY-EVDEV-01** — dedup snapshot por tick (A-09) | XS | sonnet |
| 15 | [CHORE] **DOCS-VERSION-SYNC-01** — README reflete 1.0.0 + script CI | XS | sonnet |

### Fase 6 — Polish UX visível (MERGED 2026-04-22)

Bloco dependente de fases anteriores. Inicia quando Fase 5 está quase completa.

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 16 | [UI] **UI-THEME-BORDERS-PURPLE-01** — CSS Drácula global (pré-req dos outros UI) | M | sonnet |
| 17 | [FEAT] **FEAT-BUTTON-SVG-01** — 19 SVGs minimalistas + `ButtonGlyph` (pré-req Status redesign) | M | opus (design SVG) |
| 18 | [UI] **UI-STATUS-STICKS-REDESIGN-01** — bloco Status com glyphs + PT-BR | M | sonnet |
| 19 | [UI] **UI-PROFILES-EDITOR-SIMPLE-01** — editor modo simples/avançado | M | sonnet |
| 20 | [UI] **UI-DAEMON-LOG-WRAP-01** — log com card + wrap | XS | sonnet |
| 21 | [UI] **UI-EMULATION-ALIGN-01** — alinhamento da aba Emulação | XS | sonnet |
| 22 | [UI] **UI-MOUSE-CLEANUP-01** — cleanup aba Mouse | XS | sonnet |

### Fase 7 — Estado central + perfis (MERGED 2026-04-22)

Dependência cruzada. Executa em sequência.

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 23 | [FEAT] **FEAT-PROFILE-STATE-01** (#74) — DraftConfig central (pré-req do rodapé) | L | opus |
| 24 | [UI] **UI-GLOBAL-FOOTER-ACTIONS-01** — rodapé Aplicar/Salvar/Importar/Default | M | sonnet |
| 25 | [FEAT] **FEAT-PROFILES-PRESET-06** (#73) — 6 perfis + "Meu Perfil" | M | sonnet |

### Fase 8 — Rumble + gatilhos polidos (MERGED 2026-04-22)

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 26 | [FEAT] **FEAT-TRIGGER-PRESETS-POSITION-01** — presets Feedback/Vibração por posição | M | sonnet |
| 27 | [FEAT] **FEAT-RUMBLE-POLICY-01** — política global + modo Auto | M | opus |

### Fase 9 — Marco

| Ordem | Sprint | Porte |
|---|---|---|
| 28 | [RELEASE] **Release v1.1.0** — tag publicada 2026-04-22 (17 sprints) | MERGED |

---

## Wave V1.2 — Plataforma + docs (MERGED 2026-04-22)

Objetivo: chegar a plataformas novas (COSMIC, BT) e packaging (deb, Flatpak). Lançar pra usuário Linux "assistido" que instala sem tutorial. **Entregue — tag v1.2.0 publicada.**

### Fase 1 — Plataformas (até 3 em paralelo)

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 29 | [FEAT] **FEAT-HOTPLUG-BT-01** (#82) — hotplug via Bluetooth | S | sonnet |
| 29=> | [FEAT] **FEAT-DEB-PACKAGE-01** — pacote `.deb` | M | sonnet |
| 30 | [FEAT] **FEAT-FLATPAK-BUNDLE-01** (#81) — bundle Flatpak | L | opus |
| 31 | [FEAT] **FEAT-COSMIC-WAYLAND-01** (#80) — COSMIC/Wayland via portal | L | opus (2 iter) |

### Fase 2 — Quickstart

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 32 | [DOCS] **DOCS-QUICKSTART-01** (#83) — quickstart visual com GIFs | M | sonnet |

### Fase 3 — Refactor preparatório

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 33 | [REFACTOR] **REFACTOR-DAEMON-RELOAD-01** — hot-reload do HotkeyManager (A-08) | S | sonnet |

### Fase 4 — Marco

| Ordem | Sprint | Porte |
|---|---|---|
| 34 | [RELEASE] **Release v1.2.0** — tag publicada 2026-04-22 (6 sprints) | MERGED |

---

## Wave V2.0 — Infra avançada + MIC (MERGED 2026-04-23)

Objetivo: novos controles adaptativos (Mic, áudio), plataforma de plugins. **Entregue — tag v2.0.0 publicada.**

### Fase 1 — Infra MIC (sequencial)

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 35 | [INFRA] **INFRA-BUTTON-EVENTS-01** (#90) — `EventTopic.BUTTON_DOWN` no poll loop | S | sonnet |
| 36 | [INFRA] **INFRA-MIC-HID-01** (#91) — botão Mic em `ControllerState` | S | sonnet |
| 37 | [INFRA] **INFRA-SET-MIC-LED-01** (#92) — `IController.set_mic_led` | S | sonnet |
| 38 | [FEAT] **FEAT-HOTKEY-MIC-01** (#72) — botão Mic toggle microfone sistema | S | sonnet |
| 38=> | [FEAT] **FEAT-AUDIO-CONTROL-01** (#93) — AudioControl autônomo (wpctl/pactl + debounce) | M | sonnet |

### Fase 2 — Arquitetura

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 39 | [REFACTOR] **REFACTOR-LIFECYCLE-01** (#84) — quebrar `lifecycle.py` em subsistemas | L | opus |
| 40 | [FEAT] **FEAT-METRICS-01** (#85) — endpoint Prometheus opt-in | M | opus |

### Fase 3 — Plugin API

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 41 | [FEAT] **FEAT-PLUGIN-01** (#86) — plugins Python via `plugin_api/` | XL | opus (2 iter) |

### Fase 4 — Firmware updater (experimental, paralelo a tudo)

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| ~ | [RESEARCH] **FEAT-FIRMWARE-UPDATE-01** (research-heavy, 3 fases) | XL | — |

### Fase 5 — Marco

| Ordem | Sprint | Porte |
|---|---|---|
| 42 | [RELEASE] **Release v2.0.0** — tag publicada 2026-04-23 (9 sprints) | MERGED |

---

## Wave V2.1 — Polish pós-v2.0.0 (MERGED 2026-04-23)

Objetivo: fechar dívida técnica identificada após v2.0.0 — campo `display_name` separado do slug, schema `params` aninhado para multi-position, CI smoke de `.deb` e `.flatpak`, research de firmware updater, checklist de validação em hardware, hook strict de acentuação, auditoria manual completa do diff v1.0.0..HEAD. Tudo aditivo/polish, zero quebra de API — minor bump.

### Bloco A — gate + onboarding

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 43 | [CHORE] **CHORE-ACENTUACAO-STRICT-HOOK-01** — gate strict PT-BR (primeira do ciclo) | S | sonnet | MERGED |
| 44 | [DOCS] **QUICKSTART-PROFILES-SCREENSHOT-01** — captura aba Perfis no quickstart | XS | sonnet | MERGED |

### Bloco B — schema/perfis (sequencial)

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 45 | [FEAT] **PROFILE-SLUG-SEPARATION-01** — slugify filename separa do display `Profile.name` (substitui PROFILE-DISPLAY-NAME-01 SUPERSEDIDA) | S | sonnet | MERGED |
| 46 | [FEAT] **SCHEMA-MULTI-POSITION-PARAMS-01** — params aninhado + migra aventura/corrida | L | opus | MERGED |

### Bloco C — CI/release (paralelizável)

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 47 | [CHORE] **SMOKE-DEB-INSTALL-CI-01** — CI instala `.deb` real em ubuntu-22.04 | S | sonnet | MERGED |
| 47=> | [CHORE] **SMOKE-FLATPAK-BUILD-CI-01** — CI faz install --user do bundle Flatpak | S | sonnet | MERGED |

### Bloco D — documentação técnica + auditoria (opus direto)

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 48 | [RESEARCH] **FEAT-FIRMWARE-UPDATE-PHASE1-01** — research DFU do DualSense (fase 1) | L | opus | PROTOCOL_READY |
| 49 | [DOCS] **HARDWARE-VALIDATION-PROTOCOL-01** — checklist 21 itens reprodutíveis | S | opus | PROTOCOL_READY |
| 50 | [CHORE] **AUDIT-V2-COMPLETE-01** — auditoria manual v1.0.0..HEAD (sem subagente) | L | opus | MERGED |

### Fase — Marco

| Ordem | Sprint | Porte | Status |
|---|---|---|---|
| 51 | [RELEASE] **Release v2.1.0** — tag publicada 2026-04-23 (9 sprints) | — | MERGED |

---

## Wave V2.2 — Polish pós-v2.1.0 (PENDING 2026-04-23)

Objetivo: resolver as 9 demandas do usuário reportadas após instalar v2.1.0 (UI polish, bugs da aba Daemon, rename Mouse→Mouse e Teclado com personalização completa, cores dos botões do footer, Player LEDs inoperantes, carregamento do último perfil na GUI, README renovado com screenshots, polish da aba Perfis) + 2 achados P2 da auditoria V2 (refactor do connection.py, hardening do `rumble.policy_custom`).

### Bloco A — polish visual + bugs de UX (rápido)

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 52 | [POLISH] **UI-POLISH-EMULACAO-DAEMON-STATUS-01** — alinhamentos, UINPUT maiúsculo, título Gatilhos | S | sonnet | MERGED |
| 53 | [BUG] **BUG-GUI-DAEMON-STATUS-INITIAL-01** — GUI abre com "Offline" apesar de daemon ativo | S | sonnet | MERGED |
| 54 | [FEAT] **FEAT-GUI-LOAD-LAST-PROFILE-01** — GUI abre com último perfil selecionado | S | sonnet | MERGED |
| 55 | [POLISH] **UI-FOOTER-BUTTON-COLORS-01** — cores Dracula nos 4 botões do footer | S | sonnet | MERGED |
| 56 | [BUG] **BUG-PLAYER-LEDS-APPLY-01** — Player LEDs sem botão Aplicar e inoperantes | M | sonnet | MERGED |

### Bloco B — investigação + rewrite (médio)

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 57 | [POLISH] **UI-PROFILES-LAYOUT-POLISH-01** — discovery + fixes H4 (headers) + H6 (slider marks); H1/H5 viram sprints-filhas | M | sonnet+opus | MERGED |
| 57.1 | [UI] **UI-PROFILES-RADIO-GROUP-REDESIGN-01** — radio "Aplica a:" redesign (H1, colateral) | S | opus | PENDING |
| 57.2 | [UI] **UI-PROFILES-RIGHT-PANEL-REBALANCE-01** — rebalancear coluna direita (H5, colateral) | S | sonnet | PENDING |
| 58 | [DOCS] **DOCS-README-RENOVATE-01** — README renovado com 7 screenshots, layout Conversor-Video-Para-ASCII | S | opus | MERGED |

### Bloco C — grande, estratégica (opus)

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 59 | [FEAT] ~~**FEAT-MOUSE-TECLADO-COMPLETO-01**~~ — SUPERSEDED: escopo dividido em 3 filhas (59.1/59.2/59.3) | L | — | SUPERSEDED |
| 59.1 | [FEAT] **FEAT-KEYBOARD-EMULATOR-01** — infraestrutura device virtual + wire-up A-07 + defaults conservadores (Options/Share/L1/R1) | M | opus | MERGED |
| 59.2 | [FEAT] **FEAT-KEYBOARD-PERSISTENCE-01** — campo ProfileConfig.key_bindings + mapper A-06 + JSONs defaults | M | opus | PENDING |
| 59.3 | [FEAT] **FEAT-KEYBOARD-UI-01** — aba "Mouse e Teclado" + TreeView CRUD + L3/R3 onboard/wvkbd + inversão R2/L2 | L | opus | PENDING |

### Bloco D — débito técnico da auditoria V2

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 60 | [REFACTOR] **REFACTOR-CONNECTION-FUNCTIONS-01** — move `connection.py` fora de `subsystems/` (P2-02) | XS | sonnet | MERGED |
| 61 | [HARDENING] ~~**HARDEN-IPC-RUMBLE-CUSTOM-01**~~ — SUPERSEDED por HARDEN-IPC-PAYLOAD-LIMIT-01 (L-21-3: vetor não existe) | XS | — | SUPERSEDED |
| 61.1 | [HARDENING] **HARDEN-IPC-PAYLOAD-LIMIT-01** — limite 32 KiB por request no `_dispatch` (P2-03 reescopado) | XS | opus | MERGED |

### Bloco E — CI/release (P0 — release travado há 5 tags)

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 62 | [BUG] **BUG-CI-RELEASE-MYPY-GATE-01** — release.yml aborta no mypy, nenhum release real desde v0.1.0 | S | opus | MERGED |
| 63 | [FEAT] **FEAT-CI-RELEASE-FLATPAK-ATTACH-01** — anexar bundle Flatpak ao release | XS | sonnet | MERGED |
| 64 | [CHORE] **CHORE-CI-REPUBLISH-TAGS-01** — re-publicar v2.0.0 e v2.1.0 com artifacts | XS | sonnet | PROTOCOL_READY |
| 65 | [CHORE] **CHORE-MYPY-CLEANUP-V22-01** — zerar mypy errors + gate rígido no CI | M | sonnet | MERGED |
| 62.1 | [BUG] **BUG-VALIDAR-ACENTUACAO-FALSE-POS-01** — remove par "facilmente" falso-positivo + reescrita de spec (colateral) | XS | opus | MERGED |
| 53.1 | [INFRA] **INFRA-VENV-PYGOBJECT-01** — dev-setup.sh valida gi; BRIEF ganha A-12 (colateral) | XS | opus | PENDING |
| 63.1 | [BUG] **BUG-FLATPAK-PIP-OFFLINE-01** — build-args --share=network para módulos python-uinput/pydualsense | XS | opus | MERGED |
| 63.2 | [BUG] **BUG-DEB-MISSING-DEPS-01** — .deb não declara rich/evdev/xlib/filelock (colateral dispatch v2.1.0) | XS | opus | MERGED |

### Bloco F — meta/processo (operacionaliza lições V2.1)

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 66 | [META] **META-LESSONS-V21-BRIEF-01** — registrar 6 lições V2.1 no BRIEF | XS | sonnet | MERGED |
| 67 | [CHORE] **CHORE-VENV-BOOTSTRAP-CHECK-01** — script `dev-setup.sh` + regra de sessão viva | XS | sonnet | MERGED |
| 68 | [DOCS] **DOCS-STATUS-PROTOCOL-READY-01** — status `PROTOCOL_READY` para sprints sem execução humana | XS | sonnet | MERGED |

### Bloco G — firmware (destravada por upstream em 2026-02-19)

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 69 | [RESEARCH] **FEAT-FIRMWARE-UPDATE-PHASE2-01** — captura real de protocolo DFU; **destravada pela descoberta em 2026-04-23 que nowrep/dualsensectl PR#53 já documentou e implementou o protocolo completo em main.c MIT** (reports 0x20/0xF4/0xF5, blob 950272 bytes, CDN fwupdater.dl.playstation.net); ver docs/research/firmware-dualsense-2026-04-survey.md | L→XS | opus | RESEARCH-DONE-VIA-UPSTREAM |
| 70 | [FEAT] **FEAT-FIRMWARE-UPDATE-PHASE3-01** — tooling Linux para re-aplicar firmware oficial; SUPERSEDED por 70.2 (decisão: opção A+UI, wrapper subprocess + aba GUI) | XL→— | — | SUPERSEDED |
| 70.1 | [DECISION] **FEAT-FIRMWARE-UPDATE-PHASE3-DECISION-01** — escolher entre A/B/C/D; DECIDIDO em 2026-04-23 opção A+UI | XS | humano+opus | DECIDIDO |
| 70.2 | [FEAT] **FEAT-FIRMWARE-UPDATE-GUI-01** — aba Firmware na GUI via wrapper dualsensectl; backend `src/hefesto/integrations/firmware_updater.py` + mixin `src/hefesto/app/actions/firmware_actions.py` + page glade + 17 tests unit | M | opus | MERGED |

### Bloco H — visibilidade / open source (pós-CI funcionar)

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 71 | [FEAT] **FEAT-GITHUB-PROJECT-VISIBILITY-01** — governança + social-preview PNG + badges; gh CLI em docs/history/ aguarda execução humana | S | opus | PROTOCOL_READY |

### Fase — Marco v2.2.0

| Ordem | Sprint | Porte | Status |
|---|---|---|---|
| 72 | [RELEASE] **Release v2.2.0** — publicada 2026-04-23 22:07 UTC, tag f6ca6a8 remote, 5 assets no GitHub | — | MERGED |

### Bloco I — patch release v2.2.1 (pós-v2.2.0)

Descobertos durante release v2.2.0 + decisão do usuário em 2026-04-23 de seguir com patch antes de keyboard (v2.3).

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 73 | [BUG] **BUG-APPIMAGE-VERSION-NAME-01** — AppImage gerado com nome 1.0.0 em vez da tag; causa raiz real: `__init__.py:3` hardcoded afetava 5 consumidores (CLI, TUI x2, AppImage, test_cli); fix opção B em `importlib.metadata.version` + fallback + `build_appimage.sh` alinhado ao padrão `build_deb.sh` | XS | opus | MERGED |
| 73.1 | [CHORE] **CHORE-VERSION-SYNC-GATE-01** — gate CI detecta drift fallback `__init__.py` vs `pyproject.toml` (colateral do 73, pós execução) | XS | sonnet | PENDING |
| 74 | [BUG] **BUG-DEB-PYDANTIC-V2-UBUNTU-22-01** — `control` declara `python3-pydantic (>= 2.0)` + smoke job migra para `ubuntu-24.04` + README seção Ubuntu 22.04 com 3 workarounds | S | opus | MERGED |
| 75 | [INFRA] **INFRA-VENV-PYGOBJECT-01** — `dev-setup.sh` valida `gi`+`Gtk` e imprime instrução acionável quando ausente; README marca `--with-tray` como pré-req de GUI; VALIDATOR_BRIEF.md A-12 PARCIALMENTE RESOLVIDA | XS | opus | MERGED |
| 76 | [BUG] **BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-02** — whitelist ADR-011 (`UNICODE_ALLOWED_RANGES`) em `scripts/validar-acentuacao.py` filtra substituições em `corrigir_arquivo`; warning stderr quando par malicioso é bloqueado; 23 testes regressão em `tests/unit/test_validar_acentuacao_glyphs.py` (parametrizado por codepoint, par malicioso simulado) | XS | opus | MERGED |
| 77 | [UI] **UI-PROFILES-RADIO-GROUP-REDESIGN-01** — 6 GtkRadioButton → GtkComboBoxText (`profile_aplica_a_combo`) com 6 ids em main.glade; `_selected_simple_choice`/`_select_radio` via `get/set_active_id`; handler `_on_aplica_a_changed` esconde `profile_game_entry_box` quando id != "game"; 5 testes unit; screenshot em `docs/process/screenshots/` | S | opus | MERGED |
| 77.1 | [BUG] **BUG-FIRMWARE-SIGNAL-HANDLERS-01** — colateral descoberto em validação visual da 77: handlers `on_firmware_*` faltavam em `_signal_handlers()` do `app.py`; botões da aba Firmware ficavam mortos; fix aplicado junto com 77 | XS | opus | MERGED |
| 78 | [UI] **UI-PROFILES-RIGHT-PANEL-REBALANCE-01** — preview JSON ao vivo (`GtkFrame` + `GtkScrolledWindow` + `profile_preview_label` em main.glade) ocupa o espaço vazio liberado pela 77; `_refresh_preview()` reutiliza `_build_profile_from_editor`; CSS `.hefesto-profile-preview` monospace Drácula; 3 testes unit; screenshot em `docs/process/screenshots/` | S | opus | MERGED |

### Fase — Marco v2.2.1

| Ordem | Sprint | Porte | Status |
|---|---|---|---|
| 79 | [RELEASE] **Release v2.2.1** — bump 2.2.0→2.2.1 em pyproject.toml + `__init__.py` fallback + README; CHANGELOG promovido de [Unreleased] para [2.2.1] 2026-04-23; tag v2.2.1 pushada; build workflow run 24864996747 OK em 4/5 jobs (smoke falhou); release publicado manualmente com 5 assets via `gh release create v2.2.1 <artifacts>` | — | MERGED |
| 79.1 | [BUG] **BUG-DEB-SMOKE-PYDANTIC-V2-NOBLE-01** — validação empírica 2026-04-24 (L-21-7) confirmou Jammy 1.8.2, Noble 1.10.14, Plucky 2.10.6; `control` sem `(>= 2.0)`; smoke em 22.04 + `pip install --user 'pydantic>=2.0'` antes do apt + `PYTHONPATH` user-site no validate; warning runtime via `warnings.warn(ImportWarning)` se pydantic<2; README documenta `pip install --user` como caminho oficial. Valor-chave: L-21-7 consolidada no BRIEF | S | opus | MERGED |

### Fase — Marco v2.2.2

| Ordem | Sprint | Porte | Status |
|---|---|---|---|
| 73.1 | [CI] **CHORE-VERSION-SYNC-GATE-01** — novo job `version-sync` em `.github/workflows/ci.yml` que falha se fallback `__version__` de `src/hefesto/__init__.py` divergir de `pyproject.toml [project].version`. Regex inline `tomllib` + `re.search` (YAGNI parser AST). Motivação: BUG-APPIMAGE-VERSION-NAME-01 revelou que fallback ficou hardcoded em 1.0.0 por 3 releases. Baseline 2.2.2==2.2.2 passa; drift simulado 9.9.9!=2.2.2 detectado. | XS | opus | MERGED |
| 80 | [BUG] **BUG-CI-ACENTUACAO-REGRESSION-01** — CI acentuacao vermelho em main desde pelo menos v2.2.1 por 10 violações pré-existentes: 6 em comentários de `release.yml` (l.116-136), 3 em string literals de `tests/unit/test_firmware_updater.py` (l.66,119), 2 em identifier Python `conteudo` de `tests/unit/test_validar_acentuacao_glyphs.py` (l.145-146). Descoberto durante A2b da v2.2.2. Fix em 2 camadas: adicionar acentuação em texto + renomear `conteudo`→`texto_final` (evitar falso positivo em identifiers). Não afeta release.yml (ortogonal). | XS | opus | ready |
| 81 | [RELEASE] **Release v2.2.2** — bump 2.2.1→2.2.2 + gate version-sync (73.1) + Noble migration + INFRA-EVDEV-TOUCHPAD-01 adiantado; publicada 2026-04-24 via run `24867530741` com 5 assets `isDraft:false` após 7 iterações de tag (L-21-7 disparou 6× em cascata: pydantic → structlog.typing → constraint errada → cascata tripla → typer PEP 604 → hefesto version subcomando). **Primeiro release 100% automático desde v0.1.0**. Commit final `9afac40`. | — | opus | MERGED |
| 82 | [BUG] **BUG-DEB-SMOKE-STRUCTLOG-TYPING-02** — SUPERSEDED_BY_V2_2_2. Spec original propunha compat layer `try/except types/typing` + constraint `python3-structlog (>= 21.5)`. Aplicação parcial (commits `ad80d6c` + `1c476f8`) foi insuficiente: Jammy apt tem typer 0.4, platformdirs 2.5, pydantic 1.10 — tudo velho demais. Resolução final foi arquitetural: migração do runner `deb-install-smoke` de `ubuntu-22.04` para `ubuntu-24.04` (Noble) em `b03ad48`, + `pip install --user 'pydantic>=2.0' 'typer>=0.12'` em `9afac40`. Constraint no control removida (compat layer em `logging_config.py` mantida como defesa para usuários que instalem .deb em Jammy sem pip). | XS | opus | SUPERSEDED |
| 83 | [INFRA] **INFRA-EVDEV-TOUCHPAD-01** — MERGED adiantado na v2.2.2 (commit `43f76d8`). Adiciona `find_dualsense_touchpad_evdev()` + classe `TouchpadReader` em `src/hefesto/core/evdev_reader.py`; expõe `touchpad_{left,middle,right}_press` via discriminação `ABS_X` (limites 640/1280 sobre 1920). 19 testes unit + smoke hardware-real com DualSense USB 054c:0ce6. Remove comentário "pendente" de L89. Destrava FEAT-KEYBOARD-UI-01 (59.3). | XS | opus | MERGED |

### Fase — Marco V2.3.0 (keyboard) — MERGED 2026-04-24

| Ordem | Sprint | Porte | Status |
|---|---|---|---|
| 80 | [BUG] **BUG-CI-ACENTUACAO-REGRESSION-01** — 6 violações reais corrigidas (spec dizia 10; a v2.2.2 reescreveu release.yml e baixou a contagem). Destravou `ci.yml` verde em `main`. | XS | opus | MERGED (`7e49648`) |
| 59.2 | [FEAT] **FEAT-KEYBOARD-PERSISTENCE-01** — `Profile.key_bindings` + validator regex + mapper A-06 (`_to_key_bindings` + `ProfileManager.apply_keyboard`) + 9 JSONs default + 10 testes incluindo teste dedicado do mapper. | M | opus | MERGED (`6e90f05`) |
| 59.3 | [FEAT] **FEAT-KEYBOARD-UI-01** — `InputActionsMixin` (subclasse de `MouseActionsMixin`) + aba "Mouse e Teclado" + TreeView CRUD + L3/R3 OSK via onboard/wvkbd (via tokens `__OPEN_OSK__`/`__CLOSE_OSK__`) + consumir `TouchpadReader.regions_pressed()` → KEY_BACKSPACE/ENTER/DELETE. Decisão documentada: NÃO inverter R2/L2. Validação visual em `docs/process/screenshots/FEAT-KEYBOARD-UI-01-depois.png`. 27 testes novos. Entregue em 2 commits (Fase B+D + Fase E). | L | opus | MERGED (`517a59e` + `ba104f9`) |
| 84 | [RELEASE] **Release v2.3.0** — bump 2.2.2→2.3.0; tag publicada 2026-04-24 via run `24869314981` com 5 assets `isDraft:false`. Segundo release 100% automático consecutivo. Commit final `e5384ab`. | — | — | MERGED |

### Wave V2.3 — follow-up de auditoria (PENDING 2026-04-24)

Objetivo: revisão externa sem viés do que a V2.3 acumulou em velocidade, mais 1 bug conhecido fora do caminho crítico.

| Ordem | Sprint | Porte | Modelo | Status |
|---|---|---|---|---|
| 85 | [BUG] **BUG-TEST-POLL-LOOP-UINPUT-TIMING-01** — 4 testes de `test_poll_loop_evdev_cache.py` falham em dev local com /dev/uinput (startup >60ms > budget). CI passa. Fix: `keyboard_emulation_enabled=False` nos DaemonConfig dos 5 testes do arquivo. | XS | opus | ready |
| 86 | [AUDIT] **AUDIT-V23-FORENSIC-01** — auditoria externa arquivo-por-arquivo do pós-v2.3.0 sem viés do autor da implementação. Relatório entregue em `docs/process/audits/2026-04-24-audit-v23-forensic.md` (26 achados em 6 categorias: 6 altos, 9 médios, 7 baixos, 4 cosméticos). 14 sprints-filhas geradas — ver Wave V2.4 abaixo. | L | opus | MERGED 2026-04-24 |

### Wave V2.4 — follow-up de auditoria V2.3 (PENDING 2026-04-24)

Objetivo: endereçar os 26 achados da AUDIT-V23-FORENSIC-01 em ordem de severidade. 14 sprints-filhas geradas; altos primeiro, médios depois, baixos em checklist agrupado.

| Ordem | Sprint | Porte | Severidade | Modelo | Status |
|---|---|---|---|---|---|
| 87 | [BUG] **AUDIT-FINDING-UDP-PLACEHOLDER-HANDLERS-01** — UDP PlayerLED/MicLED no-op + clamp RGB ausente. | S | alto | opus | ready |
| 88 | [BUG] **AUDIT-FINDING-IPC-DRAFT-RUMBLE-POLICY-01** — `profile.apply_draft` bypassa política de rumble. | XS | alto | opus | ready |
| 89 | [BUG] **AUDIT-FINDING-PROFILE-MIC-LED-RESET-01** — `apply_led_settings` reseta mic_led em cada profile switch. A-06 variante. | M | alto | opus | ready |
| 90 | [SECURITY] **AUDIT-FINDING-PROFILE-PATH-TRAVERSAL-01** — sanitizar identifier em `load_profile` contra path traversal (defesa em profundidade; CODE_INTERNAL leak). | S | alto | opus | ready |
| 91 | [REFACTOR] **AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01** — unificar 3 cópias de `_effective_mult` + encapsular `RumbleEngine._last_auto_*`. | M | alto | opus | ready |
| 92 | [CLEANUP] **AUDIT-FINDING-KEYBOARD-SUBSYSTEM-DEAD-01** — deletar `KeyboardSubsystem` classe paralela nunca cabeada. | XS | alto | sonnet | ready |
| 93 | [CLEANUP] **AUDIT-FINDING-DEAD-CODE-01** — deletar `profiles/autoswitch.py::start_autoswitch` + `_noop` + sentinels em validar-acentuacao. | XS | médio | sonnet | ready |
| 94 | [REFACTOR] **AUDIT-FINDING-EVDEV-READER-BASE-CLASS-01** — extrair `_EvdevReconnectLoop` base para eliminar ~100 LOC duplicados. | M | médio | opus | ready |
| 95 | [REFACTOR] **AUDIT-FINDING-IPC-BRIDGE-BARE-EXCEPT-01** — extrair `_safe_call` helper em `ipc_bridge.py` (13 wrappers idênticos). | S | médio | opus | ready |
| 96 | [SECURITY] **AUDIT-FINDING-SINGLE-INSTANCE-PID-RECYCLE-01** — verificar `/proc/<pid>/comm` antes de SIGTERM no predecessor. | S | médio | opus | ready |
| 97 | [PERF] **AUDIT-FINDING-WAYLAND-PORTAL-PERF-01** — migrar `WaylandPortalBackend` para thread de longa vida ou jeepney síncrono direto. | S | médio | opus | ready |
| 98 | [TEST] **AUDIT-FINDING-COVERAGE-ACTIONS-ZERO-01** — cobrir rumble/triggers/firmware actions + GTK real opt-in. Meta cov total 63% → 70%. | L | médio | opus | ready |
| 99 | [REFACTOR] **AUDIT-FINDING-IPC-SERVER-SPLIT-01** — split `ipc_server.py` (843 LOC) em ≤500. Dep: executar DEP 91 antes. | L | médio | opus | ready |
| 100 | [OBS] **AUDIT-FINDING-LOG-EXC-INFO-01** — checklist de 10 must-do + edits pontuais dos achados 17, 19, 20, 21, 22, 23, 26. | M | baixo | sonnet | ready |

Execução recomendada em 3 tranches:
1. **Altos (87-92):** sequencial ou em worktrees separadas. 88, 92 são XS — começar por eles (quick wins).
2. **Médios (93-99):** 93, 95, 97 paralelizáveis; 91 pré-req de 99.
3. **Baixo/checklist (100):** após 91 mergeado para aplicar edits restantes em passagem única.

---

## Execução recomendada

### Paralelização

- **V1.1 Fase 5**: 8-15 são rápidas. Sonnet pode disparar 8→9→10 em sequência; 11 em paralelo.
- **V1.1 Fase 6**: Theme (16) primeiro; depois SVG (17) e redesign (18) em sequência; outros UI em paralelo.
- **V1.1 Fase 7**: 23→24→25 sequencial (dependências reais).
- **V1.2 Fase 1**: 3 executores paralelos em worktrees isoladas.
- **V2.0 Fase 1**: sequencial (35→36→37 são pré-req de 38).

### Orçamento por iteração

`CLAUDE_SPRINT_CICLO_MAX_RETRIES=3`. Em sprints sinalizadas **L** ou **XL**, esperar 1-2 rodadas de executor com patch-brief em caso de REPROVADO.

### Validação canônica

Toda sprint passa por:

1. Pytest unit verde.
2. Ruff limpo nos arquivos tocados.
3. `./scripts/check_anonymity.sh` OK.
4. `./run.sh --smoke` USB+BT verde quando toca daemon/poll loop.
5. Proof-of-work visual via skill `validacao-visual` quando toca UI.
6. Pré-release: `docs/process/CHECKLIST_HARDWARE_V2.md` preenchido por quem tem controle físico (criado por HARDWARE-VALIDATION-PROTOCOL-01).

### Tracking

Cada sprint tem issue GitHub com labels canônicos (`P0-urgent`/`P1-high`/`P2-medium`/`P3-low` + `type:feature`/`type:refactor`/`type:infra`/`type:docs`/`type:bug` + `status:ready` + `ai-task`). PRs fecham via `Closes #N` no body.

---

## Backlog aberto sem sprint (V2.x+)

- Observabilidade estendida: tracing OpenTelemetry, dashboard Grafana canônico.
- Multi-controle simultâneo: HID + IPC multiplexado.
- UI tema claro: settings de aparência (hoje só Drácula dark).
- EN/ES/FR i18n (hoje só PT-BR).
- Onboarding wizard: dialog de primeira execução, pede perfil preferido.
- Pairing BT pela própria GUI: integração com BlueZ.
- Atalhos configuráveis: hotkey custom (hoje combo sagrado PS+D-pad).
- Sandbox forte pra plugins: bubblewrap ou cgroups.
- Rumble-per-profile override (FEAT-RUMBLE-POLICY-01 fase 2).
- Presets custom de gatilho com import/export (FEAT-TRIGGER-PRESETS-POSITION-01 fase 2).

---

*"A ordem importa menos que a constância. O dobro de sprints na metade do tempo entrega mais do que o dobro do que sprints magras em sequência longa."*
