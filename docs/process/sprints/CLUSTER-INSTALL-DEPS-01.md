# CLUSTER-INSTALL-DEPS-01 — detecção de dependências externas no install.sh

**Tipo:** infra (instalação) + bug-fix (UX silencioso na GUI).
**Wave:** V2.2.x — pós-rebrand.
**Branch:** `rebrand/dualsense4unix`. PR alvo: #103.
**Estimativa:** 1 iteração (cluster de 2 frentes em um único spec).
**Dependências:** nenhuma (extension `ubuntu-appindicators@ubuntu.com` é nativa Ubuntu/Pop!_OS; `dualsensectl` opcional via flatpak).

---

**Tracking:** label `type:infra`, `type:bug`, `area:install`, `area:firmware`, `status:ready`.

## Contexto

Cluster ataca **duas frentes que tocam `install.sh`** em uma única passagem para evitar conflitos de merge no mesmo arquivo. Ambas são **detecções de dependências externas** com prompts opt-in PT-BR e fallback gracioso.

Trechos lidos que confirmam a premissa:
- `install.sh:309-346` — passos 6/7 já usam `ask_yn` com `AUTO_YES` para sysbtemd-user units.
- `install.sh:144-160` — passo 2/7 já usa o padrão `ask_yn` + `run_apt` para GTK3, exatamente o template a replicar.
- `src/hefesto_dualsense4unix/integrations/firmware_updater.py:24` — `BINARY = "dualsensectl"`; `:86-91` — `is_available()` retorna `shutil.which(self.binary) is not None`.
- `src/hefesto_dualsense4unix/app/actions/firmware_actions.py:31-34` — texto `_INSTALL_HELP` atual ("AUR, brew, build do GitHub") já existe mas é genérico e não cita flatpak.
- `src/hefesto_dualsense4unix/app/actions/firmware_actions.py:62-67` — `install_firmware_tab` já chama `is_available()` e desabilita botões + mostra `_INSTALL_HELP` quando ausente. Comportamento NÃO é silencioso na inicialização da aba — mas mensagem atual não orienta solução real (Flathub).
- `README.md:235` — extension `AppIndicator and KStatusNotifierItem Support` já listada como recomendada para GNOME 42+ mas sem instrução de habilitação.
- `uninstall.sh:1-126` — não toca extensions nem dualsensectl; cluster atual mantém uninstall fora de escopo (não há simetria a fazer — habilitar extension não é instalar pacote).

### Frente A — TRAY-VISIBILITY-INSTALL-01

`ubuntu-appindicators@ubuntu.com` é **GNOME Shell extension instalada mas DESABILITADA por default** em Pop!_OS 22.04 e Ubuntu 22.04 vanilla. Sem habilitar, AppIndicator do Hefesto registra D-Bus item mas nada renderiza visualmente — usuário não consegue clicar em "Abrir painel", trocar perfil, ou Sair.

Reproduzido em 2026-04-27 no PC do usuário (Pop!_OS 22.04, GNOME 42 X11). Comandos canônicos:
```bash
gnome-extensions list | grep appindicator              # bate ubuntu-appindicators@ubuntu.com
gnome-extensions list --enabled | grep appindicator    # vazio
gnome-extensions enable ubuntu-appindicators@ubuntu.com  # ícone aparece
```

Outras DEs (KDE, COSMIC, XFCE) renderizam Ayatana nativamente — não precisam dessa intervenção.

### Frente B — FEAT-FIRMWARE-DUALSENSECTL-INSTALL-01

`dualsensectl` é binário externo do upstream `nowrep/dualsensectl`. **Não está em apt do Jammy/Noble**. Disponível via:
- **Flathub:** `com.github.nowrep.dualsensectl` (recomendado pelo upstream).
- **GitHub source:** `https://github.com/nowrep/dualsensectl` (cmake manual).
- AUR (Arch): `dualsensectl` (não aplicável a Pop!_OS/Ubuntu/Fedora alvo).

Sem `dualsensectl` no PATH, a aba Firmware mostra `_INSTALL_HELP` mas a mensagem cita "AUR, brew, build do GitHub" — não cita flatpak (canônico) nem URL clicável. UX subótimo.

## Escopo (touches autorizados)

**Arquivos a modificar:**
- `install.sh` — adicionar passos 8/9 (ou seções dentro do passo existente — ver Plano §3) para detecção de extension AppIndicator no GNOME e binário `dualsensectl` no PATH.
- `README.md` — seção Instalação: nota sobre habilitação automática da extension AppIndicator no GNOME; aba Firmware menciona instalação opcional via flatpak.
- `src/hefesto_dualsense4unix/app/actions/firmware_actions.py` — atualizar `_INSTALL_HELP` (linhas 31-34) com instrução acionável priorizando flatpak + URL Flathub.

**Arquivos a criar:**
- `tests/unit/test_firmware_actions_missing_binary.py` — teste de comportamento `install_firmware_tab` quando `is_available()=False`.

**Arquivos NÃO a tocar:**
- `uninstall.sh` — habilitar extension não é instalação de pacote; reverter no uninstall causaria mais confusão (usuário pode usar a extension para outros tray icons). Documentar decisão em "Riscos".
- `src/hefesto_dualsense4unix/integrations/firmware_updater.py` — `BINARY = "dualsensectl"` (linha 24) e `is_available()` (linha 89-91) já estão corretos. Não tocar.
- `src/hefesto_dualsense4unix/app/tray.py`, `src/hefesto_dualsense4unix/integrations/tray.py` — código do tray já funciona via Ayatana; problema é só a extension GNOME desabilitada, externa ao código.
- `assets/*.service`, udev rules — fora de escopo.

## Acceptance criteria

### Frente A (extension AppIndicator)

1. `install.sh` detecta GNOME Shell ativo via `XDG_CURRENT_DESKTOP` (case-insensitive contém "GNOME").
2. Quando GNOME ativo, checa via `gnome-extensions list --enabled` se `ubuntu-appindicators@ubuntu.com` está habilitada.
3. Se a extension existe (`gnome-extensions list` confirma) mas não está nas habilitadas, oferece habilitar via prompt PT-BR. Flag `--yes` aceita automaticamente.
4. Quando aceito, executa `gnome-extensions enable ubuntu-appindicators@ubuntu.com` e verifica retorno; em caso de sucesso imprime "      ok"; em falha imprime aviso e prossegue.
5. Quando a extension nem existe (caso de GNOME minimalista ou outra distro), imprime aviso citando o nome canônico e deixa de oferecer prompt — não falha o install.
6. Quando DE não é GNOME (KDE, COSMIC, XFCE, Cinnamon, MATE), passo é pulado silenciosamente com mensagem informativa "DE <nome> renderiza Ayatana nativamente — sem ação".
7. Em ambiente headless (sem `XDG_CURRENT_DESKTOP` definido — ex: CI, SSH puro) o passo é pulado sem prompt.

### Frente B (dualsensectl)

8. `install.sh` detecta `dualsensectl` no PATH via `command -v`.
9. Se ausente, imprime mensagem PT-BR explicando que a aba Firmware ficará indisponível e oferece instalação via `flatpak install --user flathub com.github.nowrep.dualsensectl` quando `flatpak` está no PATH e `flathub` aparece em `flatpak remotes`. Flag `--yes` aceita.
10. Se `flatpak` está no PATH mas o remote `flathub` não está configurado, imprime instrução para `flatpak remote-add --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo` e segue sem instalar.
11. Se `flatpak` não está disponível, imprime instrução alternativa (link `https://github.com/nowrep/dualsensectl` para build manual) e segue.
12. Em qualquer caso, install termina com `exit 0` quando dualsensectl ausente — é OPCIONAL, nunca bloquear.
13. `_INSTALL_HELP` em `firmware_actions.py:31-34` é reescrito para citar Flathub primeiro (com URL `https://flathub.org/apps/com.github.nowrep.dualsensectl`) e build manual como fallback. Mensagem permanece em PT-BR.
14. Teste `test_firmware_actions_missing_binary.py` valida que `install_firmware_tab` com `FirmwareUpdater` mockado (`is_available()=False`) chama `_set_firmware_label("firmware_status_label", _INSTALL_HELP)` e desabilita botões `firmware_check_btn`, `firmware_browse_btn`, `firmware_apply_btn`.

### Frente comum

15. README.md ganha 2 linhas curtas na seção Instalação:
    - GNOME: o `install.sh` habilita a extension `ubuntu-appindicators@ubuntu.com` automaticamente (com confirmação interativa); flag `--yes` automatiza.
    - Firmware (opcional): instalar `dualsensectl` via Flathub para habilitar a aba.
16. Gates canônicos verdes:
    - `.venv/bin/pytest tests/unit -v --no-header -q`
    - `.venv/bin/ruff check src/ tests/`
    - `.venv/bin/mypy src/hefesto_dualsense4unix`
    - `./scripts/check_anonymity.sh`
17. `install.sh -h` (help) atualizado com as flags novas (se houver) e descrição compatível.

## Invariantes a preservar

- **PT-BR obrigatório** em mensagens novas, comentários e logs (`[CORE] Identidade do projeto`).
- **Acentuação periférica** (`á é í ó ú â ê ô ã õ à ç`) em toda string adicionada — não aceitar `funcao`, `validacao`, `instalacao`, `extensao`, `aplicacao`, `informacao`, `configuracao`.
- **Zero emojis gráficos** (Emoji_Presentation block) em mensagens. Glyphs Unicode de estado permitidos (não aplicável aqui — mensagens são texto puro).
- **Idempotência do install.sh** (linha 15): reexecutar sem efeitos colaterais. A detecção da extension deve ser idempotente — se já habilitada, pula sem prompt.
- **`set -euo pipefail`** (install.sh:17): comandos novos não podem propagar exit code não-zero acidental. Usar `|| true` em probes e `if cmd; then` para fluxo de decisão.
- **Helper `ask_yn`** (install.sh:61-72): reusar; não criar prompt paralelo.
- **Helper `run_apt`** (install.sh:74-84): NÃO usar para `flatpak install` — criar helper `run_flatpak` análogo se necessário, ou inline com supressão de stdout idêntica.
- **Padrão `step "N/M" "descrição"`** (install.sh:56): ajustar o denominador `M` se passos forem adicionados (ex: passar de 7/7 para 9/9).
- **`A-12` (BRIEF)**: GUI usa `--system-site-packages` para PyGObject — não tocar este arranjo.
- **Aba Firmware NÃO é silenciosa** (já validado em `firmware_actions.py:62-67`): `install_firmware_tab` checa `is_available()` e mostra `_INSTALL_HELP`. Manter contrato; só melhorar texto.

## Plano de implementação

### 1. install.sh — passo 8/N: extension AppIndicator (GNOME)

Inserir bloco entre passos atuais 7/7 e o "Pronto" final. Renumerar denominador de todos os `step "N/M"` de `/7` para `/9` (ou para o novo total).

```bash
# ---------------------------------------------------------------------------
# 8. Extension AppIndicator no GNOME (necessária pra ícone de bandeja)
# ---------------------------------------------------------------------------
step "8/9" "GNOME: extension AppIndicator (tray icon)"

_desktop="${XDG_CURRENT_DESKTOP:-}"
if [[ -z "${_desktop}" ]]; then
    printf '      ambiente headless (sem XDG_CURRENT_DESKTOP) — pulado\n'
elif [[ "${_desktop,,}" != *gnome* ]]; then
    printf '      DE %s renderiza Ayatana nativamente — sem ação\n' "${_desktop}"
elif ! command -v gnome-extensions >/dev/null 2>&1; then
    warn "gnome-extensions CLI ausente — habilite manualmente a extension AppIndicator depois"
else
    _ext_id="ubuntu-appindicators@ubuntu.com"
    if gnome-extensions list --enabled 2>/dev/null | grep -qx "${_ext_id}"; then
        printf '      já habilitada\n'
    elif ! gnome-extensions list 2>/dev/null | grep -qx "${_ext_id}"; then
        warn "extension ${_ext_id} não instalada — instale via GNOME Extensions (https://extensions.gnome.org)"
    else
        printf '      extension %s está instalada mas desabilitada\n' "${_ext_id}"
        printf '      sem ela o ícone do Hefesto não aparece na barra superior do GNOME\n'
        ask_yn "habilitar agora?" "${AUTO_YES}"
        if [[ "${REPLY,,}" =~ ^y ]]; then
            if gnome-extensions enable "${_ext_id}" 2>/dev/null; then
                printf '      habilitada\n'
            else
                warn "falha ao habilitar — execute 'gnome-extensions enable ${_ext_id}' manualmente"
            fi
        else
            printf '      pulado a pedido — habilite depois com: gnome-extensions enable %s\n' "${_ext_id}"
        fi
    fi
fi
```

### 2. install.sh — passo 9/N: dualsensectl (Firmware opcional)

```bash
# ---------------------------------------------------------------------------
# 9. dualsensectl (opcional — aba Firmware)
# ---------------------------------------------------------------------------
step "9/9" "dualsensectl (opcional — aba Firmware)"

if command -v dualsensectl >/dev/null 2>&1; then
    printf '      já presente em %s\n' "$(command -v dualsensectl)"
elif ! command -v flatpak >/dev/null 2>&1; then
    printf '      ausente — para habilitar a aba Firmware, instale manualmente:\n'
    printf '        https://github.com/nowrep/dualsensectl  (build via cmake)\n'
    printf '      a aba Firmware ficará desabilitada até instalar (não bloqueia uso geral)\n'
elif ! flatpak --user remotes 2>/dev/null | awk '{print $1}' | grep -qx "flathub" \
   && ! flatpak remotes 2>/dev/null | awk '{print $1}' | grep -qx "flathub"; then
    printf '      flatpak presente mas remote flathub ausente. Configure com:\n'
    printf '        flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo\n'
    printf '      e rode novamente este install.sh\n'
else
    printf '      dualsensectl ausente — necessário para a aba Firmware da GUI (opcional)\n'
    printf '      Flathub: com.github.nowrep.dualsensectl\n'
    ask_yn "instalar agora via flatpak?" "${AUTO_YES}" "n"
    if [[ "${REPLY,,}" =~ ^y ]]; then
        if flatpak install --user -y flathub com.github.nowrep.dualsensectl >/dev/null 2>&1; then
            printf '      instalado via flatpak\n'
            printf '      lembrete: para que a GUI encontre o binário, exponha um wrapper:\n'
            printf '        echo -e "#!/bin/sh\\nflatpak run com.github.nowrep.dualsensectl \\"\\$@\\"" \\\n'
            printf '          | sudo tee /usr/local/bin/dualsensectl >/dev/null && sudo chmod +x /usr/local/bin/dualsensectl\n'
        else
            warn "flatpak install falhou — instale manualmente: flatpak install flathub com.github.nowrep.dualsensectl"
        fi
    else
        printf '      pulado a pedido — aba Firmware ficará desabilitada\n'
    fi
fi
```

**Nota crítica para o executor:** o flatpak instala o binário em namespace isolado; `dualsensectl` não fica no PATH automaticamente. O wrapper `/usr/local/bin/dualsensectl` é instrução para o usuário (não automatizar — exige sudo separado e altera /usr/local). Se preferir não orientar wrapper, registrar como sprint nova `FEAT-FIRMWARE-FLATPAK-WRAPPER-01` (protocolo anti-débito 9.7).

### 3. install.sh — renumerar passos

Buscar `step "N/7"` e ajustar para `step "N/9"` em todas as ocorrências. Linhas alvo: 91, 117, 173, 214, 271, 278, 309. Verificar com `grep -n 'step "[0-9]*/7"' install.sh` antes de editar.

### 4. firmware_actions.py — `_INSTALL_HELP` reescrito

Substituir linhas 31-34:

```python
_INSTALL_HELP = (
    "dualsensectl não encontrado. Instale via Flathub "
    "(https://flathub.org/apps/com.github.nowrep.dualsensectl) "
    "ou compile do fonte (https://github.com/nowrep/dualsensectl) "
    "e reabra a aba."
)
```

Mantém PT-BR. Acentuação periférica respeitada.

### 5. tests/unit/test_firmware_actions_missing_binary.py

Teste dirigido com `MagicMock` para `FirmwareUpdater.is_available() -> False`. Valida que `install_firmware_tab`:
- chama `_set_firmware_label("firmware_status_label", _INSTALL_HELP)`;
- desabilita `firmware_check_btn`, `firmware_browse_btn`, `firmware_apply_btn` (`set_sensitive(False)`).

Estrutura esperada (esqueleto):

```python
"""Testa o comportamento da aba Firmware quando dualsensectl está ausente."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# Skip cedo se PyGObject ausente (A-12).
gi = pytest.importorskip("gi")
gi.require_version("Gtk", "3.0")

from hefesto_dualsense4unix.app.actions.firmware_actions import (
    FirmwareActionsMixin,
    _INSTALL_HELP,
)


class _Host(FirmwareActionsMixin):
    def __init__(self) -> None:
        self._widgets: dict[str, MagicMock] = {}

    def _get(self, widget_id: str) -> MagicMock:
        if widget_id not in self._widgets:
            self._widgets[widget_id] = MagicMock()
        return self._widgets[widget_id]


@patch("hefesto_dualsense4unix.app.actions.firmware_actions.FirmwareUpdater")
def test_install_firmware_tab_dualsensectl_ausente(mock_updater_cls):
    fake_updater = MagicMock()
    fake_updater.is_available.return_value = False
    mock_updater_cls.return_value = fake_updater

    host = _Host()
    host.install_firmware_tab()

    status_widget = host._widgets["firmware_status_label"]
    status_widget.set_text.assert_any_call(_INSTALL_HELP)

    for btn in ("firmware_check_btn", "firmware_browse_btn", "firmware_apply_btn"):
        host._widgets[btn].set_sensitive.assert_any_call(False)
```

Validar local antes de commitar: `.venv/bin/pytest tests/unit/test_firmware_actions_missing_binary.py -v`.

### 6. README.md — ajustes mínimos

Localizar linha 235 (`AppIndicator and KStatusNotifierItem Support` na lista de Recomendados) e converter para parágrafo explicativo curto pós-tabela (ou inserir nota próxima a `./install.sh`):

```markdown
> **GNOME 42+:** o `install.sh` detecta a extension `ubuntu-appindicators@ubuntu.com`
> e oferece habilitação automática (sem ela o ícone de bandeja não aparece). Em outras
> DEs (KDE, COSMIC, XFCE, Cinnamon, MATE) o tray Ayatana funciona nativamente.

> **Aba Firmware (opcional):** depende do binário externo `dualsensectl`. O `install.sh`
> oferece instalação via Flathub (`com.github.nowrep.dualsensectl`). A GUI funciona normalmente
> com a aba desabilitada se o binário ausente.
```

Localização exata: após a seção Instalação via fonte, antes de `### Requisitos`. Confirmar com `grep -n "### Requisitos" README.md` antes de editar.

### 7. install.sh -h (help)

O `-h` (linhas 44-47) usa `sed` para imprimir o cabeçalho até a linha 15. Atualizar o cabeçalho de comentário (linhas 4-12) se nova flag for adicionada. Decisão default: **não adicionar flag nova** — `--yes` já cobre os 2 prompts novos. Apenas revisar consistência do cabeçalho.

## Aritmética estimada

- `install.sh`: 360L atuais → +~70L (passos 8 e 9 + renumeração triviais), projeção 430L. Sem teto rígido (script bash, não código Python).
- `README.md`: 444L → +~10L, projeção 454L.
- `src/hefesto_dualsense4unix/app/actions/firmware_actions.py`: 316L → ±2L (string trocada, sem nova função). Limite de 800L (CORE Padrões de código) preservado com folga.
- `tests/unit/test_firmware_actions_missing_binary.py`: arquivo novo, ~50L.

Sem meta numérica de redução — cluster é aditivo.

## Testes

- **Adicionar:** `tests/unit/test_firmware_actions_missing_binary.py` — 1 teste mínimo (cenário ausente). Possível 2º teste valida `is_available()=True` deixando botões habilitados.
- **Modificar:** nenhum.
- **Baseline esperado:** suite atual passa em 998 testes (registrado em rodapé do BRIEF, linha 262). Após cluster: 999-1000 passed.
- **Smoke:** `install.sh` é bash; pytest não cobre. Validação runtime obrigatória manual (ver Proof-of-work).

## Proof-of-work esperado

```bash
# Ambiente
bash scripts/dev-setup.sh

# Confirmar hipótese (lição L-21-2)
git stash --include-untracked  # opcional, se working tree sujo
echo $XDG_CURRENT_DESKTOP      # esperado: contém "GNOME"
gnome-extensions list | grep ubuntu-appindicators@ubuntu.com  # confirma instalada
gnome-extensions list --enabled | grep ubuntu-appindicators@ubuntu.com  # estado atual

# Frente A — rodar com extension desabilitada
gnome-extensions disable ubuntu-appindicators@ubuntu.com
./install.sh --yes 2>&1 | tee /tmp/install_run.log
grep -iE "appindicator|tray" /tmp/install_run.log
# esperado: "extension ubuntu-appindicators@ubuntu.com está instalada mas desabilitada"
#           "habilitada"
gnome-extensions list --enabled | grep ubuntu-appindicators@ubuntu.com
# esperado: bate (re-habilitada)

# Idempotência
./install.sh --yes 2>&1 | grep -i appindicator
# esperado: "já habilitada"

# Frente B — rodar com dualsensectl ausente
which dualsensectl  # esperado: nada
flatpak remotes | awk '{print $1}' | grep flathub  # confirmar remote
./install.sh --yes 2>&1 | tee /tmp/install_run2.log
grep -iE "dualsensectl|firmware|flatpak" /tmp/install_run2.log
# esperado: "dualsensectl ausente — necessário para a aba Firmware"
#           se --yes: "instalado via flatpak" OU "flatpak install falhou"
echo $?  # esperado: 0 (install não bloqueia)

# Suite de testes
.venv/bin/pytest tests/unit -v --no-header -q
# esperado: 999+ passed (998 baseline + 1-2 novos)

# Lints + types
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/hefesto_dualsense4unix
./scripts/check_anonymity.sh

# Acentuação periférica em arquivos modificados
for f in install.sh README.md src/hefesto_dualsense4unix/app/actions/firmware_actions.py \
         tests/unit/test_firmware_actions_missing_binary.py; do
    grep -nE "(funcao|validacao|instalacao|extensao|aplicacao|informacao|configuracao|descricao|comunicacao)" "$f" \
        && echo "FALHA acentuação em $f" || echo "OK $f"
done

# Validação visual (NÃO obrigatória neste cluster — sem mudança de UI GTK)
# Aba Firmware com dualsensectl ausente continua mostrando _INSTALL_HELP — texto novo:
.venv/bin/python -m hefesto_dualsense4unix.app.main &
sleep 3
WID=$(xdotool search --name "Hefesto - Dualsense4Unix v" | head -1)
TS=$(date +%Y%m%dT%H%M%S)
xdotool windowactivate "$WID" && sleep 0.4
# clicar na aba Firmware via xdotool (ou capturar imediatamente se default)
import -window "$WID" "/tmp/hefesto_gui_firmware_${TS}.png"
sha256sum "/tmp/hefesto_gui_firmware_${TS}.png"
# verificar manualmente: "Flathub" e URL aparecem no firmware_status_label

# Hipótese verificada (lição L-21-4): identificadores citados existem
rg -n 'BINARY = "dualsensectl"' src/hefesto_dualsense4unix/integrations/firmware_updater.py
rg -n '_INSTALL_HELP' src/hefesto_dualsense4unix/app/actions/firmware_actions.py
rg -n 'ask_yn' install.sh
rg -n 'XDG_CURRENT_DESKTOP' install.sh   # esperado: vazio ANTES do fix (a inserir)
```

## Riscos e não-objetivos

### Não-objetivos (registrar como sprint nova se virar dor)

- **Wrapper `/usr/local/bin/dualsensectl` automático para flatpak**: exige sudo separado, altera /usr/local. Caso usuário relate "instalei via flatpak mas a aba Firmware ainda diz ausente", abrir `FEAT-FIRMWARE-FLATPAK-WRAPPER-01`.
- **Reverter habilitação da extension no `uninstall.sh`**: a extension `ubuntu-appindicators@ubuntu.com` é compartilhada (Slack, Discord, Steam dependem). Desabilitar no uninstall causaria mais dor.
- **Detectar Wayland puro vs X11**: tray Ayatana funciona em ambos via XWayland; sem ação especial.
- **CI cobertura para o passo 8/9 do install.sh**: rodar `gnome-extensions` em headless CI exige stack X virtual + GNOME Shell — fora de escopo. Validação manual no PC do usuário.
- **Detectar Flatpak System remote (não-user)**: cluster cobre `--user` por consistência com não exigir sudo extra.

### Riscos

- **L-21-7**: premissa "Pop!_OS 22.04 tem `gnome-extensions` CLI" foi confirmada empiricamente (BRIEF "Hardware no PC do usuário"). Para Ubuntu vanilla 22.04 idem. Distros minoritárias (Fedora GNOME) também trazem CLI por default. Mitigação: passo 8 cai em `warn` quando CLI ausente; nunca falha o install.
- **Renumeração `step "N/7" → "N/9"`**: erro tipográfico ao não atualizar todas as 7 ocorrências causa output inconsistente mas não bloqueia execução. Validador deve verificar com `grep -c 'step "[0-9]*/9"' install.sh` que retorna 9.
- **`gnome-extensions enable` retorna 0 mesmo quando extension não recarrega visualmente até logout/login** (limitação conhecida do GNOME Shell em alguns casos). Aceitável — a sessão atual pode precisar de log out/in se extension foi habilitada pela primeira vez. Documentar na mensagem.
- **`firmware_actions.py` está cobrindo cenário sem PyGObject** — o `pytest.importorskip("gi")` no novo teste evita falha em CI sem GTK.

## Wire-up checklist (não aplicável)

Não é sprint de subsystem novo do Daemon (`A-07` não acionada). Não há campo novo em `*Config` (`A-06` não acionada).

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Hefesto-Dualsense4Unix/VALIDATOR_BRIEF.md`
- Precedente histórico:
  - `INFRA-VENV-PYGOBJECT-01.md` — padrão "duas camadas: install.sh detecta + README documenta + BRIEF arquiva".
  - `BUG-MULTI-INSTANCE-01` (rodapé BRIEF 2026-04-22) — passos 6/7 do install.sh viraram opt-in com prompt; mesmo padrão `ask_yn`.
  - `A-12` no BRIEF — PyGObject opt-in com fallback gracioso. Cluster reusa a filosofia para extension AppIndicator e dualsensectl.

---

*"Detecção sem fix gracioso é só barulho. Fix gracioso sem proof-of-work runtime é só fé."*
