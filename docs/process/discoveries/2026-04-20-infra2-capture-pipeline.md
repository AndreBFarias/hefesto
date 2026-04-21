# 2026-04-20 — INFRA.2: pipeline de captura HID estabelecido, fixture inicial idle

**Contexto:** implementação de INFRA.2 (captures HID determinísticos) logo após HOTFIX-2 resolver o conflito com `hid_playstation`. Primeira sprint runtime-real que produziu fixture no repo.
**Status:** Resolvida (pipeline); `INFRA.2-followup` #54 abre regravação com interação.
**Issues relacionadas:** #29 (INFRA.2, closed), #54 (follow-up), V2-13, V3-8.

## Sintoma

Após gravar com o DualSense USB conectado durante 8 e depois 15 segundos pedindo explicitamente que L2/R2 fossem pressionados:

```
OK: 240 samples gravados em tests/fixtures/hid_capture_usb.bin (1.2 KB)
  +  0.0s | remaining  8.0s | L2=  0 R2=  0 btn=[]
  +  1.0s | remaining  7.0s | L2=  0 R2=  0 btn=[]
  ...
  +  7.0s | remaining  1.0s | L2=  0 R2=  0 btn=[]
```

Todos os 240 (depois 450) samples idle. O pipeline não falhou, apenas não havia input do usuário durante a gravação.

## Hipóteses

1. **EvdevReader não está ativo no backend do gravador** — descartada: log mostrou "controle conectado via usb + evdev" e o reader foi criado.
2. **Kernel capturou os reports mesmo após HOTFIX-2** — descartada: `EvdevReader` lê de `/dev/input/event24`, que é onde o kernel publica os eventos decodificados.
3. **Usuário não interagiu durante a janela de gravação** — CONFIRMADA. Em ambiente multitarefa (responder chat + operar controle), a janela de 15s passou sem input.

## Causa

Operacional, não técnica. A UX do `record_hid_capture.py` avisa "AGORA" no stdout mas o usuário estava focado em outra tela. Pipeline correto, sample taxa correta (30Hz), `EvdevReader.snapshot()` chamado, buttons sempre vazios porque nenhum botão foi pressionado fisicamente.

Confirmado por teste paralelo com `jstest /dev/input/js0` em outro terminal mais tarde: botões e triggers aparecem normalmente.

## Solução

Aceitar a capture idle como **baseline do formato**. Ela ainda:
- Valida que a serialização JSONL + gzip funciona (`test_fake_controller_capture.py::test_from_capture_real_do_repo_se_existir`).
- Exercita o gate de 5MB (1.2 KB ficou 99.99% abaixo).
- Valida o header `version=1, transport=usb`.
- Permite que CI rode testes que chamam `FakeController.from_capture()` com o arquivo real.

Follow-up `INFRA.2-followup` #54 com passos claros pra quando o usuário puder parar e gravar com operação ativa do controle.

Alternativa considerada e rejeitada: contador regressivo interativo no script. Adicionaria dependência de `prompt_toolkit` ou readline. Prompt em stdout + `sleep 3` no shell antes já é suficiente; a falha foi de atenção, não de UX catastrófica.

## Lições

1. **Runtime-real com humano tem variável de engajamento.** Um smoke de 15s exige que o humano saiba que é AGORA que ele precisa mexer. Pra escalar, ou o teste é automatizável (sintético) ou tem etapa síncrona (beep, confirm antes de começar).
2. **Fixture idle ainda tem valor.** Ela prova formato, carrega no CI, e exercita o path. Não substitui fixture com input, mas não é inútil.
3. **Separar "pipeline valida" de "fixture valida"** na DoD. Pipeline foi validado. Fixture com input fica em follow-up.
4. **Expor `_idx` e `_states` do FakeController** (atualmente privados mas usados em test) é aceitável pra testes — evita API pública inchada.

## Impacto cross-sprint

- Sprints destravadas: CI agora tem `tests/fixtures/hid_capture_usb.bin` pra testes de replay. W1.3 smoke pode ler fixture real em vez de só synthetic states.
- Sprints arquivadas: nenhuma.
- Pendente: `hid_capture_bt.bin` (precisa pair via Bluetooth primeiro).
- ADRs afetadas: ADR-008 ganha referência ao formato JSONL gzip.
- Regra V3-8 (YAML descritor determinístico): segue válida mas sem uso imediato — hoje o record é livre-forma; quando INFRA.2-followup for executada, o YAML pode virar script de assistência ao usuário (não determinístico por bytes, mas determinístico por sequência de ações).
