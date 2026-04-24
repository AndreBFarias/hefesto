# Decisão sobre inversão R2/L2 — FEAT-KEYBOARD-UI-01 (2026-04-24)

## Contexto

A spec da sprint 59.3 (FEAT-KEYBOARD-UI-01) listou como critério de aceite:

> Inversão R2/L2 registrada em `docs/process/discoveries/`.

Durante a execução, o autor avaliou a mudança semântica proposta originalmente:
> "Ajustar `DEFAULT_BUTTON_BINDINGS` (ou `BUTTON_TO_UINPUT` no mouse se fizer
> sentido): o que hoje R2 faz, L2 passa a fazer, e vice-versa."

## Estado atual (pré-decisão)

Em `src/hefesto/integrations/uinput_mouse.py`:

- **L2** (gatilho esquerdo do DualSense) → BTN_LEFT (click esquerdo do mouse)
- **R2** (gatilho direito) → BTN_RIGHT (click direito)

Mapeamento mirroring da mão: gatilho direito = botão direito.

## Decisão

**NÃO inverter.** Razões:

1. **Convenção da mão dominante.** Em mouses tradicionais, o botão primário
   (BTN_LEFT, click esquerdo usado para seleção) fica no dedo indicador
   direito do destro. Invertendo para L2→BTN_RIGHT violaria essa convenção
   sem ganho claro.

2. **Simetria com X/Triângulo.** Hoje Cruz (X) = BTN_LEFT e Triângulo (△) =
   BTN_RIGHT. A dupla L2/X → BTN_LEFT e R2/Triângulo → BTN_RIGHT está
   coerente: dois caminhos para o mesmo botão, um de cada mão, sempre
   mirrored. Inverter só R2/L2 quebraria essa simetria.

3. **Retrocompatibilidade.** Inverter em v2.3.0 obriga usuários a
   recalibrar muscle memory sem motivo forte. Os relatos originais sobre
   "quero inverter" vieram de ergonomia pessoal, não de bug.

4. **Caminho melhor: UI de reconfiguração.** O usuário que preferir o
   inverso poderá, via a própria aba "Mouse e Teclado" adicionada nesta
   sprint, editar o binding de L2/R2 nas entradas de `key_bindings` por
   perfil — decisão individual, persistente, reversível. A sprint entrega
   a ferramenta; o default permanece o clássico.

## Follow-up

Quando a UI ganhar suporte completo a overrides de mouse buttons (não
apenas key bindings — atualmente `BUTTON_TO_UINPUT` em `uinput_mouse.py`
é fixo), o usuário pode customizar L2/R2 no perfil. Issue a criar:
`FEAT-MOUSE-BINDINGS-PER-PROFILE-01` quando houver demanda de usuário real.

## Referência

- Spec da 59.3: `docs/process/sprints/FEAT-KEYBOARD-UI-01.md`
- Mapping atual: `src/hefesto/integrations/uinput_mouse.py:54-58`
- `DEFAULT_BUTTON_BINDINGS`: `src/hefesto/core/keyboard_mappings.py:34-55`
