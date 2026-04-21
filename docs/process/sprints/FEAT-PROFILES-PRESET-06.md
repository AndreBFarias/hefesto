# FEAT-PROFILES-PRESET-06 — 6 perfis pré-configurados (Navegação, FPS, Aventura, Ação, Corrida, Esportes)

**Tipo:** feat (content + UX).
**Wave:** V1.1.
**Estimativa:** 1 iteração.
**Dependências:** FEAT-LED-BRIGHTNESS-01 (se for incluir brightness diferenciado por perfil).

---

## Contexto

Hoje existem 4 perfis default em `assets/profiles_default/`: `bow`, `driving`, `fallback`, `shooter`. Usuário quer 6 perfis pré-configurados com identidade e propósito claros, cobrindo estilos de jogo comuns. Nomes em português.

## Requisitos transversais (valem pra todos os 6 perfis)

- **Feedback por posição** (`MultiPositionFeedback`): cada perfil pode usar em vez do efeito simples quando faz sentido (ex.: aventura com stamina em zonas; corrida com breakpoints de freio). Param shape: `[pos0, pos1, ..., pos9]` com intensidade 0-9 em cada posição do curso do gatilho.
- **Vibração** (`MultiPositionVibration`): análogo ao feedback, mas com vibração discreta por posição. Adiciona sensação tátil quando atinge um "stop".
- **Rumble pré-configurado**: cada perfil define `rumble.weak` e `rumble.strong` em base de bytes (0-255) ou mantém `passthrough: true` para receber do jogo. Perfis com contexto forte (aventura/ação) têm valores pequenos pré-setados para caso o jogo não envie rumble próprio (ex.: `weak: 40, strong: 80`).

Quando o spec de um perfil listar `MultiPositionFeedback` ou `MultiPositionVibration`, o executor deve escolher valores coerentes com o estilo (pulsos mais densos em FPS, degraus largos em corrida etc.).

## Os 6 perfis

### 1. `navegacao.json` — Navegação desktop / menus
Uso: browser, terminal, launcher, navegação de menus de jogos antes de começar.
- **Triggers**: `Off` em ambos (quer cliques leves e instantâneos).
- **Lightbar**: azul suave `(40, 80, 180)`, brightness 0.4.
- **Mouse emulation**: ON por padrão (o controle vira navegador).
- **Match**: `wm_class` contendo `firefox`, `brave`, `chromium`, `google-chrome`, `gnome-terminal`, `steam` (Big Picture menu).

### 2. `fps.json` — First Person Shooter
Uso: CS, Valorant, Apex, COD, Overwatch, Cyberpunk combate.
- **R2**: `SemiAutoGun` params `(0, 9, 7, 7, 10, 0)` — resistência forte que "solta" ao atirar.
- **L2**: `Rigid` params `(0, 255)` — para mira firme.
- **R2 alt (opcional)**: `MultiPositionVibration` params `(0, 0, 0, 2, 5, 8, 9, 9, 9, 0)` — pulso crescente nos últimos 60% do curso, nada nos primeiros.
- **Lightbar**: vermelho intenso `(200, 20, 20)`, brightness 0.9.
- **Rumble**: `weak: 0, strong: 0, passthrough: true` (jogo gera).
- **Match**: nomes de processo/janela de FPS conhecidos (lista inicial 10-15).

### 3. `aventura.json` — Aventura RPG (Elden Ring, God of War, Zelda-like)
Uso: combate com timing, parries, stamina.
- **R2**: `Galloping` params `(0, 9, 7, 7, 10)` — pulsação que indica carregamento de ataque.
- **L2**: `MultiPositionFeedback` params `(0, 0, 3, 5, 7, 9, 9, 5, 3, 0)` — rampa de resistência simulando stamina drain com "alívio" no fim.
- **Lightbar**: dourado `(220, 170, 30)`, brightness 0.7.
- **Rumble**: `weak: 30, strong: 60, passthrough: true` (base pré-setada + passthrough; se jogo envia, substitui; se não, ainda sente o mundo).
- **Match**: `eldenring.exe`, `HorizonZeroDawn`, `GodOfWar.exe`, `Witcher3.exe`, `DarkSouls*`, `Sekiro`.

### 4. `acao.json` — Ação hack-and-slash
Uso: DMC, Bayonetta, Devil May Cry, Hi-Fi Rush.
- **R2**: `MultiPositionVibration` params `(0, 2, 4, 6, 8, 9, 7, 5, 3, 0)` — pulso em onda que premia manter trigger na zona "sweet".
- **L2**: `Rigid` params `(0, 180)` — firmeza para esquiva/guard.
- **Lightbar**: laranja neon `(255, 80, 0)`, brightness 1.0.
- **Rumble**: `weak: 20, strong: 40, passthrough: true`.
- **Match**: `DevilMayCry`, `Bayonetta`, `Hi-FiRush`, `NieR`.

### 5. `corrida.json` — Corrida / driving sim
Uso: Forza, Gran Turismo, Assetto Corsa, F1.
- **R2**: `MultiPositionFeedback` params `(0, 1, 2, 4, 6, 8, 9, 9, 9, 9)` — pedal de freio progressivo, trava-se perto do fundo.
- **L2**: `MultiPositionFeedback` params `(0, 0, 0, 0, 2, 5, 8, 9, 9, 9)` — embreagem/handbrake que só resiste na segunda metade (ponto de engate).
- **Lightbar**: ciano `(0, 180, 220)`, brightness 0.8.
- **Rumble**: `weak: 50, strong: 90, passthrough: true` — base tátil de motor + rumble do jogo.
- **Match**: `Forza*`, `AssettoCorsa`, `GranTurismo`, `F1_20*`, `DirtRally`.

### 6. `esportes.json` — Esportes
Uso: FIFA, eFootball, NBA 2K, MLB.
- **R2**: `PulseA` params `(0, 8, 5)` — chute/passe com resposta crescente.
- **L2**: `MultiPositionVibration` params `(0, 0, 1, 2, 3, 5, 7, 5, 3, 0)` — pulso de "dribble" no meio do curso.
- **Lightbar**: verde `(40, 200, 80)`, brightness 0.85.
- **Rumble**: `weak: 25, strong: 50, passthrough: true` — base de estádio + passthrough do jogo.
- **Match**: `FIFA*`, `eFootball`, `NBA2K*`, `MLB*`.

## Critérios de aceite

- [ ] Criar os 6 arquivos JSON em `assets/profiles_default/` com os valores acima. Schema v1 (pydantic).
- [ ] `scripts/install_profiles.sh` (NOVO) ou lógica em `install.sh`: copia os perfis de `assets/profiles_default/` para `~/.config/hefesto/profiles/` se o diretório estiver vazio (primeira instalação); NÃO sobrescreve perfis do usuário em reinstalações.
- [ ] Decisão sobre `driving.json` e `shooter.json` já existentes: **deletar** — `corrida.json` substitui `driving.json`; `fps.json` substitui `shooter.json`; `bow.json` pode ser preservado ou incorporado ao `aventura.json` (decidir).
- [ ] Teste `tests/unit/test_profiles_preset.py`: carrega cada perfil via `load_profile()` e valida que pydantic aceita; nome, priority, triggers, leds e rumble presentes.
- [ ] Aba Perfis da GUI lista os 6 (via `profile_list`); clicar ativa (via `profile.switch`).
- [ ] Proof-of-work visual: aba Perfis com lista dos 6, print + sha256.

## Arquivos tocados (previsão)

- `assets/profiles_default/navegacao.json` (novo)
- `assets/profiles_default/fps.json` (novo, renomeia shooter)
- `assets/profiles_default/aventura.json` (novo)
- `assets/profiles_default/acao.json` (novo)
- `assets/profiles_default/corrida.json` (novo, renomeia driving)
- `assets/profiles_default/esportes.json` (novo)
- `assets/profiles_default/shooter.json` (deletar)
- `assets/profiles_default/driving.json` (deletar)
- `assets/profiles_default/bow.json` (preservar ou deletar)
- `install.sh` / `scripts/install_profiles.sh` (novo)
- `tests/unit/test_profiles_preset.py` (novo)

## Notas

- Matchers devem ser PERMISSIVOS (regex `.*cyberpunk.*`) para pegar variações de nome de processo Steam (Proton).
- Priority: deixar `navegacao=50`, `fps=60`, `aventura=70`, `acao=65`, `corrida=55`, `esportes=55` — ordem do mais específico para o mais genérico. `fallback.priority=-1000` fica como padrão último.
- Se algum param do trigger não bater com a validação do `trigger_effects.py`, ajustar o param ou o modo. Verificar contra `HEFESTO_PROJECT.md §Trigger modes`.
