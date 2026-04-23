# FEAT-FIRMWARE-UPDATE-PHASE1-01 — Research do protocolo de atualização de firmware DualSense (fase 1)

**Tipo:** research (documentação técnica).
**Wave:** V2.1 — Bloco D.
**Estimativa:** 1 iteração de escrita (research externa é contínua).
**Dependências:** nenhuma. Sub-sprint da spec-mãe `FEAT-FIRMWARE-UPDATE-01`.

---

**Tracking:** issue a criar. Label: `research`, `experimental`, `P3-low`, `ai-task`, `status:ready`, `help-wanted`.

## Contexto

Usuário (2026-04-22):
> A Sony tem um updater oficial para Windows, mas não para Linux. Pode investigar se conseguimos fazer o update do firmware do DualSense por aqui também? Não precisa ser via Wine, já sei que não rola. Eu e meus amigos só queremos rodar o update deles para fazer esse controle funcionar no Android — eu não tenho PS5, só o controle.

Spec-mãe `FEAT-FIRMWARE-UPDATE-01` decompõe em 3 fases. **Esta sprint é a Fase 1**: pura pesquisa e documentação. Zero código executável, zero blob proprietário copiado. Entregável é um markdown com referências externas reprodutíveis e análise do estado da arte.

## Decisão

Criar `docs/research/firmware-update-protocol.md` com seções canônicas:

1. **Objetivo e não-objetivo**
2. **Estado da arte** (projetos upstream que já desmontaram parte)
3. **Mapa de HID reports relevantes do DualSense**
4. **Hipóteses de ativação do modo DFU**
5. **Metodologia de research reprodutível** (usbmon, Wireshark, VM Windows)
6. **Riscos** (brick de hardware)
7. **Ética e base legal** (reverse engineering para interoperabilidade)
8. **Próximos passos** (condições para fase 2 arrancar)
9. **Referências** (URLs externas com commit hash/tag quando aplicável)

### Conteúdo mínimo por seção

**Estado da arte**:
- [`dualsensectl`](https://github.com/nowrep/dualsensectl) — CLI Linux funcional (bateria, LED, rumble). **Não tem DFU.** Verificar se já foi discutido em issue.
- [`pydualsense`](https://github.com/flok/pydualsense) — biblioteca Python base do Hefesto. Cobre output/input reports de uso normal, não DFU.
- [`Ryochan7/DS4Windows`](https://github.com/Ryochan7/DS4Windows) — ancestral DS4. DS4 tem protocolo DFU parcialmente documentado em issues e código — ponto de partida para analogia.
- [`hid-playstation`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/hid/hid-playstation.c) — driver kernel. Mapeia input reports regulares; DFU não aparece (correto — driver não deveria expor DFU).
- [`controllers.fandom.com — Sony DualSense`](https://controllers.fandom.com/wiki/Sony_DualSense) — wiki community com reports documentados.
- [`DualSenseUpdater.exe`](https://controller.dl.playstation.net/controller/lang/en/DualSenseUpdater.exe) da Sony — binário de ~20 MB. **Aviso**: o executor **não** deve baixar o binário para o repo; só documentar URL e SHA-256 publicamente verificado (se divulgado por terceiros).

**Mapa de HID reports**:
- Output `0x02` (control) — RGB, rumble, trigger effects.
- Input `0x01` (USB) — estado completo do controle.
- Input `0x31` (Bluetooth) — estado completo em BT.
- Feature reports `0x03`, `0x05`, `0x81`, `0xA3` etc. — menos documentados. **Hipótese**: feature report específico habilita DFU.
- Tabela resumida: report ID → direção → tamanho → descrição conhecida → fonte.

**Hipóteses de ativação DFU**:
- Feature report específico enviado via `hid_send_feature_report()` (libhidapi) ou `ioctl HIDIOCSFEATURE` em Linux puro.
- Combo de botões físicos (improvável — Sony protege contra trigger acidental).
- Comando via canal Sony exclusivo (requer análise de tráfego do updater oficial).
- Modo bootloader automático em resposta a VID:PID alternativo (algumas revisões HW).

**Metodologia reprodutível**:
```
Setup:
  - PC Linux (host, Ubuntu 22.04+) com DualSense plugado via USB-C.
  - VM Windows 11 (VirtualBox) com USB passthrough do DualSense.
  - Wireshark no host com plugin usbmon habilitado.
  - DualSenseUpdater.exe baixado pelo usuário dentro da VM.

Captura:
  1. sudo modprobe usbmon
  2. wireshark &
     - selecionar interface "usbmon0" ou específica do bus onde DualSense está.
     - filtro: "usb.src == x.y.z" (x, y, z conforme lsusb).
  3. VM: rodar updater, apertar "Atualizar".
  4. Aguardar conclusão (ou cancelamento — vale as duas).
  5. Salvar .pcapng em docs/research/firmware-update/captures/
     (NÃO commitar a captura — pode conter blob de firmware Sony. Só análise).

Análise:
  1. Identificar transição para modo DFU (mudança de VID:PID? feature report?).
  2. Identificar reports de chunking do firmware (tamanho, ordem, checksums).
  3. Identificar relatório de conclusão e resposta ao host.
  4. Diffar pré-update vs pós-update: report de versão HID muda como?
```

**Riscos**:
- Brick de hardware — probabilidade não-nula durante protótipo. Mitigação na fase 2: `--dry-run`, verificação de bateria, timeout em cada chunk.
- Chain of trust: se Sony exige assinatura, não podemos gerar blobs próprios. Só aplicar os oficiais.
- Responsabilidade civil: disclaimer em 3 lugares antes de qualquer release (README, dialog pré-update, log).

**Ética e base legal**:
- Brasil: Art. 77, Lei 9.279/96 permite engenharia reversa para interoperabilidade.
- UE: Software Directive 2009/24/EC art. 6 (decompilação para interoperabilidade).
- EUA: DMCA 17 USC §1201(f) (reverse engineering para interoperabilidade).
- **Não distribuímos blob Sony.** Usuário baixa do site oficial. Hefesto só aplica.

**Próximos passos** (condição para Fase 2):
- Protocolo DFU identificado com ≥ 80% de confiança.
- Pelo menos 1 contribuidor com hardware disposto a testar em controle de sacrifício.
- Chain of trust: se Sony assinatura é insuperável sem chave privada, **fechar a spec honestamente** com "inviável no estado atual".

## Critérios de aceite

- [ ] `docs/research/firmware-update-protocol.md` criado, ≥ 250 linhas, todas as seções canônicas presentes.
- [ ] Zero blob proprietário no repo (nem binário, nem disassembly de firmware Sony).
- [ ] Zero código executável (apenas snippets ilustrativos em bloco de código).
- [ ] ≥ 5 referências externas com URL válida (validar via `curl -IL` opcional).
- [ ] Seção "Ética e base legal" cita pelo menos 1 artigo legal por jurisdição (BR/UE/EUA).
- [ ] Seção "Próximos passos" é honesta: lista condições para fase 2 E condições de fechamento (inviável).
- [ ] README do projeto (raiz) ganha parágrafo curto "Firmware update" mencionando que é experimental e não fornecido hoje, com link para o research.
- [ ] Markdown renderiza limpo (validar via `python3 -m markdown docs/research/firmware-update-protocol.md > /dev/null` ou `mdcat`).
- [ ] Zero menção a AI/modelo/assistente; zero emoji.
- [ ] Acentuação PT-BR correta (o hook da sprint 7 vai validar).

## Arquivos tocados

- `docs/research/firmware-update-protocol.md` (novo)
- `README.md` (parágrafo curto)

## Proof-of-work

```bash
wc -l docs/research/firmware-update-protocol.md
# Espera ≥ 250 linhas.

python3 -m markdown docs/research/firmware-update-protocol.md > /tmp/fw.html && echo "OK"

./scripts/check_anonymity.sh

python3 scripts/validar-acentuacao.py --check-file docs/research/firmware-update-protocol.md
```

## Notas para o executor

- Esta sprint é **escrita**, não código. O entregável é um documento com links e análise, não implementação.
- Se algum link externo retornar 404, substituir por archive.org wayback se existir snapshot, ou remover a referência. Nunca inventar URL.
- Hashes SHA-256 de binários externos (DualSenseUpdater.exe) — só incluir se confirmado publicamente por múltiplas fontes. Caso contrário, omitir.
- **Zero afirmação forte sem fonte**. Cada hipótese no texto deve ter qualificador ("preliminar", "requer validação", "não confirmado publicamente"). Honestidade epistêmica é o ponto — research serve também para registrar o que **não** sabemos.
- Se descobrir durante a escrita que um projeto upstream já implementou DFU (ex.: fork obscuro do pydualsense), documentar com destaque e sugerir contato com mantenedor antes da fase 2.

## Fora de escopo

- Escrever código da Fase 2 (CLI updater).
- Capturar tráfego real (requer VM Windows + hardware + tempo).
- Desmontar o `DualSenseUpdater.exe` (análise de binário proprietário — questionável legalmente, fora do escopo defensável de interoperabilidade).
- Contato direto com Sony solicitando spec (improvável de resposta).
- Discussão de DFU de outros controles (DualShock 4, Xbox, Switch).
