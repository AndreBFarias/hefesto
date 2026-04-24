# AUDIT-V23-FORENSIC-01 — Auditoria externa forense pós-v2.3.0

**Tipo:** audit (meta — processo).
**Wave:** pós-V2.3.0 (2026-04-24).
**Estimativa:** L (1.5–2 iterações).
**Modelo sugerido:** opus.
**Dependências:** v2.3.0 MERGED e pushada.

---

**Tracking:** label `type:audit`, `quality`, `ai-task`, `status:ready`.

## Contexto

A base de código evoluiu em alta velocidade: 42 sprints V1.x → 9 sprints V2.0 → 9 sprints V2.1 → 21 sprints V2.2 → 3 sprints V2.3. Muitos arquivos foram tocados múltiplas vezes por autores diferentes (o mesmo Claude em sessões distintas), em contextos diferentes, frequentemente sob pressão de tempo para fechar release. A auditoria `AUDIT-V2-COMPLETE-01` (v2.1.0) foi manual do próprio autor e naturalmente viesada pelo conhecimento do que ele acabou de escrever.

Esta sprint pede uma **auditoria sem viés**. O Claude que executar **NÃO pode** ser o mesmo que entregou as sprints V2.3 (não deve chegar com contexto carregado das decisões). A leitura precisa ser a de um revisor externo que nunca viu o projeto antes — mas com acesso total ao repo.

## Objetivo

Identificar em `src/hefesto/`, `scripts/`, `packaging/`, `.github/workflows/`, `tests/`:

1. **Bugs funcionais** — lógica que parece "quase certa" mas quebra em edge cases óbvios.
2. **Falhas de lógica** — condicionais com resultado sempre igual, laços sem saída, comparações tipadas erradas, race conditions em código concorrente.
3. **Arquivos órfãos** — módulos importados apenas por si mesmos, `__all__` exportando nomes não usados, specs marcadas MERGED cujo código não existe mais, dead code.
4. **Anti-patterns** — try/except que engolem traceback, abstracções inúteis (classe com 1 método usado 1 vez), ABCs sem implementações múltiplas, singletons acidentais.
5. **Tipos inconsistentes** — `Any` ou `object` onde existe tipo real, `# type: ignore` sem motivo claro, protocolos duck-typed sem `Protocol` declarado.
6. **Oportunidades de simplificação** — código duplicado que foi copy-paste entre sprints, config mágica de 3+ parâmetros que poderia virar dataclass.
7. **Otimizações seguras** — trechos que fazem O(n²) quando O(n) é trivial, arquivos I/O síncrono em thread hot, allocations desnecessárias em loops de 60Hz.
8. **Segurança** — input não validado que chega em `subprocess.Popen`, path traversal, permissões de socket, secrets vazando em logs.
9. **Testes ausentes ou frágeis** — funções complexas sem teste, testes que assertam apenas "não levanta" (sem verificar comportamento), testes que dependem de timing ou ordem.
10. **Débito da fase V2.3 especificamente** — os 17 testes adicionados em `test_keyboard_tokens.py` / `test_osk_handler.py` / `test_touchpad_keyboard.py` / `test_input_actions.py` precisam de review crítico: há trechos de `pytest.importorskip` defensivo, mocks frouxos, e o `_FakeMixin` em `test_input_actions.py` usa binding dinâmico de métodos via `__get__` que pode mascarar bugs reais do mixin.

## Regras de execução (anti-viés)

- **NÃO** ler `MEMORY.md` de memória auto, `docs/process/sprints/*.md`, nem `CHANGELOG.md` antes de auditar. Spec e memória enviesam: fazem o revisor "confiar" na narrativa que já existe.
- **NÃO** presumir que decisões foram boas. Avaliar cada uma pelo código final.
- **NÃO** abrir sprints antigas como referência. Se o código tem comentário `# FEAT-X-01`, ignorar o identificador e julgar só o que está escrito.
- **SIM** ler `VALIDATOR_BRIEF.md` uma vez no início — é contrato, não narrativa.
- **SIM** ler `README.md` uma vez — é o que o usuário externo vê.
- **SIM** usar `pytest`, `ruff`, `mypy` como ferramentas de diagnóstico. Se algum desses disser algo, investigar.
- **SIM** usar `git log -p <arquivo>` para entender **quando** algo foi mudado, mas não **por quê** (o porquê precisa estar no código, não no commit).

## Método

### Fase 1 — Inventário (0.25 iter)

Gerar 4 listas brutas:

1. Todos os arquivos `.py` em `src/hefesto/` com LOC + mtime.
2. Todos os arquivos de teste em `tests/unit/` com LOC + coverage atual.
3. Todos os scripts em `scripts/`.
4. Todos os workflows em `.github/workflows/`.

Anotar outliers (>500 LOC por arquivo, cobertura <50%, não tocados há >3 semanas).

### Fase 2 — Leitura sistemática (0.75 iter)

Arquivo por arquivo, nessa ordem:

1. `src/hefesto/core/` — o kernel. Bug aqui cascateia.
2. `src/hefesto/daemon/` — subsystems + lifecycle.
3. `src/hefesto/integrations/` — wrappers de uinput/evdev/subprocess.
4. `src/hefesto/profiles/` — schema + loader + manager.
5. `src/hefesto/app/` — GUI.
6. `src/hefesto/tui/` — TUI.
7. `src/hefesto/cli/` — entrypoints.
8. `src/hefesto/ipc/` e handlers em `daemon/ipc_server.py` — protocolo.
9. `src/hefesto/utils/` — base.
10. `scripts/` — shell scripts + validar-acentuacao.
11. `packaging/` — debian + flatpak + appimage.
12. `.github/workflows/` — CI.
13. `tests/unit/` — suítes (por último, para ver o que testa e o que **não** testa).

Para cada arquivo, anotar achados em formato canônico (ver "Entregável").

### Fase 3 — Consolidação e geração de sprints (0.5 iter)

Agrupar achados por tema e gerar **specs de sprint novas** em `docs/process/sprints/` seguindo o padrão do projeto. Cada sprint nova:

- Tem ID único (prefixo sugerido: `AUDIT-FINDING-<tema>-01..N`).
- Porte estimado (XS/S/M/L/XL).
- Critérios de aceite concretos.
- Proof-of-work runtime.
- Fora de escopo explícito.

A sprint nova **NÃO** faz o fix — só registra o achado e o caminho de correção. O fix vira sprint separada em sessão posterior, com validação individual.

## Entregável final

Arquivo único `docs/process/audits/2026-04-24-audit-v23-forensic.md` (criar diretório se necessário) com:

```markdown
# Auditoria externa pós-v2.3.0 — relatório

## Resumo executivo
N achados totais distribuídos em C categorias. S sprints novas criadas.

## Achados

### 1. [categoria] <título do achado>
- Arquivo: path:linha
- Severidade: bloqueante | alto | médio | baixo | cosmético
- Evidência: trecho literal do código ou saída de ferramenta
- Análise: por que é um problema
- Recomendação: ação específica
- Sprint nova: AUDIT-FINDING-<id> (ou NENHUMA se for edit trivial já aplicado)

### 2. ...
```

E **N sprints novas** escritas em `docs/process/sprints/AUDIT-FINDING-*.md`, adicionadas a `docs/process/SPRINT_ORDER.md` no bloco "Wave V2.3 — follow-up de auditoria".

## Critérios de aceite

- [ ] `docs/process/audits/2026-04-24-audit-v23-forensic.md` existe e tem ≥15 achados distintos (se houver menos, justificar — base muito saudável é um achado em si, registrar como "ok").
- [ ] Cada achado de severidade "bloqueante" ou "alto" tem sprint-nova correspondente em `docs/process/sprints/`.
- [ ] `docs/process/SPRINT_ORDER.md` tem o bloco "Wave V2.3 — follow-up de auditoria" com as sprints listadas.
- [ ] Achados de severidade "baixo"/"cosmético" podem virar checklist agrupado em uma única sprint se for ≥5 itens no mesmo arquivo/tema.
- [ ] Nenhum fix direto foi aplicado — a sprint de auditoria só diagnostica. (Exceção: typo trivial em comentário ou string de log pode ser corrigido inline com nota no relatório.)
- [ ] Relatório cita `ruff`, `mypy`, `pytest --cov` com exit codes e contagens; se algum recusar rodar, log literal do erro.
- [ ] Working tree limpo ao final OU o commit único é `audit: AUDIT-V23-FORENSIC-01 — relatório + N sprints colaterais`.

## Proof-of-work

```bash
# Antes:
ls docs/process/audits/ 2>/dev/null | wc -l  # 0 ou diretório ausente

# Executar a auditoria (sessão humana comandada).

# Depois:
ls docs/process/audits/2026-04-24-audit-v23-forensic.md  # existe
wc -l docs/process/audits/2026-04-24-audit-v23-forensic.md  # >300 linhas
ls docs/process/sprints/AUDIT-FINDING-*.md | wc -l  # >=3 (prováveis)
grep -c "AUDIT-FINDING" docs/process/SPRINT_ORDER.md  # >=3
```

## Fora de escopo

- **Fixes diretos** em qualquer arquivo de `src/` ou `tests/` — a sprint só audita.
- Refatorações arquiteturais grandes (ADR nova, split de módulos) — viram sprints separadas.
- Reescrita de testes existentes — só anotar onde a cobertura é frágil.
- Decisões de produto (features novas, mudança de escopo) — fora de auditoria.
- Dependency upgrade (pydantic, structlog, typer bump) — virar sprint separada se achado.

## Notas para quem executar

- Este spec é meta-processo: a **forma** da auditoria importa tanto quanto o resultado. Respeitar as regras anti-viés da seção "Regras de execução" é condição de aceite.
- A auditoria AUDIT-V2-COMPLETE-01 (2026-04-23) serviu de base para fixes na v2.1.0. Esta é análoga mas para v2.3 — a ideia é repetir a cadência "release → auditoria externa → próxima wave de fixes".
- Se durante a auditoria o reviewer identificar que a própria estrutura de processo (SPRINT_ORDER, VALIDATOR_BRIEF, ADRs) tem problemas, abrir achado meta na seção "Processo" do relatório.

# "O olho que não vê, o coração não lamenta — mas o bug continua em produção."
