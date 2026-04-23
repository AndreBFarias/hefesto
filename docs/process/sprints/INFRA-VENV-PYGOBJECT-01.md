# INFRA-VENV-PYGOBJECT-01 — PyGObject no bootstrap default

**Tipo:** infra (DX/boot).
**Wave:** V2.2 — achado colateral de BUG-GUI-DAEMON-STATUS-INITIAL-01.
**Estimativa:** 0.5 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:infra`, `devex`, `ai-task`, `status:ready`.

## Sintoma

Executor sem `PyGObject` no `.venv` falha ao invocar `.venv/bin/python -m hefesto.app.main` com `ModuleNotFoundError: No module named 'gi'`. O repo contorna chamando `/usr/bin/python3` no `run.sh` (system-wide `python3-gi`), mas:

1. Validação visual de sprint via `.venv/bin/python` quebra (executor precisa `PYTHONPATH` hack).
2. Em CI ou máquina sem `python3-gi` do sistema, a GUI nem sobe.
3. `scripts/dev_bootstrap.sh` exige flag `--with-tray` para instalar; sem flag, `.venv` fica sem PyGObject — e a flag é opt-in.

Evidência: durante BUG-GUI-DAEMON-STATUS-INITIAL-01 (2026-04-23) o agente precisou `PYTHONPATH="$PWD/src:$PWD/.venv/lib/python3.10/site-packages" /usr/bin/python3 -m hefesto.app.main` para reproduzir o bug; `.venv/bin/pip show PyGObject` retornou not-found.

## Decisão

Duas camadas, complementares:

1. **`scripts/dev-setup.sh` valida `gi` importável** após bootstrap. Se `import gi` falha pelo `.venv/bin/python`, reporta com instrução literal: rodar `bash scripts/dev_bootstrap.sh --with-tray` ou `sudo apt install python3-gi libgirepository-1.0-dev` + `pip install -e ".[tray]"`. Exit 1 só se usuário confirma que quer GUI.
2. **README**: adicionar linha na seção Contribuição explicando a decisão `--with-tray`.

Não forçar PyGObject por default (build pesada em máquina sem `libgirepository` causa falha pesada; melhor opt-in explícito).

## Critérios de aceite

- [ ] `scripts/dev-setup.sh` detecta ausência de `gi` e imprime instrução acionável.
- [ ] `README.md` seção Instalação menciona `--with-tray` como pré-req pra GUI.
- [ ] `VALIDATOR_BRIEF.md` ganha armadilha `A-12: PyGObject ausente no .venv sem --with-tray` em `[CORE] Armadilhas conhecidas` com fix canônico referenciado.
- [ ] Gates canônicos verdes.

## Arquivos tocados

- `scripts/dev-setup.sh`.
- `README.md`.
- `VALIDATOR_BRIEF.md`.

## Proof-of-work

```bash
# Cenário 1: .venv sem PyGObject
.venv/bin/pip uninstall -y PyGObject 2>/dev/null  # se estiver lá
bash scripts/dev-setup.sh
# esperado: mensagem acionável "para GUI rodar com .venv isolada, rode dev_bootstrap.sh --with-tray..."

# Cenário 2: .venv com PyGObject
bash scripts/dev_bootstrap.sh --with-tray
bash scripts/dev-setup.sh
# esperado: mensagem "OK: PyGObject disponível no venv"
```

## Fora de escopo

- Publicar wheels de PyGObject (deps do sistema).
- Migrar GUI pra Qt/Tk (mudança de stack, sprint separada grande).
