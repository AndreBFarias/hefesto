# BUG-GUI-DAEMON-STATUS-INITIAL-01 — GUI abre com status "Offline" apesar de daemon ativo

**Tipo:** bug (UX confuso).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:bug`, `P1`, `ui`, `ai-task`, `status:ready`.

## Sintoma

Reportado pelo usuário em 2026-04-23 testando v2.1.0:

> "na aba Daemon o status inicia sendo 'Offline', tenho que abrir e clicar manualmente em Reiniciar daemon."

Reproduzido visualmente no screenshot da aba Daemon: rótulo "Status: Iniciando..." aparece no topo, mas o footer mostra "systemctl --user restart hefesto.service → ok" confirmando que o daemon está vivo. Usuário precisa clicar "Atualizar" ou "Reiniciar daemon" pra GUI refletir o estado real.

Fluxo provável (hipótese — validador confirma via leitura direta):

1. `HefestoApp.__init__` monta aba Daemon com valor default `status="Offline"` ou `"Iniciando..."` no placeholder do Glade.
2. Timer/poll de `daemon.status` via IPC só dispara após 2-3s de uptime da GUI.
3. Antes desse primeiro poll, usuário vê rótulo desatualizado.

Esperado: GUI dispara `daemon.status` via IPC **imediatamente** no `on_realize` / `on_show` da janela, ou no `on_tab_switch` para a aba Daemon, e atualiza o label antes de o primeiro frame ser desenhado. Se daemon não respondeu ainda, mostrar "Consultando..." em vez de "Offline" (evita falso-negativo).

## Decisão

Investigar em 3 pontos:

1. `src/hefesto/app/actions/daemon_actions.py` — onde `Status: ...` é atualizado. Procurar loop/timer de refresh.
2. `src/hefesto/gui/main.glade` — valor default do label de status.
3. `src/hefesto/app/app.py` — ponto de entrada da GUI, onde actions são ligadas a tabs.

Fix esperado: chamada síncrona a `daemon.status` via IPC no `on_show` da janela principal, com fallback "Consultando..." se daemon não está up ainda (trigger um retry em 500ms).

## Critérios de aceite

- [ ] Reproduzir o bug antes do fix: abrir GUI com daemon já rodando, screenshot mostra "Offline" ou "Iniciando..." por ≥2s.
- [ ] Aplicar fix: status real (Active/Inactive/Failed) aparece em <500ms após GUI abrir.
- [ ] Se daemon realmente offline: rótulo "Inativo" aparece, não "Iniciando...".
- [ ] Se daemon ativo mas ainda não registrado socket: fallback "Consultando..." com retry 500ms até obter resposta ou 5s timeout.
- [ ] Teste unitário `tests/unit/test_daemon_status_initial.py` cobrindo os 3 cenários.
- [ ] Screenshot após fix (aba Daemon recém-aberta, daemon ativo, rótulo correto em <500ms).

## Arquivos tocados (hipótese)

- `src/hefesto/app/actions/daemon_actions.py`.
- `src/hefesto/gui/main.glade` (default label).
- `tests/unit/test_daemon_status_initial.py` (novo).

## Proof-of-work runtime

```bash
# Cenário 1: daemon já ativo
systemctl --user start hefesto.service
sleep 2
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.app.main &
sleep 0.7  # <500ms do start
import -window "$(xdotool search --name 'Hefesto' | head -1)" /tmp/status_1.png
# Verificar visualmente: rótulo não deve ler "Offline"
kill %1

# Cenário 2: daemon parado
systemctl --user stop hefesto.service
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.app.main &
sleep 0.7
import -window "$(xdotool search --name 'Hefesto' | head -1)" /tmp/status_2.png
kill %1

.venv/bin/pytest tests/unit/test_daemon_status_initial.py -v
```

## Fora de escopo

- Toda polish visual da aba Daemon (fundo cinza etc.) — sprint UI-POLISH-EMULACAO-DAEMON-STATUS-01.
- Rework de autorefresh ou watchdog — é só primeira leitura.
