# YYYY-MM-DD — Título curto da descoberta

**Contexto:** sprint, PR ou workflow onde o problema apareceu.
**Status:** Aberta / Em investigação / Resolvida / Arquivada (superada).
**Issues relacionadas:** #N, #M.

## Sintoma

O que foi observado. Prefira log literal ou diff, não paráfrase. Exemplo:

```
$ comando executado
  saída inesperada
```

## Hipóteses

Liste cada uma com resultado do teste:

1. **Hipótese A** — descartada porque X (prova: `comando Y` retornou Z).
2. **Hipótese B** — parcialmente válida mas não explicava W.
3. **Hipótese C** — confirmada (ver "Causa").

## Causa

Descrição técnica do mecanismo. Inclua referência ao código-fonte externo (e.g. linha do pydualsense, seção do man page) quando for questão de interface de terceiros.

## Solução

Mudança aplicada (link pro commit/PR quando possível). Se foi contorno temporário, anotar o que fica pendente.

## Lições

Regra que sai daqui pra acelerar a próxima jornada:
- "Sempre testar X antes de assumir Y."
- "Atributo W do pacote Z é bool; o analog fica em W_value."

## Impacto cross-sprint

- Sprints destravadas: ...
- Sprints bloqueadas: ...
- ADRs afetadas: ...
- Decisões V2/V3 que precisam revisão: ...
