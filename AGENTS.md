# AGENTS.md — Protocolo do Projeto Hefesto

Arquivo de contexto para agentes de IA colaborando neste repositório. Ler antes de abrir qualquer PR com label `ai-task`.

---

## 1. Hierarquia de regras

Em qualquer conflito, obedecer nesta ordem (mais forte primeiro):

1. `~/.config/zsh/AI.md` v4.0 — regras universais (comunicação PT-BR, anonimato absoluto, código limpo, git, proteções, 800 linhas/arquivo, `.gitignore`, princípios, meta-regras anti-regressão, workflow, checklist pré-commit, assinatura).
2. Arquivo global de extensões do CLI de IA do mantenedor (convencionalmente em diretório dotfile do CLI) — meta-regras 9.6 (evidência empírica), 9.7 (zero follow-up), 9.8 (validação runtime-real); regras 13–14 (validação visual em UI/TUI, capacidades visuais disponíveis).
3. `docs/process/HEFESTO_DECISIONS_V2.md` — patches 1–11 consolidados.
4. `docs/process/HEFESTO_DECISIONS_V3.md` — deltas V3-1 a V3-8.
5. `docs/process/HEFESTO_PROJECT.md` — visão do produto, waves e sprints.

---

## 2. Anonimato

**Proibido** em qualquer arquivo do repo, salvo whitelist:
- Nomes de modelos e provedores de IA (lista canônica em `scripts/check_anonymity.sh`).
- Assinaturas pessoais, nomes próprios, emails.
- Emojis.

**Whitelist por arquivo** (ver `scripts/check_anonymity.sh`):
- `LICENSE`, `NOTICE`, `CHANGELOG.md`.
- `docs/process/**` (artefatos vivos de processo).
- `docs/history/**` (arquivo morto: auditorias antigas, versões anteriores).
- `tests/fixtures/**`.
- O próprio script.

Violação bloqueia CI. Rodar local antes de commit: `./scripts/check_anonymity.sh`.

---

## 3. Idioma

- **PT-BR:** código, comentários, docstrings, commits, docs, logs visíveis ao usuário (níveis `INFO`+).
- **EN preservado:** termos retornados por APIs (`errno` strings, flags POSIX, nomes de protocolos, identificadores de sistema), stack traces, mensagens `DEBUG`.

Exemplos:
```python
logger.error("falha ao ler hidraw: Permission denied")   # OK
logger.warn("pacote UDP descartado: version desconhecida")  # OK
logger.error("permissão negada ao ler hidraw")           # ERRADO (traduziu errno)
logger.error("hidraw read failed")                       # ERRADO (deveria ser PT-BR)
```

Acentuação correta é obrigatória. Nunca escrever `funcao`, `validacao`, `descricao`, etc.

---

## 4. Estrutura `docs/`

- `docs/adr/` — Architecture Decision Records, um por arquivo, numerados.
- `docs/protocol/` — especificações de protocolo (UDP, IPC, trigger modes).
- `docs/usage/` — guias ao usuário final.
- `docs/process/` — artefatos vivos do processo de design: decisões atuais, roadmap, dúvidas em aberto.
- `docs/process/discoveries/` — **diário de descobertas**: uma jornada por arquivo (sintoma → hipóteses → causa → solução → lições). Criar sempre que aparecer surpresa, conflito de ambiente ou hipótese desfeita. Ver `docs/process/discoveries/README.md` e `TEMPLATE.md`.
- `docs/history/` — arquivo morto: auditorias antigas, RFCs rejeitadas, versões anteriores superadas.

Regra de movimentação: quando um documento de `docs/process/` é substituído por uma versão mais nova, a versão antiga desce para `docs/history/` com sufixo de versão (`_V1`, `_V2`).

Diário de descobertas nunca é arquivado — memória permanente.

---

## 5. Workflow de issue

```
gh issue list --label "status:ready" --label "ai-task"
         ↓
gh issue edit N --add-label "status:in-progress" --remove-label "status:ready"
         ↓
gh issue develop N --checkout
         ↓
      [implementar + testar + checks locais]
         ↓
./scripts/check_anonymity.sh    → VAZIO
ruff check src/ tests/          → VERDE
mypy src/hefesto                → VERDE
pytest tests/unit -v            → VERDE
         ↓
git commit -m "feat: descrição técnica impessoal"
         ↓
gh pr create --body "Closes #N"
```

Meta-regra 9.7: zero follow-up acumulado. Cada achado colateral vira issue nova com ID antes do merge, nunca "TODO depois" inline.

---

## 6. Validação runtime-real (meta-regra 9.8)

Pytest sozinho não basta para sprints que tocam runtime. Sprints W1.3+ exigem smoke boot real via `FakeController`:

```bash
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb ./run.sh --smoke
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=bt  ./run.sh --smoke
```

Sprints que tocam TUI exigem proof-of-work visual (regra 13 do arquivo global do CLI):

```bash
scrot /tmp/hefesto_tui_$(date +%s).png
sha256sum /tmp/hefesto_tui_*.png
```

PNG, sha256 e descrição multimodal vão no corpo do PR.

---

## 7. Limites

- Máximo 800 linhas por arquivo (exceto `tests/`, configs, registries).
- Arquivo único sempre (sem fragmentos).
- `# TODO`/`# FIXME` inline proibidos — sempre issue com ID.
- `print()`/`console.log()` proibidos — usar `structlog`.
- Paths via `pathlib.Path` + `platformdirs`, nunca absolutos hardcoded.
- Error handling explícito, nunca silent fail.

---

*"A forja não revela o ferreiro. Só a espada."*
