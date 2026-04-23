# FEAT-FIRMWARE-UPDATE-PHASE2-01 — Captura real do protocolo DFU do DualSense

**Tipo:** research (experimental — requer hardware).
**Wave:** V2.2+ — experimental.
**Estimativa:** 3-5 iterações (alta incerteza).
**Dependências:** FEAT-FIRMWARE-UPDATE-PHASE1-01 (documento base), hardware físico (PC + VM Windows + DualSense + cabo USB-C).

---

**Tracking:** label `type:research`, `experimental`, `firmware`, `hardware-required`, `status:blocked-on-hardware`.

## Contexto

Fase 1 entregou `docs/research/firmware-update-protocol.md` com hipóteses, metodologia reprodutível e base legal. Fase 2 **executa** a metodologia — captura real do tráfego USB durante um update oficial pela Sony (via PlayStation Accessories app no Windows) e extrai o protocolo DFU. Sem isso, qualquer tooling é chute.

Pré-requisitos físicos:

- PC host Linux com USB 2.0/3.0.
- VM Windows 10/11 com VirtualBox USB passthrough (ou máquina Windows real).
- DualSense físico (o alvo).
- Cabo USB-C de qualidade (sem noise).
- Conta PSN para baixar o PlayStation Accessories.
- `usbmon` habilitado no kernel (`modprobe usbmon`) + Wireshark ≥3.0.
- Espaço de disco: ≥ 5GB para capturas (cada sessão completa ~ 100-500MB).

## Procedimento

1. **Setup** (30min): ativa usbmon, baixa Wireshark, cria VM Win + passthrough USB, instala PlayStation Accessories.
2. **Baseline** (15min): captura 60s de tráfego com controle plugado sem update — traffic normal de polling, para filtrar depois.
3. **Captura do update** (15-30min): DualSense conectado, força update de firmware no PlayStation Accessories, grava toda a sessão (`wireshark -i usbmon2 -w /tmp/dfu-capture.pcap`).
4. **Análise** (2-4h):
   - Filtro `usb.transfer_type == 0x02` (CONTROL) e `usb.transfer_type == 0x01` (INTERRUPT).
   - Identificar transição de HID normal → modo DFU (comando especial).
   - Catalogar feature reports: `GET_REPORT (0xA1)` + `SET_REPORT (0x09)` com reportId alto.
   - Identificar ponto de envio do blob binário (bulk transfers grandes ou sequência de control transfers).
   - Verificar assinatura/checksum do blob (nos primeiros/últimos 256 bytes).
5. **Documentação** (1-2h): atualizar `docs/research/firmware-update-protocol.md` com os achados empíricos. Seção "Fase 2 — Resultados" acumula.
6. **Validação cruzada** (opcional): comparar com o que `DS4Windows` fez no DS4 DFU (protocolo Sony legado). Padrões similares sugerem invariantes da família.

## Critérios de aceite

- [ ] Captura `.pcap` completa do processo de update armazenada **fora do repo** (em disco local ou cloud privada — não comitar blob proprietário).
- [ ] Decisão do usuário sobre arquivamento: caminho do `.pcap` documentado em `docs/research/firmware-update-protocol.md` seção "Fase 2" como "disponível em ~/firmware-research/dfu-v1.pcap" ou equivalente.
- [ ] Documento atualizado com:
  - Report IDs identificados para entrada em DFU.
  - Sequência canônica (handshake → erase → write → commit → reboot).
  - Checksum/assinatura hipótese refutada ou confirmada.
  - Hash do blob binário (sha256) — **não** o blob em si.
- [ ] Seção "Execuções registradas" (ver DOCS-STATUS-PROTOCOL-READY-01) preenchida com data + pessoa + resultado.
- [ ] **Zero blob proprietário no repo**. Zero link para download da Sony. Só metodologia e inferências.

## Arquivos tocados

- `docs/research/firmware-update-protocol.md` (atualização).
- `.gitignore` ganha `*.pcap`, `firmware-blobs/`.

## Proof-of-work

```bash
# Pós-captura
sha256sum /caminho/dfu-capture.pcap  # registrar no doc, não comitar o pcap
tshark -r /tmp/dfu-capture.pcap -Y "usb.transfer_type == 0x02" | wc -l
# Contar control transfers; esperado ordem de 1000+
```

## Riscos

- **Brick do controle**: update oficial Sony não deveria brickar, mas é experimental. Usar controle secundário se possível.
- **IP Sony**: fase 2 é captura de protocolo oficial, não reverse engineering de firmware criptografado. Base legal (DMCA §1201(f) interoperability exemption, BR LDA art. 6° VIII) cobre. Documentar cada decisão no topo da seção "Fase 2".
- **PSN Terms of Service**: usar conta PSN pessoal, nunca conta de terceiro. Desmarcar telemetria se opt-out estiver disponível.

## Fora de escopo

- Implementar o update (vira fase 3 — sprint FEAT-FIRMWARE-UPDATE-PHASE3-01).
- Rodar blob modificado (brick garantido + fere IP se blob for derivativo).
- Distribuir a captura.
