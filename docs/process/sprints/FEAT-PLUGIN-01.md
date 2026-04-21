# FEAT-PLUGIN-01 — Sistema de plugins Lua/Python para perfis dinâmicos

**Tipo:** feat (arquitetural, grande).
**Wave:** V2.0.
**Estimativa:** 3-4 iterações.
**Dependências:** REFACTOR-LIFECYCLE-01 (precisa de subsystems bem definidos para o plugin hookar).

---

**Tracking:** issue [#86](https://github.com/AndreBFarias/hefesto/issues/86) — fechada por PR com `Closes #86` no body.

## Contexto

Perfis hoje são JSON estáticos: `triggers/leds/rumble` declarados. Não há como escrever um perfil que reaja ao jogo em tempo real — ex.: "mudar lightbar para vermelho quando HP < 30% no Elden Ring" ou "vibração forte quando recarregar no FPS".

Hefesto expõe o UDP DSX (porta 6969) para jogos/mods enviarem comandos, mas o caminho inverso (jogo → estado) requer que o próprio jogo mande pacotes. Plugin system abre alternativa: scripts lidos do disco que rodam no daemon com acesso limitado a `IController` + eventos + state.

## Decisão

Carregar plugins Python de `~/.config/hefesto/plugins/*.py` (cada arquivo = 1 plugin). Cada plugin define:

```python
from hefesto.plugin_api import Plugin, PluginContext

class HpReactivePlugin(Plugin):
    name = "hp_reactive"
    profile_match = ["eldenring", "darksouls"]

    def on_load(self, ctx: PluginContext) -> None:
        self.ctx = ctx

    def on_tick(self, state: ControllerState) -> None:
        # Ler HP via OCR / memory scan / UDP / mod externo
        hp = self._read_hp_from_mod()
        if hp is not None and hp < 30:
            self.ctx.controller.set_led((255, 0, 0))

    def on_unload(self) -> None:
        pass
```

`PluginContext` expõe interface estável mínima: `controller` (subset read-only + set_led/set_trigger/set_rumble), `bus.subscribe(topic)`, `store.counter("x")`, `log`. NUNCA expõe acesso a filesystem/network raw — plugins devem usar abstrações da API.

Alternativa Lua (via `lupa`): menor superfície, mais seguro, mas menos bibliotecas. Decisão: Python com sandbox via `RestrictedPython` inicial, Lua como V3.

## Critérios de aceite

- [ ] `src/hefesto/plugin_api/` (novo pacote): `Plugin` ABC, `PluginContext`, `load_plugins_from_dir()`.
- [ ] `src/hefesto/daemon/subsystems/plugins.py`: subsystem que carrega plugins, registra em bus, chama hooks.
- [ ] Hooks mínimos: `on_load`, `on_tick` (chamado no poll), `on_button_down`, `on_battery_change`, `on_profile_change`, `on_unload`.
- [ ] 1 plugin de exemplo em `examples/plugins/lightbar_rainbow.py` que cicla cores por tempo.
- [ ] CLI: `hefesto plugin list | reload | disable <name>`.
- [ ] ADR-017 (novo) documentando API, sandbox, versionamento.
- [ ] Testes cobrindo carregamento, isolamento, reload.

## Arquivos tocados (previsão)

- `src/hefesto/plugin_api/__init__.py` (novo)
- `src/hefesto/plugin_api/context.py` (novo)
- `src/hefesto/plugin_api/plugin.py` (novo)
- `src/hefesto/daemon/subsystems/plugins.py` (novo)
- `src/hefesto/cli/cmd_plugin.py` (novo)
- `examples/plugins/lightbar_rainbow.py` (novo)
- `docs/adr/017-plugin-system.md` (novo)
- `tests/unit/test_plugin_api.py` (novo)

## Fora de escopo

- Plugin marketplace / repositório central.
- Sandbox forte (cgroups/bubblewrap).
- Versionamento semântico da API (V1 só: API estável após primeiro release plugin).

## Notas

- Perigo: plugin malicioso pode disparar qualquer coisa do `IController`. Mitigação inicial: plugins ficam só em `~/.config/hefesto/plugins/` (owned by user), documentar que o usuário é responsável.
- Performance: plugins rodam no loop de poll. Plugin que demora > 5ms no tick DEVE ser logado como warning e eventualmente kickado.
