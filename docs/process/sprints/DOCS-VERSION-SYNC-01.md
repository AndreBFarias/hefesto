# DOCS-VERSION-SYNC-01 — Sincronizar versão do projeto em README, docs e memória

**Tipo:** docs (limpeza).
**Wave:** V1.1 — fase 5.
**Estimativa:** XS (15min).
**Dependências:** nenhuma.

---

**Tracking:** issue a criar.

## Contexto

Auditoria em 2026-04-22 revelou:

- `README.md:8` diz `Versão: 0.1.0 (alpha)`.
- `CHANGELOG.md` e tag `v1.0.0` já cravaram **1.0.0** em 2026-04-21.
- `pyproject.toml` tem a versão real (fonte de verdade).
- Memória `project_estado_atual.md` do Claude refletia HEAD antigo `13e1e0f`; real é `92efe22` (em 2026-04-22 antes da sprint BUG-MULTI-INSTANCE-01).

Inconsistência confunde qualquer leitor novo e o próprio Claude em futuras sessões.

## Decisão

1. `README.md` header passa a ler versão do `pyproject.toml` — **ou** é editado manualmente a cada bump (opção simples; escolher pelo pragmatismo).
2. Convenção: em bump de major/minor, atualizar README + CHANGELOG + memoria Claude + HISTORICO_V1 na mesma PR.
3. Criar script `scripts/check_version_consistency.py` que falha se README != pyproject.toml. Chamar no CI.

## Critérios de aceite

- [ ] `README.md`:
  - Cabeçalho `Versão: 1.0.0` (sem `(alpha)`).
  - `Estado: runtime validado em Pop!_OS 22.04 com DualSense USB e BT`.
  - Seção "Próximos passos" atualizada com link pra `docs/process/SPRINT_ORDER.md`.
- [ ] `scripts/check_version_consistency.py` (novo):
  ```python
  import sys, re, tomllib
  cfg = tomllib.loads(open("pyproject.toml", "rb").read().decode())
  expected = cfg["project"]["version"]
  readme = open("README.md").read()
  match = re.search(r"Versão:\s*(\S+)", readme)
  if not match or match.group(1) != expected:
      print(f"FAIL: README version '{match and match.group(1)}' != pyproject '{expected}'")
      sys.exit(1)
  print("OK")
  ```
- [ ] `.github/workflows/ci.yml`: novo job `version-check` roda esse script.
- [ ] Atualizar memória Claude:
  - `~/.claude/projects/<slug>/memory/project_estado_atual.md`: HEAD atual, sprints mergeadas (incluir BUG-MULTI-INSTANCE-01), PRs abertos.
  - `project_sprints_pendentes.md`: tabela atualizada.

## Arquivos tocados

- `README.md`
- `scripts/check_version_consistency.py` (novo)
- `.github/workflows/ci.yml`
- `~/.claude/projects/*/memory/project_estado_atual.md` (fora do repo — arquivo separado)
- `~/.claude/projects/*/memory/project_sprints_pendentes.md`

## Notas para o executor

- `tomllib` é stdlib Python 3.11+. Se CI roda 3.10, instalar `tomli` ou usar `tomli` com fallback:
  ```python
  try:
      import tomllib
  except ImportError:
      import tomli as tomllib
  ```
- Memória Claude NÃO é commit do repo — é arquivo local da sessão. Atualizar na sessão apropriada.
