---
name: Sprint Task
about: Tarefa rastreável de uma sprint do roadmap
labels: ["type:feature", "ai-task", "status:ready"]
---

## Contexto
Sprint: **W?.?**
Referência: `HEFESTO_PROJECT.md` + `docs/process/HEFESTO_DECISIONS_V2.md` + `V3.md`

## Critérios de aceite
- [ ] ...
- [ ] `./scripts/check_anonymity.sh` retorna vazio
- [ ] `ruff check src/ tests/` verde
- [ ] `mypy src/hefesto_dualsense4unix` verde
- [ ] `pytest tests/unit -v` verde
- [ ] Documentação atualizada se aplicável

## Runtime (se sprint toca runtime)
- [ ] `./run.sh --smoke` (FakeController USB) passa
- [ ] `./run.sh --smoke --bt` (FakeController BT) passa
- [ ] Itens correspondentes em `CHECKLIST_MANUAL.md` preenchidos por revisor com device

## UI (se sprint toca `src/hefesto_dualsense4unix/tui/**`)
- [ ] Screenshot `/tmp/hefesto_<area>_<ts>.png` anexado no PR
- [ ] `sha256sum` do PNG registrado
- [ ] Descrição multimodal 3–5 linhas (elementos, acentuação PT-BR, contraste)

## Follow-ups
- [ ] Zero `# TODO`/`# FIXME` novos inline (meta-regra 9.7)
- [ ] Achados colaterais viraram issues novas com ID
