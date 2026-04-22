# UI-PROFILES-EDITOR-SIMPLE-01 — Editor de perfil em 2 modos (simples e avançado)

**Tipo:** UI/UX.
**Wave:** V1.1 — fase 6.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** issue a criar.

## Sintoma (reportado em 2026-04-22)

> aquela parte de editor de Perfil dessa forma não faz sentido é pro user comum usar, não sei se faz sentido termos esse bloco dessa forma, com essas opções e termos.

Captura Image 6:
- Campo `Nome`, `Prioridade`, `Tipo de match`, `window_class: firefox,Chromium`, `title_regex: regex (re.search)`, `process_name: CSV: doom.x86_64,celeste`.
- Legenda: "AND entre campos preenchidos, OR dentro de cada lista. Campos vazios são ignorados."

Isso é DevEx. Para user comum não faz sentido "window_class" nem "re.search".

## Decisão

Dois modos no editor, alternados por toggle `Modo avançado`:

### Modo simples (default)
Pré-preencher listas humanamente. Campo **"Aplica a:"** com opções radio ou checkboxes em categorias:

- ○ **Qualquer janela** (mapeia pra `MatchAny`)
- ○ **Jogos da Steam** (mapeia pra `process_name: ["steam"]` + `title_regex: ".*"`)
- ○ **Navegador** (mapeia pra `window_class: ["firefox", "chromium", "brave", "google-chrome"]`)
- ○ **Terminal** (mapeia pra `window_class: ["gnome-terminal", "alacritty", "kitty", "konsole"]`)
- ○ **Editor de código** (mapeia pra `window_class: ["code", "zed", "neovide"]`)
- ○ **Jogo específico** → abre campo livre "Nome do jogo" que traduz internamente pra `process_name: [nome]`.

Campos sempre visíveis: `Nome`, `Prioridade` (slider 0-100 em vez de `-` `+`), `Aplica a`.

### Modo avançado (toggle no topo)
Mostra os campos crus `window_class`, `title_regex`, `process_name` + explicação.

Toggle persiste em `~/.config/hefesto/gui_preferences.json` (novo arquivo) — lembra preferência entre sessões.

## Contrato interno

`ProfilesActionsMixin._save_profile_from_editor`:
```python
def _save_profile_from_editor(self) -> Profile:
    if self._mode_advanced:
        # caminho atual — lê diretamente
        criteria = MatchCriteria(
            window_class=split_csv(self._get("profile_window_class").get_text()),
            title_regex=self._get("profile_title_regex").get_text() or None,
            process_name=split_csv(self._get("profile_process_name").get_text()),
        )
    else:
        # traduz radio seleção em MatchCriteria
        criteria = _match_from_simple_choice(
            choice=self._selected_simple_choice(),
            custom_name=self._get("profile_simple_custom_name").get_text() or None,
        )
    return Profile(
        name=self._get("profile_name").get_text(),
        priority=int(self._get("profile_priority_scale").get_value()),
        triggers=..., leds=..., rumble=...,
        match=criteria if criteria else MatchAny(),
    )
```

Helper `_match_from_simple_choice` mora em `src/hefesto/profiles/simple_match.py` (NOVO):

```python
SIMPLE_MATCH_PRESETS = {
    "any":       MatchAny(),
    "steam":     MatchCriteria(process_name=["steam"]),
    "browser":   MatchCriteria(window_class=["firefox", "chromium", "brave", "google-chrome"]),
    "terminal":  MatchCriteria(window_class=["gnome-terminal", "alacritty", "kitty", "konsole"]),
    "editor":    MatchCriteria(window_class=["code", "zed", "neovide"]),
}

def from_simple_choice(choice: str, custom_name: str | None = None) -> MatchCriteria | MatchAny:
    if choice == "game" and custom_name:
        return MatchCriteria(process_name=[custom_name.lower()])
    return SIMPLE_MATCH_PRESETS.get(choice, MatchAny())
```

## Critérios de aceite

- [ ] `src/hefesto/gui/main.glade`: aba Perfis reorganizada. Editor contém:
  - Toggle superior "Modo avançado" (`Gtk.Switch`).
  - Stack com 2 páginas `simples` e `avancado`.
  - Página `simples`: `Nome`, `Prioridade` (Gtk.Scale 0-100), `Aplica a` (radio buttons: Qualquer/Steam/Navegador/Terminal/Editor/Jogo específico), campo `Jogo específico` (entry, escondido a menos que radio "Jogo específico" ativo).
  - Página `avancado`: campos atuais `window_class`, `title_regex`, `process_name` + legenda.
  - Botão `Salvar` no rodapé do editor.
- [ ] `src/hefesto/profiles/simple_match.py` (NOVO): presets + `from_simple_choice`.
- [ ] `src/hefesto/app/actions/profiles_actions.py`:
  - Lê/escreve `gui_preferences.json` (`advanced_editor: bool`).
  - Handler de toggle alterna stack.
  - `_save_profile_from_editor` bifurca por modo.
  - Ao carregar um perfil existente, se `match` bate com um preset simples, seleciona-o; caso contrário, força modo avançado (não perde info).
- [ ] `src/hefesto/app/gui_prefs.py` (NOVO): utilitários pra ler/escrever `gui_preferences.json`.
- [ ] Teste `tests/unit/test_simple_match.py`: cada preset retorna MatchCriteria correto; `game` sem custom_name retorna MatchAny.
- [ ] Teste `tests/unit/test_profile_editor_roundtrip.py`: criar perfil via modo simples → salva em JSON → recarrega → editor volta pra modo simples com mesma seleção.
- [ ] Proof-of-work visual: screenshot aba Perfis modo simples, depois modo avançado.

## Arquivos tocados

- `src/hefesto/gui/main.glade`
- `src/hefesto/profiles/simple_match.py` (novo)
- `src/hefesto/app/actions/profiles_actions.py`
- `src/hefesto/app/gui_prefs.py` (novo)
- `tests/unit/test_simple_match.py` (novo)
- `tests/unit/test_profile_editor_roundtrip.py` (novo)

## Notas para o executor

- **Slider de prioridade** substituindo `SpinButton`: range 0-100, step 5, valor atual exibido ao lado. Perfil `fallback` tem prioridade -1000 mas o editor de usuário limita a 0-100 (quem edita fallback é outro caminho).
- Detecção de preset ao carregar perfil: comparar `profile.match` com cada `SIMPLE_MATCH_PRESETS[*]` via igualdade de campos; se bate, seleciona; se não bate, forçar modo avançado preservando o mesmo objeto pra não perder dados.
- **Tooltip** nos radios: "Steam" → "Qualquer processo filho do steam.exe"; "Jogo específico" → "Digite o nome do executável (ex.: eldenring)".
- Manter botão `Salvar` como único commit. Não salvar automaticamente enquanto o usuário digita.

## Fora de escopo

- Wizard de detecção automática ("clique na janela ativa pra capturar window_class") — V2.
- Preview dos efeitos do perfil (trigger, led) — já está em FEAT-PROFILE-STATE-01.
- Perfil compartilhável via export/import — **spec UI-GLOBAL-FOOTER-ACTIONS-01** (botão Importar).
