# UI-POLISH-EMULACAO-DAEMON-STATUS-01 — Alinhamento + tipografia + polish visual

**Tipo:** polish.
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:polish`, `ui`, `ai-task`, `status:ready`.

## Contexto

Auditoria visual pelo usuário em 2026-04-23 (v2.1.0) identificou 4 itens de polish na GUI:

1. **Aba Emulação**: tabelas de info (`uinput`, `Device`, `VID:PID`, `Gamepads`) estão centralizadas/deslocadas; deveriam estar alinhadas à esquerda. O mesmo para a tabela "Combo sagrado".
2. **Aba Emulação**: string "uinput" aparece minúscula; devia estar "UINPUT" (é acrônimo de subsystem do kernel).
3. **Aba Emulação**: botões "Testar criação de device virtual", "Atualizar", "Editar daemon.toml" têm padding distinto do texto "Para jogos que só aceitam..." abaixo. Alinhar padding lateral de ambos ao padding das tabelas superiores.
4. **Aba Daemon**: `GtkTextView` com saída do `systemctl status` usa fundo escuro demais (quase preto). Deixar levemente mais cinza (`#2a2a2a` ou similar do tema Dracula) para contrastar melhor com o painel.
5. **Aba Status**: título da seção lê "Gatilhos (ao vivo)". Remover "(ao vivo)" — redundante, tudo no status é ao vivo.

Screenshots de referência anexados em issue/thread do usuário (não persistidos no repo para evitar drift).

## Decisão

Sprint puramente cosmética. Toca `src/hefesto/gui/main.glade` (alinhamento + texto "UINPUT"), `src/hefesto/gui/theme.css` (fundo `TextView` na aba Daemon), `src/hefesto/app/actions/status_actions.py` (título "Gatilhos").

Usar skill `validacao-visual` — esta sprint **exige** screenshot antes/depois de cada mudança.

## Critérios de aceite

- [ ] Aba Emulação: as 4 linhas de info (`uinput`, `Device`, `VID:PID`, `Gamepads`) `halign=START` com `margin-start` canônico do tema.
- [ ] Aba Emulação: tabela "Combo sagrado" também `halign=START` e mesmo `margin-start`.
- [ ] Aba Emulação: texto "uinput: Disponível" vira "UINPUT: Disponível" (label e log).
- [ ] Aba Emulação: row de botões ("Testar criação de device virtual", "Atualizar", "Editar daemon.toml") e bloco de texto "Para jogos que só aceitam..." compartilham o mesmo `margin-start` das tabelas.
- [ ] Aba Daemon: `TextView` de saída com `background-color: #2a2a2a` via `theme.css` (classe CSS nova ou seletor existente).
- [ ] Aba Status: label da seção lê "Gatilhos" (sem "(ao vivo)").
- [ ] Screenshots antes/depois capturados via skill `validacao-visual`.
- [ ] Gates canônicos verdes: pytest, ruff, anonimato, acento, smoke USB+BT.

## Arquivos tocados

- `src/hefesto/gui/main.glade` (alinhamentos + texto UINPUT).
- `src/hefesto/gui/theme.css` (fundo TextView Daemon).
- `src/hefesto/app/actions/status_actions.py` (label Gatilhos).
- `tests/unit/test_gui_emulacao.py` (se existir, atualizar expectativas; senão, ignorar).

## Proof-of-work runtime

```bash
# GUI visual
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.app.main &
GUI_PID=$!
sleep 2
# Capturar Emulação
xdotool search --name "Hefesto" | head -1 | xargs -I{} xdotool windowactivate {}
# Clicar na aba Emulação via keyboard shortcut ou coordinates
import -window "$(xdotool search --name 'Hefesto' | head -1)" /tmp/hefesto_v22_emulacao.png
# Repetir para Daemon e Status
kill $GUI_PID

.venv/bin/pytest tests/unit -q
.venv/bin/ruff check src/ tests/
./scripts/check_anonymity.sh
python3 scripts/validar-acentuacao.py --all
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb HEFESTO_SMOKE_DURATION=2.0 ./run.sh --smoke
```

## Fora de escopo

- Renomear "Mouse" → "Mouse e Teclado" (sprint FEAT-MOUSE-TECLADO-COMPLETO-01).
- Cores diferenciadas nos botões do footer (sprint UI-FOOTER-BUTTON-COLORS-01).
- Polish de layout da aba Perfis (sprint UI-PROFILES-LAYOUT-POLISH-01).
