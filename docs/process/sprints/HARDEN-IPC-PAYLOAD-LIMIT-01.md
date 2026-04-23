# HARDEN-IPC-PAYLOAD-LIMIT-01 — Limite de bytes por request no dispatch IPC

**Tipo:** hardening.
**Wave:** V2.2 — substitui HARDEN-IPC-RUMBLE-CUSTOM-01 (SUPERSEDED).
**Estimativa:** 0.5 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:hardening`, `security`, `ai-task`, `status:ready`. Origem: AUDIT-V2-COMPLETE-01 achado P2-03 reescopado após leitura do código (L-21-3).

## Contexto

`src/hefesto/daemon/ipc_server.py:_serve_client` lê requests via `await reader.readline()`. O `asyncio.StreamReader` tem limite implícito de 64 KiB (atributo privado `_limit`), suficiente para qualquer JSON-RPC legítimo, mas:

1. Limite é **implícito** — qualquer mudança de reader (ex.: migrar para `read_until`) perde a proteção sem aviso.
2. Cliente local malicioso pode enviar 60 KiB de lixo em cada linha durante muito tempo, consumindo CPU do parser + memória transitória do GC.
3. Nenhum handler atual tem campo vetorial grande (rumble.policy_custom aceita só `mult: float`), mas handlers futuros podem precisar — melhor fechar no dispatch, não em cada handler.

Socket Unix é restrito ao `$XDG_RUNTIME_DIR` do user, então a ameaça é local (não-remota). Severidade baixa, hardening trivial.

## Decisão

Limite **explícito** de 32 KiB (`32_768` bytes) por request JSON-RPC aplicado no `_dispatch`:

1. Se `len(raw) > MAX_PAYLOAD_BYTES`: retorna erro JSON-RPC `-32600 invalid request` com mensagem `"request excede limite de 32768 bytes"`.
2. Log `logger.warning("ipc_payload_excede_limite", size=len(raw), limit=32768)`.
3. Constante `MAX_PAYLOAD_BYTES = 32_768` exportada no módulo (facilita ajuste futuro).

32 KiB é folgado: um `rumble.passthrough` com 1 KiB cabe 32 vezes; um `profile.apply_draft` típico (~2 KiB) cabe 16 vezes. Payloads legítimos ficam muito abaixo desse limite.

## Critérios de aceite

- [ ] `ipc_server.py` exporta `MAX_PAYLOAD_BYTES = 32_768`.
- [ ] `_dispatch` rejeita raw > limite com erro JSON-RPC `-32600`.
- [ ] Log `warning` emitido com tamanho e limite.
- [ ] Teste `tests/unit/test_ipc_payload_limit.py`: aceita 1 KiB, aceita 30 KiB, rejeita 33 KiB, rejeita 100 KiB — todos formando JSON válido (padding com campo arbitrário).
- [ ] BRIEF ganha nota sobre o limite no `[CORE] Invariantes de arquitetura`.
- [ ] Gates canônicos.

## Arquivos tocados

- `src/hefesto/daemon/ipc_server.py`.
- `tests/unit/test_ipc_payload_limit.py` (novo).
- `VALIDATOR_BRIEF.md`.

## Proof-of-work runtime

```bash
.venv/bin/pytest tests/unit/test_ipc_payload_limit.py -v
.venv/bin/pytest tests/unit -q
.venv/bin/ruff check src/ tests/
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 \
  HEFESTO_IPC_SOCKET_NAME=hefesto-smoke.sock ./run.sh --smoke
```

## Fora de escopo

- Rate limiting (N requests/seg por cliente).
- Schema validation pydantic por handler.
- Limite no lado do cliente (`IpcClient` — não envia gigante).
