# SPRINT_ORDER.md — Roadmap de execução do Hefesto

> Ordem recomendada de execução das sprints pendentes, agrupadas por wave/milestone.
> Cada sprint tem spec em `docs/process/sprints/<ID>.md` e issue correspondente no GitHub.

**Status de main:** `v1.0.0` publicada em 2026-04-21. Release `release.yml` dispara wheel + AppImage + GitHub release automaticamente na tag.

---

## Legenda

- **[BUG]** correção crítica de UX (reportado pelo usuário).
- **[FEAT]** feature nova pedida pelo usuário.
- **[CHORE]** dívida técnica interna.
- **[DOCS]** documentação.
- **[RELEASE]** marco de publicação.
- **=>** pode rodar em paralelo com a sprint acima.

---

## Wave V1.1 — Correções de UX + features pequenas

Objetivo: fechar os buracos de UX que o usuário reportou logo após a V1.0.0. Cadência curta, muito paralelismo.

### Fase 1 — Bugs críticos (bloqueiam o uso cotidiano)

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 1 | [BUG] [**BUG-DAEMON-AUTOSTART-01**](https://github.com/AndreBFarias/hefesto/issues/68) — daemon não sobe sozinho ao abrir GUI | S | sonnet |
| 2 | [BUG] [**BUG-MOUSE-TRIGGERS-01**](https://github.com/AndreBFarias/hefesto/issues/69) — triggers param ao ligar mouse | M (investigação) | opus |

### Fase 2 — Features pequenas, paralelizáveis

Três sprints independentes, disparadas simultaneamente em worktrees isoladas.

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 3 | [FEAT] [**FEAT-LED-BRIGHTNESS-01**](https://github.com/AndreBFarias/hefesto/issues/70) — slider de luminosidade do lightbar | S | sonnet |
| 3=> | [FEAT] [**FEAT-HOTKEY-STEAM-01**](https://github.com/AndreBFarias/hefesto/issues/71) — botão PS abre/foca Steam | S | sonnet |
| 3=> | [FEAT] [**FEAT-HOTKEY-MIC-01**](https://github.com/AndreBFarias/hefesto/issues/72) — botão Mic toggle microfone do sistema | S | sonnet |
| 3=> | [FEAT] [**FEAT-MOUSE-02**](https://github.com/AndreBFarias/hefesto/issues/87) — Circle=Enter, Square=Esc no modo Mouse | XS | sonnet |

### Fase 3 — Perfis + estado central (depende da Fase 2)

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 4 | [FEAT] [**FEAT-PROFILES-PRESET-06**](https://github.com/AndreBFarias/hefesto/issues/73) — 6 perfis (navegação, fps, aventura, ação, corrida, esportes) com feedback/vibração por posição | M | sonnet |
| 5 | [FEAT] [**FEAT-PROFILE-STATE-01**](https://github.com/AndreBFarias/hefesto/issues/74) — DraftConfig central, sync entre abas, apply-all atômico | M | opus |
| 6 | [FEAT] [**FEAT-HOTPLUG-GUI-01**](https://github.com/AndreBFarias/hefesto/issues/75) — GUI abre automaticamente ao plugar controle (USB) | S | sonnet |

### Fase 4 — Dívida técnica + paridade

Quatro sprints paralelizáveis, fecham a V1.1.

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 7 | [CHORE] [**CHORE-FAKEPATH-01**](https://github.com/AndreBFarias/hefesto/issues/76) — mover FakeController para `src/hefesto/testing/` | S | sonnet |
| 7=> | [CHORE] [**CHORE-ACENTO-01**](https://github.com/AndreBFarias/hefesto/issues/77) — 6 violações PT-BR em strings de código do IPC | XS | sonnet |
| 7=> | [CHORE] [**CHORE-CI-SMOKE-01**](https://github.com/AndreBFarias/hefesto/issues/78) — rodar `./run.sh --smoke` no workflow CI | S | sonnet |
| 7=> | [FEAT] [**FEAT-CLI-PARITY-01**](https://github.com/AndreBFarias/hefesto/issues/79) — CLI expõe luminosidade LED + mouse + daemon restart | M | sonnet |

### Fase 5 — Marco

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 8 | [RELEASE] **Release v1.1.0** — CHANGELOG + tag + push, workflow dispara artifacts | — | — |

---

## Wave V1.2 — Plataforma + docs

Objetivo: expandir onde o Hefesto roda (COSMIC, BT) e abrir a porta de entrada (quickstart).

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 9 | [FEAT] [**FEAT-COSMIC-WAYLAND-01**](https://github.com/AndreBFarias/hefesto/issues/80) — compat com Pop!_OS 24.04 COSMIC via portal XDG | L | opus |
| 10 | [FEAT] [**FEAT-FLATPAK-BUNDLE-01**](https://github.com/AndreBFarias/hefesto/issues/81) — manifest Flatpak + udev install-helper | L | opus |
| 11 | [FEAT] [**FEAT-HOTPLUG-BT-01**](https://github.com/AndreBFarias/hefesto/issues/82) — auto-abertura GUI ao parear via Bluetooth | S | sonnet |
| 12 | [DOCS] [**DOCS-QUICKSTART-01**](https://github.com/AndreBFarias/hefesto/issues/83) — guia visual com GIFs (pode começar antes, em paralelo) | M | sonnet |
| 13 | [RELEASE] **Release v1.2.0** | — | — |

---

## Wave V2.0 — Arquitetura + observabilidade

Objetivo: refatorar internals para sustentar crescimento; abrir plugin API.

| Ordem | Sprint | Porte | Modelo |
|---|---|---|---|
| 14 | [CHORE] [**REFACTOR-LIFECYCLE-01**](https://github.com/AndreBFarias/hefesto/issues/84) — quebrar `lifecycle.py` em `subsystems/` | L | opus |
| 15 | [FEAT] [**FEAT-METRICS-01**](https://github.com/AndreBFarias/hefesto/issues/85) — endpoint Prometheus `/metrics` opt-in | M | opus |
| 16 | [FEAT] [**FEAT-PLUGIN-01**](https://github.com/AndreBFarias/hefesto/issues/86) — sistema de plugins Python via `plugin_api/` | XL | opus (2 iterações) |
| 17 | [RELEASE] **Release v2.0.0** | — | — |

---

## Execução recomendada

### Paralelização

- **Fase 1 V1.1**: sequencial (BUG-DAEMON-AUTOSTART-01 → BUG-MOUSE-TRIGGERS-01). São bugs que podem interagir.
- **Fase 2 V1.1**: 3 executores em paralelo (worktrees isoladas).
- **Fase 4 V1.1**: 4 executores em paralelo.
- **Wave V1.2**: até 3 executores em paralelo (COSMIC+Flatpak dependem entre si; HOTPLUG-BT e DOCS independentes).
- **Wave V2.0**: sequencial (REFACTOR antes de METRICS e PLUGIN).

### Orçamento

Por iteração (CLAUDE_SPRINT_CICLO_MAX_RETRIES=3). Em sprints sinalizadas L ou XL, esperar 1-2 rodadas de executor com patch-brief em caso de REPROVADO.

### Validação

Toda sprint passa por:
1. Pytest unit verde.
2. Ruff clean.
3. `./scripts/check_anonymity.sh` OK.
4. `./run.sh --smoke` USB+BT verde (quando aplicável).
5. Proof-of-work visual quando toca UI (skill `validacao-visual`).

### Merge

Ordem de cherry-pick entre worktrees preserva dependências. Conflitos típicos em `main.glade`, `app.py`, `status_actions.py` — resolvidos preservando a intenção de CADA sprint (nunca descartar delta).

### Tracking

Cada sprint tem issue GitHub correspondente com labels canônicos do projeto (`P1-high`/`P2-medium`/`P3-low` + `type:feature`/`type:refactor`/`type:infra`/`type:docs` + `status:ready` + `ai-task`). O número da issue é registrado em cada spec `.md` na seção **Tracking** no topo do arquivo. PRs devem fechar a issue via `Closes #N` no body.

---

## Backlog aberto sem sprint (para V2.x+)

- **Observabilidade estendida**: tracing OpenTelemetry, dashboard Grafana canônico.
- **Multi-controle simultâneo**: HID + IPC multiplexado.
- **UI tema claro/escuro**: settings de aparência.
- **EN/ES/FR i18n**: só PT-BR hoje.
- **Onboarding wizard**: dialog de primeira execução, pede perfil preferido.
- **Pairing BT pela própria GUI**: integração com BlueZ.
- **Atalhos configuráveis**: hotkey customizado pelo usuário (hoje só combo sagrado PS+D-pad).
- **Sandbox forte para plugins**: bubblewrap ou cgroups.

---

*"A ordem importa menos que a constância. O dobro de sprints na metade do tempo entrega mais do que o dobro do que sprints magras em sequência longa."*
