# BUG-DEB-MISSING-DEPS-01 — .deb não declara deps Python de runtime

**Tipo:** bug (packaging).
**Wave:** V2.2 — achado colateral da re-publicação v2.1.0 via workflow_dispatch.
**Estimativa:** 0.25 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:bug`, `P0-urgent`, `packaging`, `deb`, `ai-task`, `status:ready`.

## Sintoma

Run `24860669570` (2026-04-23, release v2.1.0 via dispatch) falhou no job `Smoke install do .deb` ao validar o binário `hefesto`:

```
File "/usr/lib/python3/dist-packages/hefesto/cli/cmd_emulate.py", line 16, in <module>
    from rich.console import Console
ModuleNotFoundError: No module named 'rich'
```

`packaging/debian/control` declara `python3-typer`, `python3-structlog`, `python3-pydantic`, `python3-platformdirs`, mas **não** declara `python3-rich`, `python3-evdev`, `python3-xlib` nem `python3-filelock` — todas runtime deps declaradas em `pyproject.toml`.

Consequência: `sudo apt install ./hefesto_*.deb` instala pacote, mas qualquer comando CLI/GUI quebra no primeiro import.

## Decisão

Adicionar as 4 deps faltantes em `Depends` do control. Sem empacotar como pip-only — todos os 4 têm pacotes Debian/Ubuntu canônicos:
- `python3-rich` (rich ≥13)
- `python3-evdev`
- `python3-xlib`
- `python3-filelock`

## Critérios de aceite

- [ ] `packaging/debian/control` lista as 4 deps extras no campo `Depends:`.
- [ ] `bash scripts/build_deb.sh` localmente gera `.deb` válido.
- [ ] Push re-dispara release e `Smoke install do .deb` verde.
- [ ] Gates canônicos.

## Arquivos tocados

- `packaging/debian/control` (+4 deps).

## Proof-of-work

```bash
bash scripts/build_deb.sh
# local: pacote gerado

# validação em CI:
gh workflow run release.yml -f tag=v2.1.0
gh run watch $(gh run list --workflow release.yml --limit 1 --json databaseId --jq '.[0].databaseId')
```

## Fora de escopo

- Migrar para `dh_python3`/`dpkg-buildpackage` (refactor grande).
- Empacotar `pydualsense` como `.deb` (upstream pip-only).
