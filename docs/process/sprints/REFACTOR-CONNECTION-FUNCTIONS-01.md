# REFACTOR-CONNECTION-FUNCTIONS-01 — Mover `connection.py` de `subsystems/` (não é subsystem)

**Tipo:** refactor.
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 0.5 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:refactor`, `ai-task`, `status:ready`. Origem: AUDIT-V2-COMPLETE-01 achado P2-02.

## Contexto

`src/hefesto/daemon/subsystems/connection.py` contém funções soltas (`connect_with_retry`, `restore_last_profile`, `reconnect`, `shutdown`), todas recebendo `daemon: Any` como argumento. **Não é um subsystem** no sentido do protocolo em `subsystems/base.py` (classes com `start()/stop()` — padrão dos outros 9 módulos do diretório).

Auditoria marcou como P2 documental/convenção. Não é bug — só diverge do padrão do diretório e confunde leitor novo ("esperava uma classe, achei funções").

## Decisão

Duas opções; sprint escolhe após ler:

**Opção A (preferida)**: mover para `src/hefesto/daemon/connection.py` (fora de `subsystems/`). Atualizar imports em `src/hefesto/daemon/lifecycle.py` e onde mais for usado.

**Opção B**: renomear para `src/hefesto/daemon/subsystems/connection_functions.py` — deixa claro que são funções, não subsystem. Menos ideal porque o diretório continua misto.

## Critérios de aceite

- [ ] Arquivo movido/renomeado conforme opção escolhida.
- [ ] Todos os imports atualizados (`grep -rn "from hefesto.daemon.subsystems.connection" src/ tests/`).
- [ ] Testes continuam passando (978 baseline).
- [ ] ruff + mypy verdes.
- [ ] Smoke USB+BT verde.
- [ ] Commit message explicita origem: `refactor: REFACTOR-CONNECTION-FUNCTIONS-01 — move connection.py (audit P2-02)`.

## Arquivos tocados

- Arquivo movido de `src/hefesto/daemon/subsystems/connection.py` → `src/hefesto/daemon/connection.py` (Opção A).
- `src/hefesto/daemon/lifecycle.py` (imports).
- Outros consumidores (verificar com grep).

## Proof-of-work runtime

```bash
.venv/bin/pytest tests/unit -q
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
```

## Fora de escopo

- Qualquer lógica dentro das funções (refactor é só de path).
