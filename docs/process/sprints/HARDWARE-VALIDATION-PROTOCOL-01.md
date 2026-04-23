# HARDWARE-VALIDATION-PROTOCOL-01 — Checklist reprodutível de validação em hardware real

**Tipo:** chore (documentação de processo).
**Wave:** V2.1 — Bloco D.
**Estimativa:** 1 iteração de escrita.
**Dependências:** nenhuma.

---

**Tracking:** issue a criar. Label: `type:docs`, `P1-high`, `ai-task`, `status:ready`.

## Contexto

Toda validação de v1.0.0 → v2.0.0 foi feita via `FakeController` (smoke USB/BT em subprocess com `HEFESTO_FAKE=1`). Features que afirmam "funciona no hardware" (Player LEDs bitmask, Rumble Policy com multiplicadores, botão Mic mutando sistema + sincronizando LED, hotplug USB/BT, autoswitch por janela, etc.) **não foram rodadas em controle físico** nesta cadeia de sessões.

Isso não é falha — é trade-off consciente (sessão de IA sem hardware). Mas v2.1.0 e diante precisam de um protocolo reprodutível para quem **tem** o controle validar pré-release. Sem protocolo escrito, cada mantenedor inventa o próprio checklist (ou pula a etapa).

## Decisão

Criar `docs/process/CHECKLIST_HARDWARE_V2.md` com 15-20 itens numerados, cada um com:

- **Pré-requisito** (controle conectado, daemon rodando, perfil ativo).
- **Comando exato** a rodar.
- **Resultado esperado** (observação física + saída de log).
- **Critério de falha** (o que significa "não passou").
- **Foto opcional** (quando aplicável).

### Tabela de itens canônicos (base — o executor afina a redação)

| # | Feature | Comando | Observação física | Sprint de origem |
|---|---|---|---|---|
| 1 | Player LEDs bitmask | `hefesto led player 0b10101` | LEDs 1, 3, 5 acesos | FEAT-PLAYER-LEDS-APPLY-01 |
| 2 | Rumble policy Economia | aplicar via GUI → `hefesto rumble set 255 255` | vibração sutil (~30% força) | FEAT-RUMBLE-POLICY-01 |
| 3 | Rumble policy Máximo | aplicar via GUI → `hefesto rumble set 100 100` | vibração plena | FEAT-RUMBLE-POLICY-01 |
| 4 | Mic button muta sistema | apertar botão Mic | LED apaga + `pactl get-source-mute @DEFAULT_SOURCE@` retorna `yes` | FEAT-HOTKEY-MIC-01 |
| 5 | Mic button desmuta | apertar novamente | LED acende + `pactl` retorna `no` | FEAT-HOTKEY-MIC-01 |
| 6 | Hotkey PS solo → Steam | segurar PS por ~800ms, nenhum outro botão | Steam Big Picture abre (se `action=steam` no config) | FEAT-HOTKEY-STEAM-01 |
| 7 | Hotplug USB | desplugar USB, replugar | GUI detecta em ≤ 2s, tray atualiza | FEAT-HOTPLUG-GUI-01 |
| 8 | Hotplug BT | desligar controle BT, reconectar | daemon reconecta, perfil mantido | FEAT-HOTPLUG-BT-01 |
| 9 | Lightbar brightness slider | aba LEDs → slider nível 1 | RGB escala ~25% intensidade | FEAT-LED-BRIGHTNESS-01 |
| 10 | Multi-position aventura (L2/R2) | carregar perfil aventura, apertar gatilhos gradualmente | 4-5 zonas distintas de resistência perceptíveis | SCHEMA-MULTI-POSITION-PARAMS-01 |
| 11 | Multi-position corrida (R2) | carregar perfil corrida, apertar R2 gradualmente | vibração crescente com posição, linear | SCHEMA-MULTI-POSITION-PARAMS-01 |
| 12 | Autoswitch por janela | abrir app whitelisted (ex.: firefox se no matcher) | perfil troca sozinho, GUI reflete | FEAT-PROFILE-STATE-01 |
| 13 | daemon.reload hot | editar `~/.config/hefesto/config.toml` campo hotkey, `hefesto daemon reload` | log `hotkey.manager.reloaded` | REFACTOR-DAEMON-RELOAD-01 |
| 14 | Single-instance daemon takeover | `hefesto daemon start; hefesto daemon start` (2×) | 2º mata 1º, **nenhum cursor errático** | BUG-MULTI-INSTANCE-01 |
| 15 | Single-instance GUI bring-to-front | `hefesto-gui; hefesto-gui` (2×) | 2ª traz 1ª ao foco, exit 0 | BUG-TRAY-SINGLE-FLASH-01 |
| 16 | Plugin lifecycle | `hefesto plugin list; hefesto plugin reload lightbar_rainbow` | plugin recarregado, LED animado | FEAT-PLUGIN-01 |
| 17 | Plugin watchdog | plugin simulado com `time.sleep(0.01)` por 3 ticks | 3ª vez desativa com log `plugin.watchdog.disabled` | FEAT-PLUGIN-01 |
| 18 | Metrics endpoint | `curl -s localhost:9100/metrics` | 8 métricas canônicas (`hefesto_poll_ticks_total`, etc.) | FEAT-METRICS-01 |
| 19 | Mouse emulation toggle | aba Mouse → ativar → apertar Circle | `xev` mostra Enter, `xdotool getmouselocation` estável | FEAT-MOUSE-02 |
| 20 | UDP compat DSX | cliente DSX externo envia JSON → `127.0.0.1:6969` | daemon aceita, aplica trigger effect | (runtime UDP existente) |
| 21 | USB autosuspend não derruba | plugar controle, deixar idle 10 min | controle ainda responde sem reconnect (requer `72-ps5-controller-autosuspend.rules` instalado) | USB-POWER-01 (A-05) |

### Seção "Onde marcar"

Template para quem valida:

```
Validação pré-release: v2.1.0
Validador: [seu nome]
Data: YYYY-MM-DD
Hardware: DualSense CFI-ZCT1W / CFI-ZCT1J / Edge / etc. (VID:PID)

[ ] Item 1 — Player LEDs bitmask
[ ] Item 2 — Rumble policy Economia
...
```

Fotos opcionais: `docs/process/validacoes/<release>/<item>.jpg` (git LFS ou repo separado se crescer).

## Critérios de aceite

- [ ] `docs/process/CHECKLIST_HARDWARE_V2.md` criado, ≥ 21 itens numerados.
- [ ] Cada item tem pré-requisito + comando + resultado esperado + critério de falha.
- [ ] Tabela de cross-reference com sprint de origem (rastreabilidade).
- [ ] Seção "Onde marcar" com template copy-paste.
- [ ] Instruções iniciais: setup mínimo (`sudo apt install curl socat wireshark` etc.), controle conectado, udev rules instaladas.
- [ ] Seção "Bateria mínima" — validar com bateria ≥ 30% para evitar desligamento no meio.
- [ ] Markdown renderiza limpo.
- [ ] Acentuação PT-BR correta.
- [ ] Zero emoji; glyphs Unicode de estado (`U+25CF`, `U+25CB`) permitidos se usados para indicar "passou/falhou".
- [ ] Referência cruzada: `docs/process/SPRINT_ORDER.md` ganha link curto para o checklist na seção "Validação canônica".

## Arquivos tocados

- `docs/process/CHECKLIST_HARDWARE_V2.md` (novo)
- `docs/process/SPRINT_ORDER.md` (linha de link)

## Proof-of-work

```bash
wc -l docs/process/CHECKLIST_HARDWARE_V2.md
grep -c "^## Item" docs/process/CHECKLIST_HARDWARE_V2.md  # espera ≥ 21

python3 -m markdown docs/process/CHECKLIST_HARDWARE_V2.md > /dev/null && echo "OK"

./scripts/check_anonymity.sh
python3 scripts/validar-acentuacao.py --check-file docs/process/CHECKLIST_HARDWARE_V2.md
```

## Notas para o executor

- Este documento **não é execução** — só protocolo escrito. Ninguém precisa ter o controle para esta sprint passar.
- **Não inventar items**. Cada linha da tabela acima vem de uma sprint real já mergeada — o executor só redige o texto, não acrescenta features inexistentes.
- **Item 10 e 11** dependem de SCHEMA-MULTI-POSITION-PARAMS-01 ter sido mergeada primeiro (estão em Bloco B, antes desta sprint no Bloco D). Se a ordem mudar, ajustar.
- **Formato amigável**: mantenedor vai ler isso em terminal ou editor — evitar tabelas muito largas, preferir itens em markdown com subcabeçalhos.
- **Texto de instruções neutro e direto** — evitar adjetivos ("extremamente importante", "fundamental"). Estilo do projeto é seco.
- Se durante a escrita identificar uma feature que **deveria** estar no checklist mas não foi lembrada no plano (ex.: UDP DSX), **adicionar** sem perguntar — é exatamente o escopo desta sprint.

## Fora de escopo

- Validação automatizada via script que tenta todos os itens sozinho (impossível sem hardware controlado por robô).
- Integração com Bugzilla/Jira/Linear para tracking.
- Tradução para inglês (PT-BR é idioma canônico do projeto).
- Criar fotos de referência (depende de ter hardware).
