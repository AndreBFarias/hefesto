# DOCS-README-RENOVATE-01 — README modernizado com prints, layout Conversor-Video-Para-ASCII, acentuação

**Tipo:** docs.
**Wave:** V2.2 — polish pós-v2.1.0.
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

**Tracking:** label `type:docs`, `ai-task`, `status:ready`.

## Contexto

Usuário em 2026-04-23 pediu:

> "Requirements, install, run, desktop, uninstall estão atualizados? Pode tirar printscreens inserir e deixar o README melhor (com acentuação corrigida, inclusive?) e atualizado? Pode deixar o layout igual em formato ao do `~/Desenvolvimento/Conversor-Video-Para-ASCII`?"

README atual (v2.1.0) tem as seções certas mas:

- Algumas strings em PT-BR sem acento (reprovado pelo hook strict, mas whitelisted para o README — débito).
- Screenshots antigos ou ausentes.
- Layout difere do projeto irmão `Conversor-Video-Para-ASCII` (referência visual que o usuário quer espelhar).

## Decisão

1. **Ler a estrutura do projeto-irmão**: `cat ~/Desenvolvimento/Conversor-Video-Para-ASCII/README.md | head -200` e mapear seções (Badges? Hero image? Quickstart? Features em cards?).
2. **Re-organizar o README** do Hefesto usando o mesmo layout:
   - Header com nome + versão + badges de CI.
   - Hero image (screenshot principal da GUI, provavelmente Status ou Lightbar).
   - "O que é" + "Por quê".
   - Quickstart em 3 linhas (`apt install ./hefesto_2.1.0_amd64.deb` + `systemctl --user enable --now hefesto.service` + `hefesto-gui`).
   - Features (lista canônica com ícones/glyphs Unicode de estado).
   - Instalação detalhada (.deb + AppImage + Flatpak + from-source).
   - Troubleshooting (udev, autosuspend, hidraw permissions).
   - Contribuição (pre-commit install).
   - Referências (links para ADRs, CHANGELOG).
3. **Screenshots**: capturar 5-6 PNGs das abas principais da GUI via skill `validacao-visual` e guardar em `docs/usage/assets/readme_<aba>.png`. Referenciar no README com alt text PT-BR.
4. **Corrigir acentuação**: rodar `python3 scripts/validar-acentuacao.py --check-file README.md` e acentuar o que aparecer. Se README estiver na whitelist, **tirar da whitelist** — README deve ser exemplar.
5. Atualizar versões de download para v2.1.0 (ou usar `latest` se for CI-aware).

## Critérios de aceite

- [ ] README segue layout visual do projeto-irmão (título/seções análogos).
- [ ] 5-6 screenshots em `docs/usage/assets/readme_*.png` referenciados.
- [ ] Zero palavras PT-BR sem acento (`validar-acentuacao.py --check-file README.md` retorna 0).
- [ ] `check_anonymity.sh` verde.
- [ ] Links quebrados verificados (CI ou `markdown-link-check` local).
- [ ] Versão coerente (`check_version_consistency.py` verde).
- [ ] Comparação visual side-by-side do README renderizado no GitHub com o do projeto-irmão.

## Arquivos tocados

- `README.md` (rewrite).
- `docs/usage/assets/readme_*.png` (novos).
- `scripts/validar-acentuacao.py` se README for tirado da whitelist implícita.

## Proof-of-work runtime

```bash
# Capturar screenshots
HEFESTO_FAKE=1 .venv/bin/python -m hefesto.app.main &
sleep 2
WID=$(xdotool search --name 'Hefesto' | head -1)
for TAB in status gatilhos lightbar rumble perfis daemon; do
  # Switch pra tab via keyboard nav (Ctrl+Tab) ou mouse-click
  import -window "$WID" "docs/usage/assets/readme_${TAB}.png"
done
kill %1

# Validação
python3 scripts/validar-acentuacao.py --check-file README.md
python3 scripts/check_version_consistency.py
./scripts/check_anonymity.sh

# Renderização local (opcional)
# pip install grip && grip README.md
```

## Referência externa

- Projeto-irmão: `~/Desenvolvimento/Conversor-Video-Para-ASCII/README.md` (ler inteiro antes de começar).

## Fora de escopo

- Traduzir README para inglês (esta sprint é PT-BR; sprint futura pode criar `README.en.md`).
- Rewrite das ADRs ou do `docs/process/SPRINT_ORDER.md`.
