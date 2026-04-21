# POLISH-CAPS-01 — Acentuação e capitalização consistente em toda a GUI

**Tipo:** polish (UX + i18n PT-BR).
**Modelo sugerido:** sonnet (tarefa repetitiva de varredura).
**Estimativa:** 1 iteração.
**Dependências:** pode rodar em paralelo com FEAT-MOUSE-01. Merge após todos mergeados.

---

## Contexto

Auditoria visual da GUI em 2026-04-21 achou strings visíveis ao usuário em caixa baixa sem Title Case e/ou sem acentuação PT-BR. A regra canônica (AI.md §1) obriga acentuação completa em strings PT-BR; UX consistente obriga capitalização cuidada em labels humanos.

## Regras canônicas (aplicar TODAS)

1. **Acentuação PT-BR completa** em qualquer palavra portuguesa visível ao usuário. Nunca `funcao`, `nao`, `configuracao`, `descricao`, `simbolo`, `proximo`, etc. Sempre `função`, `não`, `configuração`, `descrição`, `símbolo`, `próximo`.
2. **Primeira letra maiúscula** em valores exibidos como status humano: `online`/`offline`/`active`/`disabled`/`enabled`/`reconectando` → `Online`, `Offline`, `Ativo`, `Desativado`, `Ativado`, `Reconectando`. Idem `conectado`/`desconectado` → `Conectado` / `Desconectado`.
3. **Siglas em maiúsculas**: `usb` → `USB`, `bt` → `BT`, `ipc` → `IPC`, `udp` → `UDP`, `cli` → `CLI`, `tui` → `TUI`, `gui` → `GUI`.
4. **Markup Pango do header de conexão** em Title Case curto:
   - `● conectado via usb` → `● Conectado Via USB`
   - `● conectado via bt` → `● Conectado Via BT`
   - `◐ tentando reconectar...` → `◐ Tentando Reconectar...`
   - `○ daemon offline` → `○ Daemon Offline`
   - `○ controle desconectado` → `○ Controle Desconectado`
5. **Rótulos de botões em Title Case**: `Ver logs` → `Ver Logs`, `Reiniciar daemon` → `Reiniciar Daemon`, `Start`/`Stop`/`Restart`/`Atualizar` permanecem (ou traduzir para `Iniciar`/`Parar`/`Reiniciar`/`Atualizar` — decidir consistente, **preferir português em todos**).
6. **Nome do perfil** NÃO é capitalizado (é identificador, preservar caixa original: `fallback`, `shooter`, `driving`, `cyberpunk_driving`).
7. **Label fixo "Unit: hefesto.service"** (da SIMPLIFY-UNIT-01) — mantém caixa baixa do nome do service (é identificador systemd).
8. **Janela**: título da barra do WM `Hefesto - DSX para Unix` (sem versão). Aplicar no `<property name="title">` da `GtkWindow` principal em `main.glade`.
9. **Valor de transporte no painel Estado**: `usb` → `USB`, `bt` → `BT` (toda sigla maiúscula).
10. **Valor de Daemon no painel Estado**: `online`/`offline`/`reconectando` → `Online`/`Offline`/`Reconectando`.
11. **"nenhum"** (rótulo placeholder de botões pressionados) → `Nenhum`.
12. **Tooltip e mensagens de erro** visíveis ao usuário: mesmas regras.

## Escopo

Varrer e ajustar strings visíveis ao usuário em:

- `src/hefesto/gui/main.glade` — todos `<property name="label">`, `<property name="title">`, `<property name="tooltip-text">`, `<property name="placeholder-text">`.
- `src/hefesto/app/actions/*.py` — strings passadas para `.set_label()`, `.set_markup()`, `.set_text()`, `.set_tooltip_text()`, `Gtk.MessageDialog(...)`, strings que viram label de widget.
- `src/hefesto/app/app.py`, `src/hefesto/app/tray.py` — mesma regra.

NÃO alterar:
- Logs (`logger.info/warning/error` em nível técnico, ficam em PT-BR com acentuação correta mas sem Title Case forçado).
- Identificadores (nomes de perfil, nome de unit systemd, chaves JSON, nomes de método IPC).
- Docstrings internos (regras separadas, baixa prioridade).
- Strings de teste (`tests/**`).

## Critérios de aceite

- [ ] Todos os markups Pango em `status_actions.py` e `daemon_actions.py` em Title Case conforme regra 4.
- [ ] Título da janela GTK = `Hefesto - DSX para Unix`.
- [ ] `grep -niE "\bnao\b|funcao|validacao|configuracao|descricao|proximo|simbolo|botao|sao" src/hefesto/app/` vazio (acentuação completa).
- [ ] `grep -niE "conectado via (usb|bt)\b" src/hefesto/app/` com matches apenas em Title Case.
- [ ] Captura antes/depois na aba Status mostrando o header em Title Case.
- [ ] Captura na aba Daemon mostrando `Status: ● Ativo` (se decidir traduzir) e botões em PT-BR.
- [ ] `.venv/bin/pytest tests/unit -q` verde.
- [ ] `./scripts/check_anonymity.sh` OK.
- [ ] `.venv/bin/ruff check src/ tests/` OK.

## Proof-of-work

```bash
# Captura antes
.venv/bin/python -m hefesto.app.main &
sleep 3
WID=$(xdotool search --name "Hefesto" | head -1)
TS=$(date +%Y%m%dT%H%M%S)
import -window "$WID" "/tmp/hefesto_polish_caps_antes_status_${TS}.png"
# Navegar aba Daemon (click na coord)
pkill -f hefesto.app.main

# ...aplicar fix...

# Captura depois
.venv/bin/python -m hefesto.app.main &
sleep 3
WID=$(xdotool search --name "Hefesto" | head -1)
TS=$(date +%Y%m%dT%H%M%S)
import -window "$WID" "/tmp/hefesto_polish_caps_depois_status_${TS}.png"
pkill -f hefesto.app.main

# Verificação textual
grep -iE "conectado via" src/hefesto/app/actions/status_actions.py
grep -iE "offline|online|reconectando|reconectar" src/hefesto/app/actions/*.py

# Suite
.venv/bin/pytest tests/unit -q --no-header
./scripts/check_anonymity.sh
.venv/bin/ruff check src/ tests/
```

## Notas

- Se o hook `guardian.py` reclamar de algum caractere funcional (U+25CF, U+25CB, U+25D0, etc.), é falso positivo — preservar.
- Algumas strings são construídas em runtime via f-string (ex.: `f'● conectado via {transport}'`). Nesse caso, aplicar `.upper()` no transport e capitalizar literal: `f'● Conectado Via {transport.upper()}'`.
- Se encontrar string que não cabe em Title Case (ex.: frase longa descritiva), preservar sentence case (primeira letra maiúscula, resto natural).
- Commit final: `polish: POLISH-CAPS-01 acentuação PT-BR e capitalização consistente na GUI`.
