# FEAT-PROFILE-STATE-01 — Estado central de configuração (sync entre abas, commit atômico)

**Tipo:** feat (arquitetural).
**Wave:** V1.1 — fase 4.
**Estimativa:** 2 iterações.
**Dependências:** nenhuma. **Pré-requisito de:** UI-GLOBAL-FOOTER-ACTIONS-01, FEAT-PROFILES-PRESET-06 (linha "perfil do usuário").

---

**Tracking:** issue [#74](https://github.com/AndreBFarias/hefesto/issues/74) — fechada por PR com `Closes #74` no body.

## Contexto

Hoje cada aba (Gatilhos, Lightbar, Rumble, Mouse, Emulação) aplica mudanças direto no daemon via IPC — isoladamente. Trocar de aba perde o estado intermediário. Não há visão "estou configurando um perfil inteiro" vs "estou aplicando um efeito ao vivo". O usuário reforçou em 2026-04-22 que:

> As configs precisam ser lembradas ao trocar de abas ou aplicar. Elas precisam funcionar em conjunto.
> Falta um [botão] pra o usuário caso eu mexa em todas as abas e queira salvar tudo.

Essa spec cria o "cérebro" compartilhado que vai alimentar o rodapé global (UI-GLOBAL-FOOTER-ACTIONS-01) e o "perfil do usuário" (FEAT-PROFILES-PRESET-06).

## Decisão

Criar `DraftConfig` na camada GUI: pydantic v2 imutável (`frozen=True`, método `model_copy(update=...)` pra mudanças), com snapshot de tudo que o daemon pode aplicar. Cada aba bind duas direções:

- Widget → `DraftConfig.model_copy(update=...)` a cada `changed` signal.
- `DraftConfig` → widget a cada `switch-page` do `GtkNotebook` destino.

Botões "Aplicar" em cada aba continuam funcionando (teste rápido de efeito único, envia só aquele setor via IPC). Um **novo rodapé global** (spec UI-GLOBAL-FOOTER-ACTIONS-01) oferece 4 ações que consomem o `DraftConfig`:

- **Aplicar**: manda `profile.apply_draft {triggers, leds, rumble, mouse}` em uma transação.
- **Salvar Perfil**: abre dialog `Gtk.Dialog` pedindo nome; chama `draft.to_profile(name)`; salva em `~/.config/hefesto/profiles/<name>.json`; atualiza aba Perfis.
- **Importar**: `Gtk.FileChooserDialog` abre .json; valida via `Profile.model_validate`; copia pra `~/.config/hefesto/profiles/`.
- **Default**: reseta `DraftConfig` do perfil `fallback`.

Ao abrir a GUI, `DraftConfig` é inicializado do perfil ativo (`daemon.state_full`). Ao trocar perfil via aba Perfis ou tray, `DraftConfig` é refeito.

## Arquitetura

```
HefestoApp
 └── self.draft: DraftConfig (imutável, replace on change)
     ├── triggers: {left: TriggerDraft, right: TriggerDraft}
     │   └── TriggerDraft(mode: str, params: tuple[int, ...])
     ├── leds: LedsDraft
     │   ├── lightbar_rgb: (r, g, b) | None
     │   ├── lightbar_brightness: int (0-100)
     │   ├── player_leds: tuple[bool, bool, bool, bool, bool]
     │   └── mic_led: bool  # reservado p/ V2.0 (depende INFRA-SET-MIC-LED-01)
     ├── rumble: RumbleDraft
     │   ├── weak: int (0-255)
     │   ├── strong: int (0-255)
     │   └── policy: Literal["economia", "balanceado", "max", "auto"]  # FEAT-RUMBLE-POLICY-01
     ├── mouse: MouseDraft
     │   ├── enabled: bool
     │   ├── speed: int (1-12)
     │   └── scroll_speed: int (1-5)
     └── emulation: EmulationDraft
         └── xbox360_enabled: bool

 ├── StatusActionsMixin (read-only do daemon)
 ├── TriggersActionsMixin (edita draft.triggers)
 ├── LightbarActionsMixin (edita draft.leds)
 ├── RumbleActionsMixin (edita draft.rumble)
 ├── MouseActionsMixin (edita draft.mouse)
 └── ProfilesActionsMixin (carrega perfil → draft; salva draft → perfil)
```

Novo método IPC `profile.apply_draft {triggers, leds, rumble, mouse}` aplica em sequência atômica no daemon.

## Contrato IPC novo

```json
// request
{
  "jsonrpc": "2.0",
  "id": "42",
  "method": "profile.apply_draft",
  "params": {
    "triggers": {
      "left":  {"mode": "Galloping", "params": [0, 9, 7, 7, 10]},
      "right": {"mode": "Rigid",     "params": [0, 100, 255]}
    },
    "leds": {
      "lightbar_rgb": [128, 0, 255],
      "lightbar_brightness": 80,
      "player_leds": [true, true, true, true, true]
    },
    "rumble": {"weak": 40, "strong": 80, "policy": "balanceado"},
    "mouse":  {"enabled": true, "speed": 6, "scroll_speed": 1}
  }
}

// response
{
  "jsonrpc": "2.0",
  "id": "42",
  "result": {"status": "ok", "applied": ["triggers", "leds", "rumble", "mouse"]}
}
```

Aplicação segue ordem canônica para evitar transiente desagradável: **leds → triggers → rumble → mouse**. Se qualquer setor falhar, loga `warning` mas continua (best-effort; nenhum setor é bloqueante para os outros).

## Critérios de aceite

- [ ] `src/hefesto/app/draft_config.py` (NOVO): pydantic v2 `DraftConfig` + `TriggerDraft`, `LedsDraft`, `RumbleDraft`, `MouseDraft`, `EmulationDraft`. Método `from_profile(profile: Profile) -> DraftConfig` e `to_profile(self, name: str, priority: int = 5) -> Profile`. `DraftConfig.default() -> DraftConfig` cria instância vazia com defaults seguros.
- [ ] `HefestoApp.__init__` cria `self.draft = DraftConfig.default()`. `HefestoApp.show()` e `run()` chamam `self._load_draft_from_active_profile()` (lê via IPC `daemon.state_full` + `profile.get_active`).
- [ ] Cada `*ActionsMixin` ganha:
  - `_refresh_widgets_from_draft()` — popula widgets a partir de `self.draft.<seção>`.
  - Handlers de signal atualizam `self.draft` via `model_copy`.
- [ ] `GtkNotebook switch-page` signal: handler dispara `_refresh_widgets_from_draft()` da aba destino.
- [ ] `src/hefesto/daemon/ipc_server.py`: handler `profile.apply_draft` aplica triggers+leds+rumble+mouse em sequência. Retorna lista `applied` com setores que não falharam.
- [ ] `src/hefesto/app/ipc_bridge.py`: novo `apply_draft(draft_dict) -> bool`.
- [ ] Testes:
  - `tests/unit/test_draft_config.py`: (a) default seguro; (b) `from_profile` preserva campos; (c) `to_profile` gera JSON válido (round-trip via `Profile.model_validate`); (d) `model_copy` em uma seção preserva outras.
  - `tests/unit/test_ipc_apply_draft.py`: handler aplica cada setor; falha em um não bloqueia os outros; retorna lista correta.

## Proof-of-work

**Runtime:**
```bash
HEFESTO_FAKE=1 HEFESTO_FAKE_TRANSPORT=usb ./run.sh --smoke
.venv/bin/pytest tests/unit/test_draft_config.py tests/unit/test_ipc_apply_draft.py -v
```

**Visual (manual):**
1. Abrir GUI com DSX conectado.
2. Aba Gatilhos: trocar R2 para Galloping, ajustar 3 params.
3. Aba Lightbar: cor roxa 128,0,255 + brightness 80%.
4. Aba Rumble: weak 40, strong 80.
5. Voltar pra Gatilhos — valores preservados.
6. Aplicar (rodapé global — UI-GLOBAL-FOOTER-ACTIONS-01). Observar hardware responder a tudo.
7. Screenshot com `import -window`, sha256sum.

## Arquivos tocados (previsão)

- `src/hefesto/app/draft_config.py` (novo, ~220 linhas)
- `src/hefesto/app/app.py` (+ `self.draft`, `_load_draft_from_active_profile`)
- `src/hefesto/app/actions/triggers_actions.py`, `lightbar_actions.py`, `rumble_actions.py`, `mouse_actions.py`, `profiles_actions.py` (bind ao draft)
- `src/hefesto/app/ipc_bridge.py` (+ `apply_draft`)
- `src/hefesto/daemon/ipc_server.py` (+ handler `profile.apply_draft`)
- `tests/unit/test_draft_config.py` (novo)
- `tests/unit/test_ipc_apply_draft.py` (novo)

## Fora de escopo

- Histórico/undo de edições (V2).
- Sincronização multi-controle.
- Preview em tempo real sem aplicar (V2).
- UI do rodapé com botões Aplicar/Salvar/Importar/Default — **spec UI-GLOBAL-FOOTER-ACTIONS-01** consome esta sprint.

## Notas para o executor (haiku/dev jr)

- `DraftConfig` deve ser **pydantic v2** com `model_config = ConfigDict(frozen=True)`. Toda mudança cria nova instância via `model_copy(update={"seção": nova})`.
- **Não confundir com `Profile`** (`src/hefesto/profiles/schema.py`). `DraftConfig` é efêmero de GUI; `Profile` é persistível em JSON. Conversão via `from_profile`/`to_profile`.
- Bind GTK correto: conectar signals de cada widget UMA vez no `install_<tab>_tab` (não duplicar handlers).
- `_refresh_widgets_from_draft()` deve estar protegido por `self._guard_refresh=True/False` pra evitar loop (widget muda → trigger handler → set draft → trigger refresh → ...).
- Persistência de `DraftConfig` entre sessões da GUI NÃO faz parte desta sprint (é "in-memory only"). Usuário perde edições ao fechar a GUI, a não ser que tenha clicado em Salvar Perfil.
- Rota crítica de race: ao clicar "Aplicar" no rodapé, desabilitar botões de todas as abas via `Gtk.widget.set_sensitive(False)` durante a transação IPC (~500ms) para evitar aplicação concorrente. Reabilitar no callback `on_apply_draft_done`.

## Armadilhas previstas

- **A-06 bis**: campo novo em `LedsDraft`/`TriggersDraft`/`RumbleDraft` precisa atualizar mappers no daemon (`_to_led_settings`, `build_from_name`). Ver BRIEF A-06.
- **A-07 bis**: novo handler IPC precisa estar wireado no dict `self._handlers` de `IpcServer._dispatch` + teste.
- **A-10 bis**: `HefestoApp` já faz `acquire_or_takeover("gui")`. Não duplicar lock aqui.
