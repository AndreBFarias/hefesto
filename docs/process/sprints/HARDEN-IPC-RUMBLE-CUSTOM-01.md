# HARDEN-IPC-RUMBLE-CUSTOM-01 — Limite de tamanho no handler `rumble.policy_custom`

**Tipo:** hardening.
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 0.5 iteração.
**Dependências:** FEAT-RUMBLE-POLICY-CUSTOM-01 (existente).

---

**Tracking:** label `type:hardening`, `security`, `ai-task`, `status:ready`. Origem: AUDIT-V2-COMPLETE-01 achado P2-03.

## Contexto

Handler IPC `rumble.policy_custom` aceita payload com curva customizada de rumble (vetor `list[int]`). Auditoria (AUDIT-V2-COMPLETE-01) identificou que o handler **não valida tamanho do vetor**. Cliente local malicioso poderia enviar `[0] * 10_000_000` — consome memória temporária até o parser terminar, mesmo que a aplicação subsequente clampe.

Risco: DoS local (não remoto — socket Unix restrito ao `$XDG_RUNTIME_DIR` do user). Severidade baixa, mas trivial de fechar.

## Decisão

1. Limite de **256 entradas** no vetor. Curva de rumble tem resolução útil ≤64; 256 é folgado para evolução futura.
2. Handler retorna erro JSON-RPC padrão `-32602 invalid params` com mensagem `"curva excede limite de 256 pontos"` se exceder.
3. Teste unitário em `tests/unit/test_ipc_rumble_custom_limits.py`.

## Critérios de aceite

- [ ] Handler em `src/hefesto/daemon/ipc_server.py` valida `len(params.curve) <= 256` antes de processar.
- [ ] Erro retornado é `-32602 invalid params` (padrão JSON-RPC).
- [ ] Teste unitário cobre: aceita 256, rejeita 257, rejeita 10000, aceita payload normal (<64).
- [ ] Log de warning em caso de rejeição: `logger.warning("rumble_custom_rejected size=<N> limit=256")`.
- [ ] Gates canônicos verdes.

## Arquivos tocados

- `src/hefesto/daemon/ipc_server.py` (handler).
- `tests/unit/test_ipc_rumble_custom_limits.py` (novo).

## Proof-of-work runtime

```bash
# Manual via IPC:
python3 -c "
import json, socket, os
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(os.path.expanduser('~/.local/state/hefesto/ipc.sock'))
req = {'jsonrpc':'2.0','id':1,'method':'rumble.policy_custom','params':{'curve':[0]*10000}}
sock.sendall((json.dumps(req)+'\n').encode())
print(sock.recv(4096).decode())
# Esperado: {'jsonrpc':'2.0','id':1,'error':{'code':-32602,'message':'curva excede limite de 256 pontos'}}
"

.venv/bin/pytest tests/unit/test_ipc_rumble_custom_limits.py -v
```

## Fora de escopo

- Rate limiting (quantos `rumble.policy_custom` por segundo) — sprint futura se relevante.
- Schema validation via pydantic pro payload inteiro (overkill aqui — check explícito é mais barato).
