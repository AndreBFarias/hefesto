# FEAT-TRIGGER-PRESETS-POSITION-01 — Presets para Feedback e Vibração por posição

**Tipo:** feat (UX).
**Wave:** V1.1 — fase 6.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** issue a criar.

## Pedido do usuário (2026-04-22)

> nesses dois tipos de gatilhos [Feedback por posição / Vibração por posição] não temos os pré sets configurados por default seria bom isso.

Captura Image 4: ao selecionar "Feedback por posição" ou "Vibração por posição", a GUI mostra 9-10 sliders zerados (`Pos 0 (0-8)` ... `Pos 8 (0-8)`). Usuário tem que mexer em cada um, o que desestimula o uso.

## Decisão

Adicionar **dropdown de preset** acima dos sliders. 5 presets por tipo, que populam os sliders instantaneamente. Usuário ainda pode ajustar fino depois.

### Presets para Feedback por posição (MultiPositionFeedback)

Range de cada posição: 0-9. Array com 10 posições (Pos 0 a Pos 9).

| Preset | Descrição | Valores |
|---|---|---|
| **Rampa crescente** | Resistência sobe linearmente (curso completo do gatilho) | `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]` |
| **Rampa decrescente** | Resistência cai linearmente (solta no final) | `[9, 8, 7, 6, 5, 4, 3, 2, 1, 0]` |
| **Plateau central** | Leve nos extremos, forte no meio (zone sweet) | `[0, 2, 4, 7, 9, 9, 7, 4, 2, 0]` |
| **Stop hard** | Livre até 60%, bate numa parede dura | `[0, 0, 0, 0, 0, 0, 9, 9, 9, 9]` |
| **Stop macio** | Rampa suave até 50%, plateau firme | `[0, 1, 2, 4, 6, 8, 9, 9, 9, 9]` |
| **Linear médio** | Resistência constante 5 em todas | `[5, 5, 5, 5, 5, 5, 5, 5, 5, 5]` |
| **Custom** | Não altera — permite ajustar à mão | (preserva valores atuais) |

### Presets para Vibração por posição (MultiPositionVibration)

Mesmo shape de 10 posições, 0-9.

| Preset | Descrição | Valores |
|---|---|---|
| **Pulso crescente** | Vibração sobe com o curso (carga de tiro) | `[0, 0, 1, 2, 4, 6, 7, 8, 9, 9]` |
| **Machine gun** | Pulsos regulares (rajada) | `[0, 9, 0, 9, 0, 9, 0, 9, 0, 9]` |
| **Galope (cavalo)** | Duplo pulso em onda | `[0, 7, 9, 4, 0, 0, 7, 9, 4, 0]` |
| **Senoide** | Onda suave | `[0, 2, 5, 8, 9, 9, 8, 5, 2, 0]` |
| **Vibração final** | Só no fim do curso (bala chegando no fundo) | `[0, 0, 0, 0, 0, 0, 2, 5, 8, 9]` |
| **Custom** | Não altera | (preserva valores atuais) |

Perfis FEAT-PROFILES-PRESET-06 vão referenciar esses presets via comentário, mas o preset resolvido é sempre aplicado como `params=[...]` no JSON.

## Arquitetura

```python
# src/hefesto/profiles/trigger_presets.py (NOVO)

FEEDBACK_POSITION_PRESETS: dict[str, list[int]] = {
    "rampa_crescente":   [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    "rampa_decrescente": [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
    "plateau_central":   [0, 2, 4, 7, 9, 9, 7, 4, 2, 0],
    "stop_hard":         [0, 0, 0, 0, 0, 0, 9, 9, 9, 9],
    "stop_macio":        [0, 1, 2, 4, 6, 8, 9, 9, 9, 9],
    "linear_medio":      [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
}

VIBRATION_POSITION_PRESETS: dict[str, list[int]] = {
    "pulso_crescente": [0, 0, 1, 2, 4, 6, 7, 8, 9, 9],
    "machine_gun":     [0, 9, 0, 9, 0, 9, 0, 9, 0, 9],
    "galope":          [0, 7, 9, 4, 0, 0, 7, 9, 4, 0],
    "senoide":         [0, 2, 5, 8, 9, 9, 8, 5, 2, 0],
    "vibracao_final":  [0, 0, 0, 0, 0, 0, 2, 5, 8, 9],
}

# Labels PT-BR pra dropdown
FEEDBACK_POSITION_LABELS = {
    "rampa_crescente":   "Rampa crescente",
    "rampa_decrescente": "Rampa decrescente",
    ...
    "custom":            "Personalizar"
}
```

## Critérios de aceite

- [ ] `src/hefesto/profiles/trigger_presets.py` (NOVO): dicts acima + constante `TriggerPositionPreset = Literal[...]`.
- [ ] `src/hefesto/gui/main.glade`: aba Gatilhos, ao lado do dropdown `Modo` de cada gatilho (L2 e R2), novo dropdown `Preset` visível apenas quando modo == `Feedback por posição` ou `Vibração por posição`.
- [ ] `src/hefesto/app/actions/triggers_actions.py`:
  - Handler `on_trigger_left_mode_changed` / `on_trigger_right_mode_changed` mostra/esconde o dropdown de preset.
  - Handler `on_trigger_left_preset_changed` / `on_trigger_right_preset_changed` popula os sliders conforme preset, exceto "Custom".
  - Quando usuário move um slider manualmente após aplicar preset, o preset volta pra "Custom" automaticamente (preservar edições).
- [ ] Teste `tests/unit/test_trigger_presets.py`:
  - Todos os valores de preset respeitam 0-9.
  - Todos os arrays têm 10 posições.
  - `custom` é excluído dos dicts de preset resolvíveis (só nos labels).
- [ ] Proof-of-work visual: screenshot aba Gatilhos com modo "Feedback por posição" e dropdown aberto; seleção de "Rampa crescente" popula sliders visivelmente.

## Arquivos tocados

- `src/hefesto/profiles/trigger_presets.py` (novo)
- `src/hefesto/gui/main.glade`
- `src/hefesto/app/actions/triggers_actions.py`
- `tests/unit/test_trigger_presets.py` (novo)

## Notas para o executor

- Os presets acima são **subjetivos** — derivados de intuição sobre mecânica de gatilhos adaptativos. Se forem ruins na prática, trocar valores (sem mudar estrutura). Documentar escolhas na seção "Notas" do discovery se houver tunning.
- Dropdown de preset deve ser `Gtk.ComboBoxText` (mais simples que ComboBox genérico).
- Esconder/mostrar dropdown via `widget.set_visible(True/False)` ou `gtk.Revealer` pra animação suave.
- Ao aplicar preset, disparar `queue_draw` em cada slider pra atualização visual imediata.

## Fora de escopo

- Presets pro modo simples (`Rigid`, `Pulse`, etc.) — V2.
- Preview em tempo real no hardware ao selecionar (teste de 500ms) — V2 (pode virar sprint).
- Import/export de presets customizados — V2.
