# FEAT-GITHUB-PROJECT-VISIBILITY-01 — SEO, topics, social preview e descoberta

**Tipo:** feat (open source / marketing).
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** CHORE-CI-REPUBLISH-TAGS-01 (release com artifacts públicos fortalece descoberta).

---

**Tracking:** label `type:feat`, `open-source`, `seo`, `ai-task`, `status:ready`.

## Epígrafe

> *"A forja não revela o ferreiro. Só a espada."*

Hefesto é o ferreiro dos deuses. O projeto não expõe seu autor por anonimato absoluto — mas a ferramenta em si precisa ser achada por quem procura.

## Contexto

O repositório `AndreBFarias/hefesto` hoje:

- Descrição ausente ou genérica no GitHub (topo do repo).
- **Zero topics** configuradas — GitHub não sugere o projeto em busca por `dualsense`, `adaptive-triggers`, `linux-gamepad`, etc.
- Social preview (og-image) não customizada — compartilhar o link gera card genérico com logo GitHub.
- Nenhum `.github/FUNDING.yml` (ok — autor tem anonimato por decisão; mas se quiser doações anônimas via OpenCollective/LFX, caberia futuro).
- `README.md` não tem badges de descoberta (PyPI, AUR, crates equivalent — aqui: `.deb`/`.AppImage`/`.flatpak` download counts, CI status, license).
- Sem seção `Alternatives / Comparable projects` que linka para `dualsensectl`, `DSX`, `dualsensex-linux` — essa "vizinhança" é SEO orgânico.
- `CONTRIBUTING.md` ausente — barreira para PRs externos.
- `SECURITY.md` ausente — dificulta disclosure responsável.
- `CODE_OF_CONDUCT.md` ausente — alguns maintainers evitam contribuir sem isso.

## Decisão

Sprint faz 3 peças:

### 1. Descoberta orgânica (SEO do GitHub)

- **Descrição do repo** (campo `About` no topo): `"Daemon Linux para DualSense: gatilhos adaptativos, rumble, LEDs, perfis e emulação. Zero-dep, anônimo, PT-BR."` (≤140 char, inclui keywords-alvo).
- **Topics** (até 20, `gh repo edit --add-topic`):
  - `dualsense` · `playstation-5` · `ps5-controller` · `adaptive-triggers` · `linux-gamepad` · `gamepad-driver` · `hidapi` · `python-daemon` · `gtk3` · `textual-tui` · `udev-rules` · `flatpak` · `appimage` · `debian-package` · `cosmic-desktop` · `gnome` · `open-source` · `portuguese-brazilian` · `accessibility` · `input-device`.
- **Website** (campo `URL` no About): `https://github.com/AndreBFarias/hefesto` ou, se houver GH Pages futuro, o subdomínio próprio.

### 2. Documentação para entrada de contribuidores

- `.github/FUNDING.yml` — **omitir** (decisão de anonimato do autor).
- `CONTRIBUTING.md` (novo): como rodar `scripts/dev-setup.sh`, como abrir sprint (link para `SPRINT_ORDER.md`), como rodar gates locais, convenção de commit PT-BR, ciclo auto-merge sem PR (documentar que é **projeto pessoal**, PRs externos de desconhecidos passam por revisão manual antes de merge).
- `SECURITY.md` (novo): disclosure responsável, e-mail de contato (usar o do autor registrado em `~/.git-personal/.gitconfig` ou criar alias dedicado).
- `CODE_OF_CONDUCT.md` (novo): Contributor Covenant 2.1 PT-BR adaptado.
- `ISSUE_TEMPLATE/`: 3 templates (`bug.md`, `feature.md`, `question.md`) com placeholders PT-BR.
- `PULL_REQUEST_TEMPLATE.md`: checklist (testes, ruff, acentuação, anonimato preservado).

### 3. Cartão social (og-image)

- Criar imagem 1280×640 PNG em `docs/usage/assets/social-preview.png`:
  - Fundo roxo Dracula (`#44475a` + gradiente para `#282a36`).
  - Logo do Hefesto (círculo RGB lightbar estilizado) à esquerda.
  - Texto à direita:
    - Linha 1 grande: **Hefesto**
    - Linha 2: "daemon de gatilhos adaptativos para DualSense em Linux"
    - Linha 3 pequena no rodapé: *"A forja não revela o ferreiro. Só a espada."*
- Upload via `Settings > Social preview` (manual via navegador ou `gh api repos/AndreBFarias/hefesto -X PATCH -f ...` — ver se API permite; se não, documentar passo manual).
- `README.md` topo: o mesmo og-image serve de hero.
- Frase da epígrafe vira citação no README (destaque em blockquote) — entra no espírito do projeto sem quebrar anonimato.

### 4. Badges no README

- CI: `![Release](https://github.com/AndreBFarias/hefesto/actions/workflows/release.yml/badge.svg)` + CI + Flatpak.
- License: `![License](https://img.shields.io/github/license/AndreBFarias/hefesto)`.
- Versão: `![Release](https://img.shields.io/github/v/release/AndreBFarias/hefesto)`.
- Downloads totais do `.deb`: `![Downloads](https://img.shields.io/github/downloads/AndreBFarias/hefesto/total)`.
- Python: `![Python](https://img.shields.io/badge/python-3.10+-blue)`.
- Plataformas: `![Linux](https://img.shields.io/badge/platform-Linux-informational)`.

## Critérios de aceite

- [ ] GitHub About tem descrição + até 20 topics + URL.
- [ ] `.github/` tem `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `PULL_REQUEST_TEMPLATE.md`, `ISSUE_TEMPLATE/` com 3 arquivos.
- [ ] `docs/usage/assets/social-preview.png` criado e upload como og-image (manual via Settings se API não suporta).
- [ ] README topo com blockquote da epígrafe + 5+ badges.
- [ ] Verificar descoberta: em 7 dias, query `site:github.com dualsense linux portuguese` ou similar retorna o repo na primeira página (não-determinístico — não bloqueia sprint).
- [ ] Anonimato preservado — nenhum arquivo novo menciona autor real além do `git commit author` já normalizado.

## Arquivos tocados

- `.github/CONTRIBUTING.md` (novo).
- `.github/SECURITY.md` (novo).
- `.github/CODE_OF_CONDUCT.md` (novo).
- `.github/PULL_REQUEST_TEMPLATE.md` (novo).
- `.github/ISSUE_TEMPLATE/bug.md`, `.github/ISSUE_TEMPLATE/feature.md`, `.github/ISSUE_TEMPLATE/question.md` (novos).
- `docs/usage/assets/social-preview.png` (novo binário).
- `README.md` (blockquote epígrafe + badges + hero image).

## Proof-of-work runtime

```bash
# Descrição e topics via gh CLI
gh repo edit AndreBFarias/hefesto \
  --description "Daemon Linux para DualSense: gatilhos adaptativos, rumble, LEDs, perfis e emulação. Zero-dep, anônimo, PT-BR." \
  --add-topic dualsense --add-topic playstation-5 --add-topic ps5-controller \
  --add-topic adaptive-triggers --add-topic linux-gamepad --add-topic gamepad-driver \
  --add-topic hidapi --add-topic python-daemon --add-topic gtk3 --add-topic textual-tui \
  --add-topic udev-rules --add-topic flatpak --add-topic appimage --add-topic debian-package \
  --add-topic cosmic-desktop --add-topic gnome --add-topic open-source \
  --add-topic portuguese-brazilian --add-topic accessibility --add-topic input-device

# Confirmar
gh repo view AndreBFarias/hefesto --json description,repositoryTopics --jq '.'

# Social preview — tentar via API (se falhar, manual via navegador)
gh api -X PATCH repos/AndreBFarias/hefesto \
  -f name=hefesto \
  # upload de og-image não é exposto via REST — fazer pela UI em Settings > General > Social preview
```

## Notas

- **Anonimato**: topics usadas não expõem autor. Descrição não menciona nome próprio. Social preview não tem foto do autor. `SECURITY.md` usa e-mail público do git (`andre.dsbf@gmail.com` já está em commits — sem vazamento novo).
- **Epígrafe "A forja não revela o ferreiro. Só a espada."**: entra no README como blockquote destacado, com atribuição vaga (`— dito da forja`) para manter o tom mítico sem reivindicar autoria de aforismo nem expor quem escreveu. Casa com o mito de Hefesto, casa com o anonimato.
- **Conversor-Video-Para-ASCII como referência visual**: conferir se o projeto-irmão já tem topics/descrição/badges e espelhar o padrão se sim. Consistência entre os repos pessoais ajuda.

## Fora de escopo

- Criar GitHub Pages / site dedicado.
- Submeter a Flathub (sprint futura — requer revisão upstream).
- Anúncio em Reddit/HN/lobsters/LWN/Fedora Planet — decisão do usuário se e quando.
- Vídeo demo em YouTube — fora do projeto em si.
