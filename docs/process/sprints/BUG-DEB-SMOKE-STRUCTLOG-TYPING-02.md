# BUG-DEB-SMOKE-STRUCTLOG-TYPING-02 — Smoke do .deb falha no Jammy por `structlog.typing` ausente

**Tipo:** bug (packaging/CI).
**Wave:** V2.2.2 — patch bloqueador de release.
**Estimativa:** XS (0.10 iteração).
**Dependências:** nenhuma.
**Sprint-mãe:** BUG-DEB-SMOKE-PYDANTIC-V2-NOBLE-01 (79.1) — mesmo padrão de falha empírica (L-21-7) com outra lib.

---

**Tracking:** label `type:bug`, `packaging`, `ci`, `quality`, `ai-task`, `status:ready`, `P0-urgent`.

## Contexto

Durante a Fase A3 da release v2.2.2 (2026-04-24), a tag `v2.2.2` foi pushada e disparou `release.yml` (run `24866299294`). Todos os jobs passaram — exceto **`deb-install-smoke`**, que quebrou com:

```
File "/usr/lib/python3/dist-packages/hefesto/utils/logging_config.py", line 23, in <module>
    from structlog.typing import Processor
ModuleNotFoundError: No module named 'structlog.typing'
```

O fix `BUG-DEB-SMOKE-PYDANTIC-V2-NOBLE-01` (79.1) resolveu o caso do pydantic mas **não previu** que outras deps Python do sistema pudessem estar em versões incompatíveis. Este é o segundo disparo do mesmo pattern — L-21-7 reconfirmada: toda premissa sobre versão de lib do sistema precisa `apt-cache policy` empírico **por lib**.

## Causa raiz

O módulo `structlog.typing` foi introduzido em **structlog 22.1.0** (agosto/2022). O Ubuntu 22.04 LTS (Jammy, runner do smoke desde o fix 79.1) empacota `python3-structlog` em versão anterior, que só expunha `structlog.types` (plural, sem o `ing` final).

Local (dev): `structlog 25.5.0` — funciona.  
Runner `ubuntu-22.04` no CI (apt): versão antiga (hipótese: 21.x) — quebra.

O `packaging/debian/control` declara `python3-structlog` sem constraint de versão, então o apt aceita a 21.x instalada.

## Decisão

**Fix de 2 camadas** (mais robusto que o padrão do 79.1 porque não exige `pip install --user` adicional no smoke):

### 1. Compat layer em `src/hefesto/utils/logging_config.py`

```python
try:
    from structlog.typing import Processor
except ImportError:  # structlog < 22.1 (Jammy apt default)
    from structlog.types import Processor  # type: ignore[no-redef]
```

`structlog.types` existe desde versões muito antigas e expõe `Processor` com assinatura idêntica. A transição `types` → `typing` foi interna, não API-quebrante.

### 2. Documentar o requisito mínimo em `control`

```
Depends: ..., python3-structlog (>= 21.5),
```

Versão mínima que existe no Jammy (21.5 é a versão 21.x mais recente distribuída). Garante que, se alguém tentar em uma distro ainda mais antiga, o apt rejeita com mensagem clara.

### Não mexer em `release.yml`

Diferente do fix 79.1 (pydantic), aqui a compat layer resolve sem precisar injetar `pip install --user 'structlog>=22.1'`. Menos código no CI, menos pontos de falha.

## Plano de re-release

- Opção **recomendada**: após esta sprint MERGED, **re-dispatch** de `release.yml` via `gh workflow run release.yml --field tag=v2.2.2`. Os 6 jobs re-executam sobre a mesma tag, `github-release` roda e publica os 5 assets. Não "queima" o número v2.2.2.
- Opção alternativa: delete tag remoto + bump 2.2.2 → 2.2.3 + re-tag. Pior: inflaciona versão e embaraça CHANGELOG.

## Critérios de aceite

- [ ] `src/hefesto/utils/logging_config.py:22-23` passa a usar `try/except ImportError` para `Processor`.
- [ ] `packaging/debian/control` declara `python3-structlog (>= 21.5)`.
- [ ] `.venv/bin/pytest tests/unit -q --no-header` sem regressão.
- [ ] `.venv/bin/mypy src/hefesto` limpa (com `# type: ignore[no-redef]` no except).
- [ ] `.venv/bin/ruff check src/hefesto/utils/logging_config.py` limpa.
- [ ] Teste novo `tests/unit/test_logging_compat_import.py` cobrindo o fallback via monkeypatch removendo `structlog.typing` do `sys.modules`.
- [ ] `gh workflow run release.yml --field tag=v2.2.2` executa com **6 jobs success + pypi skipped** + `gh release view v2.2.2 --json isDraft` → `false` + 5 assets `state: uploaded`.

## Arquivos tocados

- `src/hefesto/utils/logging_config.py` (compat import — ~3 linhas).
- `packaging/debian/control` (1 linha — version constraint em structlog).
- `tests/unit/test_logging_compat_import.py` (novo).
- `CHANGELOG.md` — bullet em `[Unreleased]` ou `[2.2.2]` (já publicado?) — decidir com release strategy.

## Proof-of-work

```bash
# Antes (reproduz bug):
# Não é reprodutível em dev local (structlog 25.x tem .typing). Reproduzível em
# container Jammy com python3-structlog do apt:
docker run -it --rm ubuntu:22.04 bash -c \
  "apt-get update -qq && apt-get install -y -qq python3-structlog && python3 -c 'from structlog.typing import Processor'"
# Esperado: ModuleNotFoundError antes do fix.

# Depois:
.venv/bin/pytest tests/unit -q --no-header
# Smoke manual em container Jammy:
docker run -it --rm -v $PWD:/mnt ubuntu:22.04 bash -c "apt-get update -qq && apt-get install -y -qq ./mnt/dist/hefesto_*_amd64.deb python3-structlog && hefesto --version"
```

## Fora de escopo

- Reescrever logging para não depender de `Processor` (over-engineering).
- Exigir structlog >= 22.1 e deixar Jammy quebrar (seria uma decisão de DS, não de fix).
- Atualizar o smoke CI para injetar `pip install --user 'structlog>=22.1'` (padrão 79.1 — mas a compat layer já resolve, então YAGNI).

## Notas

- Segunda vez que L-21-7 (validação empírica de versão de lib de sistema) dispara no mesmo ciclo. Sinal: quando declarar dep Python em `.deb`, varrer **cada uma** das deps explicitamente contra `apt-cache policy`/packages.ubuntu.com antes do release.
- Fix local (docker de test) recomendado antes de re-disparar workflow no GitHub.
- Se re-dispatch falhar outra vez por outra dep: criar `BUG-DEB-SMOKE-<LIB>-NOBLE-03` seguindo mesmo padrão (L-21-7 é processo, não one-shot).

# "Mesma vela, outro vento." — Heráclito, repetidamente.
