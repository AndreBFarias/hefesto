# PROFILE-DISPLAY-NAME-01 — Campo `display_name` separado do slug em `Profile`

**Tipo:** feat (schema + backend + GUI).
**Wave:** V2.1 — Bloco B.
**Estimativa:** 1-2 iterações.
**Dependências:** nenhuma técnica. Recomendado rodar depois de CHORE-ACENTUACAO-STRICT-HOOK-01 (o hook ajuda a pegar `Ação` vs `acao` automaticamente).

---

**Tracking:** issue a criar. Label: `type:feature`, `P2-medium`, `ai-task`, `status:ready`.

## Contexto

Hoje `Profile.name` acumula dois papéis:

1. **Slug de arquivo** — usado em `src/hefesto/profiles/loader.py:35-41` para localizar `<name>.json` no disco. Precisa ser ASCII-safe, lowercase, sem espaço nem barra.
2. **Display na GUI** — lista da aba Perfis mostra `profile.name` direto.

Resultado: `FEAT-PROFILES-PRESET-06` foi forçada a criar arquivos `acao.json`, `navegacao.json`, `aventura.json` (sem acento) porque a capitalização e acentuação quebrariam o path. A GUI mostra `acao` e o usuário lê `ação` na cabeça — acentuação perdida na camada visual.

Precisamos separar os dois papéis: `name` continua sendo o slug técnico (filename), e `display_name` é o texto visível.

## Decisão

Adicionar `display_name: str | None = None` ao schema `Profile`. Quando `display_name` está vazio/None, derivar automaticamente de `name` via `name.replace("_", " ").capitalize()` (fallback compatível com perfis antigos). Nunca alterar o filename existente — migração é transparente.

### Propagação

- **Schema** `src/hefesto/profiles/schema.py:107-131`: campo novo.
- **Loader** `src/hefesto/profiles/loader.py`: lê `display_name` se presente no JSON; passa para `Profile`; não fabrica valor no disco.
- **Manager** `src/hefesto/profiles/manager.py`: `_to_led_settings` e demais mappers **não precisam mudança** — `display_name` nunca vai para hardware. Documentar no spec contra A-06 (armadilha de esquecer o mapper quando campo novo aparece).
- **IPC** `src/hefesto/daemon/ipc_server.py`: handler `profile.list` retorna `[{name: str, display_name: str}]`. Backcompat: clientes antigos que só leem `.name` continuam funcionando.
- **GUI** `src/hefesto/app/actions/profiles_actions.py`: treestore usa `display_name` na coluna visível; `name` aparece como tag `Arquivo: <name>.json` em readonly abaixo.
- **Editor de perfil** (modo simples/avançado): campo "Nome exibido" (entry) editável; "Identificador" (label readonly) mostrando o slug.
- **Persistência de edição**: se usuário renomeia `display_name`, só `display_name` muda no JSON. Se usuário quer renomear o arquivo, é operação separada (fora de escopo aqui).

### JSONs default (8 arquivos, todos em `assets/profiles_default/`)

Adicionar `display_name` acentuado:

| Arquivo | `name` (slug) | `display_name` |
|---|---|---|
| `acao.json` | `acao` | `Ação` |
| `aventura.json` | `aventura` | `Aventura` |
| `corrida.json` | `corrida` | `Corrida` |
| `esportes.json` | `esportes` | `Esportes` |
| `fallback.json` | `fallback` | `Fallback` |
| `fps.json` | `fps` | `FPS` |
| `meu_perfil.json` | `meu_perfil` | `Meu Perfil` |
| `navegacao.json` | `navegacao` | `Navegação` |

## Critérios de aceite

- [ ] `src/hefesto/profiles/schema.py`: `Profile.display_name: str | None = None`; validator `@field_validator("display_name", mode="before")` trim strings; propriedade computada `Profile.display_name_effective` que retorna `display_name or name.replace("_", " ").capitalize()`.
- [ ] `src/hefesto/profiles/loader.py`: roundtrip JSON preserva `display_name` se presente, omite se None (serialização limpa — `exclude_none=True` no `model_dump`).
- [ ] 8 JSONs em `assets/profiles_default/` atualizados com `display_name` acentuado.
- [ ] `src/hefesto/daemon/ipc_server.py`: `handle_profile_list` retorna `[{name, display_name}]`. Test `tests/unit/test_ipc_server.py::test_profile_list_inclui_display_name`.
- [ ] `src/hefesto/app/actions/profiles_actions.py`: treestore/liststore tem coluna visível = `display_name_effective`; coluna auxiliar = `name` (renderizada como tag pequena cinza).
- [ ] `src/hefesto/gui/main.glade`: editor de perfil ganha `GtkEntry id=entry_profile_display_name`; label `Identificador` readonly mostrando slug.
- [ ] Salvar edição via editor: só `display_name` muda, `name` preservado.
- [ ] Teste `tests/unit/test_profile_display_name.py` (novo, ≥ 5 casos):
  - Profile sem display_name → `display_name_effective == "Meu Perfil"` derivado.
  - Profile com `display_name="Ação"` → `display_name_effective == "Ação"`.
  - Roundtrip load/save preserva display_name.
  - Slug inalterado quando display_name muda.
  - JSON sem display_name carrega sem erro.
- [ ] `check_anonymity.sh`, ruff, mypy verdes.
- [ ] Smoke USB+BT verde (`profile.switch` via IPC não regride).
- [ ] Proof-of-work visual: screenshot aba Perfis com 8 nomes acentuados visíveis.

## Arquivos tocados

- `src/hefesto/profiles/schema.py`
- `src/hefesto/profiles/loader.py`
- `src/hefesto/profiles/manager.py` (só revisar — provavelmente sem mudança)
- `src/hefesto/daemon/ipc_server.py`
- `src/hefesto/app/actions/profiles_actions.py`
- `src/hefesto/gui/main.glade`
- `assets/profiles_default/acao.json`
- `assets/profiles_default/aventura.json`
- `assets/profiles_default/corrida.json`
- `assets/profiles_default/esportes.json`
- `assets/profiles_default/fallback.json`
- `assets/profiles_default/fps.json`
- `assets/profiles_default/meu_perfil.json`
- `assets/profiles_default/navegacao.json`
- `tests/unit/test_profile_display_name.py` (novo)
- `tests/unit/test_ipc_server.py` (estender)

## Proof-of-work runtime

```bash
.venv/bin/pytest tests/unit/test_profile_display_name.py tests/unit/test_ipc_server.py -v
.venv/bin/ruff check src/hefesto/profiles src/hefesto/daemon/ipc_server.py src/hefesto/app/actions/profiles_actions.py
.venv/bin/mypy src/hefesto/profiles
./scripts/check_anonymity.sh
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke --bt

# Verifica que profile.list retorna display_name
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.daemon.main &
DPID=$!
sleep 2
echo '{"jsonrpc":"2.0","id":1,"method":"profile.list"}' | socat - UNIX-CONNECT:$XDG_RUNTIME_DIR/hefesto/hefesto.sock | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); assert any('display_name' in p for p in d['result']), 'display_name ausente'; print('OK')"
kill $DPID
```

## Notas para o executor

- **A-06 (campo novo precisa mapper sincronizado)**: `display_name` **NÃO** vai para `_to_led_settings` nem `TriggerSettings` — é só UI + IPC. Documentar explicitamente no spec para não despertar o reflexo de "preciso adicionar em todos os mappers". Confirmar com `rg "name:" src/hefesto/profiles/manager.py` — se aparecer uso de `profile.name` que deveria ser `display_name`, é bug (não regressão; invariante "slug para arquivo, display para tela").
- **Backcompat de leitura**: perfis criados pelo usuário antes desta sprint não têm `display_name` no JSON. Loader precisa aceitar ausência silenciosa. Validator pydantic `Optional` resolve.
- **Treestore + coluna auxiliar**: `Gtk.TreeStore` admite múltiplas colunas; a GUI pode esconder a coluna `name` com `col.set_visible(False)` ou mostrar como subtítulo. Preferir mostrar como label cinza pequeno abaixo do display_name — ajuda o usuário entender que o arquivo é `acao.json`.
- **Edição via GUI**: botão Salvar grava `display_name` no JSON existente — não copiar o perfil. Se usuário digitar display_name vazio, validator aceita (None → fallback derivado no render).
- **Acentuação em JSON**: Python `json.dump(..., ensure_ascii=False)` para preservar `Ação` como UTF-8. Se gravar com `ensure_ascii=True`, fica `"Ação"` escapado — tecnicamente correto mas visualmente ruim em diff.
- **GUI label tag**: CSS classe `.profile-slug-tag` com cor `#6c6c8c` (tom drácula secundário) e fonte pequena 10pt. Se já existe tag parecida em outra parte do CSS, reusar.

## Fora de escopo

- Renomear arquivo de perfil pela GUI (operação destrutiva; fica para sprint separada).
- Importar perfil externo com display_name custom (CSV/YAML) — não priorizado.
- Tradução automática do slug para display_name (Alemão? Espanhol? Só PT-BR suportado hoje).
- Alteração de IPC `profile.switch` — continua recebendo slug (`{profile: "acao"}`), nunca display_name.
