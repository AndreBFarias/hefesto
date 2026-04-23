# CHORE-ACENTUACAO-STRICT-HOOK-01 — Gate strict de acentuação PT-BR via pre-commit + CI

**Tipo:** chore (qualidade + infraestrutura).
**Wave:** V2.1 — primeira sprint do ciclo (estabelece gate antes das demais).
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** issue a criar. Label: `type:infra`, `P1-high`, `ai-task`, `status:ready`.

## Contexto

Hoje o projeto depende de um script externo do usuário (`~/.config/zsh/scripts/validar-acentuacao.py`) para varredura de acentuação PT-BR. O hook `.git/hooks/pre-commit` local só avisa — não bloqueia. Resultado concreto: sprints recentes (`FEAT-PROFILES-PRESET-06` especialmente) introduziram `acao`/`funcao`/`descricao` onde deveria haver `ação`/`função`/`descrição`, e a violação só foi pega na validação manual pós-fato.

Invariante canônica (`VALIDATOR_BRIEF.md`): **"Acentuação PT-BR obrigatória — todo arquivo tocado pela sprint passa por varredura de acentuação periférica"**. Sem gate automatizado, a invariante depende de disciplina humana.

## Decisão

Internalizar o validador no repo + configurar `pre-commit` framework + job CI dedicado. Hook `pre-commit install` ativo nesta sessão, vale para todos os commits subsequentes deste ciclo V2.1.

### Escopo

1. **`scripts/validar-acentuacao.py`** (novo — local):
   - Lê lista de palavras-risco (dicionário ampliado de 200+ pares `sem_acento → com_acento` cobrindo casos comuns: `acao`, `funcao`, `descricao`, `nao`, `configuracao`, `validacao`, `comunicacao`, `usuario`, `opcao`, `operacao`, `versao`, `padrao`, `conteudo`, `atencao`, `informacao`, `producao`, `conexao`, `execucao`, `instalacao`, `aplicacao`, `prioridade`, `proximo`, etc).
   - Varre arquivos passados via argv ou, sem args, varre repo via `git ls-files`.
   - Exit 0 se limpo, 1 se violação. Formato de saída: `<arquivo>:<linha>:<palavra_ruim> → sugestão <palavra_correta>`.
   - Whitelist canônica (match por path regex):
     - `^VALIDATOR_BRIEF\.md$`
     - `^AGENTS\.md$`
     - `^LICENSE$`
     - `^NOTICE$`
     - `^CHANGELOG\.md$`
     - `^tests/fixtures/.*`
     - `^docs/history/.*`
     - `^docs/research/.*` (pode ter nomes externos sem acento)
     - `^scripts/validar-acentuacao\.py$` (o próprio script lista palavras ASCII por design)
     - `^scripts/check_anonymity\.sh$` (tem lista de nomes em inglês)
     - `\.json$` (configs; se acentuação importar no JSON, é teste de integração e não do hook)
   - Opção `--check-file <path>` para pre-commit passar 1 arquivo por vez.
   - Opção `--all` para varredura ampla.
   - Opção `--show-whitelist` para debug.

2. **`.pre-commit-config.yaml`** (novo):
   ```yaml
   repos:
     - repo: local
       hooks:
         - id: acentuacao-strict
           name: Acentuação PT-BR estrita
           entry: python3 scripts/validar-acentuacao.py --check-file
           language: system
           types: [text]
           exclude: '^(tests/fixtures/|docs/history/|docs/research/|LICENSE$|NOTICE$|CHANGELOG\.md$|VALIDATOR_BRIEF\.md$|AGENTS\.md$|scripts/validar-acentuacao\.py$|scripts/check_anonymity\.sh$)'
         - id: anonimato
           name: Anonimato (sem menção a IA)
           entry: bash scripts/check_anonymity.sh
           language: system
           pass_filenames: false
         - id: ruff-check
           name: Ruff check
           entry: ruff check
           language: system
           types: [python]
   ```

3. **`.github/workflows/ci.yml`** (editar — job novo `acentuacao`):
   ```yaml
   acentuacao:
     name: Acentuação PT-BR estrita
     runs-on: ubuntu-22.04
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: "3.11"
       - name: Varredura estrita
         run: python3 scripts/validar-acentuacao.py --all
   ```
   Hardening: sem referência a `github.event.*` em `run:`.

4. **`README.md`** (editar — seção Contribuição ou equivalente): instrução `pip install pre-commit && pre-commit install` na primeira clonagem.

5. **`CHANGELOG.md`** (entrada pendente v2.1.0): mencionar o gate.

## Critérios de aceite

- [ ] `scripts/validar-acentuacao.py` criado, executável, ≥ 200 palavras no dicionário.
- [ ] `python3 scripts/validar-acentuacao.py --all` retorna exit 0 no repo atual (ou exit 1 com lista de violações pré-existentes que o executor corrige/whitelista no mesmo commit).
- [ ] `.pre-commit-config.yaml` criado; `pip install pre-commit && pre-commit run --all-files` verde.
- [ ] `.github/workflows/ci.yml` com job `acentuacao` adicionado, YAML válido (validar via `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`).
- [ ] Teste `tests/unit/test_validar_acentuacao.py` (novo) com 5+ casos: arquivo com `nao` pega; arquivo com `não` passa; whitelist respeitada; JSON ignorado; teste-fixture ignorado.
- [ ] `README.md` documenta `pre-commit install`.
- [ ] Proof-of-work: injetar `funcao` em arquivo temp `src/hefesto/test_tmp.py` e verificar que `pre-commit run --files src/hefesto/test_tmp.py` retorna exit 1 com mensagem pertinente; remover o arquivo.

## Arquivos tocados

- `scripts/validar-acentuacao.py` (novo)
- `.pre-commit-config.yaml` (novo)
- `.github/workflows/ci.yml` (editar)
- `README.md` (editar)
- `tests/unit/test_validar_acentuacao.py` (novo)

## Proof-of-work runtime

```bash
python3 scripts/validar-acentuacao.py --all
.venv/bin/pip install pre-commit
.venv/bin/pre-commit run --all-files
.venv/bin/pytest tests/unit/test_validar_acentuacao.py -v
.venv/bin/pre-commit install

echo "def funcao(): pass" > /tmp/hefesto_teste_falso_positivo.py
.venv/bin/pre-commit run --files /tmp/hefesto_teste_falso_positivo.py && echo "FALHA: deveria bloquear" || echo "OK: hook bloqueou"
rm /tmp/hefesto_teste_falso_positivo.py
```

## Notas para o executor

- **Estratégia para falsos-positivos pré-existentes**: antes de `pre-commit install`, rodar `pre-commit run --all-files` em dry-run. Se estourar ≤ 3 arquivos, corrigir no commit desta sprint. Se 4-10, fazer mini-commit separado `chore: acentuação pré-existente` imediatamente após. Se > 10, revisar whitelist — provavelmente capturando alvos por engano.
- **Dicionário de palavras-risco**: começar pelo conjunto da script externa do usuário, adaptar para PT-BR puro. Palavras técnicas em inglês (`config`, `function`, `option`) nunca entram no dicionário — só variantes sem acento de palavras PT-BR.
- **Edge case**: strings literais em testes que intencionalmente têm texto ASCII (ex.: mock de payload malformado). Essas ficam via whitelist de path (`tests/fixtures/`) ou via comentário inline `# noqa: acentuacao`. Preferir whitelist de path — comentário inline polui.
- **Hook falso-positivo em markdown**: URLs, nomes próprios, siglas. Se o dicionário gerar ruído, a palavra sai do dicionário — não o arquivo entra na whitelist.

## Fora de escopo

- Migrar `check_anonymity.sh` para python (fica pra outra sprint).
- Type-checking via mypy no hook (ruff já cobre grande parte).
- Formatador automático de acentuação (requer NLP, é armadilha).
- Traduzir `ruff`/`pytest`/`mypy` output para PT-BR.
