# FEAT-HOTKEY-MIC-01 — Botão Mute do DualSense controla microfone do sistema

**Tipo:** feat.
**Wave:** V1.1.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** issue [#72](https://github.com/AndreBFarias/hefesto/issues/72) — fechada por PR com `Closes #72` no body.

## Contexto

DualSense tem um botão físico dedicado ao microfone (ao lado do touchpad). Nativamente ele muta o microfone interno do controle. O usuário quer que ele **também toggle o microfone padrão do sistema Linux** — toda vez que pressionar, o mic do host liga ou desliga.

## Decisão

Handler `on_mic_button_pressed()` chama `wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle` (PipeWire) ou `pactl set-source-mute @DEFAULT_SOURCE@ toggle` (PulseAudio legado). Detectar qual daemon de áudio está ativo no primeiro uso e cachear a escolha.

Também: atualizar o `MicLED` do controle para refletir o estado do sistema (vermelho = mutado, apagado = ativo). Dupla sincronização para evitar confusão.

## Critérios de aceite

- [ ] `src/hefesto/integrations/audio_control.py` (NOVO): classe `AudioControl` com método `toggle_default_source_mute() -> bool` retornando o novo estado (`True` se mutado). Auto-detecta `wpctl` vs `pactl` no primeiro init.
- [ ] `src/hefesto/daemon/lifecycle.py` subscribe em `EventTopic.BUTTON_DOWN` e trata evento de código `MIC_BTN` (ou equivalente no evdev): chama `audio.toggle_default_source_mute()` e então `controller.set_mic_led(muted)`.
- [ ] Debounce 200ms para evitar toggle duplo em pressões rápidas involuntárias.
- [ ] Config `DaemonConfig.mic_button_toggles_system: bool = True` (opt-out pra quem não quer).
- [ ] Teste `tests/unit/test_audio_control.py`: (a) detecta wpctl; (b) detecta pactl fallback; (c) toggle chama subprocess correto; (d) falha graciosa se nenhum dos dois disponível.
- [ ] Proof-of-work: DualSense plugado, `pavucontrol` aberto na aba Input Devices. Pressionar botão Mic → ícone no pavucontrol vira mute e LED do controle fica vermelho. Pressionar de novo → desmutado, LED apaga.

## Arquivos tocados (previsão)

- `src/hefesto/integrations/audio_control.py` (novo)
- `src/hefesto/daemon/lifecycle.py`
- `src/hefesto/daemon/config.py` (se existir; senão lifecycle.py `DaemonConfig`)
- `tests/unit/test_audio_control.py` (novo)

## Notas

- `wpctl` requer `wireplumber` instalado (default em Pop!_OS 22.04+).
- `pactl` fallback cobre Ubuntu 20.04 / Debian legacy.
- Distros sem nem um nem outro: daemon loga warning uma vez e desiste; botão Mic continua funcionando nativamente no controle (muta só o mic interno do DualSense).
- NUNCA `shell=True`.

## Fora de escopo

- UI para escolher qual source (input device) é afetado — sempre usa `@DEFAULT_AUDIO_SOURCE@`.
- Hold do botão Mic com ação diferente.
