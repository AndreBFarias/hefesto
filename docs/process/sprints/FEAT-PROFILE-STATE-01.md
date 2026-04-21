# FEAT-PROFILE-STATE-01 — Estado central de configuração (sync entre abas, commit atômico)

**Tipo:** feat (arquitetural).
**Wave:** V1.1.
**Estimativa:** 1-2 iterações.
**Dependências:** nenhuma.

---

## Contexto

Hoje cada aba (Gatilhos, Lightbar, Rumble, Mouse, Emulação) aplica mudanças direto no daemon via IPC — isoladamente. Trocar de aba perde o estado intermediário. Não há visão "estou configurando um perfil inteiro" vs "estou aplicando um efeito ao vivo". Usuário relata:

> As configs precisam ser lembradas ao trocar de abas ou aplicar. Elas precisam funcionar em conjunto.

Pedido: quando eu configurar R2 na aba Gatilhos, mudar cor na aba Lightbar e clicar Aplicar — tudo vai junto, atomicamente, no controle. E ao trocar para aba Rumble e voltar, os valores editados continuam lá.

## Decisão

Criar `DraftConfig` na camada GUI: estado central com todos os widgets de edição de efeito ativo. Cada aba consulta/atualiza o `DraftConfig`. Botões "Aplicar":

- **Aplicar local (por aba)**: envia APENAS aquele setor (trigger, led, rumble, mouse) — rápido, para testar.
- **Aplicar tudo (global)**: envia todos os setores em uma chamada IPC batched ou em sequência coerente. Novo botão na toolbar superior.
- **Salvar como perfil**: gera um JSON novo em `~/.config/hefesto/profiles/user_<n>.json` com o snapshot atual.

Ao abrir a GUI, `DraftConfig` é inicializado do perfil ativo do daemon (`daemon.state_full` + `profile.get_active`). Ao trocar perfil, `DraftConfig` é refeito a partir do novo.

Ao trocar de aba, os widgets continuam mostrando o `DraftConfig` — persistência in-memory trivial.

## Arquitetura

```
HefestoApp
 └── DraftConfig (pydantic, in-memory)
     ├── triggers: {left, right} → (mode, params)
     ├── leds: {lightbar_rgb, lightbar_brightness, player_leds, mic_led}
     ├── rumble: {weak, strong}
     ├── mouse: {enabled, speed, scroll_speed}
     └── emulation: {xbox360_enabled}

 ├── StatusActionsMixin (read-only do daemon)
 ├── TriggersActionsMixin (edita DraftConfig.triggers + aplicar local)
 ├── LightbarActionsMixin (edita DraftConfig.leds + aplicar local)
 ├── RumbleActionsMixin (edita DraftConfig.rumble + aplicar local)
 ├── MouseActionsMixin (edita DraftConfig.mouse)
 └── ProfilesActionsMixin (carrega perfil → DraftConfig; salva DraftConfig → perfil)
```

Novo método IPC `profile.apply_draft {triggers, leds, rumble, mouse}` que aplica tudo em uma transação.

## Critérios de aceite

- [ ] `src/hefesto/app/draft_config.py` (NOVO): pydantic `DraftConfig` com seções; método `from_profile(profile)` e `to_profile(name)`.
- [ ] `HefestoApp.__init__`: cria `self.draft = DraftConfig.default()`; `on_activate` chama `self._load_draft_from_active_profile()`.
- [ ] Cada `*ActionsMixin` ganha `_bind_to_draft(draft)` + `_refresh_widgets_from_draft()`.
- [ ] `GtkNotebook switch-page` signal dispara `_refresh_widgets_from_draft()` da aba destino — preserva edições entre abas.
- [ ] Botão novo "Aplicar Tudo" na toolbar superior da janela (ao lado do logo). Handler envia `profile.apply_draft` via IPC.
- [ ] Botão "Salvar Como Perfil" abre dialog pedindo nome; escreve JSON em `~/.config/hefesto/profiles/`.
- [ ] `src/hefesto/daemon/ipc_server.py`: handler `profile.apply_draft` aplica triggers+leds+rumble+mouse em sequência idempotente.
- [ ] Teste `tests/unit/test_draft_config.py`: (a) default; (b) load de perfil; (c) to_profile gera JSON válido; (d) atualização seção a seção preserva outras seções.
- [ ] Proof-of-work visual: editar 3 abas, trocar entre elas, valores preservados. Capturar sequência.

## Arquivos tocados (previsão)

- `src/hefesto/app/draft_config.py` (novo, ~150 linhas)
- `src/hefesto/app/app.py`
- `src/hefesto/app/actions/*.py` (5 arquivos)
- `src/hefesto/gui/main.glade` (botões Aplicar Tudo / Salvar Como)
- `src/hefesto/daemon/ipc_server.py`
- `tests/unit/test_draft_config.py` (novo)

## Fora de escopo

- Histórico/undo de edições (V2).
- Sincronização multi-controle.
- Preview em tempo real sem aplicar (V2).

## Notas

- `DraftConfig` NÃO é persistido entre sessões da GUI — perder ao fechar é OK. Se o usuário quer persistência, salva perfil explicitamente.
- Botões "Aplicar local" preservados em cada aba para testes rápidos de um único efeito.
- Atenção a race: ao aplicar global, desabilitar os botões das abas durante os ~500ms da transação IPC para evitar aplicação concorrente.
