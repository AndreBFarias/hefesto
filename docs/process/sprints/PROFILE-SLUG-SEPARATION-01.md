# PROFILE-SLUG-SEPARATION-01 — Separar slug filesystem do display `Profile.name`

**Tipo:** feat (bug latente + infraestrutura).
**Wave:** V2.1 — Bloco B.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma. Substitui PROFILE-DISPLAY-NAME-01 (SUPERSEDIDA).

---

**Tracking:** issue a criar. Label: `type:feature`, `P1-high`, `ai-task`, `status:ready`.

## Contexto

Estado real descoberto em 2026-04-23 após sprint 6 (`QUICKSTART-PROFILES-SCREENSHOT-01`):

- **JSONs default** em `assets/profiles_default/*.json` têm `"name"` acentuado (`"Ação"`, `"Navegação"`, `"FPS"`, etc.).
- **Filename** é ASCII (`acao.json`, `navegacao.json`) — não gerado pelo código, só convenção humana.
- `Profile.name` validator (`src/hefesto/profiles/schema.py:120-127`) só rejeita `/`, `..`, `os.sep` — aceita qualquer outra string incluindo acentuação.
- `_profile_path(name)` (`src/hefesto/profiles/loader.py:31-32`) retorna `f"{name}.json"` literalmente.
- **Consequência latente**: se usuário cria perfil via GUI com display `"Ação"`, `save_profile` grava `~/.config/hefesto/profiles/Ação.json`. Com os defaults em `acao.json` já presentes (cópia do `install.sh` ou `first_run_seed`), passa a existir **dois perfis** ocupando o mesmo espaço conceitual, cada um sob filename diferente. Próxima edição pode abrir o errado. Collision silenciosa.
- GUI mostra `name` direto na treestore (screenshot da sprint 6 confirmou — "Ação" visível).

## Decisão

Manter `name` como display canônico acentuado. **Adicionar função `slugify()`** que deriva filename ASCII do name. `save_profile` e `delete_profile` passam a usar slug derivado. `load_profile` aceita slug OU name (busca adaptativa).

### Função `slugify`

Adicionar em `src/hefesto/profiles/slug.py` (módulo novo):

```python
"""Normalização de `Profile.name` para filename filesystem-safe.

Regras:
- Unicode NFKD + remoção de combining marks → `"Ação"` → `"Acao"`.
- Lowercase → `"acao"`.
- Espaço e traço → underscore → `"Meu Perfil"` → `"meu_perfil"`.
- Remove tudo que não for [a-z0-9_] → mantém apenas ASCII alfanumérico + underscore.
- Colapsa underscores consecutivos → `"a__b"` → `"a_b"`.
- Trim de underscores de borda → `"_foo_"` → `"foo"`.
- Resultado não-vazio obrigatório — raise ValueError se input não produz slug válido.
"""
from __future__ import annotations

import re
import unicodedata


_NON_ALNUM_UNDERSCORE = re.compile(r"[^a-z0-9_]")
_MULTI_UNDERSCORE = re.compile(r"_+")


def slugify(name: str) -> str:
    if not name or not name.strip():
        raise ValueError("slugify: nome vazio não tem slug")
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    lowered = ascii_only.lower()
    dashes_underscored = lowered.replace("-", "_").replace(" ", "_")
    alnum = _NON_ALNUM_UNDERSCORE.sub("", dashes_underscored)
    collapsed = _MULTI_UNDERSCORE.sub("_", alnum).strip("_")
    if not collapsed:
        raise ValueError(f"slugify: {name!r} não produz slug válido")
    return collapsed
```

Casos de teste obrigatórios:

| Input | Output |
|---|---|
| `"Ação"` | `"acao"` |
| `"Navegação"` | `"navegacao"` |
| `"FPS"` | `"fps"` |
| `"Meu Perfil"` | `"meu_perfil"` |
| `"Corrida Máxima"` | `"corrida_maxima"` |
| `"São José"` | `"sao_jose"` |
| `"über"` | `"uber"` |
| `"a/b"` | `"ab"` (barra removida) |
| `""` | raise ValueError |
| `"   "` | raise ValueError |
| `"???"` | raise ValueError (produz vazio) |
| `"_foo_bar_"` | `"foo_bar"` (trim) |
| `"a__b"` | `"a_b"` (colapsa) |

### Mudanças no `loader.py`

```python
from hefesto.profiles.slug import slugify

def _profile_path(identifier: str | Profile) -> Path:
    """Resolve filename a partir de slug direto ou de Profile."""
    if isinstance(identifier, Profile):
        return profiles_dir(ensure=True) / f"{slugify(identifier.name)}.json"
    return profiles_dir(ensure=True) / f"{identifier}.json"


def load_profile(identifier: str) -> Profile:
    """Carrega por slug direto ou por display name.
    
    Ordem de busca:
    1. `<identifier>.json` (assume que identifier já é slug).
    2. `<slugify(identifier)>.json` (se identifier era display name).
    3. Varredura fallback: itera diretório buscando `profile.name` cujo slug bate.
    """
    direct = profiles_dir() / f"{identifier}.json"
    if direct.exists():
        with FileLock(str(_lock_path(direct))):
            raw = json.loads(direct.read_text(encoding="utf-8"))
        return Profile.model_validate(raw)
    
    slug = slugify(identifier)
    slugged = profiles_dir() / f"{slug}.json"
    if slugged.exists():
        with FileLock(str(_lock_path(slugged))):
            raw = json.loads(slugged.read_text(encoding="utf-8"))
        return Profile.model_validate(raw)
    
    # Fallback: varredura
    for path in profiles_dir().glob("*.json"):
        with FileLock(str(_lock_path(path))):
            raw = json.loads(path.read_text(encoding="utf-8"))
        profile = Profile.model_validate(raw)
        if slugify(profile.name) == slug:
            return profile
    
    raise FileNotFoundError(f"perfil não encontrado: {identifier}")


def save_profile(profile: Profile) -> Path:
    path = _profile_path(profile)  # usa slugify(profile.name) internamente
    payload = profile.model_dump(mode="json")
    with FileLock(str(_lock_path(path))):
        _atomic_write_json(path, payload)
    return path


def delete_profile(identifier: str) -> None:
    # Busca-e-deleta: resolve o path como load_profile faz
    profile = load_profile(identifier)
    path = _profile_path(profile)
    with FileLock(str(_lock_path(path))):
        path.unlink()
```

### Collision detection

Se duas chamadas de `save_profile` produzirem o mesmo slug (ex.: `"Ação"` e `"ação"` — ambas slugificam para `"acao"`), a segunda **sobrescreve** a primeira silenciosamente. Mitigação: validator em `Profile`:

```python
@field_validator("name")
@classmethod
def _name_nonempty(cls, value: str) -> str:
    if not value or not value.strip():
        raise ValueError("name não pode ser vazio")
    if "/" in value or ".." in value or os.sep in value:
        raise ValueError(f"name contém caractere inválido: {value!r}")
    # Garante que slugify funciona (levanta se não produzir slug válido)
    from hefesto.profiles.slug import slugify
    slugify(value)
    return value
```

A **detecção de colisão entre perfis existentes** fica a cargo do loader: em `load_all_profiles()`, se dois perfis produzem mesmo slug, log warning + lista ambos (decisão do usuário qual manter via GUI — fora do escopo aqui).

### Migração transparente

Perfis existentes do usuário em `~/.config/hefesto/profiles/`:
- Não renomear silenciosamente. Renomear arquivo em disco é ação destrutiva.
- `load_all_profiles()` aceita qualquer filename — ignora divergência slug vs filename.
- `save_profile(loaded_profile)` **pode** acabar gravando em arquivo novo (se filename original divergia do slug). Comportamento aceitável: velho arquivo fica até delete explícito.
- Opcional: utility `migrate_profile_filename(path: Path) -> Path | None` (não chamada automaticamente) renomeia arquivo divergente.

### IPC

`profile.list` continua retornando lista de `{name, priority, match_summary, ...}`. Não adiciona campo novo — `name` já é o display.

`profile.switch`, `profile.delete` aceitam tanto slug quanto display name (graças ao novo `load_profile`).

### GUI

**Zero mudança visual** — a GUI já mostra `name` acentuado. O único impacto é que `save_profile` agora grava arquivo com filename consistente, evitando duplicação silenciosa.

## Critérios de aceite

- [ ] `src/hefesto/profiles/slug.py` criado com função `slugify(name)` + docstring + validation conforme tabela.
- [ ] `src/hefesto/profiles/loader.py`: `_profile_path` aceita `str | Profile`; `load_profile` faz busca adaptativa; `save_profile` usa slugify; `delete_profile` resolve via load_profile.
- [ ] `src/hefesto/profiles/schema.py`: validator `_name_nonempty` adicionalmente garante que `slugify(name)` não levanta (previne `name="???"` passar).
- [ ] Nenhum JSON default alterado (defaults já estão corretos).
- [ ] Teste `tests/unit/test_slug.py` (novo, ≥ 13 casos da tabela).
- [ ] Teste `tests/unit/test_profile_loader.py` estendido:
  - `test_save_profile_usa_slug`: `Profile(name="Ação")` → grava `acao.json`.
  - `test_load_profile_por_slug`: `load_profile("acao")` → retorna `Profile(name="Ação")`.
  - `test_load_profile_por_display`: `load_profile("Ação")` → retorna mesmo.
  - `test_load_profile_fallback_scan`: filename arbitrário com name="Ação", `load_profile("Ação")` encontra via varredura.
  - `test_delete_profile_resolve_slug`: `delete_profile("Ação")` remove `acao.json`.
- [ ] Teste `tests/unit/test_profile_manager.py` estendido: `profile.switch` via IPC aceita tanto slug quanto display.
- [ ] `.venv/bin/pytest tests/unit -q` verde (espera ≥ 941 passed; baseline 928 + 13 de slug + 4 de loader).
- [ ] `.venv/bin/ruff check src/ tests/` verde.
- [ ] `.venv/bin/mypy src/hefesto/profiles` verde.
- [ ] `./scripts/check_anonymity.sh` OK.
- [ ] `python3 scripts/validar-acentuacao.py --all` OK (hook strict).
- [ ] Smoke USB+BT verde.

## Arquivos tocados

- `src/hefesto/profiles/slug.py` (novo, ≤ 50 linhas)
- `src/hefesto/profiles/loader.py` (editar)
- `src/hefesto/profiles/schema.py` (validator estendido)
- `tests/unit/test_slug.py` (novo)
- `tests/unit/test_profile_loader.py` (estender)
- `tests/unit/test_profile_manager.py` (estender opcional)

## Proof-of-work runtime

```bash
.venv/bin/pytest tests/unit/test_slug.py tests/unit/test_profile_loader.py tests/unit/test_profile_manager.py -v
.venv/bin/pytest tests/unit -q
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto/profiles
./scripts/check_anonymity.sh
python3 scripts/validar-acentuacao.py --all

HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt

# Teste end-to-end: criar perfil via IPC, confirmar filename ASCII
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.daemon.main &
DPID=$!
sleep 2
# Simular criação via save_profile direto
.venv/bin/python -c "
from hefesto.profiles.schema import Profile
from hefesto.profiles.loader import save_profile
from hefesto.profiles.schema import MatchAny
p = Profile(name='Ação Teste Slugify', match=MatchAny(type='any'))
path = save_profile(p)
print(f'Salvou em: {path.name}')
assert path.name == 'acao_teste_slugify.json', f'filename errado: {path.name}'
print('OK: slug derivado corretamente')
path.unlink()
"
kill $DPID
```

## Notas para o executor

- **Não renomear perfis existentes do usuário**. `~/.config/hefesto/profiles/` pode conter arquivos que o usuário editou manualmente com filenames arbitrários. Sprint não mexe com eles — só garante que **novos** saves usam slug.
- **Backwards compat do `load_profile`**: código existente chama `load_profile("acao")` (slug) e outros possivelmente `load_profile("Ação")` (display). Ambos devem funcionar. Varrer o codebase com `rg "load_profile\(" src/` pra inventariar calls.
- **IPC `profile.switch`**: provavelmente aceita `{"name": "acao"}` hoje. Depois desta sprint, também aceita `{"name": "Ação"}`. Teste ambos.
- **Validator de `Profile.name`**: adicionar call a `slugify()` no validator captura nomes exóticos que não produzem slug válido (só emoji, só símbolos). Mantém garantia filesystem-safe.
- **GUI: nenhuma mudança**. Treestore já usa `profile.name` direto — continua funcionando.
- **Perfil `fallback`**: slug == name == `"fallback"`. Sem mudança. Invariante "priority: -1000 + match universal" preservada.

## Fora de escopo

- Renomear automaticamente arquivos divergentes do usuário (ação destrutiva).
- GUI para resolver colisões quando 2 perfis slugificam igual.
- Importar/exportar com slug explícito no payload.
- Migrar JSONs default em `assets/profiles_default/` — já estão com filename canônico.
- Quebrar IPC v1 (`profile.switch` segue aceitando slug ASCII como antes).
