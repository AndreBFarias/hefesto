# AUDIT-V2-COMPLETE-01 — Auditoria manual completa do diff v1.0.0..HEAD

**Tipo:** chore (auditoria de qualidade).
**Wave:** V2.1 — Bloco D (última sprint antes do bump).
**Estimativa:** 1-2 iterações de leitura.
**Dependências:** todas as sprints anteriores do ciclo V2.1 mergeadas.

---

**Tracking:** issue a criar. Label: `type:refactor`, `P1-high`, `ai-task`, `status:ready`.

**Quem executa:** Opus direto, sem dispatch para subagente. Pedido explícito do usuário: "usuário quer revisão rigorosa sem delegar para sub-agentes".

## Contexto

Entre `v1.0.0` (baseline de qualidade do primeiro release estável) e HEAD (`7e6b369`, v2.0.0 + patches V2.1), 32 sprints mergeadas introduziram:

- 10 subsystems modulares (`src/hefesto/daemon/subsystems/`).
- Sistema de plugins Python (`src/hefesto/plugin_api/`).
- Endpoint Prometheus.
- 5 novos handlers IPC.
- Refatoração de lifecycle (677L → 365L).
- GUI ampliada (editor de perfil simples/avançado, tema roxo drácula global, 19 SVGs, rodapé global).
- Integração PipeWire/PulseAudio (AudioControl).

Esse volume de código não foi submetido a uma leitura humana sequencial. Auditoria pega regressões latentes que passam por testes unitários (cobertura é boa, mas não cobre tudo: closures, wire-up, edge cases de FS, race conditions).

## Decisão

**Opus (eu) executa a auditoria pessoalmente, sem delegação**. Escopo limitado a leitura + análise + produção de achados. **Não implementa fixes aqui** — P0/P1 viram sprints novas (auto-dispatch pós-release v2.1.0).

### Checklist de auditoria

#### A) Código Python (`src/hefesto/**`)

Rodar como base mecânica:

```bash
git diff v1.0.0..HEAD --stat src/hefesto/
.venv/bin/ruff check --select F401,F403,F841,E501 src/hefesto/
rg -n "TODO|FIXME|XXX|HACK" src/hefesto/
rg -n "^\s*print\(|\bpdb\." src/hefesto/
rg -n "except:\s*$|except Exception:\s*pass" src/hefesto/
rg -n "shell=True" src/hefesto/
rg -n "'/home/|\"/home/|'/etc/|'/usr/|'/tmp/" src/hefesto/
rg -n "subprocess\.(run|call|Popen)" src/hefesto/ | grep -v "check=True" | grep -v "capture_output"
rg -n "\.unlink\(\)|\.write_text\(|\.mkdir\(|os\.remove\(" src/hefesto/
```

Leitura manual focada em:

1. **Imports não usados** — além do ruff, revisar se algum import útil só em ramo condicional pode ter sido flagado erroneamente.
2. **TODOs/FIXMEs esquecidos** — cada match vira ou sprint-filha ou remoção.
3. **print() / pdb.set_trace()** — proibidos pelo AGENTS.md; devem ter sido pegos antes mas revisar.
4. **Exception bare** — `except:` ou `except Exception: pass` são candidatos a bug silencioso.
5. **shell=True** — vetor de injection. Qualquer uso precisa justificativa documentada.
6. **Paths hardcoded** — `/home/`, `/etc/`, `/usr/`, `/tmp/` devem usar `pathlib` + `xdg_paths`.
7. **subprocess sem check=True** — silenciosamente ignora falha do comando externo.
8. **FS operations sem tratamento** — unlink/write_text/mkdir sem try ou sem log em caso de falha.
9. **Closures capturando config por alias (A-08 regressão)**:
   - Revisar **cada** subsystem em `src/hefesto/daemon/subsystems/` (poll, ipc, udp, autoswitch, mouse, rumble, hotkey, metrics, plugins, connection).
   - Cada `_start_*` ou `__init__` deve ler `self.config.x` **em runtime** (dentro da função chamada), não em closure capturada no construtor.
   - A-08 está RESOLVIDA para `_on_ps_solo`, mas refatoração V2.0 introduziu novos subsystems — verificar se o padrão se mantém.
10. **Idempotência de handlers IPC** (`src/hefesto/daemon/ipc_server.py`):
    - Cada handler dos 10 métodos canônicos (`profile.switch`, `profile.list`, `trigger.set`, `trigger.reset`, `led.set`, `rumble.set`, `daemon.status`, `daemon.state_full`, `controller.list`, `daemon.reload`) + novos (ex.: `rumble.policy_set`) tem:
      - Validação de tipo dos params.
      - Resposta de erro com code canônico em caso de má formação.
      - Idempotência onde aplicável (ex.: `trigger.reset` chamado 2× não muda estado).
    - A-01 (unlink cego de socket IPC) está **aberta** no brief — auditar se o fix canônico (verificar se socket está vivo antes de unlink) foi aplicado em algum lugar.

#### B) Subsystems (`src/hefesto/daemon/subsystems/`)

Para cada subsystem:

1. **start/stop simétrico** — cada recurso alocado em `start()` é liberado em `stop()`.
2. **Shutdown graceful** — tasks `asyncio` cancelladas antes de `stop()` retornar; sockets fechados; arquivos flushed.
3. **Vazamento de recurso em path de erro** — se `start()` falha no meio, o que foi alocado é liberado?
4. **Wire-up no `Daemon`** (A-07):
   - Slot no dataclass `Daemon`?
   - `_start_<subsys>()` chamado em `run()` antes do `await self._stop_event.wait()`?
   - Consumo no `_poll_loop()` quando aplicável?
   - Zeragem no `_shutdown()`?
5. **Double-start proteção** — se `start()` for chamado 2× sem `stop()`, o comportamento é bem definido?

#### C) CSS + GLADE

1. **`src/hefesto/gui/theme.css`**:
   ```bash
   rg -oP "style_class=[\"']([^\"']+)" src/hefesto/app/ | sort -u  # classes usadas
   rg -oP "\.[\w-]+" src/hefesto/gui/theme.css | sort -u            # classes definidas
   # Diff: usadas não definidas = bug latente (CSS não aplica); definidas não usadas = lixo.
   ```
2. **GLADE (`src/hefesto/gui/*.glade`)**:
   ```bash
   # IDs definidos no XML:
   rg -oP 'id="([^"]+)"' src/hefesto/gui/main.glade | sort -u
   # IDs referenciados em código:
   rg -oP "get_object\(['\"]([^'\"]+)" src/hefesto/app/ | sort -u
   # Diff: referenciados não definidos = AttributeError em runtime.
   ```

#### D) Configuração e dependências

1. **`pyproject.toml`**:
   - Extras (`[metrics]`, `[plugins]`, `[uinput]`) bem declarados com versões mínimas.
   - Deps principais com versão mínima (`pydantic>=2.0`, `typer>=0.9`, etc.).
   - `[tool.ruff]` coerente com `.ruff.toml` ou ausência de conflito.
   - `[tool.pytest]` com markers declarados.
2. **`.github/workflows/*`**:
   - Hardening (env vars, não interpolação direta).
   - Matriz de Python (3.10, 3.11, 3.12 conforme declarado em `pyproject.toml`).
   - Dependências de jobs (needs) corretas.

#### E) Cross-check armadilhas A-01 a A-11

Para cada armadilha do brief:

| Armadilha | Status brief | Ação auditor |
|---|---|---|
| A-01: `IpcServer.start()/stop()` unlink cego | **ABERTA** | P0 candidato — propor fix na auditoria |
| A-02: `udp_server.py:106` AssertionError | **ABERTA** | P1 candidato — fix de 1 linha |
| A-03: Smoke compartilha socket | **ABERTA** (decorre de A-01) | P2 candidato — dep de A-01 |
| A-04: Diff removeu glyphs Unicode | RESOLVIDA | Verificar regressão no diff v2.0 |
| A-05: USB autosuspend | Documentada (dep de udev rule externa) | Sem ação direta |
| A-06: Mapper esquecido (brightness) | RESOLVIDA para brightness | Verificar se novos campos (display_name, audio config) estão OK |
| A-07: Wire-up subsystem 3 pontos | ATIVA como regra | Aplicar checklist C em cada subsystem |
| A-08: Closure captura config alias | RESOLVIDA | Verificar se novos subsystems mantêm padrão |
| A-09: Snapshot evdev duplicado | RESOLVIDA | Verificar que novos consumidores recebem `buttons_pressed` por parâmetro |
| A-10: Multi-instância | RESOLVIDA | Verificar que todos os spawn points usam `single_instance` |
| A-11: Race udev ADD 2× | RESOLVIDA | Verificar que hotplug unit não reintroduziu guard `pgrep` |

#### F) Logs INFO+ em PT-BR acentuado

```bash
rg -n "logger\.(info|warning|error|critical)\(" src/hefesto/ | grep -iE "(nao|funcao|descricao|validacao|configuracao|erro|falha)" | grep -v "não\|função\|descrição\|validação\|configuração"
```

Qualquer match é violação — mensagem INFO+ sem acento. Vira P2-low.

### Formato do entregável

`docs/process/discoveries/2026-04-23-auditoria-v2.md`:

```markdown
# Auditoria completa v1.0.0..HEAD — 2026-04-23

## Sumário executivo

[3-5 linhas: quantos arquivos lidos, X P0, Y P1, Z P2, W P3. Grau de confiança da cobertura.]

## Achados

### P0 — crítico, bloqueia usuário

#### P0-01: [título]
- **Arquivo**: src/.../foo.py:42
- **Problema**: [descrição 1-2 linhas]
- **Fragment atual**:
  ```python
  [código]
  ```
- **Fragment proposto**:
  ```python
  [código]
  ```
- **Sprint-candidata**: BUG-AUDIT-FOO-01

### P1 — alto, regressão latente

#### P1-01: ...

### P2 — médio, polish

- P2-01: src/.../bar.py:10 — mensagem INFO sem acento (`"operacao falhou"` → `"operação falhou"`).
- ...

### P3 — baixo, ruído

- P3-01: ...

## Métricas

- Arquivos Python lidos: N
- Linhas lidas (estimado): N
- Subsystems revisados: 10/10
- Handlers IPC revisados: 11/11
- Armadilhas cruzadas: 11/11

## Próximas sprints a criar (auto-dispatch pós-release)

- BUG-AUDIT-IPC-UNLINK-01 (P0-01)
- BUG-AUDIT-UDP-ASSERT-01 (P1-01)
- ...

## Conclusão

[O código está saudável? Onde tem mais risco concentrado? Há padrão recorrente?]
```

## Critérios de aceite

- [ ] `docs/process/discoveries/2026-04-23-auditoria-v2.md` criado.
- [ ] Sumário executivo com contagem por prioridade.
- [ ] **Todos** os 10 subsystems revisados explicitamente (item por item).
- [ ] **Todos** os 11 handlers IPC cross-checados com os 10 métodos canônicos do brief + `rumble.policy_set` etc.
- [ ] **Todas** as 11 armadilhas A-01…A-11 revisitadas com verdict atual.
- [ ] Cada P0/P1 tem arquivo:linha + fragment atual + fragment proposto + sprint-candidata-ID.
- [ ] Cada P2/P3 tem arquivo:linha + bullet explicativo.
- [ ] Seção "Próximas sprints a criar" lista candidatas com ID canônico.
- [ ] Nenhum fix implementado aqui — só listagem. Pool de commits só tem o `.md` novo.
- [ ] A-01 (abertura documentada) recebe tratamento explícito: ou propor fix (P0), ou justificar por que fica aberta.
- [ ] Markdown renderiza limpo.
- [ ] Acentuação PT-BR correta.

## Arquivos tocados

- `docs/process/discoveries/2026-04-23-auditoria-v2.md` (novo)

## Proof-of-work

```bash
wc -l docs/process/discoveries/2026-04-23-auditoria-v2.md

grep -c "^#### P0-" docs/process/discoveries/2026-04-23-auditoria-v2.md
grep -c "^#### P1-" docs/process/discoveries/2026-04-23-auditoria-v2.md
grep -c "^- P2-" docs/process/discoveries/2026-04-23-auditoria-v2.md

# Cross-check que todos os 10 subsystems aparecem no documento:
for subsys in poll ipc udp autoswitch mouse rumble hotkey metrics plugins connection; do
  grep -qi "$subsys" docs/process/discoveries/2026-04-23-auditoria-v2.md || echo "FALTA: $subsys"
done

# Cross-check que A-01..A-11 aparecem:
for a in A-01 A-02 A-03 A-04 A-05 A-06 A-07 A-08 A-09 A-10 A-11; do
  grep -q "$a" docs/process/discoveries/2026-04-23-auditoria-v2.md || echo "FALTA: $a"
done
```

## Notas para o executor

- **Esta sprint é executada por mim (Opus) direto, sem dispatch.** Pedido explícito do usuário para não delegar.
- **Não implementar fixes aqui**. Listar, priorizar, propor sprint-filha. Implementação vira v2.1.1 ou v2.2.
- **Honestidade epistêmica**: se a leitura for parcial (ex.: 80% do código analisado por limite de tempo/contexto), declarar explicitamente no sumário. "Auditei 32 dos 40 arquivos" é melhor do que afirmação vazia de cobertura 100%.
- **Confidence calibration**: cada P0/P1 deve ter evidência concreta (arquivo:linha + comportamento problemático). Não especular "pode ser que isso seja bug" — ou é, e prova, ou não lista.
- **Cross-reference com discoveries/**: se algum achado já foi reportado em discovery anterior, citar e dizer se ainda é válido.
- **Priorização**: P0 = usuário final vê o bug hoje (crash, data loss, funcionalidade essencial quebrada). P1 = race condition ou regressão latente. P2 = polish funcional (acentuação, mensagem confusa). P3 = ruído cosmético.

## Fora de escopo

- Implementar qualquer fix (viram sprints novas).
- Expandir cobertura de testes (sprint separada pós-auditoria).
- Revisar documentação (separado).
- Revisar código pré-v1.0.0 (escopo é `v1.0.0..HEAD`).
- Revisar commits de merge (conteúdo já aparece nos arquivos finais).
