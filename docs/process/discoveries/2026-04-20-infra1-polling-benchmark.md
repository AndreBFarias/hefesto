# 2026-04-20 — INFRA.1: polling HID é barato, CPU fica em 4-9% até 1000 Hz

**Contexto:** benchmark real do `PyDualSenseController.read_state()` contra DualSense USB conectado via cabo, backend híbrido ativo (evdev + pydualsense). Queríamos validar se 60 Hz (ADR-008 default) faz sentido ou se subir pra 120/250 Hz vale a pena.
**Status:** Resolvida.
**Issues relacionadas:** #27 (INFRA.1), PR aplicado.

## Sintoma

Sem medição empírica, a escolha de 60 Hz era baseada em heurística ("suficiente pra gatilhos"). Podia ser excesso de cautela — ou insuficiente pra competitivo.

## Medida

Rodei `scripts/benchmark_polling.py --duration 2 --frequencies 30,60,120,250,500,1000`.
Resultado em `benchmarks/2026-04-20-polling-usb.csv`:

| target_hz | effective_hz | samples | mean_read_ms | p95_read_ms | p99_read_ms | jitter_ms | cpu_pct |
|-----------|--------------|---------|--------------|-------------|-------------|-----------|---------|
| 30        | 29.89        | 60      | 0.080        | 0.115       | 0.120       | 0.172     | 8.5     |
| 60        | 59.58        | 120     | 0.087        | 0.135       | 0.155       | 0.086     | 9.1     |
| 120       | 117.37       | 235     | 0.080        | 0.131       | 0.217       | 0.578     | 9.2     |
| 250       | 245.45       | 491     | 0.041        | 0.074       | 0.112       | 0.026     | 6.3     |
| 500       | 485.24       | 971     | 0.017        | 0.028       | 0.040       | 0.020     | 4.3     |
| 1000      | 944.44       | 1889    | 0.013        | 0.024       | 0.031       | 0.019     | 4.7     |

## Hipóteses

1. **60 Hz é limite superior por custo de HID** — descartada: p99 é 0.155 ms em 60 Hz; read custa <1% do período.
2. **1000 Hz vai saturar CPU** — descartada: 1000 Hz dá 944 Hz efetivo com 4.7% CPU. Totalmente viável.
3. **Eficiência cai muito em taxas altas** — parcialmente certa: effective_hz / target_hz cai de 99% (30 Hz) para 94% (1000 Hz) por conta do overhead do `time.sleep()` do Python, que não é muito preciso em <1ms.
4. **Leitura do snapshot evdev + pydualsense é rápida** — CONFIRMADA: `mean_read_ms` é 0.013-0.087 ms. O evdev snapshot thread já atualizou os valores em background; nosso `read_state()` só copia campos.

## Causa técnica

`read_state()` faz 2 coisas: lê snapshot do `EvdevReader` (lock + cópia de dataclass) e lê `ds.battery.Level` do pydualsense (atributo simples). Nenhuma I/O HID acontece diretamente no read — a I/O está no thread do evdev e no thread do pydualsense. Read_state é essencialmente getter de memória.

Logo o custo real do polling é dominado por:
1. `time.sleep()` entre ticks.
2. Publish no `EventBus` (`asyncio.Queue.put_nowait`).
3. Update no `StateStore` (RLock + atribuição).

Nenhum desses é HID-bound.

## Solução / recomendação

- **Default segue em 60 Hz** no `DEFAULT_POLL_HZ` (ADR-008). Margem boa sobre o necessário pra trigger effects sem gastar CPU à toa.
- **Config exposta via `daemon.toml`** `[poll].hz` já é suportada no `DaemonConfig.poll_hz`. Usuários competitivos podem subir pra **250 Hz** tranquilamente (6.3% CPU).
- **1000 Hz não é recomendado**: effective_hz saturado em 944 por conta do sleep do Python. Pra 1000 Hz real precisaria substituir sleep por `clock_nanosleep` via ctypes ou `select.select` com timeout curto. Fora de escopo pra v0.x.

## Lições

1. **Medir antes de otimizar.** A hipótese tácita era "60 Hz é o máximo viável"; a realidade é que tem 4x de headroom.
2. **Leitura de estado é getter barato graças ao backend híbrido.** Evdev thread faz o trabalho pesado em background; nosso sync read só copia campos.
3. **time.sleep() é o limite superior.** Em Linux com GIL, ~94% de precisão em 1000 Hz já é bom; sub-ms exige busy-wait ou nanosleep nativo.
4. **CPU não é problema** em nenhuma faixa razoável. Bateria do laptop não é argumento contra subir poll rate.

## Impacto cross-sprint

- ADR-008 ganha nota empírica com a tabela de benchmarks.
- `daemon.toml` exemplo deve mostrar `[poll].hz = 60` como default e mencionar que 120-250 é seguro.
- README pode atualizar "requisitos de hardware" confirmando que funciona bem em CPUs modestas (benchmark rodou em Pop!_OS 22.04 em máquina com AMD Ryzen — nada especial).
- Benchmark CSV vai para `benchmarks/YYYY-MM-DD-polling-<transport>.csv` como trilha histórica (não é fixture de teste).
