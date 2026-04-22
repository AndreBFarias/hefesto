# FEAT-RUMBLE-POLICY-01 — Aba Rumble vira política global (Economia / Balanceado / Máx / Auto)

**Tipo:** feat (UX + backend).
**Wave:** V1.1 — fase 6.
**Estimativa:** 1-2 iterações.
**Dependências:** BUG-RUMBLE-APPLY-IGNORED-01 (corrige a persistência do rumble ativo primeiro).

---

**Tracking:** issue a criar.

## Pedido do usuário (2026-04-22)

> A ideia dessa aba é testarmos apenas a vibração do controle? Se for complica nossa vida, não teria usabilidade mas com isso conseguimos setar o valor máximo e mínimo na vibração, tipo pra eu conseguir usar no máximo ou no modo economia de bateria diminuindo tudo ou máx, maximizando tudo. Acho que essa é a ideia.

E:

> Rumble policy: global, mas adicionar um auto ali pode ser legal também pra ele ir mudando

## Decisão

Aba Rumble deixa de ser "testador" e vira **controle de política global de intensidade**. Sliders weak/strong viram testadores no rodapé; acima, 4 botões de política + slider contínuo.

### Layout

```
+-- Política de rumble ---------------------------------------+
|                                                             |
|  [Economia]  [Balanceado]  [Máximo]  [Auto]                 |
|                                                             |
|  Intensidade global:  [=====.....] 55%                      |
|                                                             |
|  Auto ajusta a intensidade conforme a bateria do controle.  |
|  Bateria >50%: 100%. 20-50%: 70%. <20%: 30%.                |
|                                                             |
+-------------------------------------------------------------+

+-- Testar motores -------------------------------------------+
|  Motor fraco (weak):  [====......] 40                       |
|  Motor forte (strong):[========..] 80                       |
|                                                             |
|  [Testar por 500 ms]  [Aplicar]  [Parar]                    |
+-------------------------------------------------------------+
```

### Semântica

A política é um **multiplicador sobre o rumble efetivo** (tanto do daemon quanto passthrough do jogo via gamepad virtual Xbox360).

| Política | Multiplicador weak | Multiplicador strong | Notas |
|---|---|---|---|
| Economia | 0.3 | 0.3 | Vibração sutil, 70% menos energia |
| Balanceado | 0.7 | 0.7 | Default |
| Máximo | 1.0 | 1.0 | Sem limite, usa o que vier |
| Auto | ver abaixo | ver abaixo | Depende de bateria |

**Modo Auto (dinâmico)**:
- `battery > 50%`: `mult = 1.0` (Máximo)
- `20 <= battery <= 50%`: `mult = 0.7` (Balanceado)
- `battery < 20%`: `mult = 0.3` (Economia)

Transições com debounce de 5s para evitar oscilação quando a bateria passa o threshold.

O slider "Intensidade global" permite ajuste fino (0-100%) que substitui o preset e vira modo Custom. Clicar em uma política reseta o slider pro valor canônico.

### Backend

`DaemonConfig.rumble_policy: Literal["economia", "balanceado", "max", "auto", "custom"] = "balanceado"`
`DaemonConfig.rumble_policy_custom_mult: float = 0.7` (usado se policy == "custom")

`RumbleEngine.set(weak, strong)` aplica o multiplicador **antes** de escrever no hardware:

```python
def _effective_mult(self, daemon_config: DaemonConfig, state: ControllerState) -> float:
    p = daemon_config.rumble_policy
    if p == "custom":
        return daemon_config.rumble_policy_custom_mult
    if p == "auto":
        if state.battery_pct > 50:  return 1.0
        if state.battery_pct >= 20: return 0.7
        return 0.3
    return {"economia": 0.3, "balanceado": 0.7, "max": 1.0}[p]

# no .set(weak, strong):
mult = self._effective_mult(daemon_config, latest_state)
effective_weak   = int(round(weak   * mult))
effective_strong = int(round(strong * mult))
self._controller.set_rumble(effective_weak, effective_strong)
```

IPC novos:
- `rumble.policy_set {policy}` → atualiza `DaemonConfig.rumble_policy`.
- `rumble.policy_custom {mult: float}` → seta `"custom"` e `mult`.
- `daemon.state_full` retorna `rumble_policy` no payload.

## Critérios de aceite

- [ ] `src/hefesto/daemon/lifecycle.py`: `DaemonConfig.rumble_policy`, `rumble_policy_custom_mult`.
- [ ] `src/hefesto/core/rumble_engine.py`: aplica multiplicador em `.set()` e `.pulse()`. Precisa de referência ao `DaemonConfig` + último estado (bateria) — passar via construtor ou método `link(config_ref, state_ref)`.
- [ ] `src/hefesto/daemon/ipc_server.py`: handlers `rumble.policy_set`, `rumble.policy_custom`. `daemon.state_full` inclui `rumble_policy`, `rumble_policy_custom_mult`, `rumble_mult_applied` (valor efetivo naquele momento).
- [ ] `src/hefesto/app/ipc_bridge.py`: `rumble_policy_set(policy)`, `rumble_policy_custom(mult)`.
- [ ] `src/hefesto/app/actions/rumble_actions.py`:
  - Grupo de 4 `Gtk.ToggleButton` (rádio visual) para as políticas.
  - Slider 0-100% abaixo (representa mult * 100).
  - Label educativo do modo Auto (texto acima).
  - Clicar preset: seta policy + move slider.
  - Mover slider: seta policy "custom" + envia `rumble.policy_custom`.
- [ ] Switch do Rumble passthrough (para jogo) preservado.
- [ ] Teste `tests/unit/test_rumble_policy.py`:
  - Cada preset retorna mult correto.
  - Modo Auto respeita battery thresholds (mock battery_pct 80/40/10).
  - Debounce 5s evita flapping (mock monotonic).
  - `rumble.set(100, 200)` com policy "economia" aplica `(30, 60)`.
- [ ] Proof-of-work runtime com hardware:
  1. Aplicar policy "Economia", `rumble.set(255, 255)` -> controle vibra suave.
  2. Aplicar policy "Máximo", `rumble.set(100, 100)` -> controle vibra normal.
  3. Policy "Auto", simular bateria baixa via `--fake` -> observar log `rumble_auto_policy_change mult=0.3`.
  4. Deslizar slider pra 20% -> policy vira "custom", mult aplicado.
- [ ] Proof-of-work visual: aba Rumble novo layout, sha256.

## Arquivos tocados

- `src/hefesto/daemon/lifecycle.py`
- `src/hefesto/core/rumble_engine.py`
- `src/hefesto/daemon/ipc_server.py`
- `src/hefesto/app/ipc_bridge.py`
- `src/hefesto/app/actions/rumble_actions.py`
- `src/hefesto/gui/main.glade`
- `tests/unit/test_rumble_policy.py` (novo)

## Notas para o executor

- **Debounce auto**: guardar `self._last_auto_mult` + `self._last_auto_change_at`. Só mudar mult se `now - last_change > 5s`.
- **Ordem com passthrough**: quando `daemon.config.emulation_enabled == True` (passthrough do jogo via Xbox360 virtual), o jogo envia valores de rumble via uinput. Esse caminho passa pelo `RumbleEngine.set()` também — aplicar o mult aqui é correto e desejado.
- **UI**: não usar 4 GtkRadioButton (feios). Usar 4 GtkToggleButton agrupados via `group`, com `style_class=rumble-policy`. CSS do UI-THEME-BORDERS-PURPLE-01 acomoda isso com borda roxa quando active.
- **Regressão possível**: FEAT-MOUSE-02 (Circle/Square -> Enter/Esc) não emite rumble, sem conflito.

## Fora de escopo

- Rumble-per-profile override (V1.2).
- Perfis com política automática por janela (V2).
- Curva personalizada de resposta à bateria (V2).
