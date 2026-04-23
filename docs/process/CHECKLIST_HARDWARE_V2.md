# CHECKLIST_HARDWARE_V2 — Protocolo de validação em DualSense real

Checklist reprodutível para validar em hardware físico as features entregues nas waves V1.1, V1.2 e V2.0+ do Hefesto. Criado pela sprint `HARDWARE-VALIDATION-PROTOCOL-01` em 2026-04-23.

Todas as features abaixo foram testadas via `FakeController` no CI. A validação em controle real é trilho manual — executada por quem tem hardware — **antes** de cada release (`v2.1.0` em diante). O mantenedor com DualSense preenche os checkboxes e arquiva o documento preenchido em `docs/process/validacoes/<release>/` ao final.

---

## Setup mínimo

- Distribuição Linux com kernel ≥ 6.0 (driver `hid-playstation` já no mainline).
- Pacotes no host (validar com `apt list --installed 2>/dev/null | grep -E "^(curl|socat|wireshark|pactl|wpctl|xdotool)" | head`):
  - `curl`, `socat` (testes de IPC/UDP/metrics).
  - `pactl` ou `wpctl` (teste Mic mute).
  - `xdotool`, `xev` (teste mouse emulation).
  - `jq` (opcional — parse do retorno IPC).
- Hefesto instalado na versão alvo (via `.deb` ou `flatpak` ou `pip install -e .`).
- Daemon rodando via `systemctl --user start hefesto.service` ou `hefesto daemon start`.
- `udev` rules instaladas (`sudo bash scripts/install_udev.sh`) — obrigatório para evitar `CAP_A-05` (autosuspend derrubando controle).
- **DualSense** conectado via USB-C ou pareado via Bluetooth.
- **Bateria ≥ 30%** — itens com hotplug repetido podem esgotar bateria fraca; testes de rumble máximo puxam corrente não-trivial.

---

## Convenção de marcação

Para cada item abaixo, preencher com:

- `[ ]` — ainda não testado.
- `[X]` — testado e passou.
- `[F]` — testado e **falhou** — abrir sprint-filha referenciando a sprint de origem + este checklist.
- `[~]` — parcialmente testado (ex.: smoke OK, validação tátil inconclusa).

Adicionar nota em linha nova indentada (4 espaços) se o resultado exigir explicação.

---

## Item 1 — Player LEDs bitmask (FEAT-PLAYER-LEDS-APPLY-01)

- [ ] Aplicar via CLI ou GUI o bitmask `0b10101` (LEDs 1, 3, 5 acesos).
    - Pré-requisito: controle conectado, daemon rodando.
    - Comando: `echo '{"jsonrpc":"2.0","id":1,"method":"led.set","params":{"player_mask":21}}' | socat - UNIX-CONNECT:$XDG_RUNTIME_DIR/hefesto/hefesto.sock` — ou via GUI aba LEDs.
    - Observação esperada: LEDs Player 1, 3 e 5 acesos; 2 e 4 apagados.
    - Critério de falha: qualquer outro padrão aceso; nenhum LED aceso; todos apagados.

---

## Item 2 — Rumble policy Economia (FEAT-RUMBLE-POLICY-01)

- [ ] Selecionar política Economia na aba Rumble, aplicar rumble máximo.
    - Comando: abrir GUI, aba Rumble, clicar "Economia"; slider mantém default.
    - Em paralelo: `echo '{"jsonrpc":"2.0","id":1,"method":"rumble.set","params":{"weak":255,"strong":255}}' | socat - UNIX-CONNECT:$XDG_RUNTIME_DIR/hefesto/hefesto.sock`.
    - Observação esperada: controle vibra **suavemente** (~30% intensidade plena).
    - Critério de falha: vibração plena (mult não aplicado); vibração zero (mult errado para 0).

---

## Item 3 — Rumble policy Máximo (FEAT-RUMBLE-POLICY-01)

- [ ] Mudar política para Máximo, aplicar rumble moderado.
    - Comando: GUI → "Máximo" → `rumble.set weak=100 strong=100`.
    - Observação esperada: vibração em `100/255 × 1.0 = 100` por motor — intensidade moderada perceptível.
    - Critério de falha: vibração ainda atenuada (mult < 1.0 não foi aplicado corretamente).

---

## Item 4 — Mic button muta sistema (FEAT-HOTKEY-MIC-01)

- [ ] Plugar cabo USB, iniciar daemon, apertar botão Mic do controle.
    - Pré-requisito: PipeWire ou PulseAudio rodando (default em distros modernas).
    - Observação esperada: LED do Mic apaga **simultaneamente** ao mute do sistema.
    - Validação: `pactl get-source-mute @DEFAULT_SOURCE@` (PulseAudio) ou `wpctl get-volume @DEFAULT_AUDIO_SOURCE@` (PipeWire) retorna `yes` / `MUTED`.
    - Critério de falha: LED apaga mas sistema não muta (FEAT-AUDIO-CONTROL-01 quebrado); sistema muta mas LED fica aceso (INFRA-SET-MIC-LED-01 quebrado); nada acontece.

---

## Item 5 — Mic button desmuta (FEAT-HOTKEY-MIC-01)

- [ ] Com sistema mutado do item 4, apertar Mic novamente.
    - Observação esperada: LED acende, sistema desmuta.
    - Validação: `pactl get-source-mute @DEFAULT_SOURCE@` retorna `no`.
    - Critério de falha: ciclo sem toggle correto.

---

## Item 6 — Hotkey PS solo dispara Steam (FEAT-HOTKEY-STEAM-01)

- [ ] Configurar `~/.config/hefesto/config.toml` com `ps_button_action = "steam"`.
- [ ] Reiniciar daemon (`hefesto daemon reload` ou restart via systemctl).
- [ ] Segurar o botão PS solitário (sem D-pad/combos) por 800 ms, soltar.
    - Observação esperada: Steam Big Picture abre.
    - Critério de falha: Steam não abre; daemon crasha; combo PS+D-pad segue funcionando (esse combo deve continuar válido — é o "sagrado").

---

## Item 7 — Hotplug USB (FEAT-HOTPLUG-GUI-01, BUG-TRAY-SINGLE-FLASH-01)

- [ ] Com daemon rodando, desplugar o cabo USB, aguardar 5 s, replugar.
- [ ] Repetir 5 vezes consecutivas.
    - Observação esperada:
      - GUI detecta desconexão em ≤ 2 s (`header` vira vermelho `○ Daemon Offline` ou equivalente).
      - Ao replugar, GUI volta a `● Conectado Via USB` em ≤ 2 s.
      - **Nenhum flash de janela** ao replugar (a janela existente volta ao foco, não abre uma nova).
    - Critério de falha: GUI abre e fecha (regressão A-11); tray mostra 2 ícones temporários; daemon nunca reconhece replug.

---

## Item 8 — Hotplug BT (FEAT-HOTPLUG-BT-01)

- [ ] Parear controle via Bluetooth, conectar com daemon rodando.
- [ ] Desligar controle (pressionar PS por 10 s), aguardar 5 s, religar.
    - Observação esperada: daemon reconecta automaticamente em ≤ 3 s; perfil ativo preservado.
    - Critério de falha: reconexão não acontece; perfil volta para `fallback`; cursor errático (regressão BUG-MULTI-INSTANCE-01).

---

## Item 9 — Lightbar brightness slider (FEAT-LED-BRIGHTNESS-01-03)

- [ ] Aba LEDs, mover slider "Brilho" para nível 1 (mínimo visível).
    - Observação esperada: lightbar RGB escala para ~25 % da intensidade anterior.
- [ ] Subir para nível 4 (máximo).
    - Observação esperada: lightbar em intensidade plena.
- [ ] Salvar perfil com slider em nível 2, trocar para outro perfil, voltar.
    - Observação esperada: slider volta para nível 2 (persistência no JSON via FEAT-LED-BRIGHTNESS-03).
    - Critério de falha: nenhuma mudança visível; slider volta para default ao trocar perfil (propagação A-06 regrediu).

---

## Item 10 — Multi-position aventura em L2 + R2 (SCHEMA-MULTI-POSITION-PARAMS-01)

- [ ] Carregar perfil `aventura` (slug `aventura`, display `Aventura`).
- [ ] Com os gatilhos relaxados, apertar L2 gradualmente da posição neutra até o fim.
    - Observação esperada: **4–5 zonas distintas** de resistência perceptíveis ao longo do curso (zona inicial leve, zonas intermediárias progressivamente mais firmes, zona final rígida).
- [ ] Repetir para R2.
    - Observação esperada: mesma progressão, simétrica.
    - Critério de falha: resistência uniforme (params aninhado não chegou ao hardware); sem resistência alguma (mode não aplicado); controle trava.

---

## Item 11 — Multi-position corrida em R2 (SCHEMA-MULTI-POSITION-PARAMS-01)

- [ ] Carregar perfil `corrida`.
- [ ] Apertar R2 gradualmente do neutro ao fim.
    - Observação esperada: **vibração crescente** linear com a posição — neutro = sem vibração; posição média = vibração leve; final = vibração plena.
    - Critério de falha: vibração constante desde o início; vibração some no meio do curso; nenhuma vibração.
- [ ] L2 permanece em modo Resistance (canônico).

---

## Item 12 — Autoswitch por janela (FEAT-PROFILE-STATE-01)

- [ ] Abrir terminal, verificar perfil ativo = `fallback` ou `navegacao` dependendo do matcher.
- [ ] Abrir Firefox.
    - Observação esperada: perfil troca automaticamente (ex.: para `navegacao` ou para o perfil cujo `match.window_class` contém `firefox`).
- [ ] Fechar Firefox.
    - Observação esperada: perfil volta para o anterior.
    - Critério de falha: perfil não troca; troca para errado; daemon entra em loop.

---

## Item 13 — daemon.reload hot (REFACTOR-DAEMON-RELOAD-01)

- [ ] Com daemon rodando, editar `~/.config/hefesto/config.toml` — trocar `ps_button_action` de `"custom"` para `"steam"` (ou vice-versa).
- [ ] Executar `hefesto daemon reload` (ou IPC `daemon.reload`).
    - Observação esperada: log estruturado inclui `hotkey.manager.reloaded`; novo comportamento do PS solo reflete a mudança imediatamente **sem reiniciar o daemon**.
    - Critério de falha: daemon precisa restart; closure antiga continua ativa (regressão A-08).

---

## Item 14 — Single-instance daemon takeover (BUG-MULTI-INSTANCE-01)

- [ ] Iniciar daemon via `hefesto daemon start`. Confirmar PID com `pgrep -f "hefesto daemon"`.
- [ ] Iniciar novamente: `hefesto daemon start`.
    - Observação esperada: PID antigo recebe SIGTERM e morre; PID novo assume. `pgrep` retorna **um único** PID.
    - **Crítico**: nenhum cursor errático, nenhuma vibração fantasma — se o mouse pular aleatoriamente, é regressão BUG-MULTI-INSTANCE-01 (duas instâncias concorrendo via uinput).

---

## Item 15 — Single-instance GUI bring-to-front (BUG-TRAY-SINGLE-FLASH-01)

- [ ] Abrir GUI via `hefesto-gui`. Janela aparece.
- [ ] Rodar `hefesto-gui` novamente.
    - Observação esperada: **não abre segunda janela**. A primeira é trazida ao foco (X11 via `xdotool windowactivate`; Wayland via SIGUSR1 → `show_window`). Exit code do segundo launch: `0`.
    - Critério de falha: duas janelas simultâneas; primeira fecha; segunda trava sem foco.

---

## Item 16 — Plugin lifecycle (FEAT-PLUGIN-01)

- [ ] Listar plugins: `hefesto plugin list`.
    - Observação esperada: lista inclui ao menos `lightbar_rainbow` (plugin de exemplo) se diretório `~/.config/hefesto/plugins/` existir com arquivos.
- [ ] Recarregar: `hefesto plugin reload lightbar_rainbow`.
    - Observação esperada: plugin descarregado e recarregado; log `plugin.reloaded`; lightbar animação reinicia.

---

## Item 17 — Plugin watchdog (FEAT-PLUGIN-01)

- [ ] Criar plugin malicioso em `~/.config/hefesto/plugins/slow.py`:
    ```python
    import time
    from hefesto.plugin_api import Plugin, PluginContext
    
    class SlowPlugin(Plugin):
        def on_tick(self, ctx: PluginContext) -> None:
            time.sleep(0.01)  # 10ms excede budget de 5ms
    ```
- [ ] Rodar `hefesto plugin reload slow`.
    - Observação esperada: após 3 ticks com violação (>5 ms), daemon emite log `plugin.watchdog.disabled name=slow` e o plugin é desativado automaticamente.
    - Critério de falha: plugin continua ativo após violações; daemon trava; outros plugins afetados.

---

## Item 18 — Metrics endpoint Prometheus (FEAT-METRICS-01)

- [ ] Habilitar métricas: `~/.config/hefesto/config.toml` com `[metrics] enabled = true`.
- [ ] Reiniciar daemon. Consultar: `curl -s localhost:9100/metrics | grep hefesto_`.
    - Observação esperada: ≥ 8 métricas canônicas, incluindo `hefesto_poll_ticks_total`, `hefesto_ipc_requests_total`, `hefesto_subsystem_up`.
    - Bind **obrigatoriamente** em `127.0.0.1` (não `0.0.0.0`) — confirmar com `ss -tnlp | grep 9100`.
    - Critério de falha: endpoint indisponível; bind em `0.0.0.0`; métricas vazias.

---

## Item 19 — Mouse emulation toggle (FEAT-MOUSE-02)

- [ ] Aba Mouse → ativar toggle "Emulação de mouse".
- [ ] Apertar Circle (O).
    - Validação: `xev` em janela separada captura `KeyPress Return` (Enter).
- [ ] Apertar Square (□).
    - Validação: `xev` captura `KeyPress Escape` (Esc).
- [ ] Mover stick direito.
    - Validação: `xdotool getmouselocation` muda; cursor segue o stick sem saltos erráticos.
    - Critério de falha: cursor errático (regressão BUG-MULTI-INSTANCE-01); Enter/Esc não disparam; outros botões interferem.

---

## Item 20 — UDP compat DSX (protocolo legacy)

- [ ] Enviar pacote JSON UDP para `127.0.0.1:6969` com payload compat DSX:
    ```bash
    echo '{"instructions":[{"type":"TriggerUpdate","parameters":[0,"Resistance",0,5]}]}' | socat - UDP:127.0.0.1:6969
    ```
    - Observação esperada: L2 adquire resistência moderada; daemon loga `udp.compat.applied`.
    - Critério de falha: daemon ignora; crash de parse.

---

## Item 21 — USB autosuspend não derruba o controle (A-05)

- [ ] Com controle plugado via USB-C e `72-ps5-controller-autosuspend.rules` instalada, deixar sistema ocioso **10 minutos** sem tocar no controle.
    - Observação esperada: após o idle, pressionar qualquer botão **responde imediatamente**; daemon não reporta reconnect.
    - Critério de falha: `journalctl --user -u hefesto.service` mostra ciclos de reconnect durante o idle — a udev rule não foi aplicada ou não bate com o device.

---

## Pós-validação

Ao preencher o checklist para uma release:

1. Salvar cópia em `docs/process/validacoes/v<versao>/CHECKLIST_HARDWARE_V2-preenchido.md`.
2. Para cada item com `[F]`:
   - Registrar em `docs/process/discoveries/<data>-<sintoma>.md` com sintoma observado, hipótese, logs anexados.
   - Abrir sprint-filha `BUG-HW-<area>-01` referenciando o item.
3. Se ≥ 3 itens com `[F]`, **bloqueia** a release até serem resolvidos.
4. Se a release sai com `[~]` (parcialmente validado), mencionar em `CHANGELOG.md` seção `Known issues` explicitando o item e o motivo da inconclusividade.

---

## Referências cruzadas

| Item | Sprint de origem | Status no brief |
|---|---|---|
| 1 | FEAT-PLAYER-LEDS-APPLY-01 | entregue v1.1 |
| 2–3 | FEAT-RUMBLE-POLICY-01 | entregue v1.1 |
| 4–5 | FEAT-HOTKEY-MIC-01 + INFRA-SET-MIC-LED-01 + FEAT-AUDIO-CONTROL-01 | entregue v2.0 |
| 6 | FEAT-HOTKEY-STEAM-01 | entregue v1.1 |
| 7 | FEAT-HOTPLUG-GUI-01 + BUG-TRAY-SINGLE-FLASH-01 | entregue v1.1 |
| 8 | FEAT-HOTPLUG-BT-01 | entregue v1.2 |
| 9 | FEAT-LED-BRIGHTNESS-01 + 02 + 03 | entregue v1.1 |
| 10–11 | SCHEMA-MULTI-POSITION-PARAMS-01 | entregue v2.1 |
| 12 | FEAT-PROFILE-STATE-01 + autoswitcher | entregue v1.1 |
| 13 | REFACTOR-DAEMON-RELOAD-01 (A-08) | entregue v1.2 |
| 14 | BUG-MULTI-INSTANCE-01 (A-10) | entregue v1.1 |
| 15 | BUG-TRAY-SINGLE-FLASH-01 (A-11) | entregue v1.1 |
| 16–17 | FEAT-PLUGIN-01 | entregue v2.0 |
| 18 | FEAT-METRICS-01 | entregue v2.0 |
| 19 | FEAT-MOUSE-02 | entregue v1.1 |
| 20 | UDP compat DSX (runtime base) | entregue pré-v1.0 |
| 21 | USB-POWER-01 (A-05) | entregue v1.1 |

---

*"A forja não revela o ferreiro. Só a espada."*
