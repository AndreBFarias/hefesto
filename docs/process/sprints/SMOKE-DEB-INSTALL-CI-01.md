# SMOKE-DEB-INSTALL-CI-01 — CI instala `.deb` real em ubuntu-22.04

**Tipo:** chore (infra CI).
**Wave:** V2.1 — Bloco C.
**Estimativa:** 1 iteração.
**Dependências:** `.github/workflows/release.yml` com job `deb` já existente.

---

**Tracking:** issue a criar. Label: `type:infra`, `P1-high`, `ai-task`, `status:ready`.

## Contexto

`.github/workflows/release.yml` job `deb` constrói `hefesto_<versao>_amd64.deb` como artifact. Não há teste de instalação — se o pacote está corrompido, deps erradas, postinst quebrado ou conflito de filesystem, só descobrimos pós-release com usuário reportando falha.

## Decisão

Novo job `deb-install-smoke` no mesmo workflow, rodando após `deb`, que baixa o artifact e roda `sudo apt install ./hefesto_*.deb` em ubuntu-22.04 limpo. Valida binários instalados respondem `--version` e `--help`. Gatilho idêntico ao job `deb` (PR + push de tag).

### Passos do job

```yaml
deb-install-smoke:
  name: Smoke install do .deb
  needs: deb
  runs-on: ubuntu-22.04
  steps:
    - name: Baixar artifact do .deb
      uses: actions/download-artifact@v4
      with:
        name: hefesto-deb
        path: ./dist
    - name: Listar conteúdo baixado
      run: ls -lah ./dist
    - name: Instalar .deb
      run: |
        sudo apt update
        sudo apt install -y ./dist/hefesto_*_amd64.deb
    - name: Validar binário hefesto
      run: |
        which hefesto
        hefesto --version
    - name: Validar binário hefesto-gui
      env:
        DISPLAY: ""
      run: |
        which hefesto-gui
        hefesto-gui --help || true
        # --help em headless pode falhar por falta de display; aceitar rc != 0 mas exigir binário localizável.
    - name: Desinstalar (verifica postrm limpo)
      run: |
        sudo apt remove -y hefesto
```

### Hardening

- Sem interpolação `${{ github.event.* }}` em `run:`. Se precisar de campo do evento, passa via `env:` explícito.
- `needs: deb` garante que só roda se o job upstream passou.
- `if: always()` no step de upload de log (se adicionar log) — ajuda debug em falha.

## Critérios de aceite

- [ ] `.github/workflows/release.yml` tem job `deb-install-smoke` válido.
- [ ] YAML parse OK (`python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"`).
- [ ] Job depende de `deb` (`needs: deb`).
- [ ] Job instala via `sudo apt install ./arquivo.deb` (não `dpkg -i` — apt resolve deps).
- [ ] Validação: `hefesto --version` retorna exit 0 e imprime versão esperada.
- [ ] Validação: `hefesto-gui --help` localiza o binário (exit 0 opcional — GUI em headless pode sair != 0 por falta de display).
- [ ] Desinstala ao fim para validar `postrm` limpo.
- [ ] Se o job falhar em push de tag, bloqueia criação do GitHub Release (via `needs` do job `github-release`).
- [ ] Sem vazamento de token/secret em log.
- [ ] Proof-of-work local: `act -j deb-install-smoke` ou equivalente opcional; alternativa é push para branch de teste e observar Actions.

## Arquivos tocados

- `.github/workflows/release.yml` (job novo + ajuste de `needs` no `github-release`)

## Proof-of-work

```bash
# Validar YAML
python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/release.yml')); assert 'deb-install-smoke' in d['jobs']; print('OK')"

# Opcional: usar act para simular local (se instalado)
# act -j deb-install-smoke --container-architecture linux/amd64
```

## Notas para o executor

- O job `deb` upstream precisa expor o artifact com nome canônico (`hefesto-deb`). Se o nome atual for outro (ex.: `dist-deb`), ajustar ambos os pontos.
- `hefesto-gui --help` em runner GitHub Actions sem display: pode falhar importando GTK. Aceitar rc != 0; só checar que `which hefesto-gui` retorna path válido.
- `sudo apt install ./pkg.deb` só funciona em ubuntu-20.04+; 22.04 é o canônico do projeto.
- Se o pacote declara deps que não existem em ubuntu-22.04 (ex.: `python3.11` quando só `python3.10` está disponível), o job falha corretamente — é o sinal que queremos.
- **Não adicionar step de `runtime smoke`** aqui (smoke do daemon é job separado `runtime-smoke` em `ci.yml`). Escopo desta sprint é só validar *instalação*, não runtime.

## Fora de escopo

- Testar `.deb` em ubuntu-20.04 ou 24.04 (matrix expansion fica para sprint separada).
- Testar `.rpm` ou Arch package (não existem no projeto hoje).
- Testar upgrade de versão antiga (`apt install v2.0.0; apt upgrade → v2.1.0`).
- Instalar no container Docker ao invés de runner nativo.
