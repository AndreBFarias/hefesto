# AUDIT-FINDING-PROFILE-PATH-TRAVERSAL-01 — Sanitizar `identifier` em `load_profile` contra path traversal

**Origem:** achado 4 de `docs/process/audits/2026-04-24-audit-v23-forensic.md`.
**Porte:** S (≤3h). **Severidade:** alto (defesa em profundidade; risco real baixo por socket 0600).
**Tracking:** label `type:security`, `ai-task`, `status:ready`.

## Contexto

`src/hefesto/profiles/loader.py::load_profile` constrói `Path` via `directory / f"{identifier}.json"`. `pathlib.Path` semantics: se identifier começa com `/` ou `\`, o concat descarta o diretório à esquerda (escape absoluto). Se identifier contém `..`, escape relativo após `.resolve()`. Validação de `Profile.name` no schema rejeita `/` e `..` (OK para dados JSON), mas `load_profile(identifier)` é chamado diretamente pelo IPC handler `_handle_profile_switch` (`ipc_server.py:270-278`) que apenas valida `isinstance(name, str) and name`. Socket IPC é 0600 em `$XDG_RUNTIME_DIR`, então só UID do user conecta — ataque real exige atacante já ter UID, baixa probabilidade. Porém: `_json_rpc_error(req_id, CODE_INTERNAL, str(exc))` pode leak path absoluto via ValidationError em `str(exc)`.

## Objetivo

Adicionar sanitização no boundary (IPC handler ou `load_profile`). Rejeitar identifier com `/`, `\`, `..`, ou caracteres nulos. Opção complementar: `resolved_path.is_relative_to(profiles_dir())` check após concat — rejeita qualquer escape que `.resolve()` revele.

## Critérios de aceite

- [ ] `load_profile` valida identifier contra regex `^[A-Za-z0-9_.-]+$` (ou equivalente) antes do concat. Levanta `ValueError` se fora.
- [ ] Alternativa: após `directory / f"{identifier}.json"`, chamar `.resolve()` e confirmar `is_relative_to(directory.resolve())`. Se escapa, levanta `ValueError`.
- [ ] `_dispatch` em `ipc_server.py:262` normaliza `str(exc)` para não vazar path completo em CODE_INTERNAL — filtrar o detalhe de ValidationError ou usar `str(type(exc).__name__)` + mensagem genérica.
- [ ] Testes em `tests/unit/test_profile_loader.py`:
  - `test_load_profile_rejeita_path_absoluto` — identifier=`/etc/passwd` → raise ValueError.
  - `test_load_profile_rejeita_parent_dir` — identifier=`../../etc/passwd` → raise ValueError.
  - `test_load_profile_rejeita_backslash` — identifier=`..\\etc\\passwd` → raise ValueError.
  - `test_load_profile_rejeita_null_byte` — identifier=`foo\x00bar` → raise ValueError.
- [ ] Teste adicional em `tests/unit/test_ipc_server.py`: handler `profile.switch` com nome malicioso retorna erro JSON-RPC sem leak de path no `message`.
- [ ] Suite segue verde; ruff + mypy limpos.

## Proof-of-work

```bash
bash scripts/dev-setup.sh
.venv/bin/pytest tests/unit/test_profile_loader.py tests/unit/test_ipc_server.py -v -q
.venv/bin/pytest tests/unit -q --no-header
.venv/bin/ruff check src tests
.venv/bin/mypy src/hefesto
# Runtime:
printf '{"jsonrpc":"2.0","id":1,"method":"profile.switch","params":{"name":"../../etc/passwd"}}\n' \
  | nc -U $XDG_RUNTIME_DIR/hefesto/hefesto.sock
# Esperado: erro JSON-RPC com "profile não encontrado" ou "identifier inválido",
# NÃO com stacktrace revelando path absoluto
```

## Fora de escopo

- Revisar `_handle_profile_apply_draft` para paths em outros campos — só `name` é usado como identifier de arquivo.
- Mudar permissões do socket IPC — já é 0600.
- Assinar perfis / validar origem — fora de escopo do threat model atual.
