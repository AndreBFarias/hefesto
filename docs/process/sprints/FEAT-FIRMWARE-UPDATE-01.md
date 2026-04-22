# FEAT-FIRMWARE-UPDATE-01 — Atualizador de firmware do DualSense em Linux (3 fases)

**Tipo:** feat experimental (research + protótipo).
**Wave:** V2.0+ (experimental — pode virar V1.2 se fase 1 bater em trilho claro).
**Estimativa:** 3-6 iterações por fase.
**Dependências:** nenhuma técnica; depende de vontade + tempo de pesquisa.
**Risco:** brick de hardware em protótipo/teste. **Aviso obrigatório em toda UI e docs.**

---

**Tracking:** issue a criar. Label: `research`, `experimental`, `P3-low`.

## Contexto e motivação

Usuário em 2026-04-22:

> A sony tem um updater official, pra windows, mas não pra linux. Pode investigar se conseguimos fazer o update do firmaware do dsx por aqui também? Não precisa ser via wine, já sei que não rola. Eu e meus amigos só queremos rodar o update deles pra fazer esse joça funcionar no android, eu não tenho ps5 só o controle.

Caso de uso concreto: updates de firmware do DualSense da Sony melhoram compatibilidade com Android (e em teoria iOS, Switch 2 etc.). Usuário sem PS5 + sem Windows fica excluído do ecossistema.

## Estado-da-arte (pesquisa inicial — preliminar, precisa validação)

**O que sabemos:**
1. Sony distribui **`DualSenseUpdater.exe`** (Windows 10+) em https://controller.dl.playstation.net/controller/lang/en/DualSenseUpdater.exe — binário de ~20MB.
2. O updater detecta o controle via USB (força uso de cabo), baixa blob de firmware da CDN Sony, e faz upload via HID.
3. Existe **`dualsensectl`** (github.com/nowrep/dualsensectl, MIT) — CLI Linux que lê bateria, muda LED, rumble, mas **não** tem update de firmware.
4. Relatos de reverse engineering parcial em:
   - https://controllers.fandom.com/wiki/Sony_DualSense (HID reports documentados).
   - Projeto `pydualsense` (base do Hefesto) cobre reports de uso (RGB, rumble, trigger effects), não DFU.
5. **Modo DFU** (Device Firmware Update): controles Sony típicos entram em DFU via HID feature report ou combo especial. **Ainda não confirmado publicamente** para DualSense — precisa sniffing do updater Windows.

**Não é viável via Wine** (usuário já sabe) porque o updater usa camada WinUSB específica + HID privilegiado que Wine não proxya pra USB Linux.

## Estratégia em 3 fases (cada uma é sprint-filha)

### Fase 1 — Research e documentação (sprint FEAT-FIRMWARE-UPDATE-01-RESEARCH)

**Objetivo:** descobrir se é tecnicamente possível. Sem código de execução; só captura, análise e doc.

Entregáveis:
- `docs/research/firmware-update/README.md`: achados, referências, diagrama de fluxo.
- `docs/research/firmware-update/captures/`: captures `usbmon` + `Wireshark` do updater Windows em máquina virtual ou PC separado com DualSense plugado e firmware sendo aplicado. **2-3 capturas** (update real + cancelamento).
- `docs/research/firmware-update/protocol-analysis.md`: dissecação do protocolo — reports HID usados, ordem das mensagens, checksums, chunking.
- `docs/research/firmware-update/dfu-entry.md`: como entra/sai do modo DFU. Se requer feature report específico, documentar bytes.
- `docs/research/firmware-update/risks.md`: vetores conhecidos de brick. Mitigações possíveis.

Ferramentas:
- **usbmon** (`modprobe usbmon; cat /sys/kernel/debug/usb/usbmon/0u`) — linha Linux.
- **Wireshark** com `usbmon` capture interface.
- **VM Windows** (VirtualBox com USB passthrough) rodando o updater oficial.
- Opcional: **OpenUSBAnalyzer** (USB hardware analyzer) — caro.

Critério de saída: ou temos protocolo suficientemente claro pra fase 2, ou declaramos "inviável com recursos atuais" e fechamos a spec como "aprendemos, parou aqui".

Estimativa: **2-3 semanas de research part-time**. Bloco grande.

### Fase 2 — Protótipo CLI (sprint FEAT-FIRMWARE-UPDATE-01-CLI)

**Pré-requisito:** fase 1 concluída com protocolo viável.

**Objetivo:** CLI Python isolada que pega um blob de firmware conhecido (baixado manualmente do site da Sony via wget) e aplica no controle.

Entregáveis:
- `scripts/firmware_update.py` (não é integrado ao daemon; processo separado intencional).
- Interface:
  ```bash
  python scripts/firmware_update.py --blob ~/Downloads/dualsense_fw_0x0800.bin --yes
  # Avisos obrigatórios + confirmação dupla.
  # Progresso por chunk.
  # Verificação pós-update (report de versão HID).
  ```
- Abortar com erro claro se:
  - controle não entra em DFU no tempo esperado.
  - checksum do chunk falha.
  - bateria abaixo de 50% (requisito fixo; brick acontece se morre no meio).

Testes:
- **NÃO há teste automatizado que de fato atualize o controle.** Teste em controle real é one-shot (manual, um por iteração).
- Mock do controle simulando respostas DFU (casos: progresso ok, timeout, checksum fail).

Segurança:
- Flag `--dry-run` que simula tudo mas não escreve o último chunk (o que seria commit real do flash).
- Verificação de `vid:pid 054c:0ce6` antes de proceder.
- Resetar lightbar vermelho intenso durante o update pro usuário não encostar.

Estimativa: **3-4 semanas** com hardware à disposição.

### Fase 3 — Integração UI (sprint FEAT-FIRMWARE-UPDATE-01-UI)

**Pré-requisito:** fase 2 com update bem-sucedido em pelo menos 3 controles diferentes (volume mínimo de confiança).

**Objetivo:** aba nova na GUI ou ação no menu Daemon.

Entregáveis:
- Aba "Firmware" (nova) com:
  - Versão atual do firmware (lida via HID report).
  - Botão "Verificar atualização" (consulta CDN Sony ou lista local).
  - Lista de blobs baixados em `~/.cache/hefesto/firmware/`.
  - Botão "Atualizar" com dialog de **3 confirmações** (este é destrutivo!).
  - Barra de progresso + log em tempo real.
  - Screen-lock via GTK: impede interação com outras abas durante update.
- Daemon **suspende poll** durante update (evita escrita concorrente que brickaria).

Estimativa: 1 semana.

## Critérios de aceite do spec-mãe (esta sprint)

Esta spec **é um roadmap**. Entregáveis concretos:

- [ ] `docs/research/firmware-update/README.md` criado como stub — template pros achados da fase 1.
- [ ] Sub-sprints criadas: `FEAT-FIRMWARE-UPDATE-01-RESEARCH`, `FEAT-FIRMWARE-UPDATE-01-CLI`, `FEAT-FIRMWARE-UPDATE-01-UI` como specs separadas (cada uma pode ou não ser executada dependendo do progresso da anterior).
- [ ] Issue GitHub com label `research`, `experimental`, `help-wanted` — abre oportunidade de contribuidores com know-how de reverse engineering.
- [ ] README do projeto ganha seção "Firmware update" informando que é experimental, não fornecido hoje.

## Aviso legal / ética

O DualSense é hardware comercial da Sony. O firmware é propriedade da Sony. O projeto Hefesto:

- **NÃO** redistribui blobs de firmware (usuário baixa do site oficial da Sony).
- **NÃO** modifica firmware (só aplica blobs assinados pela Sony).
- **Faz reverse engineering do protocolo de aplicação** — legal no Brasil, UE, EUA e maioria das jurisdições sob doutrina de interoperabilidade (art. 77/Lei 9.279/96 no Brasil; EU Software Directive 2009/24/EC art. 6).
- **Assume o risco**: usuário aceita que pode brickar o controle. Disclaimer em 3 lugares: README, dialog pré-update, log de daemon.

## Fora de escopo

- Hackear/modificar firmware (nunca — só aplica blobs oficiais Sony).
- Downgrade de firmware (improvável Sony permitir).
- Update via Bluetooth (só USB — Sony obriga).
- Update de outros controles (Xbox, Switch Pro, Stadia).
- Análise de vulnerabilidades de firmware.

## Recursos pra fase 1

- **Sniffing Linux**: `wireshark`, `usbmon`, `tshark`.
- **VM Windows**: VirtualBox + Win11 licenciado + USB passthrough.
- **DualSense reference**: https://github.com/Ryochan7/DS4Windows (DS4 tem protocolo DFU documentado — ponto de partida).
- **pydualsense source**: base do backend atual; ver se já exposta alguma API DFU dormente.
- **Sony PS5 IP stack**: não faz sentido, DSX é USB HID local.

## Notas para o executor

- Fase 1 é 80% pesquisa + 20% escrita. Não se comprometer com deliverable de código na fase 1.
- Conversar com mantenedores de `dualsensectl` e `pydualsense` — pode ter alguém que já explorou isso.
- Se possível, comprar ou emprestar um **2º controle DualSense** antes da fase 2 — pra ter "backup" caso o primeiro brick.
- Documentar **todos** os passos no discovery. Mesmo se a spec falhar, o aprendizado fica.

## Crítico: discoverability

A pesquisa pode revelar que:
- O firmware update do DualSense **exige** chain of trust via chave Sony embedded no updater Windows — descriptografia impossível sem a chave. Se for o caso, Fase 1 termina em "inviável" e o projeto fecha a spec honestamente.
- Ou: protocolo é simples HID puro, e podemos ter CLI funcional em 2 semanas de protótipo.

Nenhum dos cenários é fracasso. Ambos são aprendizado. Spec está desenhada pra aceitar qualquer desfecho.
