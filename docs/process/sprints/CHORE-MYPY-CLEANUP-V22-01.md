# CHORE-MYPY-CLEANUP-V22-01 — Zerar mypy errors em `src/hefesto`

**Tipo:** chore (débito técnico).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1-2 iterações.
**Dependências:** BUG-CI-RELEASE-MYPY-GATE-01 (débito só destravou release; agora fechar).

---

**Tracking:** label `type:chore`, `typecheck`, `ai-task`, `status:ready`.

## Contexto

Sprint BUG-CI-RELEASE-MYPY-GATE-01 moveu `mypy` para job informacional em `ci.yml` com `continue-on-error: true`. Prazo interno: 30 dias para tornar gate rígido.

Categorias de erro no último run `release.yml@v2.1.0`:

1. **GTK3 subclasses** (`stick_preview_gtk.py`, `button_glyph.py`): `Class cannot subclass "DrawingArea" (has type "Any")` + `Unused "type: ignore"`. Correção: remover `type: ignore` e adicionar `GObject`/`Gtk` como `# type: ignore[import]` ou configurar stubs.
2. **Return Any de GTK dialogs** (`gui_dialogs.py:55,82,143`): `Returning Any from function declared to return "str | None"/"bool"`. Correção: `cast()` explícito ou tipar retorno com `Any`.
3. **Union in tuple** (`draft_config.py:144,148`): `list[int] | list[list[int]]` não satisfaz `Iterable[int]`. Correção: branch explícito via `is_nested` + cast.
4. **Wayland portal type: ignore unused** (`wayland_portal.py:32,33,59`): remover.
5. **poll.py type: ignore unused** (`subsystems/poll.py:82,90`): remover.
6. **Logger kwargs** (`backend_pydualsense.py:182`): `bits`/`bitmask` não são kwargs do `Logger.debug`. Correção: passar como dict via `extra=` ou usar f-string.
7. **plugin_api** (`loader.py:26,54,74`): `list` sem generic arg; `append(object)` em `list[Plugin]`; `type: ignore` unused. Correção trivial.

Todos são baixo risco — nada muda semântica de runtime.

## Decisão

Fix cirúrgico por categoria. Não refatorar enquanto corrige. Cada commit endereça 1-2 categorias para facilitar revisão/reversão.

## Critérios de aceite

- [ ] `mypy src/hefesto` retorna 0 errors.
- [ ] `ci.yml` job `typecheck` perde `continue-on-error: true` — vira gate rígido.
- [ ] README / seção Contribuição menciona gate mypy ativo.
- [ ] Gates canônicos (pytest, ruff, anonimato, acento, smoke).

## Arquivos tocados

- ~8 arquivos listados nas categorias acima.
- `.github/workflows/ci.yml`.

## Proof-of-work runtime

```bash
.venv/bin/mypy src/hefesto
# esperado: "Success: no issues found in N files"

.venv/bin/pytest tests/unit -q
.venv/bin/ruff check src/ tests/
```

## Fora de escopo

- Tipar código novo além do mínimo.
- Adotar pyright.
- Type stubs customizados para pydualsense.
