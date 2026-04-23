# META-LESSONS-V21-BRIEF-01 — Registrar 6 lições do ciclo V2.1 no BRIEF

**Tipo:** meta (processo).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 0.5 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:meta`, `process`, `ai-task`, `status:ready`.

## Contexto

Fim do ciclo V2.1 (2026-04-23), o executor (Opus) entregou uma "bronca honesta" com 6 falhas de processo observadas durante os 9 sprints. Cada uma é acionável como regra permanente no `VALIDATOR_BRIEF.md` para que planejador/executor futuros não repitam.

Origem: mensagem final do release v2.1.0, consolidada em `docs/process/discoveries/2026-04-23-auditoria-v2.md` (já existente) e na mensagem do usuário que pediu "isso precisa virar sprints".

## As 6 lições

1. **L-21-1: Spec com gate massivo exige dry-run ANTES do spec.** Sprint 7 previa 3-10 falsos-positivos; explodiu em 267. Se uma sprint instala um gate novo (pre-commit, CI check, linter), rodar o dry-run contra a base inteira antes de escrever o spec e dimensionar a whitelist/correção em massa com número real.
2. **L-21-2: Bug vira sprint só após reprodução em árvore limpa.** BUG-VALIDAR-ACENTUACAO-FIX-GLYPHS-01 foi escrito baseado em diff sujo do working tree, sem `git stash` + teste isolado. Regra: antes de abrir spec de bug, rodar `git stash && <reprodução>` e anexar o diff do comando-bug isolado ao spec.
3. **L-21-3: Ler o código-chave ANTES de escrever spec.** PROFILE-DISPLAY-NAME-01 assumiu premissa falsa (que `Profile.name` era ASCII). Regra: todo spec que toca um módulo deve listar em "Contexto" os trechos lidos do módulo (arquivo:linha) que confirmam a premissa. Se não foi lido, planejador não pode escrever sobre ele.
4. **L-21-4: Toda sessão nova valida `.venv` antes de rodar sprints.** AUDIT-V2-COMPLETE-01 rodou sem `.venv` pronto e o auditor confiou em "último baseline passou". Regra: todo executor começa com `scripts/dev-setup.sh` (a ser criado em CHORE-VENV-BOOTSTRAP-CHECK-01). Se script não existe, primeiro passo é `pip install -e ".[dev]" + .venv/bin/pytest --collect-only` para confirmar que o ambiente está vivo.
5. **L-21-5: Paralelo de subagents só se pool <50% usado.** 4 subagents em paralelo com pool em 80% deram 2 rate-limited e zero ganho de velocidade. Regra: antes de disparar N subagents, estimar tokens/minuto ativos (sessão + agents em voo). Se pool >50%, serializar.
6. **L-21-6: "Protocolo escrito" ≠ "Executado".** HARDWARE-VALIDATION-PROTOCOL-01 foi marcada MERGED sem item nenhum executado — ninguém com hardware plugou o controle para validar. Regra: sprints que produzem só documento/protocolo ganham status distinto `PROTOCOL_READY` (não `MERGED`) até um humano executar ao menos 1 item. Conta em relatório de release como "dívida de execução".

## Decisão

Adicionar seção nova `[PROCESS] Lições acumuladas por ciclo` em `VALIDATOR_BRIEF.md` logo após `[CORE] Armadilhas conhecidas`. Cada lição tem ID `L-<wave>-<n>`, one-liner, regra, e sprint de origem para rastro.

Planejador/executor/validador passam a ler esta seção como trilho. Revisão em cada release: lições violadas geram achado na auditoria.

## Critérios de aceite

- [ ] `VALIDATOR_BRIEF.md` ganha seção `## [PROCESS] Lições acumuladas por ciclo` com as 6 lições L-21-1 a L-21-6.
- [ ] Formato de cada lição: `**L-21-N: <nome curto>.** <contexto>. **Regra:** <regra acionável>. **Origem:** <sprint>.`.
- [ ] Índice da seção cita que a cada release o auditor deve revisar a lista e marcar lições violadas.
- [ ] Gates canônicos verdes.

## Arquivos tocados

- `VALIDATOR_BRIEF.md`.

## Proof-of-work

```bash
python3 scripts/validar-acentuacao.py --check-file VALIDATOR_BRIEF.md
# esperado: zero erros
grep -c "^### L-21-" VALIDATOR_BRIEF.md
# esperado: 6
```

## Fora de escopo

- Refatorar seções pré-existentes do BRIEF.
- Criar lições para V1.x ou V2.0 retroativamente (o ciclo onde foram descobertas é V2.1; lições V2.0 seriam arqueologia).
