# UI-GLOBAL-FOOTER-ACTIONS-01 — Rodapé global com Aplicar / Salvar Perfil / Importar / Default

**Tipo:** UI (arquitetural visual).
**Wave:** V1.1 — fase 6.
**Estimativa:** 1-2 iterações.
**Dependências:** **FEAT-PROFILE-STATE-01** (DraftConfig), **FEAT-PROFILES-PRESET-06** ("Meu Perfil").

---

**Tracking:** issue a criar.

## Pedido do usuário (2026-04-22)

> No rodapé onde temos Cor RG... No lado direito alinhado a direita desse rodapé seria botões, Aplicar, Salvar Perfil, Importar, Default. E esses botões serem funcionais pra isso.

Captura Image 5 mostra rodapé atual: `Cor RGB (97, 53, 131) a 9% aplicada` (status bar textual). Queremos 4 botões alinhados à direita que operem sobre o `DraftConfig` inteiro (todas as abas).

## Layout do novo rodapé

```
+----------------------------------------------------------------+
| Cor RGB (97, 53, 131) a 9% aplicada      [Aplicar] [Salvar Perfil] [Importar] [Restaurar Default] |
+----------------------------------------------------------------+
```

- Lado esquerdo: `Gtk.Statusbar` atual (preservado).
- Lado direito: `Gtk.Box` horizontal com 4 `Gtk.Button`, packed END.

## Ações

### 1. Aplicar
Envia `DraftConfig` inteiro pro daemon via IPC `profile.apply_draft` (FEAT-PROFILE-STATE-01). Durante a transação (~500ms), desabilita os 4 botões e exibe spinner. Toast no statusbar: "Aplicando perfil inteiro..." → "OK" ou "ERRO".

### 2. Salvar Perfil
Abre `Gtk.Dialog` modal:
- Campo `Nome` (pré-preenchido: perfil ativo).
- Toggle `Sobrescrever se existir` (default ON quando nome == perfil ativo).
- Botões `Cancelar` / `Salvar`.

Ao confirmar: `DraftConfig.to_profile(name)` → `save_profile(path, profile)` → refresh da aba Perfis.

Se `nome` for `meu_perfil` ou `Meu Perfil`, escreve em `meu_perfil.json` (slot canônico do usuário — FEAT-PROFILES-PRESET-06).

### 3. Importar
`Gtk.FileChooserDialog` filtrado pra `*.json`. Ao selecionar:
1. Carrega via `json.load`.
2. Valida via `Profile.model_validate`.
3. Copia pro `~/.config/hefesto/profiles/<nome>.json` (reusa nome do perfil importado, não do arquivo).
4. Se nome já existe, dialog "Perfil com esse nome já existe. Sobrescrever / Renomear / Cancelar".
5. Refresh aba Perfis.

### 4. Restaurar Default
Dialog de confirmação: "Isso vai restaurar o `meu_perfil` para a cópia original (Navegação). Continuar?".

Se confirmar:
- Copia `assets/profiles_default/meu_perfil.json` → `~/.config/hefesto/profiles/meu_perfil.json`.
- Recarrega `DraftConfig` via `from_profile(meu_perfil)`.
- Refresh todas as abas.

**NÃO** toca outros perfis (navegacao, fps etc.) — só o slot do usuário.

## Critérios de aceite

- [ ] `src/hefesto/gui/main.glade`: rodapé reconstruído como descrito.
- [ ] `src/hefesto/app/actions/footer_actions.py` (NOVO): classe `FooterActionsMixin` com handlers `on_apply_draft`, `on_save_profile`, `on_import_profile`, `on_restore_default`.
- [ ] `HefestoApp`: incorpora `FooterActionsMixin` na MRO.
- [ ] `src/hefesto/app/gui_dialogs.py` (NOVO): helpers `prompt_profile_name`, `prompt_overwrite_existing`, `confirm_restore_default` para abstrair `Gtk.Dialog` reutilizável.
- [ ] Handlers instrumentam `Gtk.Statusbar` com mensagens: "Aplicando...", "Perfil salvo em ~/.config/hefesto/profiles/X.json", etc.
- [ ] Durante `on_apply_draft`, desabilita todos os botões das abas via `_freeze_ui(True)` e reabilita via callback.
- [ ] Teste `tests/unit/test_footer_actions.py`: monkeypatch de `ipc_bridge.apply_draft`, `save_profile`, etc. Verifica fluxo feliz + erros.
- [ ] Teste `tests/unit/test_footer_restore_default.py`: com tmp_path como profiles dir, cria `meu_perfil.json` modificado; executa `restore_default()`; conteúdo volta ao asset default.
- [ ] Proof-of-work visual: screenshot rodapé + cada dialog.

## Arquivos tocados

- `src/hefesto/gui/main.glade` (rodapé)
- `src/hefesto/app/actions/footer_actions.py` (novo)
- `src/hefesto/app/gui_dialogs.py` (novo)
- `src/hefesto/app/app.py` (MRO)
- `tests/unit/test_footer_actions.py` (novo)
- `tests/unit/test_footer_restore_default.py` (novo)

## Notas para o executor

- Rodapé é `Gtk.Box` horizontal; `Gtk.Statusbar` ocupa espaço flexível (`expand=True, fill=True`); box de botões packed END com spacing 6.
- Tooltips obrigatórios em cada botão:
  - Aplicar: "Envia toda a configuração (gatilhos, LEDs, rumble, mouse) ao controle"
  - Salvar Perfil: "Salva o estado atual como um perfil nomeado"
  - Importar: "Carrega um perfil de arquivo .json"
  - Restaurar Default: "Restaura o perfil 'Meu Perfil' ao estado original"
- `_freeze_ui(freeze: bool)`: itera pelos widgets das abas via `self.builder.get_objects()` filtrando pelos que têm ID conhecido (lista em `FROZEN_WIDGET_IDS`).
- Evitar threads complexas: `on_apply_draft` chama `ipc_bridge.apply_draft` em executor, callback via `GLib.idle_add(...)`.

## Fora de escopo

- Undo do "Restaurar Default" (V2).
- Sincronização de perfis com nuvem (V2).
- Compartilhar perfis via URL (V2).
