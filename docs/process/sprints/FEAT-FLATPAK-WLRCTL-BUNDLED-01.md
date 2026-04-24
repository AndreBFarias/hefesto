# FEAT-FLATPAK-WLRCTL-BUNDLED-01 — Bundlar `wlrctl` dentro do Flatpak

**Tipo:** feature (packaging).
**Wave:** V2.5 — sprint #3 da ordem recomendada em `docs/process/SPRINT_ORDER.md:433`.
**Porte:** S.
**Estimativa:** 1-2 iterações.
**Dependências:** BUG-COSMIC-WLR-BACKEND-01 (v2.4.1 — já entregue), BUG-FLATPAK-DEPS-01, BUG-FLATPAK-PIP-OFFLINE-01.

---

**Tracking:** label `type:feature`, `packaging`, `flatpak`, `wayland`, `ai-task`, `status:ready`.

## Objetivo

Incluir o binário `wlrctl` dentro do bundle Flatpak do Hefesto, de modo que `WlrctlBackend` funcione no sandbox sem depender de binário do host. Resolve o fallback atual em COSMIC (Flatpak só opera via XWayland hoje porque `wlrctl` não existe em `/app/bin`).

## Contexto

Pós-v2.4.1, o fluxo em Wayland é `WaylandPortalBackend` → `WlrctlBackend` → XWayland. Em COSMIC alpha, o portal `GetActiveWindow` não responde, então o caminho canônico deveria ser `WlrctlBackend`. Porém dentro do sandbox Flatpak, `shutil.which("wlrctl")` retorna `None` (binário não está em `/app/bin` nem no PATH do sandbox), e o backend marca-se indisponível — o app cai para XWayland via `--socket=fallback-x11`.

No `.deb`, `install.sh` instala `wlrctl` via `apt` (Recommends do debian/control) e o problema não aparece. No Flatpak, a única via é bundlar.

Arquivos relevantes (confirmados via grep):

- `flatpak/br.andrefarias.Hefesto.yml` — manifesto ativo. App ID: `br.andrefarias.Hefesto` (NÃO `br.com.hefesto.Hefesto` como o prompt sugeria). Runtime: `org.gnome.Platform//47`. SDK: `org.gnome.Sdk//47`. Dois módulos hoje: `hefesto-deps` (pip) e `hefesto` (wheel local).
- `flatpak/br.andrefarias.Hefesto.desktop`, `flatpak/br.andrefarias.Hefesto.metainfo.xml` — não tocados.
- `src/hefesto/integrations/window_backends/wlr_toplevel.py` — backend que consome o binário via `subprocess.run([_WLRCTL_BIN, "toplevel", "list", "--json", "--state", "activated"], timeout=1.0)`. Disponibilidade cacheada em `self._available` na instanciação.
- `tests/unit/test_wlr_toplevel.py` — 13 testes unitários existentes com mock de `shutil.which` e `subprocess.run`. Nenhum invoca binário real.
- `scripts/build_flatpak.sh` — referenciado por BUG-FLATPAK-PIP-OFFLINE-01. Script canônico para build local.

Upstream do `wlrctl` (confirmado em 2026-04-24 via `curl https://git.sr.ht/~brocellous/wlrctl/refs`):

- Tags publicadas: `v0.2.2` (latest), `v0.2.1`, `v0.2.0`, `v0.1.1`, `v0.1.0`.
- **Decisão:** usar `v0.2.2` (o prompt mencionava 0.2.1, mas 0.2.2 é superior e tem os mesmos requisitos de build).
- Build system: meson + ninja.
- Deps diretas de `meson.build` (raiz): `xkbcommon`, `wayland-client`.
- Deps transitivas de `protocol/meson.build`: `wayland-scanner` (programa). **Bundla os XMLs wayland-protocols dentro do próprio repo** (`virtual-keyboard-unstable-v1.xml`, `wlr-virtual-pointer-unstable-v1.xml`, `wlr-foreign-toplevel-management-unstable-v1.xml`, `wlr-output-management-unstable-v1.xml`) — ou seja, NÃO depende de `wayland-protocols` do sistema. Isso simplifica o bundling.

L-21-7 aplicado: probe local de `flatpak info org.gnome.Sdk//47` retornou "não instalado" — SDK GNOME 47 não está presente na máquina de desenvolvimento. Isso significa que a validação empírica das versões de `meson`/`ninja`/`wayland-scanner`/`xkbcommon` do runtime **precisa ser feita na iteração executora**, rodando o build real do flatpak (que instala SDK sob demanda) ou inspecionando o SDK após pull. Runtimes instalados hoje no host: `org.freedesktop.Platform` 23.08 / 24.08 / 25.08. Nenhum SDK GNOME. O executor-sprint DEVE registrar no proof-of-work as versões observadas dentro do SDK (probe sugerido abaixo).

## Escopo

### Arquivos a modificar

- `flatpak/br.andrefarias.Hefesto.yml` — adicionar módulo `wlrctl` ANTES do módulo `hefesto` (e idealmente antes ou depois do `hefesto-deps`, irrelevante porque não há cruzamento). Compila via meson+ninja com `--prefix=/app` → produz `/app/bin/wlrctl`.

### Arquivos a criar

- Nenhum arquivo novo de código. Se `flatpak/README.md` for criado nesta sprint (opcional), documentar que o bundle inclui `wlrctl` e qual versão.

### Testes a ajustar

- `tests/unit/test_wlr_toplevel.py` — adicionar ao menos 1 teste novo que exercite o caminho de PATH customizado (smoke de que `WlrctlBackend` lida com `shutil.which` retornando `/app/bin/wlrctl`). Os mocks existentes já cobrem "presente" com `/usr/bin/wlrctl` — acrescentar variante `/app/bin/wlrctl` confirma robustez a múltiplos paths. Este é teste mínimo de regressão, não substitui o teste de runtime no sandbox.

### Arquivos NÃO tocar

- `src/hefesto/integrations/window_backends/wlr_toplevel.py` — nenhuma mudança de lógica. Backend já usa `shutil.which("wlrctl")` genericamente; basta o binário estar no PATH do sandbox (`/app/bin` já é automaticamente incluído pelo flatpak).
- `flatpak/br.andrefarias.Hefesto.desktop`, `flatpak/br.andrefarias.Hefesto.metainfo.xml`.
- `install.sh`, `debian/control` — fluxo `.deb` intocado.
- Qualquer workflow `.github/workflows/*.yml`. O workflow Flatpak já executa `flatpak-builder` com rede na fase de sources — as tarballs do wlrctl serão baixadas na mesma fase que as deps pip já existentes.

## Escolha técnica: source `archive` vs `git`

Duas opções para declarar o source do `wlrctl`:

**Opção A (recomendada):** `type: archive` com tarball de release assinado.

```yaml
sources:
  - type: archive
    url: https://git.sr.ht/~brocellous/wlrctl/archive/v0.2.2.tar.gz
    sha256: <HASH-A-CALCULAR-NA-EXECUCAO>
```

**Opção B:** `type: git` fixando commit SHA.

```yaml
sources:
  - type: git
    url: https://git.sr.ht/~brocellous/wlrctl
    tag: v0.2.2
    commit: <COMMIT-SHA-DA-TAG>
```

Preferência: **A** — alinha com o padrão do ecossistema Flathub (tarballs com sha256 são preferidos para reprodutibilidade e cache do mirror). O executor deve calcular `sha256sum` do tarball baixado e cravar no manifesto. Fallback para B só se o sr.ht archive URL apresentar instabilidade (raro, mas já aconteceu historicamente — registrar no riscos).

## Critérios de aceite

- [ ] `flatpak/br.andrefarias.Hefesto.yml` declara módulo `wlrctl` com `buildsystem: meson`, `config-opts: [--buildtype=release]` (ou equivalente), e source `archive` apontando para `v0.2.2` com `sha256` cravado.
- [ ] `flatpak-builder --force-clean --user --install build-dir flatpak/br.andrefarias.Hefesto.yml` completa sem erro localmente.
- [ ] Após build, `flatpak run --command=which br.andrefarias.Hefesto wlrctl` retorna `/app/bin/wlrctl` (string não-vazia, exit code 0).
- [ ] `flatpak run --command=wlrctl br.andrefarias.Hefesto --version` retorna string contendo `0.2.2`.
- [ ] `flatpak run --command=python3 br.andrefarias.Hefesto -c "from hefesto.integrations.window_backends.wlr_toplevel import WlrctlBackend; b=WlrctlBackend(); print('available=', b._available)"` imprime `available= True`.
- [ ] Workflow `.github/workflows/flatpak.yml` verde no próximo push (sem mudança no workflow).
- [ ] Tamanho do bundle `.flatpak` aumenta em ≤300 KiB vs baseline v2.4.1. Executor deve registrar delta medido no proof-of-work.
- [ ] Testes unitários: `pytest tests/unit/test_wlr_toplevel.py -q` verde com ≥14 testes (baseline 13 + ao menos 1 novo).
- [ ] Gates canônicos verdes: `ruff check .`, `ruff format --check .`, `mypy src`, `pytest` full suite, `python3 scripts/audit_*.py` (todos os scripts de auditoria listados no `VALIDATOR_BRIEF.md`).
- [ ] Acentuação PT-BR correta em todo arquivo tocado; zero emojis gráficos (glifos `●`, `○`, `█` permitidos se preexistirem por outra finalidade).

## Plano de implementação

1. **Probe empírico (L-21-7).** Baixar o SDK GNOME 47 se ainda não estiver:
   ```bash
   flatpak install --user --noninteractive flathub org.gnome.Sdk//47 org.gnome.Platform//47
   flatpak run --command=meson org.gnome.Sdk//47 --version
   flatpak run --command=ninja org.gnome.Sdk//47 --version
   flatpak run --command=pkg-config org.gnome.Sdk//47 --modversion wayland-client xkbcommon
   flatpak run --command=which org.gnome.Sdk//47 wayland-scanner
   ```
   Registrar as versões observadas no proof-of-work. Se `meson` < 0.60 ou `xkbcommon` ausente, parar e abrir sprint derivada `INFRA-FLATPAK-SDK-DEPS-01`.

2. **Calcular sha256 do tarball upstream.**
   ```bash
   curl -sL -o /tmp/wlrctl-0.2.2.tar.gz https://git.sr.ht/~brocellous/wlrctl/archive/v0.2.2.tar.gz
   sha256sum /tmp/wlrctl-0.2.2.tar.gz
   ```
   Copiar o hash para o manifesto.

3. **Editar `flatpak/br.andrefarias.Hefesto.yml`** — adicionar módulo novo após `hefesto-deps` e antes de `hefesto`. Esqueleto:

   ```yaml
     # Módulo: wlrctl — CLI wayland wlroots usado por WlrctlBackend
     # (BUG-COSMIC-WLR-BACKEND-01). No .deb vem via Recommends do apt;
     # no sandbox do Flatpak precisa ser bundlado.
     # Upstream: https://git.sr.ht/~brocellous/wlrctl
     # Deps: xkbcommon, wayland-client, wayland-scanner — todas no
     # org.gnome.Sdk//47. Protocolo XMLs bundlados no próprio repo
     # do wlrctl, então não precisa de wayland-protocols do sistema.
     - name: wlrctl
       buildsystem: meson
       config-opts:
         - --buildtype=release
       sources:
         - type: archive
           url: https://git.sr.ht/~brocellous/wlrctl/archive/v0.2.2.tar.gz
           sha256: <CALCULADO-NO-PASSO-2>
       cleanup:
         - /share/man
   ```

   Ordem de módulos final: `hefesto-deps` → `wlrctl` → `hefesto`.

4. **Rodar build local.**
   ```bash
   cd ~/Desenvolvimento/Hefesto-DualSense_Unix
   bash scripts/build_flatpak.sh  # ou comando equivalente do script atual
   # Alternativa crua:
   # flatpak-builder --user --force-clean --install build-dir flatpak/br.andrefarias.Hefesto.yml
   ```

5. **Validar o binário no sandbox.**
   ```bash
   flatpak run --command=which br.andrefarias.Hefesto wlrctl
   flatpak run --command=wlrctl br.andrefarias.Hefesto --version
   flatpak run --command=python3 br.andrefarias.Hefesto -c \
     "from hefesto.integrations.window_backends.wlr_toplevel import WlrctlBackend; \
      b=WlrctlBackend(); print('available=', b._available)"
   ```

6. **Medir delta de tamanho.**
   ```bash
   ls -l build-dir/*.flatpak  # ou onde o script gera
   # Comparar com asset v2.4.1 baixado do release anterior
   ```
   Registrar delta KiB no proof-of-work.

7. **Ajustar teste unitário.** Em `tests/unit/test_wlr_toplevel.py`, adicionar:

   ```python
   def test_wlrctl_aceita_path_em_app_bin_flatpak(
       monkeypatch: pytest.MonkeyPatch,
   ) -> None:
       """Backend aceita wlrctl em /app/bin (PATH do sandbox Flatpak)."""
       monkeypatch.setattr(
           wlr_toplevel.shutil, "which",
           lambda binary: "/app/bin/wlrctl",
       )
       _patch_run(
           monkeypatch,
           stdout='[{"app_id": "steam", "title": "Steam"}]',
       )
       backend = wlr_toplevel.WlrctlBackend()
       assert backend._available is True
       info = backend.get_active_window_info()
       assert info is not None
       assert info.app_id == "steam"
   ```

8. **Rodar gates canônicos.**
   ```bash
   ruff check . && ruff format --check .
   mypy src
   pytest -q
   # Scripts de auditoria listados no VALIDATOR_BRIEF
   ```

9. **Push em branch e observar workflow Flatpak Build.**
   ```bash
   gh workflow run flatpak.yml
   gh run watch $(gh run list --workflow flatpak.yml --limit 1 --json databaseId --jq '.[0].databaseId')
   ```

## Aritmética

Não há meta numérica de LOC em arquivo de código fonte. Deltas esperados:

- `flatpak/br.andrefarias.Hefesto.yml`: +13 a +16 linhas (módulo `wlrctl` novo, incluindo comentários explicativos). Baseline atual: 114 linhas. Projetado: ~128-130 linhas.
- `tests/unit/test_wlr_toplevel.py`: +15 a +20 linhas (1 teste novo + imports se necessário). Baseline: 205 linhas.
- Tamanho do bundle `.flatpak`: +≤300 KiB (alvo). `wlrctl` compilado com strip é tipicamente ~80-150 KiB; com man pages removidos (`cleanup: [/share/man]`), fica abaixo do teto.

## Invariantes a preservar

- **L-21-7**: validar empiricamente o SDK; não assumir versões. Probe registrado no proof-of-work.
- **L-21-4**: não citar identificadores inventados. Manifesto real é `br.andrefarias.Hefesto` (não `br.com.hefesto.Hefesto` como sugerido no prompt).
- **L-21-2**: reprodução em árvore limpa. Antes do build, verificar `git status` limpo.
- **L-21-5**: não rodar mais de 1 executor paralelo — build flatpak é pesado (CPU + disco).
- **CLAUDE.md §9 zero emojis gráficos**: glifos decorativos `●`, `○`, `█` usados em TUI não são emojis e permanecem; nenhum emoji gráfico em comentário de manifesto ou spec.
- **Backend wlr_toplevel.py não muda**: toda lógica de fallback e mocks existentes continuam válidos. Se o executor sentir necessidade de mexer em `wlr_toplevel.py`, PARAR e confirmar — é sinal de escopo creep.
- **Runtime GNOME 47 é imutável nesta sprint**: migração para runtime//48 é sprint separada (BLOCKED histórico).

## Proof-of-work esperado

O executor entrega:

1. Diff do `flatpak/br.andrefarias.Hefesto.yml` e `tests/unit/test_wlr_toplevel.py`.
2. Output do probe do SDK (passo 1 do plano) — versões de meson, ninja, xkbcommon, wayland-client, wayland-scanner registradas.
3. SHA256 do tarball `v0.2.2` calculado e cravado no manifesto.
4. Log completo do `flatpak-builder` (pode ser recortado nos últimos 80 linhas + "MODULE COMPLETE: wlrctl" visível).
5. Output literal dos 3 probes de runtime:
   ```
   flatpak run --command=which br.andrefarias.Hefesto wlrctl
   flatpak run --command=wlrctl br.andrefarias.Hefesto --version
   flatpak run --command=python3 br.andrefarias.Hefesto -c "..."
   ```
6. Delta de tamanho medido (KiB) com referência ao asset v2.4.1.
7. Output de `pytest tests/unit/test_wlr_toplevel.py -v` mostrando 14+ testes passando.
8. Output dos gates canônicos (ruff, mypy, pytest completo).
9. URL do run do workflow Flatpak Build verde no GitHub Actions.
10. Acentuação periférica verificada com grep simples:
    ```bash
    rg -n '[aeiouAEIOU]~|\\`[aeiouAEIOU]' flatpak/br.andrefarias.Hefesto.yml \
        tests/unit/test_wlr_toplevel.py docs/process/sprints/FEAT-FLATPAK-WLRCTL-BUNDLED-01.md
    # Resultado esperado: nenhuma acentuação quebrada (zero matches de padrões errados).
    ```

Validação visual não aplicável (não há mudança de UI).

## Riscos conhecidos

- **sr.ht instabilidade (raro).** Se `https://git.sr.ht/~brocellous/wlrctl/archive/v0.2.2.tar.gz` retornar 5xx durante o build CI, o workflow Flatpak quebra. Mitigação: fallback para `type: git` com `commit:` cravado (Opção B). Se virar padrão, abrir sprint `INFRA-FLATPAK-MIRROR-WLRCTL-01`.
- **Incompatibilidade com SDK 47.** Se `wayland-scanner` ou `xkbcommon` no GNOME Sdk 47 não forem suficientes (improvável — GNOME Sdk é superconjunto de freedesktop), meson pode falhar. Plano B: compilar `xkbcommon` como módulo shared-modules antes do `wlrctl`. Shared-modules do Flathub já tem receita pronta.
- **`werror=true` no meson.build do wlrctl.** wlrctl compila com `-Werror`. Se o compilador do SDK for mais novo que a última revisão do wlrctl e introduzir warnings, o build quebra. Mitigação: passar `config-opts: [--buildtype=release, -Dwerror=false]` no manifesto. Incluir no primeiro shot para evitar re-roll.
- **Tamanho excedendo 300 KiB.** Se o bundle crescer mais, revisar cleanup (adicionar `/include`, `/share/doc`). Último recurso: aumentar o teto e documentar no próximo release note.
- **SDK GNOME 47 local ausente durante planejamento.** L-21-7 exige probe — foi documentado acima que o executor precisa rodar `flatpak install org.gnome.Sdk//47` antes do primeiro build. Se a máquina de CI do GitHub Actions já baixa runtime automaticamente no workflow, local é suficiente ter espaço em disco (~2 GiB para SDK).

## Não-objetivos

- **Reimplementar `WlrctlBackend` em `pywayland` puro** — essa é a sprint **FEAT-WLR-TOPLEVEL-PYWAYLAND-01** (alternativa #2 da Wave V2.5). Se executada, esta sprint vira obsoleta, mas enquanto não for, bundlar é mais barato.
- **Publicar no Flathub oficial** — ainda não é objetivo V2.5.
- **Migrar para `org.gnome.Platform//48`** — sprint separada, dependência de validação.
- **Testar `WlrctlBackend.get_active_window_info()` de ponta a ponta contra compositor real** — requer COSMIC rodando em ambiente de desenvolvimento. Essa validação é coberta pela sprint #1 da Wave V2.5 (validação manual em Pop!_OS COSMIC).

## Rollback

Se após merge a sprint romper builds Flatpak downstream:

1. Reverter commit do manifesto: `git revert <sha>`.
2. Executar `scripts/build_flatpak.sh` para confirmar retorno ao estado v2.4.1.
3. Abrir sprint derivada com evidência do erro (log do flatpak-builder).

O backend `WlrctlBackend` continua funcional para usuários `.deb` / AppImage (onde `wlrctl` vem pelo host). Rollback no Flatpak apenas retorna o fluxo ao fallback XWayland — nenhum usuário perde funcionalidade relativa ao baseline pré-sprint.

## Referências

- `VALIDATOR_BRIEF.md` — raiz do repo.
- `docs/process/SPRINT_ORDER.md:433` — justificativa da ordem Wave V2.5.
- `docs/process/sprints/BUG-FLATPAK-PIP-OFFLINE-01.md` — padrão de sources offline no manifesto.
- `docs/process/sprints/FEAT-FLATPAK-BUNDLE-01.md`, `docs/process/sprints/BUG-FLATPAK-DEPS-01.md` (se existir) — histórico de decisões do manifesto.
- `src/hefesto/integrations/window_backends/wlr_toplevel.py` — backend consumidor.
- `tests/unit/test_wlr_toplevel.py` — baseline de testes.
- Upstream wlrctl: https://git.sr.ht/~brocellous/wlrctl (tag `v0.2.2`).
- Protocolo wlr-foreign-toplevel-management-unstable-v1 (bundlado no repo do wlrctl, não requer `wayland-protocols` do sistema).
