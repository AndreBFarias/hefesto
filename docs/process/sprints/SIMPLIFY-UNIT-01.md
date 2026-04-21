# SIMPLIFY-UNIT-01 — Remover dualidade hefesto.service / hefesto-headless.service

**Tipo:** refactor + UX simplification.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

## Contexto

A GUI atual expõe na aba Daemon um dropdown `Unit:` com duas opções: `hefesto.service` (normal) e `hefesto-headless.service` (sem GUI). Sintomas do problema visto pelo usuário em 2026-04-21:

- Ao selecionar `hefesto-headless.service` no dropdown, a UI mostra "unit não instalada em ~/.config/systemd/user/" em vermelho, Auto-start desabilitado, Start/Stop/Restart sem efeito — estado confuso para usuário que apenas clicou curioso.
- Instalador `install.sh` cria só `hefesto.service`. Nunca cria `hefesto-headless.service`. A segunda opção é fantasma.
- Na prática nenhum usuário final precisa da versão headless: o Hefesto é um daemon de gatilhos adaptativos para DualSense num desktop com jogos — contexto inerentemente GUI-able. Headless só faria sentido em laboratório/CI, já coberto por pytest.

## Decisão

Eliminar a dualidade. `hefesto.service` vira a única unidade oficial. `hefesto-headless.service` é removido dos assets e de toda referência.

## Critérios de aceite

- [ ] `assets/hefesto-headless.service` — deletado.
- [ ] `src/hefesto/daemon/service_install.py` — remover `SERVICE_HEADLESS`, `detect_installed_units` vira `detect_installed_unit` (singular) retornando `"hefesto"` ou `None`. `ServiceInstaller` só manipula a unit normal.
- [ ] `src/hefesto/app/actions/daemon_actions.py` — remover dropdown `daemon_unit_combo`. Label "Unit:" fica estático mostrando `hefesto.service`. `_selected_unit()` removido; todas chamadas usam `hefesto` hardcoded.
- [ ] `src/hefesto/gui/main.glade` — substituir `GtkComboBoxText id="daemon_unit_combo"` por `GtkLabel` fixo com texto `hefesto.service`.
- [ ] `src/hefesto/cli/cmd_daemon.py` (se existir) — remover flags ou subcomandos relacionados a headless.
- [ ] Testes unitários atuais em `tests/unit/test_service_install.py` (ou similar) — atualizar para a API simplificada.
- [ ] `docs/process/HEFESTO_DECISIONS_V3.md` V3-3 (detect_installed_unit defensivo) — atualizar menção plural/singular.
- [ ] `docs/adr/004-systemd-user-service.md` — se menciona headless, remover.
- [ ] `scripts/install_udev.sh` — não mexe (já não toca hefesto-headless).
- [ ] `install.sh` — não mexe (já só instala a normal).
- [ ] Proof-of-work: GUI aberta mostra aba Daemon com rótulo `hefesto.service` fixo, status active, botão Reiniciar daemon habilitado. Captura antes/depois.
- [ ] `.venv/bin/pytest tests/unit -q` verde; `./scripts/check_anonymity.sh` OK; `ruff` OK.

## Arquivos tocados (previsão)

- `assets/hefesto-headless.service` (delete)
- `src/hefesto/daemon/service_install.py`
- `src/hefesto/app/actions/daemon_actions.py`
- `src/hefesto/gui/main.glade`
- `tests/unit/test_service_install.py` (se aplicável)
- `docs/process/HEFESTO_DECISIONS_V3.md`

## Fora de escopo

- Mudar unit file `hefesto.service` em si.
- Adicionar variantes (ex.: `hefesto-debug.service`).
- Tocar no IPC/UDP/autoswitch.

## Notas para o executor

- `detect_installed_unit()` retorna `"hefesto"` quando o unit está enabled/enabled-runtime; `None` caso contrário.
- O botão "Reiniciar daemon" (UX-RECONNECT-01) depende de `detect_installed_units()` plural — adaptar a chamada.
- Se main.glade for editado por Cambalache, registrar apenas o nó alterado.
