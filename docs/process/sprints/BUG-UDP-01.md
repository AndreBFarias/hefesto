# BUG-UDP-01 — Remover AssertionError do `udp_server.connection_made`

**Tipo:** fix (baixo impacto, alta visibilidade no log).
**Wave:** fora de wave (correção pós-PR #67).
**Estimativa:** 1 iteração de executor, diff minúsculo.
**Dependências:** nenhuma.

---

## Contexto

`src/hefesto/daemon/udp_server.py:106` contém:

```python
def connection_made(self, transport: asyncio.BaseTransport) -> None:
    assert isinstance(transport, asyncio.DatagramTransport)
    self.transport = transport
```

Em Python 3.10 o objeto real entregue é `_SelectorDatagramTransport` (detalhe do asyncio). Esse objeto é subclasse de `asyncio.DatagramTransport` formalmente, mas na prática o `isinstance` falha por motivos de como asyncio expõe os tipos no namespace público naquela versão. Resultado: a cada boot do daemon (produção ou smoke), o journal recebe:

```
Exception in callback DsxProtocol.connection_made(<_SelectorDat...e, bufsize=0>>)
handle: <Handle DsxProtocol.connection_made(<_SelectorDat...e, bufsize=0>>)>
Traceback (most recent call last):
  File "/usr/lib/python3.10/asyncio/events.py", line 80, in _run
    self._context.run(self._callback, *self._args)
  File ".../udp_server.py", line 106, in connection_made
    assert isinstance(transport, asyncio.DatagramTransport)
AssertionError
```

O UDP server funciona mesmo assim (asyncio captura o erro como handler exception), mas polui logs de produção e esconde erros reais. Ver `VALIDATOR_BRIEF.md` armadilha A-02.

---

## Critérios de aceite

- [ ] `connection_made` não lança `AssertionError`. Escolher uma das abordagens:
  - (a) Remover o assert (defensivo gratuito — o tipo já está anotado).
  - (b) Substituir por guarda defensiva `if transport is None: logger.error("udp_transport_null"); return`.
  - Decisão: **(a) + manter annotação de tipo no atributo**. Justificativa: o asyncio já garante via contrato da API; assert só causaria ruído em tempo de execução.
- [ ] `self.transport = transport` (atribuição direta) preserva o tipo via annotation `transport: asyncio.DatagramTransport | None`.
- [ ] Smoke não loga mais traceback de AssertionError. Verificar via:
  ```bash
  HEFESTO_FAKE=1 ./run.sh --smoke 2>&1 | grep -i "AssertionError\|Exception in callback" | wc -l
  # esperado: 0
  ```
- [ ] Unit test novo (ou estendido) em `tests/unit/test_udp_server.py` instancia `DsxProtocol`, chama `connection_made` com um mock de `asyncio.DatagramTransport`, verifica que `.transport` foi atribuído e nenhuma exception foi levantada.
- [ ] Suite completa `tests/unit` continua verde (≥289 passing).

---

## Proof-of-work esperado

```bash
# 1. Unit específico
.venv/bin/pytest tests/unit/test_udp_server.py -v

# 2. Smoke sem traceback
HEFESTO_FAKE=1 HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke 2>&1 | tee /tmp/bug_udp_01_smoke.log
grep -c "AssertionError" /tmp/bug_udp_01_smoke.log   # esperado: 0
grep -c "udp_server_listening" /tmp/bug_udp_01_smoke.log  # esperado: 1

# 3. Suíte completa
.venv/bin/pytest tests/unit -q
./scripts/check_anonymity.sh
.venv/bin/ruff check src/
.venv/bin/mypy src/hefesto
```

**Aritmética esperada:**
- `grep AssertionError` em 2s de smoke: **0** ocorrências (antes: 1).
- `grep udp_server_listening`: **1** ocorrência (preservado).
- Testes totais: 289 atuais + 1 novo = ≥290 passing.

---

## Arquivos tocados (previsão)

- `src/hefesto/daemon/udp_server.py` — remove linha 106 ou substitui.
- `tests/unit/test_udp_server.py` — se não existir, criar.

---

## Fora de escopo

- Refatorar o `DsxProtocol` inteiro.
- Mudar o RateLimiter (já foi decidido em V3-1).
- Adicionar métricas/telemetria.

---

## Notas para o executor

- Diff de 1 linha em `src/`. Sprint é pequena de propósito: baixo risco, alto valor de sinal-ruído no log.
- Se detectar outro bug durante a investigação, abrir sprint nova com ID próprio (meta-regra 9.7).
