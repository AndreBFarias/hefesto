# DOCS-STATUS-PROTOCOL-READY-01 — Status `PROTOCOL_READY` para sprints sem execução humana

**Tipo:** docs (processo).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 0.25 iteração.
**Dependências:** nenhuma. Operacionaliza lição L-21-6 de META-LESSONS-V21-BRIEF-01.

---

**Tracking:** label `type:docs`, `process`, `ai-task`, `status:ready`.

## Contexto

`HARDWARE-VALIDATION-PROTOCOL-01` foi marcada `MERGED` em `SPRINT_ORDER.md` sem que nenhum dos 21 itens tenha sido executado em hardware real. Isso esconde débito — leitor futuro assume que a feature foi validada porque o status diz MERGED.

Regra nova necessária: sprint cujo entregável é **apenas** documento/protocolo/checklist ganha status distinto `PROTOCOL_READY`. Para virar `MERGED`, precisa de registro de ≥1 execução humana do protocolo (data, nome, resultado).

Candidatas retroativas a `PROTOCOL_READY`:

- `HARDWARE-VALIDATION-PROTOCOL-01` (zero itens executados).
- `FEAT-FIRMWARE-UPDATE-PHASE1-01` (documento de research, fase 2 pendente).

## Decisão

1. Adicionar em `docs/process/SPRINT_ORDER.md` seção de legenda explicando os 4 status: `PENDING` / `IN_PROGRESS` / `PROTOCOL_READY` / `MERGED`.
2. Reclassificar as 2 sprints acima de MERGED → PROTOCOL_READY.
3. Em `docs/process/CHECKLIST_HARDWARE_V2.md` e `docs/research/firmware-update-protocol.md` adicionar seção "Execuções registradas" inicialmente vazia. Quando usuário executar algum item, ele (ou um agent a pedido) preenche com `{data, quem, item, resultado}`.
4. Release notes futuras diferenciam "Sprints MERGED" vs. "Protocolos entregues (PROTOCOL_READY)" — transparência sobre o que realmente virou produto vs. doc.

## Critérios de aceite

- [ ] `SPRINT_ORDER.md` tem legenda de status (4 estados) no topo da primeira wave.
- [ ] HARDWARE-VALIDATION-PROTOCOL-01 e FEAT-FIRMWARE-UPDATE-PHASE1-01 reclassificadas de MERGED para PROTOCOL_READY na tabela V2.1.
- [ ] CHECKLIST_HARDWARE_V2.md e firmware-update-protocol.md ganham seção "## Execuções registradas" (vazia inicialmente).
- [ ] CHANGELOG v2.1.0 atualizado com nota "2 sprints em PROTOCOL_READY (dívida de execução humana)".

## Arquivos tocados

- `docs/process/SPRINT_ORDER.md`.
- `docs/process/CHECKLIST_HARDWARE_V2.md`.
- `docs/research/firmware-update-protocol.md`.
- `CHANGELOG.md`.

## Proof-of-work

```bash
grep -c "PROTOCOL_READY" docs/process/SPRINT_ORDER.md
# esperado: >= 2
grep -A 2 "Execuções registradas" docs/process/CHECKLIST_HARDWARE_V2.md | head -5
# esperado: header presente, conteúdo vazio
```

## Fora de escopo

- Executar itens da checklist (fica para o humano).
- Automação de registro de execução (futuro).
