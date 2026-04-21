# DOCS-QUICKSTART-01 — Quickstart visual com GIFs

**Tipo:** docs.
**Wave:** V1.1 (concorrente).
**Estimativa:** 1 iteração.
**Dependências:** nenhuma.

---

## Contexto

`README.md` atual é técnico — lista dependências, arquitetura, protocolos. Bom para contribuidores, ruim para o usuário final que acabou de plugar o DualSense e quer fazer funcionar. Hefesto v1.0.0 merece um guia visual com GIFs: instalação, primeira conexão, troca de perfil, aba Mouse, etc.

## Decisão

Criar `docs/usage/quickstart.md` seguindo este roteiro:

1. **Antes de começar**: pré-requisitos (Python 3.10+, `libhidapi`, `libudev`, `PyGObject` — comando `apt`/`dnf`).
2. **Instalação em 1 comando**: `./install.sh --yes` + o que esperar (prompt sudo, systemd ativo, ícone no menu).
3. **Primeira abertura**: screenshot da GUI com banner + aba Status + daemon online.
4. **Troca de perfil** por janela ativa: GIF de abrir Firefox → Steam → jogo, lightbar mudando de cor. Asciinema alternativo aceitável.
5. **Emulação de mouse**: GIF de habilitar toggle + stick esquerdo movendo o cursor.
6. **Solução de problemas comuns**:
   - "Daemon offline e não sobe": checar `systemctl --user status hefesto.service`.
   - "Gatilhos sem efeito": checar udev rules (`ls -l /dev/hidraw*`).
   - "DualSense desconecta sozinho": confirmar regra autosuspend (`cat /sys/bus/usb/devices/*/power/control | head -5`).
7. **Onde ir em seguida**: link para `docs/usage/creating-profiles.md`, `docs/usage/hotkeys.md`, `docs/adr/`.

Ferramentas para GIFs:
- `peek` (GUI, simples) — output `.gif` direto.
- `asciinema` + `agg` para sequências CLI.

## Critérios de aceite

- [ ] `docs/usage/quickstart.md` completo, em PT-BR.
- [ ] Pelo menos 3 GIFs (ou PNGs de passo-a-passo se GIFs pesarem demais — limite 2MB/asset).
- [ ] Assets em `docs/usage/assets/` com nomes `quickstart_<passo>_<descricao>.gif`/`.png`.
- [ ] `README.md` no topo ganha seção "Começar em 2 minutos" apontando para o quickstart.
- [ ] Lint de markdown opcional (`mdl` ou `markdownlint-cli`).

## Arquivos tocados (previsão)

- `docs/usage/quickstart.md` (novo)
- `docs/usage/assets/quickstart_*.{gif,png}` (≥ 3 arquivos)
- `README.md` (acréscimo de link no topo)

## Fora de escopo

- Traduzir para EN (próxima sprint).
- Tutorial de criação de perfis (fica em `creating-profiles.md` — sprint irmã).
- Videos longos (YouTube). GIFs curtos (≤ 10s) suficientes.

## Notas

- Capturar com daemon ativo + DualSense real. Sem fake para o quickstart ter autenticidade visual.
- Evitar mostrar paths pessoais (`/home/<nome>`). Usar `~` ou `/home/andre` anonimizado se necessário.
