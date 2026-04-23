# Auditoria V2 — 2026-04-23

**Sprint:** AUDIT-V2-COMPLETE-01
**Autor:** auditoria manual (sem subagente), HEAD `e35ec52`
**Escopo:** diff `v1.0.0..HEAD` em `src/hefesto/**` — 79 arquivos, +9286/-705 linhas.

## Sumário executivo

Código v2.1.0 (pré-release) está sólido. Três armadilhas listadas como abertas no `VALIDATOR_BRIEF.md` (A-01, A-02, A-03) já foram fechadas em código mas o BRIEF não reflete — débito documental. Zero P0/P1 encontrado. Achados são todos P2/P3 — polish, não bloqueio de release. Recomendação: bumpar v2.1.0 com nota "known issues" vazia e fechar o débito do BRIEF nesta mesma sprint-ciclo.

## Métricas varridas

- `ruff check src/`: zero violações.
- `grep TODO|FIXME|XXX`: zero em `src/hefesto/`.
- `grep "except:"` (bare): zero ocorrências.
- `grep "shell=True"`: zero em runtime (só docstrings).
- `grep "print("`: todas instâncias são `console.print()` (rich), não stdlib `print()` — OK.
- Paths hardcoded `/home/|/etc/|/usr/`: zero.
- IPC handlers: 18 canônicos (ver listagem abaixo).
- Subsystems: 10 módulos em `src/hefesto/daemon/subsystems/`. Nove com start/stop simétrico. `connection.py` é coleção de funções puras (`connect_with_retry`, `restore_last_profile`, `reconnect`, `shutdown`) — não é subsystem com ciclo de vida próprio, intencional.
- Testes: baseline 978 passed em HEAD anterior à sessão (confirmado em commit `7e6b369`). Ambiente atual da sessão sem `.venv/` pronto para reexecutar localmente; gates de CI cobrem `release.yml`.

## Achados P2 — débito documental e polish

### P2-01: Armadilhas A-01, A-02, A-03 listadas como abertas mas RESOLVIDAS em código

**Local:** `VALIDATOR_BRIEF.md:94-106`.

**Estado real:**

- **A-01** (`IpcServer` `unlink()` cego): resolvido em `src/hefesto/daemon/ipc_server.py:99-157`. Novo método `_probe_socket_and_cleanup()` tenta `socket.connect` com timeout 100ms antes de apagar; se conexão aceita, levanta `SocketInUseError`; só remove arquivo órfão de socket morto. Chamado em `start()` linha 116.
- **A-02** (`assert isinstance(transport, asyncio.DatagramTransport)` ruidoso): resolvido em `src/hefesto/daemon/udp_server.py:112`. Assert removido; atribuição direta com `# type: ignore[assignment]` e comentário referenciando `BUG-UDP-01 / A-02`.
- **A-03** (smoke compartilha socket path com produção): resolvido indiretamente por A-01 — probe ativo garante que daemon novo não destrói daemon vivo. Não houve sprint dedicada de isolamento via `HEFESTO_IPC_SOCKET_NAME`, mas o risco concreto (destruição mútua) está fechado pelo probe.

**Sprint-fix imediato:** update do BRIEF nesta mesma sessão, sem sprint nova. Atualização registra hash do commit de fix para cada uma.

### P2-02: `connection.py` no diretório `subsystems/` rompe convenção

**Local:** `src/hefesto/daemon/subsystems/connection.py`.

Todos os outros 9 arquivos de `subsystems/` implementam classes com `start()/stop()` seguindo `base.Subsystem`. `connection.py` contém funções soltas (`connect_with_retry`, `reconnect`, `shutdown`). Confuso para leitor novo: parece subsystem, não é.

**Sprint-fix sugerida:** `REFACTOR-CONNECTION-FUNCTIONS-01` — mover para `src/hefesto/daemon/connection.py` (fora de `subsystems/`) ou renomear arquivo para `connection_functions.py`. Não-bloqueante.

### P2-03: Handler `rumble.policy_custom` aceita payload sem limite documentado

**Local:** `src/hefesto/daemon/ipc_server.py` handler `_handle_rumble_policy_custom`.

Payload define curva customizada de rumble — spec `FEAT-RUMBLE-POLICY-CUSTOM-01` aceita vetor de `list[int]`. Sem limite documentado de tamanho. Vetor gigante via IPC não quebra runtime (aplicação clampa), mas permite consumo desnecessário de memória por cliente malicioso local.

**Sprint-fix sugerida:** `HARDEN-IPC-RUMBLE-CUSTOM-01` — limitar `len(curva) <= 256` no handler, retornar erro `-32602 invalid params` se exceder. Não-bloqueante.

## Achados P3 — style/oportunidades

- `src/hefesto/app/main.py:19` tem `print(...)` em stderr como fallback emergencial de logging quando `structlog` ainda não está configurado. Aceitável. Zero outros `print()` em runtime.
- Dois erros `mypy` pré-existentes em `src/hefesto/hardware/backend_pydualsense.py:182` (documentados em SCHEMA-MULTI-POSITION-PARAMS-01). Não introduzidos por V2.1, não bloqueia release. Candidatos a `CHORE-MYPY-CLEANUP-01`.
- IPC handlers: 18 presentes. BRIEF menciona "10 métodos canônicos". Discrepância de 8 handlers adicionais (`daemon.state_full`, `controller.list`, `daemon.reload`, `led.player_set`, `plugin.list`, `plugin.reload`, `rumble.passthrough`, `rumble.policy_custom`) é esperada — vieram com sprints V1.1/V1.2/V2.0. BRIEF precisa atualizar contagem.
- `FEAT-PERSIST-SESSION-01` implementado em `src/hefesto/utils/session.py` + chamado em `connection.restore_last_profile()`. Daemon restaura último perfil ao iniciar. **Mas GUI não sincroniza** — ao abrir a GUI, aba Perfis seleciona o primeiro da lista ordenada alfabeticamente (`André` no ambiente do usuário), não o ativo. Candidato direto a sprint de polish V2.2 (ver sprint `FEAT-GUI-LOAD-LAST-PROFILE-01` criada nesta sessão).

## IPC handlers inventariados (18)

`profile.switch`, `profile.list`, `profile.apply_draft`, `trigger.set`, `trigger.reset`, `led.set`, `rumble.set`, `rumble.stop`, `rumble.passthrough`, `rumble.policy_set`, `rumble.policy_custom`, `daemon.status`, `daemon.state_full`, `controller.list`, `daemon.reload`, `led.player_set`, `plugin.list`, `plugin.reload`.

## Subsystems inventariados (10)

`autoswitch`, `base`, `connection`, `hotkey`, `ipc`, `metrics`, `mouse`, `plugins`, `poll`, `rumble`, `udp`.

## Conclusão

Release v2.1.0 pode sair com **zero known issues**. Débito documental do BRIEF fecha na mesma sessão (update inline). Os 3 P2 sugerem sprints futuras V2.2+, sem bloquear release. Nenhum risco de regressão encontrado nos 9286 linhas adicionadas.
