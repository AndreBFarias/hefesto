# BUG-DEB-PYDANTIC-V2-UBUNTU-22-01 — python3-pydantic em Ubuntu 22.04 é v1, código usa v2

**Tipo:** bug (packaging/compat).
**Wave:** V2.2 — achado colateral da tag v2.2.0.
**Estimativa:** 0.5 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:bug`, `P1-high`, `packaging`, `deb`, `ai-task`, `status:ready`.

## Sintoma

Run `24861148981` (2026-04-23, release v2.2.0 por push de tag) falhou no job `Smoke install do .deb` com:

```
ImportError: cannot import name 'ConfigDict' from 'pydantic'
  (/usr/lib/python3/dist-packages/pydantic/__init__.py)
```

`packaging/debian/control` declara `python3-pydantic` sem versão mínima; o apt do Ubuntu 22.04 entrega `python3-pydantic 1.9.x`; o código do Hefesto usa `pydantic.ConfigDict` (API da v2).

## Reprodução

```bash
# Em Ubuntu 22.04 limpa:
sudo apt install ./hefesto_2.2.0_amd64.deb
hefesto --version
# ImportError ao carregar hefesto/profiles/schema.py
```

## Decisão

Duas camadas, complementares:

**Camada 1 — control declara versão mínima:**
```
Depends: ..., python3-pydantic (>= 2.0), ...
```
Isso força apt a falhar com mensagem clara se pydantic v2 não disponível, em vez de instalar com dep errada.

**Camada 2 — instruções no README + Troubleshooting** explicando que Ubuntu 22.04 precisa de `pip install 'pydantic>=2.0' --user` antes do `apt install hefesto_*.deb` (até 22.04 sair de suporte). Ubuntu 24.04+ tem pydantic 2 nativo.

**Camada 3 (opcional)** — mudar job `deb-install-smoke` para rodar em `ubuntu-24.04` ao invés de `ubuntu-22.04`. Assim o CI smoke valida no cenário que realmente funciona out-of-the-box; Ubuntu 22.04 fica documentado como plataforma que requer pip-install-adicional.

## Critérios de aceite

- [ ] `packaging/debian/control` declara `python3-pydantic (>= 2.0)`.
- [ ] README seção Troubleshooting explica workaround 22.04.
- [ ] `.github/workflows/release.yml` job `deb-install-smoke` roda em `ubuntu-24.04`.
- [ ] Gates canônicos.

## Arquivos tocados

- `packaging/debian/control`.
- `README.md`.
- `.github/workflows/release.yml`.

## Proof-of-work

```bash
# Local:
bash scripts/build_deb.sh
dpkg-deb -I dist/hefesto_*.deb | grep pydantic
# esperado: python3-pydantic (>= 2.0)

# CI:
gh workflow run release.yml -f tag=v2.2.0
# novo run deve ter smoke verde em ubuntu-24.04
```

## Fora de escopo

- Empacotar pydantic2 dentro do .deb (complexo, desnecessário).
- Migrar para pydantic v1 (regressão inviável).
