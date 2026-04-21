# CHORE-ACENTO-01 — Corrigir acentuação PT-BR em mensagens e comentários legados

**Tipo:** chore.
**Wave:** fora de wave (dívida técnica).
**Estimativa:** < 1 iteração de executor.
**Dependências:** nenhuma.
**Origem:** achado colateral durante execução de `BUG-IPC-01` (meta-regra 9.7).

---

**Tracking:** issue [#77](https://github.com/AndreBFarias/hefesto/issues/77) — fechada por PR com `Closes #77` no body.

## Contexto

Durante o proof-of-work de `BUG-IPC-01`, a varredura de acentuação periférica
(`~/.config/zsh/scripts/validar-acentuacao.py --paths ...`) detectou 6 violações
pré-existentes de PT-BR em código que NÃO faz parte do diff da sprint corrente.
Protocolo anti-débito (meta-regras 9.5 e 9.7) proíbe fix inline — por isso esta
sprint registra os locais exatos e o Edit canônico.

Invariante violada: `VALIDATOR_BRIEF.md` seção `[CORE] Invariantes de arquitetura`
— "Acentuação PT-BR obrigatória — todo arquivo tocado pela sprint passa por
varredura de acentuação periférica".

---

## Violações detectadas (2026-04-21)

| Arquivo | Linha | Palavra atual | Correção |
|---|---|---|---|
| `src/hefesto/daemon/ipc_server.py` | 203 | `nao eh objeto` | `não é objeto` (dentro de `"payload nao eh objeto"`) |
| `src/hefesto/daemon/ipc_server.py` | 212 | `nao eh objeto` | `não é objeto` (dentro de `"params nao eh objeto"`) |
| `run.sh` | 19 | `nao encontrado` | `não encontrado` (dentro da mensagem de erro) |
| `run.sh` | 90 | `proximo` | `próximo` (citação final de Tolstoi) |
| `tests/unit/test_ipc_server.py` | 192 | `payload nao eh objeto` | `payload não é objeto` (match na asserção) |
| `tests/unit/test_ipc_server.py` | 201 | `params nao eh objeto` | `params não é objeto` (match na asserção) |

Observação: as linhas 203 e 212 do `ipc_server.py` referem-se aos valores
literais em `_json_rpc_error(None, CODE_PARSE_ERROR, "payload nao eh objeto")`
e `_json_rpc_error(req_id, CODE_INVALID_PARAMS, "params nao eh objeto")`. Qualquer
teste em `test_ipc_server.py` que compara essas strings precisa ser atualizado
em conjunto (sincronização N-para-N — meta-regra 9.1).

---

## Critérios de aceite

- [ ] `python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths src/hefesto/daemon/ipc_server.py src/hefesto/utils/xdg_paths.py run.sh tests/unit/test_ipc_server.py tests/unit/test_xdg_paths.py` retorna `Total: 0 violação(ões)`.
- [ ] Varredura ampla `validar-acentuacao.py --paths src/ tests/ docs/ scripts/` não regride (zero novos casos introduzidos).
- [ ] Todos os 298 testes unitários continuam passing.
- [ ] Ruff e anonimato ok.

---

## Fora de escopo

- Qualquer mudança comportamental em `ipc_server.py`, `run.sh` ou nos testes —
  apenas substituição de strings literais.
- Outros arquivos do repo fora da lista acima (exceto se violação correlata
  bloquear o teste — nesse caso estender via sincronização N-para-N).

---

## Notas

Sprint gerada automaticamente pelo executor-sprint ao concluir `BUG-IPC-01`,
respeitando meta-regra 9.7 (zero follow-up acumulado). Nenhuma correção inline
foi feita nos 6 pontos — o executor se manteve estritamente dentro do escopo
autorizado pela spec original.
