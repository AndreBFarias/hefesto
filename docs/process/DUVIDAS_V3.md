# Auditoria V3 — Pós-HEFESTO_DECISIONS_V2.md

> Análise do `HEFESTO_DECISIONS_V2.md` (consolidado) + `check_anonymity.sh` contra o `DUVIDAS_V2.md`.
> Regras globais (`~/.config/zsh/AI.md` v4.0 + `~/.claude/CLAUDE.md` com meta-regras 9.6–9.8 e validação visual 13–14) **valem por padrão** e não precisam ser re-declaradas no spec do projeto. Este documento lista apenas o que resta fora desse guarda-chuva.

---

## 0. STATUS DE COBERTURA

- **17/17** recomendações do `DUVIDAS_V2.md` seção 5 → endereçadas.
- **5/5** perguntas pendentes do V1 → respondidas.
- **`check_anonymity.sh`** → resolve 1.2 e 1.3 da auditoria original com qualidade (whitelist por arquivo é a decisão certa).

Este V3 **não é bloqueio**. São 3 bugs de implementação nos patches + 5 ajustes específicos do domínio Hefesto que não caem sob as regras globais.

---

## 1. A "PENDÊNCIA" DA SEÇÃO 1 V1 JÁ ESTÁ RESOLVIDA

O V2 marca como "pendente, destravar após 48h". Revisando a seção 1 da auditoria original (`DUVIDAS.md` v1):

| Item | Contradição original                                          | Resolvida em                 |
|------|---------------------------------------------------------------|------------------------------|
| 1.1  | `CLAUDE.md` na árvore viola REGRA -1                          | V2-2 (renome `AGENTS.md`)    |
| 1.2  | `check_anonymity.sh` regex incompleto                         | V2-1 + script entregue       |
| 1.3  | `ALLOWED_CONTEXT` gera falso negativo                         | V2-1 (whitelist por arquivo) |
| 1.4  | Aridade de `Galloping` diverge em 3 lugares                   | 5.6 (tabela canônica)        |
| 1.5  | Labels GitHub usadas sem criação prévia                       | Patch 1 item 11 (`setup_labels.sh`) |

**Ação sugerida:** editar `HEFESTO_DECISIONS_V2.md` e marcar a linha da tabela "Pendência aberta" como **RESOLVIDA**, com as referências acima. Não há 48h a esperar.

---

## 2. BUGS REAIS NOS PATCHES DO V2

### 2.1 Patch 4 — eviction do `RateLimiter` é no-op funcional

Código atual (linhas 387-394 do V2):

```python
ip_window = self.per_ip[ip]                   # cria via defaultdict
while ip_window and ip_window[0] < cutoff:
    ip_window.popleft()

if not ip_window:
    del self.per_ip[ip]                       # deleta
    ip_window = self.per_ip[ip]               # recria via defaultdict
```

O `del` seguido de re-acesso com `defaultdict` produz uma `deque` nova com mesmo `maxlen`, vazia — **idêntica** à que acabou de ser deletada. Não há economia de memória na chamada atual.

Pior: o uso real de memória (IPs que aparecem UMA vez e nunca mais) **continua acumulando**, porque o eviction só dispara quando `allow(ip)` é chamado de novo para o mesmo IP. Se o IP some, a entrada fica lá pra sempre.

**Correção proposta:**

```python
def __init__(self):
    self.global_window: deque[float] = deque(maxlen=RATE_GLOBAL)
    self.per_ip: dict[str, deque[float]] = {}
    self._last_sweep: float = 0.0

def _sweep(self, now: float) -> None:
    """Remove IPs sem atividade na última 1s. Chamado no máximo 1x/s."""
    if now - self._last_sweep < 1.0:
        return
    cutoff = now - 1.0
    self.per_ip = {
        ip: wnd for ip, wnd in self.per_ip.items()
        if wnd and wnd[-1] >= cutoff
    }
    self._last_sweep = now

def allow(self, ip: str) -> bool:
    now = time.monotonic()
    cutoff = now - 1.0
    self._sweep(now)

    while self.global_window and self.global_window[0] < cutoff:
        self.global_window.popleft()
    if len(self.global_window) >= RATE_GLOBAL:
        return False

    ip_window = self.per_ip.setdefault(ip, deque(maxlen=RATE_PER_IP))
    while ip_window and ip_window[0] < cutoff:
        ip_window.popleft()
    if len(ip_window) >= RATE_PER_IP:
        return False

    self.global_window.append(now)
    ip_window.append(now)
    return True
```

O `_sweep` roda no máximo 1x/s, O(n) sobre os IPs ativos. Sem sweep, o dict cresce sem limite.

### 2.2 Patch 9 — combo sagrado sem política de timing

Código descreve `DEFAULT_SACRED_COMBO = ["ps", "dpad_up"]` mas não resolve o dilema:

Usuário pressiona PS sozinho → daemon precisa decidir entre:
- **Repassar PS imediato** ao uinput (jogo abre overlay Steam). Se usuário completar combo 80ms depois, o D-pad vai pro jogo sem efeito de troca de perfil.
- **Bufferizar PS por 200ms** esperando D-pad. Se usuário só queria PS, overlay abre com atraso perceptível.

**Correção:** documentar no Patch 9 o buffer e o trade-off:

```python
HOTKEY_BUFFER_MS = 150

# Política: PS sempre é bufferizado por HOTKEY_BUFFER_MS.
# Se chegar D-pad nesse intervalo → consome combo, não repassa.
# Se intervalo expira sem segundo botão → repassa PS atrasado ao uinput.
# Custo: overlay Steam abre ~150ms tarde. Aceitável.
```

Sem essa decisão escrita, o dev de W6.3 vai tropeçar.

### 2.3 Patch 11 — parsing frágil de `list-unit-files`

Código atual assume `parts[1]` é o estado. Em systemd ≥ 245, o formato real é:

```
UNIT FILE                  STATE           PRESET
hefesto.service            disabled        enabled
hefesto-headless.service   enabled         disabled
```

`line.split()` em uma linha com 3 colunas retorna lista de 3 elementos. `parts[1] in ("enabled", ...)` funciona. **Mas**: em systemd antigo (≤ 239) só há 2 colunas (sem PRESET). `parts[1]` ainda é STATE. OK.

**Problema real**: `--no-legend` foi renomeado pra `--legend=false` em systemd 256. Versões intermediárias aceitam ambos. Pop!_OS 22.04 (systemd 249) aceita os dois.

**Correção defensiva:**

```python
cmd = ["systemctl", "--user", "list-unit-files",
       "hefesto.service", "hefesto-headless.service",
       "--no-pager", "--plain"]
# --plain garante output sem cores/control chars, consistente entre versões.
# list-unit-files em output vazio (nenhuma unit encontrada) retorna exit 0 com stdout vazio,
# não erro — tratar.
```

Adicionar teste: se `result.stdout.strip() == ""`, retornar `None` explícito.

---

## 3. AJUSTES ESPECÍFICOS DO DOMÍNIO HEFESTO

### 3.1 `docs/process/` vs `docs/history/`

O script `check_anonymity.sh` exclui ambos. Nenhum documento formal define a distinção.

**Proposta:** `docs/process/` = artefatos de processo ativo (DECISIONS, ROADMAP, DOUBTS atuais). `docs/history/` = material arquivado (audit reports antigos, RFCs rejeitadas). Documentar em `AGENTS.md`.

### 3.2 Gate de 5MB pros HID captures (V2-13)

Razoável mas não tem validação automática no CI.

```yaml
- name: Verificar tamanho de captures
  run: |
    find tests/fixtures -name "*.bin" -size +5M -exec \
      bash -c 'echo "ERRO: $0 excede 5MB"; exit 1' {} +
```

### 3.3 Xlib `wm_class` é tupla, não string

Xlib retorna `wm_class` como tupla `(instance, class)`. O código do Patch 3 trata como string (`window_info["wm_class"] in self.window_class`). Precisa decidir: usar `class` (segundo elemento, mais estável) ou `instance` (primeiro, mais granular)?

**Proposta:** `window_info["wm_class"]` = segundo elemento da tupla Xlib (`class`). Steam usa `steam_app_XXXX` em ambos, mas apps nativos variam. `class` é mais estável entre distros. Documentar no W6.1.

### 3.4 `check_anonymity.sh` precisa teste de regressão

Script inclui `:!scripts/check_anonymity.sh` na lista de excludes. Bom. Mas **sem** isso, o próprio regex pegaria palavras dentro do script como violação. Precisa prova empírica (meta-regra 9.2 — filtros sem falso-positivo).

**Proposta:** `tests/shell/test_check_anonymity.bats` com:

```bash
@test "detecta violação óbvia" {
    echo "# claude test" > src/hefesto/_fake_.py
    run bash scripts/check_anonymity.sh
    rm src/hefesto/_fake_.py
    [ "$status" -eq 1 ]
}

@test "ignora whitelist (LICENSE)" {
    echo "Copyright Claude" >> LICENSE
    run bash scripts/check_anonymity.sh
    git checkout LICENSE
    [ "$status" -eq 0 ]
}

@test "não falsamente casa 'model' em contexto técnico" {
    echo "model_name = 'ps5'" > src/hefesto/_fake_.py
    run bash scripts/check_anonymity.sh
    rm src/hefesto/_fake_.py
    [ "$status" -eq 0 ]
}
```

Usa `bats-core` (comum no ecossistema shell). Adicionar `bats` ao bootstrap opcional.

### 3.5 HID captures: procedimento de geração

`record_hid_capture.py` foi aprovado em V2-13 mas o protocolo de gravação precisa ser determinístico pra que o mesmo replay valide:

**Proposta:** script tem modo scripted:

```bash
python scripts/record_hid_capture.py --transport usb --duration 30 \
    --script captures/script_default.yaml \
    --output tests/fixtures/hid_capture_usb.bin
```

Onde `script_default.yaml` lista a sequência esperada (pressionar botões, mover sticks, etc.) pra garantir que captures em devices diferentes gerem fixtures equivalentes.

---

## 4. CHECKLIST FINAL (antes de começar W0.1)

Sigo com estas decisões se você confirmar (ou disser "ok em todas"):

- [ ] **Marcar pendência 1.1 do V2 como RESOLVIDA** (seção 1).
- [ ] **Substituir Patch 4** pela versão com `_sweep` periódico (seção 2.1).
- [ ] **Documentar buffer de 150ms** no Patch 9 (seção 2.2).
- [ ] **Adicionar `--plain`** e tratamento de stdout vazio no Patch 11 (seção 2.3).
- [ ] **Definir `docs/process/` vs `docs/history/`** em `AGENTS.md` (seção 3.1).
- [ ] **Gate de 5MB** nos captures no CI (seção 3.2).
- [ ] **`wm_class` = segundo elemento** da tupla Xlib, documentado em W6.1 (seção 3.3).
- [ ] **Teste `bats` do `check_anonymity.sh`** (seção 3.4).
- [ ] **Script determinístico** pra `record_hid_capture.py` (seção 3.5).

Com essa confirmação, consolido um `HEFESTO_DECISIONS_V3.md` enxuto (só deltas sobre V2) e começo a aplicar os patches ao `HEFESTO_PROJECT.md`.

---

## 5. PÓS-CONFIRMAÇÃO

Se você concordar:

1. Edito `HEFESTO_DECISIONS_V2.md` marcando a pendência 1.1 resolvida.
2. Crio `HEFESTO_DECISIONS_V3.md` com os 9 deltas acima.
3. Aplico ao `HEFESTO_PROJECT.md` (um commit só, mensagem `chore: consolidar decisões pós-auditoria`).
4. Executo W0.1. Estrutura, scripts, CI, ADR stubs — tudo em conformidade com `AI.md` universal + extensões do `CLAUDE.md` (meta-regras 9.6–9.8 e validação visual 13–14) aplicadas por padrão, sem precisar repeti-las no spec.
5. Entrego o DoD do W0.1 pra você validar antes de abrir as 26 issues.

Aguardo seu "ok" ou ajustes.
