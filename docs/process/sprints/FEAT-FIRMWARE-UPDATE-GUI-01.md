# FEAT-FIRMWARE-UPDATE-GUI-01 — Aba Firmware na GUI Hefesto (wrapper dualsensectl)

**Tipo:** feat (GUI + integração nova).
**Wave:** V2.2.1 — patch release.
**Estimativa:** 2 iterações.
**Dependências:** nenhuma em código. Backend `dualsensectl >= branch main (2026-02-19)` instalado pelo usuário (ou detectado como ausente com mensagem guiada).

---

**Tracking:** label `type:feat`, `firmware`, `gui`, `P2-medium`, `status:ready`.

## Contexto

Survey de firmware (`docs/research/firmware-dualsense-2026-04-survey.md` §0) descobriu que `nowrep/dualsensectl` merged firmware update funcional em 2026-02-19. O protocolo DFU do DualSense deixou de ser hardware-blocked. Das 4 opções arquiteturais discutidas (§0.5), dono do projeto escolheu **opção A + UI**: wrapper subprocess do `dualsensectl` com interface gráfica em aba nova.

Esta sprint encerra a decisão arquitetural (70.1 PROPOSTA) e materializa o caminho A.

## Decisão

### Backend — `src/hefesto/integrations/firmware_updater.py`

Novo módulo com padrão semelhante a `audio_control.py`. Classe `FirmwareUpdater` encapsula `dualsensectl`:

```python
class FirmwareUpdater:
    BINARY = "dualsensectl"
    SUBPROCESS_TIMEOUT_INFO = 5.0     # info é rápido
    SUBPROCESS_TIMEOUT_UPDATE = 600.0 # update pode durar minutos

    def is_available(self) -> bool:
        """True se binário existe no PATH."""

    def get_info(self) -> FirmwareInfo | None:
        """Retorna dict com hardware, build_date, firmware_version, update_version,
        fw_type, sw_series. None se controle ausente ou dualsensectl faltando."""

    def apply(
        self,
        firmware_bin: Path,
        progress_callback: Callable[[int], None] | None = None,
    ) -> FirmwareApplyResult:
        """Aplica o blob. Callback recebe 0-100 (percentual).
        Levanta FirmwareError com subtipo (NotAvailable, InvalidBlob, Timeout, Internal)."""
```

### Frontend — `src/hefesto/app/actions/firmware_actions.py`

Novo mixin `FirmwareActionsMixin(WidgetAccessMixin)` seguindo padrão de `EmulationActionsMixin`:

- `install_firmware_tab()` — preenche labels iniciais, detecta ausência de `dualsensectl` e desabilita botões com mensagem.
- `on_firmware_check(btn)` — chama `get_info()` em thread, atualiza labels via `GLib.idle_add`.
- `on_firmware_browse(btn)` — abre `Gtk.FileChooserDialog` filtrado para `.bin`.
- `on_firmware_apply(btn)` — confirma com diálogo MAIÚSCULO, roda `apply()` em thread com progress callback, atualiza ProgressBar + Label via `GLib.idle_add`.

### UI — `main.glade`

Nova page em `main_notebook`:

- Título da aba: "Firmware".
- Label de versão atual (`firmware_current_version_label`).
- Botão "Verificar versão" (`firmware_check_btn`).
- Campo read-only com path do arquivo (`firmware_file_entry`).
- Botão "Selecionar .bin..." (`firmware_browse_btn`).
- Botão "Aplicar firmware" com classe CSS `btn-destructive` (`firmware_apply_btn`).
- ProgressBar (`firmware_progress_bar`).
- Label de status (`firmware_status_label`).
- Banner de aviso MAIÚSCULO: "RISCO DE BRICK. USE APENAS BLOBS OFICIAIS SONY DO CDN fwupdater.dl.playstation.net. NÃO DESCONECTE DURANTE O UPDATE."

### Wire-up — `src/hefesto/app/app.py`

- Importar `FirmwareActionsMixin` e adicionar na herança de `HefestoApp`.
- Chamar `self.install_firmware_tab()` no bootstrap junto com demais instaladores.

## Critérios de aceite

- [ ] `dualsensectl` ausente: aba mostra "dualsensectl não instalado. Instale via <link>" — botões desabilitados.
- [ ] `dualsensectl` presente + controle ausente: "Nenhum controle conectado." — botão "Aplicar" desabilitado, "Verificar" habilitado.
- [ ] `dualsensectl` presente + controle presente: versão atual + campos do info (hardware, build date, firmware_version, update_version) aparecem na UI.
- [ ] Seleção de arquivo rejeita não-`.bin` ou arquivos < 900KB (blob deve ser 950272 bytes; 900KB pega truncados).
- [ ] "Aplicar firmware" abre diálogo `Gtk.MessageDialog` com aviso de risco e exige clique em "Confirmar". Cancelamento volta ao estado anterior.
- [ ] Durante apply: ProgressBar atualiza 0-100%; label mostra "Aplicando firmware: XX%".
- [ ] Após sucesso: label mostra "Firmware atualizado de 0xAAAA para 0xBBBB."
- [ ] Após erro: label mostra mensagem clara + sugestão (ex: "Código 0x03 — blob inválido. Verifique se o arquivo é do modelo correto (DualSense vs Edge).").
- [ ] Durante apply, outras abas continuam responsivas (thread worker, `GLib.idle_add`).
- [ ] Sem `FirmwareUpdater.apply` rodando em thread principal.
- [ ] Testes unit em `tests/unit/test_firmware_updater.py` cobrem:
  - `is_available()` com binário ausente / presente.
  - `get_info()` parse correto de output padrão `dualsensectl info`.
  - `get_info()` retorna None em timeout, erro de subprocess.
  - `apply()` chama callback a cada linha "Writing firmware: XX%".
  - `apply()` levanta `FirmwareError` em erros 0x02/0x03/0x04/0x11/0xFF.
- [ ] Baseline pytest permanece verde (1041 tests + novos).
- [ ] ruff + mypy limpos nos novos arquivos.

## Arquivos tocados

### Novos
- `src/hefesto/integrations/firmware_updater.py`
- `src/hefesto/app/actions/firmware_actions.py`
- `tests/unit/test_firmware_updater.py`

### Modificados
- `src/hefesto/gui/main.glade` — adiciona página Firmware ao `main_notebook`.
- `src/hefesto/app/app.py` — inclui mixin + chamada `install_firmware_tab()`.
- `docs/process/SPRINT_ORDER.md` — ordem 70.2 MERGED + remove 70.1 PROPOSTA (consumida por esta sprint).
- `CHANGELOG.md` — entry v2.2.1 "Added: aba Firmware com integração dualsensectl".

## Fora de escopo

- **Download automático do CDN Sony** (helper baixar blob via `info.json` + `/fwupdate0004/`). Opcional para v2.3. Usuário baixa manualmente nesta versão.
- **Integração fwupd/LVFS** (opção C). Depende de Sony publicar no LVFS — fora do controle do projeto.
- **CLI `hefesto firmware apply`**. GUI-first; CLI pode vir em sprint separada se pedido.
- **Detecção automática de modelo** (DualSense vs Edge). Usuário seleciona o arquivo certo; mensagem de erro guia em caso de mismatch.
- **Rollback in-process**. Após o blob ser enviado não há rollback — confiança no dualsensectl.
- **Teste de integração com hardware real**. Impossível em CI; usuário confirma localmente.

## Proof-of-work

```bash
# 1. Sem dualsensectl instalado
which dualsensectl || echo "(ausente — aba deve mostrar mensagem guiada)"

# 2. pytest novo módulo
.venv/bin/pytest tests/unit/test_firmware_updater.py -v

# 3. pytest completo não regride
.venv/bin/pytest -q

# 4. mypy e ruff
.venv/bin/mypy src/hefesto/integrations/firmware_updater.py src/hefesto/app/actions/firmware_actions.py
.venv/bin/ruff check src/hefesto/integrations/firmware_updater.py src/hefesto/app/actions/firmware_actions.py

# 5. Validação visual (se INFRA-VENV-PYGOBJECT-01 estiver resolvido)
./run.sh --gui &
# esperado: aba "Firmware" aparece; clicar em Verificar e ler labels.
```

## Notas para o implementador

- `dualsensectl info` imprime em stdout chave:valor por linha. Parser robusto: `re.match(r'^(\w+[\w\s]*):\s*(.+)$', line)`.
- `dualsensectl update firmware.bin` imprime `Writing firmware: NN%` com `\r` (carriage return) — capturar via `stdout.readline()` em loop, não `stdout.read()`.
- Timeout de 10 min (`SUBPROCESS_TIMEOUT_UPDATE = 600.0`) é seguro; updates reais duram 1-3 min.
- Desabilitar botão "Aplicar" durante o processo (evita duplo-clique).
- Usar `Gio.AppInfo` ou equivalente para abrir link de instalação se `dualsensectl` ausente (package manager guideline).

## Riscos

| Risco | Severidade | Mitigação |
|---|---|---|
| Brick do controle | Crítico | Aviso MAIÚSCULO; só blob oficial; redirect para Updater Windows como rescue |
| Usuário seleciona blob errado (DualSense vs Edge) | Médio | Validação de tamanho; mensagem de erro clara se `dualsensectl` rejeitar |
| `dualsensectl` branch instável (API futura muda) | Baixo | Versão mínima documentada; parser tolerante a linhas extras |
| Thread worker deixa estado inconsistente se crashar | Baixo | `try/except` final retorna UI a "Falha: ..." com erro genérico |

## Referências

- Survey: `docs/research/firmware-dualsense-2026-04-survey.md` §0.
- Upstream: https://github.com/nowrep/dualsensectl/pull/53 (merged 2026-02-19).
- Padrão subprocess: `src/hefesto/integrations/audio_control.py`.
- Padrão mixin aba: `src/hefesto/app/actions/emulation_actions.py`.
