# Análise do HEFESTO_PROJECT.md — Dúvidas e Falhas Detectadas



Sim, nenhuma menção a uso de ia, vc tá certo, vamos obviamente excluir esse arquivo depois de criada as sprints iniciais.  Então não estaremos quebrando as regras.
Decisões bloqueantes (2.1–2.3)

2.1 IController síncrona + executor. pydualsense é sync; backends futuros (cffi/Rust) provavelmente também. Acoplar a asyncio trava troca. Daemon chama via loop.run_in_executor.
2.2 AND entre campos, OR dentro de listas. Se window_class: ["a", "b"], bate qualquer. Se tem window_class E process_name, ambos precisam bater. Documentar no profiles/schema.py com exemplo.
2.3 NDJSON puro, UTF-8, delimitador \n. JSON escapa newline dentro de strings como \n (não literal), então não há ambiguidade. Length-prefix é overkill aqui.

Lacunas (2.4–2.8)

2.4 Dois rate limits combinados: global de 2000 pkt/s no daemon + 1000 pkt/s por IP (não por tupla — cliente pode rotacionar porta de origem). Excedeu, drop com log warn de 1x/s.
2.5 W6.3 sem HidHide. Esconder HID real vira W9 exploratória. W6.3 fica só criando o uinput virtual. Usuário escolhe no Steam qual controlador usar. Aceitar dualidade temporária.
2.6 Adicionar VID/PID do Edge (054c:0df2) no udev desde W0.1. Uma linha, zero risco.
2.7 Stubs de todas ADRs (001–008) no W0.1. Título + contexto (3 linhas) + decisão (1 linha). Detalhe conforme sprint. Stub vazio é melhor que ADR esquecida.
2.8 TUI mostra tela "daemon offline" com botão [Iniciar daemon] que invoca systemctl --user start hefesto. Não sobe daemon autônomo (fere arquitetura). Não aborta (hostil).

Riscos operacionais (3.1–3.6)

3.1 Adicionar libhidapi-hidraw0 ao bootstrap + CI + README. Runtime, não dev. Falta disso = ImportError obscuro pro usuário final.
3.2 install_udev.sh também instala modules-load.d/hefesto.conf com uinput + udev rule pra /dev/uinput grupo hefesto. Documenta que W6.3 requer reboot ou modprobe manual.
3.3 NÃO adicionar usuário ao grupo input. Criar udev rule seletiva por VID/PID pra /dev/input/by-id/*playstation*. Hotkey via teclado comum fica como --unsafe-keyboard-hotkeys opcional, exigindo consentimento explícito. Hotkey via botões do controle é default (passa pelo daemon, não precisa de input group).
3.4 Manter graphical-session.target como default + criar hefesto-headless.service com default.target documentada pra Big Picture/SSH. Usuário escolhe no install.
3.5 Detectar AppIndicator em runtime + log warning + README quickstart lista extensão GNOME requerida. Silêncio não é opção.
3.6 FakeController em tests/fixtures/ desde W1.1. HID captures reais gravados uma vez, replayed em CI. DoDs que exigem device físico viram smoke tests manuais em CHECKLIST_MANUAL.md, não bloqueiam CI.

Design (4.1–4.5)

4.1 platformdirs. Concordo. Zero motivo pra reinventar XDG.
4.2 filelock. Concordo. MIT, testado, cross-platform de graça.
4.3 Schema UDP posicional v1 (compat DSX) validado com pydantic discriminator. Schema v2 nomeado fica pra W9+ quando valer quebrar compat.
4.4 PT-BR em tudo visível ao usuário. CLI help, TUI, erros, logs. Consistente com Luna e público-alvo.
4.5 Esqueleto da CLI adiantado pra W4.1 só pra hefesto daemon start/stop/install-service. Subcomandos de profile/test/led ficam em W5.3.

Menores (5.1–5.10)

5.1 Fixar hatchling>=1.20 no [build-system.requires].
5.2 Adicionar .gitattributes no W0.1: *.sh text eol=lf, *.rules text eol=lf, *.py text eol=lf.
5.3 Criar NOTICE no W0.1 atribuindo o .rules ao pydualsense.
5.4 Mover .desktop + ícone pra W5.4 (sprint do tray).
5.5 def main(): app() explícito em cli/app.py.
5.6 Criar docs/protocol/trigger-modes.md no W0.1 com tabela canônica (arity + ranges) extraída do README Paliverse + enum pydualsense. Pré-requisito de W2.1.
5.7 Ruff: exclude = ["tests/fixtures/**"].
5.8 Mypy overrides pra textual, typer, evdev, Xlib, pydualsense com ignore_missing_imports.
5.9 Abrir ADR-008 (BT vs USB polling): FakeController replay de ambos os modos, W1.3 testa ambos.
5.10 W4.3 rejeita payload com version != 1, log warn, drop.

