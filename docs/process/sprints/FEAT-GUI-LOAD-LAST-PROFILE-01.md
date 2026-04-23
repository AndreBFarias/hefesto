# FEAT-GUI-LOAD-LAST-PROFILE-01 — GUI abre com o último perfil ativo selecionado

**Tipo:** feat (UX).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma (FEAT-PERSIST-SESSION-01 já existe no daemon).

---

**Tracking:** label `type:feat`, `ui`, `ai-task`, `status:ready`.

## Contexto

Usuário relatou em 2026-04-23 (v2.1.0):

> "Ao abrir o hefesto ele já deveria abrir com o meu perfil anterior carregado."

Situação atual — confirmada por inspeção da auditoria AUDIT-V2-COMPLETE-01:

- **Daemon**: `src/hefesto/daemon/subsystems/connection.py:34-49` chama `restore_last_profile(daemon)` ao conectar o controller (FEAT-PERSIST-SESSION-01). Persistência em `src/hefesto/utils/session.py` via `load_last_profile` / `save_last_profile`. **Já funciona lado daemon.**
- **GUI**: ao abrir, aba Perfis mostra o primeiro da lista ordenada alfabeticamente (ex.: "André" no ambiente do usuário), não o perfil atualmente ativo. **Sem sincronia com o daemon.**

Esperado: GUI, no primeiro refresh da aba Perfis, consulta `daemon.status` (ou handler dedicado `profile.active`) para descobrir qual perfil está em execução e seleciona essa linha na `TreeView`. Se daemon offline ou sem perfil ativo, cai no fallback atual (primeiro da lista ou `fallback`).

## Decisão

1. **Handler IPC novo** (opcional — verificar se `daemon.state_full` já retorna o perfil ativo): `profile.active` retorna `{"name": <slug do perfil ativo>}` ou `{"name": null}` se nada aplicado.
2. **GUI em `profiles_actions.py`**: no `on_tab_show` da aba Perfis (ou no `HefestoApp.__init__` se lista de perfis é carregada uma vez), chamar `profile.active`, buscar linha correspondente no model e definir `treeview.set_cursor(row)`.
3. **Persistência já existe** — não tocar em `save_last_profile`.

## Critérios de aceite

- [ ] Cenário 1: daemon rodando com perfil `meu_perfil` ativo. Abrir GUI → aba Perfis abre com `meu_perfil` já selecionado (highlight roxo).
- [ ] Cenário 2: daemon offline. Abrir GUI → aba Perfis cai no fallback (primeiro da lista).
- [ ] Cenário 3: daemon rodando mas sem `switch` explícito (startup fresh). GUI seleciona o que `restore_last_profile` carregou (persistido em `~/.local/state/hefesto/last_profile`).
- [ ] Se handler novo `profile.active` for criado, teste unitário em `tests/unit/test_ipc_profile_active.py`.
- [ ] Teste GUI em `tests/unit/test_profiles_gui_sync.py` mockando IPC.
- [ ] Screenshot: aba Perfis aberta com perfil ativo selecionado.

## Arquivos tocados (hipótese)

- `src/hefesto/daemon/ipc_server.py` (handler novo, se necessário).
- `src/hefesto/app/actions/profiles_actions.py` (sync on open).
- `tests/unit/test_profiles_gui_sync.py` (novo).

## Proof-of-work runtime

```bash
# Garantir que há um last_profile persistido
systemctl --user start hefesto.service
sleep 2
hefesto profile switch meu_perfil
sleep 1
systemctl --user restart hefesto.service
sleep 2
# daemon.restore_last_profile deve ter carregado meu_perfil
# Agora abrir GUI
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.app.main &
sleep 2
# Ir na aba Perfis
# Screenshot deve mostrar meu_perfil selecionado, NÃO "André"
import -window "$(xdotool search --name 'Hefesto' | head -1)" /tmp/perfil_carregado.png
kill %1

.venv/bin/pytest tests/unit/test_profiles_gui_sync.py -v
```

## Fora de escopo

- Mudar modelo de persistência.
- Refactor da seleção em `TreeView` (só adicionar a chamada de sync inicial).
