# FEAT-METRICS-01 — Endpoint de métricas Prometheus

**Tipo:** feat (observabilidade).
**Wave:** V2.0.
**Estimativa:** 2 iterações.
**Dependências:** REFACTOR-LIFECYCLE-01 (métricas viram um subsistema).

---

**Tracking:** issue [#85](https://github.com/AndreBFarias/hefesto/issues/85) — fechada por PR com `Closes #85` no body.

## Contexto

Daemon hoje não expõe métricas. Para o usuário debugar "por que o controle está lento" ou "o daemon está pesado?" é preciso `top` / `htop` + ler logs. Sem dados quantitativos. Observabilidade é lição empírica (meta-regra 9.4 — "sistema adaptativo sem métrica de saúde é bomba-relógio").

## Decisão

Expor métricas via HTTP em `127.0.0.1:9090/metrics` no formato Prometheus text exposition. Porta configurável via `DaemonConfig.metrics_port`. Padrão desligado (`metrics_enabled: false`) — opt-in para quem quer scraping.

Métricas canônicas:

```
# HELP hefesto_poll_ticks_total Total de ticks do poll loop
# TYPE hefesto_poll_ticks_total counter
hefesto_poll_ticks_total 123456

# HELP hefesto_poll_duration_seconds Duração de cada tick
# TYPE hefesto_poll_duration_seconds histogram
hefesto_poll_duration_seconds_bucket{le="0.001"} 12000
hefesto_poll_duration_seconds_bucket{le="0.005"} 122000
...

# HELP hefesto_controller_connected 1 se conectado, 0 caso contrário
# TYPE hefesto_controller_connected gauge
hefesto_controller_connected{transport="usb"} 1

# HELP hefesto_battery_pct Bateria atual em %
# TYPE hefesto_battery_pct gauge
hefesto_battery_pct 85

# HELP hefesto_ipc_requests_total Requisições IPC recebidas
# TYPE hefesto_ipc_requests_total counter
hefesto_ipc_requests_total{method="daemon.state_full",status="ok"} 42000

# HELP hefesto_udp_packets_total Pacotes UDP recebidos
# TYPE hefesto_udp_packets_total counter
hefesto_udp_packets_total{result="accepted"} 15000
hefesto_udp_packets_total{result="rate_limited"} 23

# HELP hefesto_events_dispatched_total Eventos publicados no bus
# TYPE hefesto_events_dispatched_total counter
hefesto_events_dispatched_total{topic="battery_change"} 87
```

## Critérios de aceite

- [ ] `src/hefesto/daemon/subsystems/metrics.py`: HTTP server Python `http.server` minimalista + coletor que lê `StateStore` e `EventBus`.
- [ ] `DaemonConfig.metrics_enabled: bool = False`; `DaemonConfig.metrics_port: int = 9090`.
- [ ] Biblioteca nova: `prometheus_client` adicionada em `pyproject.toml` como extra `[metrics]` (opcional).
- [ ] Teste `tests/unit/test_metrics.py`: mock server + request HTTP; assert formato Prometheus válido.
- [ ] Aba Daemon da GUI ganha toggle "Expor métricas na porta 9090" (opt-in com warning de segurança — bind localhost-only).
- [ ] ADR-016 (novo) documentando schema de métricas e convenção de nomes.
- [ ] `docs/usage/metrics.md` (novo): exemplo de Prometheus scrape config + dashboard Grafana básico.

## Proof-of-work

```bash
HEFESTO_METRICS=1 ./run.sh --daemon --fake &
sleep 2
curl -s http://127.0.0.1:9090/metrics | grep -c "^hefesto_"
# esperado: ≥ 10 linhas
curl -s http://127.0.0.1:9090/metrics | grep "hefesto_poll_ticks_total"
# esperado: hefesto_poll_ticks_total 60 (aprox)
```

## Arquivos tocados (previsão)

- `src/hefesto/daemon/subsystems/metrics.py` (novo)
- `src/hefesto/daemon/context.py` (adiciona referência)
- `src/hefesto/daemon/state_store.py` (helper `observe_counter`)
- `pyproject.toml` (extra `[metrics]`)
- `tests/unit/test_metrics.py` (novo)
- `docs/adr/016-prometheus-metrics.md` (novo)
- `docs/usage/metrics.md` (novo)

## Fora de escopo

- Tracing OpenTelemetry.
- Métricas de hardware (temperatura, vibração latência).
- Dashboard Grafana preparado (referência no docs é suficiente).

## Notas

- Bind apenas `127.0.0.1`, nunca `0.0.0.0`. Prometheus scraping remoto usa reverse proxy.
- Porta 9090 é convenção Prometheus mas pode colidir — documentar alternativas.
