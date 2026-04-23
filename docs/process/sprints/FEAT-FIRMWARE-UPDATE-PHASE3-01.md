# FEAT-FIRMWARE-UPDATE-PHASE3-01 — Tooling Linux para re-aplicar firmware oficial

**Tipo:** feat (experimental — alto risco).
**Wave:** V2.3+ — experimental.
**Estimativa:** 5-10 iterações (alta incerteza).
**Dependências:** FEAT-FIRMWARE-UPDATE-PHASE2-01 completa (protocolo mapeado).

---

**Tracking:** label `type:feat`, `experimental`, `firmware`, `hardware-required`, `status:blocked-on-phase-2`.

## Contexto

Fase 3 implementa o utilitário Linux que, partindo do blob de firmware **que o próprio usuário** obtém via PlayStation Accessories e da especificação derivada na fase 2, re-aplica o update sem depender de Windows.

**Escopo ético rígido**: esta sprint **não** distribui, redistribui, incorpora, embala ou faz referência a blob proprietário. A ferramenta aceita um arquivo local que o próprio usuário forneceu. Sem URL de download. Sem mirror. Sem cache.

## Decisão

Módulo novo `src/hefesto/firmware/updater.py` — CLI opt-in via subcomando `hefesto firmware`:

```
hefesto firmware check              # lê versão atual via HID report
hefesto firmware apply <caminho>    # aplica blob local
hefesto firmware info               # docs + riscos + checklist pré-apply
```

Design:

- `FirmwareUpdater` classe com interface bem marcada como `Experimental`.
- Sequência inferida em fase 2 executada como state machine: `probe → enter_dfu → erase → write_blocks → commit → exit_dfu → probe_new_version`.
- Validação obrigatória: SHA256 do blob é calculado e comparado contra whitelist opcional (arquivo `~/.config/hefesto/firmware-hashes.txt` mantido pelo usuário). Se blob não bate, sistema exige `--force` explícito.
- Rollback: se `write_blocks` falha entre blocos, tentar sair do DFU sem commit. Se commit já foi enviado, firmware corrompido → instrução clara "plug controle no Windows PlayStation Accessories para rescue".
- Watchdog de 30s para cada estágio — se USB trava, sair com erro claro, não loop infinito.

## Critérios de aceite

- [ ] `hefesto firmware check` funciona em controle comum (retorna versão atual).
- [ ] `hefesto firmware apply <path>` rejeita caminho inexistente, blob com SHA mismatch (sem `--force`), blob menor que ~1MB (sanity).
- [ ] Teste de integração em controle descartável (o sacrifício): atualizar para a mesma versão corrente (nop funcional; valida que a sequência inteira executa sem erro).
- [ ] Teste de rollback: injetar falha no meio do write via `HEFESTO_FIRMWARE_INJECT_FAIL=write_block_42`; sistema aborta em DFU e controle sobrevive.
- [ ] Documentação em `docs/usage/firmware.md` com avisos MAIÚSCULOS no topo, link para suporte PlayStation Accessories como fallback.
- [ ] Flag de feature `config.firmware_cli_enabled: bool = False` em `DaemonConfig` — opt-in explícito via `daemon.toml`.
- [ ] Testes unitários com FakeController simulando cada estágio.

## Arquivos tocados

- `src/hefesto/firmware/__init__.py` (novo).
- `src/hefesto/firmware/updater.py` (novo).
- `src/hefesto/firmware/protocol.py` (novo — state machine).
- `src/hefesto/cli/cmd_firmware.py` (novo).
- `docs/usage/firmware.md` (novo).
- `tests/unit/test_firmware_*.py` (novos).

## Riscos e mitigações

| Risco | Severidade | Mitigação |
|---|---|---|
| Brick do controle | Crítico | Watchdog + rollback + docs apontando rescue via Windows; primeiro teste em controle descartável |
| Corrupção parcial | Alto | Commit só após todos os blocos confirmados |
| Falha de energia mid-write | Alto | Doc orienta USB direto no PC (não hub), bateria do notebook não crítica |
| Update errado para controle errado | Médio | `firmware check` confirma VID:PID:revHW antes; hash whitelist |
| Questão legal (IP Sony) | Baixo (ferramenta não distribui blob) | Disclaimer MAIÚSCULO no topo; ferramenta só opera com blob local do usuário |

## Proof-of-work

```bash
# Controle conectado
hefesto firmware check
# esperado: "DualSense v02.15.00 (054c:0ce6, rev 0x0100)"

# Blob fornecido pelo usuário
hefesto firmware apply ~/Downloads/dualsense-02.15.00.bin --dry-run
# esperado: mostra sequência de transfers que SERIAM executados, sem executar

hefesto firmware apply ~/Downloads/dualsense-02.15.00.bin
# esperado: progresso por bloco, commit, reboot, check final

.venv/bin/pytest tests/unit/test_firmware_*.py -v
```

## Fora de escopo

- Distribuir blob de firmware (nunca).
- Modificar firmware (outro projeto, outra ética).
- Compatibilidade com DualShock 4 (projeto irmão, fora de Hefesto).
- GUI do updater (CLI é suficiente para experimental).
