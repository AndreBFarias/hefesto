# Diário de descobertas

Pasta de memória viva do projeto. Cada arquivo é uma jornada fechada — sintoma encontrado, hipóteses testadas, causa confirmada, solução aplicada. Complementa ADRs (que registram decisões) e commits (que registram mudanças). Aqui fica o **porquê da surpresa**.

## Convenção de nomeação

`YYYY-MM-DD-kebab-slug.md`

Exemplos:
- `2026-04-20-hotfix-1-pydualsense-state-attrs.md`
- `2026-04-20-hotfix-2-hid-playstation-kernel-conflict.md`
- `2026-04-22-udp-rate-limiter-eviction-bug.md`

A data é da **descoberta**, não da solução. Se a investigação durar dias, o arquivo vai crescendo até fechar.

## Quando criar

Sempre que aparecer algo que:
- Surpreendeu (comportamento diferente do esperado).
- Exigiu mais de uma hipótese pra entender.
- Revelou restrição não-óbvia do ambiente (kernel, distro, driver).
- Bloqueou uma sprint e abriu issue nova.
- Destruiu uma premissa de ADR ou de um patch V2/V3.

Não criar para:
- Bugs triviais (commit resolve, sem jornada).
- Refatorações de estilo.
- Decisões já cobertas por ADR.

## Template

Ver `TEMPLATE.md` na mesma pasta.

## Relação com meta-regras

- **9.6 (evidência empírica > hipótese do revisor)**: os sintomas e logs literais em cada jornada são prova crua, não opinião.
- **9.7 (zero follow-up acumulado)**: cada descoberta que bloqueia vira issue nova — o arquivo aponta pra ela.
- **9.8 (validação runtime-real)**: descobertas só existem quando a sprint passou por runtime-real (unit tests cegos não revelam conflito de kernel).

## Índice

Atualize esta lista ao fechar cada jornada:

| Data       | Arquivo                                                      | Status     | Issues relacionadas |
|------------|--------------------------------------------------------------|------------|---------------------|
| 2026-04-20 | `2026-04-20-hotfix-1-pydualsense-state-attrs.md`             | Resolvida  | #48                 |
| 2026-04-20 | `2026-04-20-hotfix-2-hid-playstation-kernel-conflict.md`     | Resolvida  | #49                 |
| 2026-04-20 | `2026-04-20-infra2-capture-pipeline.md`                      | Resolvida  | #29, #54 (follow-up)|
| 2026-04-20 | `2026-04-20-w5-1-tui-textual-proof-of-work.md`               | Resolvida  | #11                 |
| 2026-04-20 | `2026-04-20-infra1-polling-benchmark.md`                     | Resolvida  | #27                 |
