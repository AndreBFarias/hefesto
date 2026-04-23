# CHORE-VERSION-SYNC-GATE-01 — Gate CI que detecta drift entre fallback de __init__.py e pyproject.toml

**Tipo:** chore (qualidade + regressão).
**Wave:** V2.2.1 ou V2.3 — flexível; colateral do BUG-APPIMAGE-VERSION-NAME-01.
**Estimativa:** XS (0.25 iteração).
**Dependências:** BUG-APPIMAGE-VERSION-NAME-01 (MERGED).

---

**Tracking:** label `type:chore`, `ci`, `quality`, `ai-task`, `status:ready`.

## Contexto

BUG-APPIMAGE-VERSION-NAME-01 revelou que `src/hefesto/__init__.py` tinha `__version__ = "1.0.0"` hardcoded por ~3 releases sem ser bumpado, enquanto `pyproject.toml` avançava até 2.2.0. O fix aplicado torna `__version__` dinâmico via `importlib.metadata.version("hefesto")` com **fallback** hardcoded para casos onde o pacote é instalado sem metadata (ex: `.deb` via `cp -r`, não `pip install`).

O fallback é a "última linha de defesa" — se ele divergir de `pyproject.toml`, usuários de `.deb` verão versão errada silenciosamente. O bug original volta pela janela.

## Decisão

Novo job `version-sync` em `ci.yml` que falha se o fallback de `__init__.py` divergir de `pyproject.toml`. Pequena regex OK — não precisa parser AST completo.

```yaml
version-sync:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Verificar sync fallback vs pyproject
      run: |
        PYPROJECT_VERSION=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
        FALLBACK_VERSION=$(python3 -c "
        import re
        src = open('src/hefesto/__init__.py').read()
        m = re.search(r'__version__\s*=\s*\"([^\"]+)\"', src)
        print(m.group(1) if m else '')
        ")
        if [ "$PYPROJECT_VERSION" != "$FALLBACK_VERSION" ]; then
          echo "::error::Fallback desatualizado: __init__.py=$FALLBACK_VERSION mas pyproject.toml=$PYPROJECT_VERSION"
          exit 1
        fi
        echo "Sync OK: $PYPROJECT_VERSION"
```

Alternativa mais simples (se regex parecer frágil): importar `hefesto` no CI e comparar com pyproject.

## Critérios de aceite

- [ ] `.github/workflows/ci.yml` ganha job `version-sync` paralelo aos outros.
- [ ] Job falha com mensagem clara se fallback ≠ pyproject.
- [ ] Job passa no baseline atual (ambos em 2.2.0).
- [ ] Documentação `docs/process/RELEASE_CHECKLIST.md` (se existir) menciona bump do fallback junto com pyproject.

## Arquivos tocados

- `.github/workflows/ci.yml`.
- Opcionalmente `docs/process/RELEASE_CHECKLIST.md`.

## Proof-of-work

```bash
# 1. Sync atual
grep "^version" pyproject.toml
grep "__version__ = " src/hefesto/__init__.py

# 2. Intencionalmente dessyncar → pipe local do workflow → deve falhar
# (não aplicar; só demo conceitual)

# 3. act para rodar ci.yml local (se instalado) OU push para branch teste
```

## Fora de escopo

- Remover fallback totalmente. `.deb` via `cp -r` continua ausente de metadata; fallback é necessário.
- Bump automático do fallback no release workflow. Decisão futura.
- Gate AST em vez de regex. YAGNI por enquanto.

## Notas

- Sprint colateral identificada por `executor-sprint` durante BUG-APPIMAGE-VERSION-NAME-01 (análise pré-execução).
- Protocolo anti-débito 9.7: documentada como spec-nova, não como "TODO depois".
