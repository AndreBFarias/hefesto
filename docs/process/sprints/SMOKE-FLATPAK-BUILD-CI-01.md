# SMOKE-FLATPAK-BUILD-CI-01 — CI faz build + install --user do bundle Flatpak

**Tipo:** chore (infra CI).
**Wave:** V2.1 — Bloco C.
**Estimativa:** 1 iteração.
**Dependências:** `.github/workflows/flatpak.yml` existente.

---

**Tracking:** issue a criar. Label: `type:infra`, `P2-medium`, `ai-task`, `status:ready`.

## Contexto

Exploração preliminar sugere que o workflow `.github/workflows/flatpak.yml` já tem job `build-flatpak` com `flatpak-builder` real gerando bundle. Falta confirmar e adicionar o passo final: instalar o bundle em modo usuário (`flatpak install --user`) dentro do próprio runner, e tentar rodar `--version` para validar que o bundle não está corrompido.

Se a exploração durante a execução revelar que o workflow hoje só valida manifest/metainfo sem build real, escopo escala para "criar build + install".

## Decisão

1. Auditar `.github/workflows/flatpak.yml` no início da execução.
2. Se build real já existe: **adicionar step de `flatpak install --user --bundle`** + `flatpak run <app-id> --version`.
3. Se build real não existe: criar step de build completo primeiro, depois install.
4. Sempre: upload do log de build como artifact `flatpak-build.log` com `if: always()` para debug pós-falha.

### Passos (se build já existe)

```yaml
# Após o step que gera hefesto.flatpak
- name: Install --user do bundle
  run: |
    flatpak install --user --noninteractive --bundle ./hefesto.flatpak
    flatpak list --user --app | grep -i hefesto
- name: Validar execução básica
  env:
    DISPLAY: ""
  run: |
    # App ID canônico lido de assets/flatpak/*.metainfo.xml (ex.: br.dev.hefesto.Hefesto)
    APP_ID=$(grep -oP '(?<=<id>)[^<]+' assets/flatpak/*.metainfo.xml | head -1)
    echo "APP_ID=$APP_ID"
    flatpak run --user "$APP_ID" --version || echo "GUI sem display é esperado; binário localizado é o critério"
- name: Upload log de build
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: flatpak-build-log
    path: .flatpak-builder/build/**/*.log
    retention-days: 7
```

### Hardening

- Sem `${{ github.event.* }}` em `run:`.
- `noninteractive` em `flatpak install` para não travar runner.
- `if: always()` no upload garante log mesmo em falha.

## Critérios de aceite

- [ ] `.github/workflows/flatpak.yml` contém step de `flatpak install --user` após build.
- [ ] Step de execução (`flatpak run --version`) localiza o binário (exit 0 na versão; tolerância se GUI falhar por falta de display).
- [ ] Upload do log de build sempre (`if: always()`).
- [ ] YAML parse OK.
- [ ] **Auditoria documentada**: no corpo do commit ou no CHANGELOG, mencionar "Antes desta sprint, flatpak.yml [fazia build real | só validava manifest]" conforme descoberta durante execução.
- [ ] Se descoberto que o build já era real: diff limitado a adição de steps de install + validate + upload-log.
- [ ] Se descoberto que só validava: diff maior, mas ainda cabe em 1 iteração (flatpak-builder CLI é direto).
- [ ] Job dispara em PR para main + push de tag `v*`.
- [ ] Em caso de falha do bundle install, o job falha e bloqueia release.

## Arquivos tocados

- `.github/workflows/flatpak.yml` (editar — escopo depende da auditoria)
- Possivelmente `assets/flatpak/*.yaml` se manifest precisar ajuste para install limpo.

## Proof-of-work

```bash
# 1. Auditoria inicial
cat .github/workflows/flatpak.yml | head -100
grep -n "flatpak-builder" .github/workflows/flatpak.yml

# 2. Após edição, validar YAML
python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/flatpak.yml')); print('jobs:', list(d['jobs'].keys()))"

# 3. Opcional: simular local com act se disponível
# act -j build-flatpak --container-architecture linux/amd64
```

## Notas para o executor

- **Passo 1 obrigatório**: ler `flatpak.yml` completo antes de editar. Não assumir que o step de build existe. A exploração inicial desta spec foi preliminar.
- **App ID**: ler de `assets/flatpak/*.metainfo.xml` ou `*.yaml`. Não hardcodar `br.dev.hefesto.Hefesto` se o manifest declara outro.
- **Falha esperada em `--version` GUI**: se o app for puramente GUI (sem CLI `--version` support), substituir por `flatpak info --user <app-id>` que só verifica registro, não execução.
- **Tamanho do bundle**: bundles Flatpak podem ser > 100 MB; upload do log sempre, upload do bundle **não** (economia de storage CI).
- **Runtime base**: se o manifest usa `org.gnome.Platform//44` ou similar, o runner precisa baixar. Tempo de job pode chegar a 10-15 min — isso é normal para flatpak.
- **Cache**: considerar cache do diretório `~/.local/share/flatpak/` entre runs. Fica para otimização futura se o job ficar lento.

## Fora de escopo

- Publicar em Flathub (fluxo separado, requer aprovação de mantenedores Flathub).
- Testar em múltiplas distros (Debian, Fedora, openSUSE) — ubuntu-22.04 é suficiente.
- Screenshot da GUI rodando via Flatpak (requer xvfb + display virtual — incremento grande).
- Criar canal Beta/Stable no Flathub.
