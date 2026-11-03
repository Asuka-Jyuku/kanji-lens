# 0001. Registrar decisões de arquitetura em ADRs

- **Status:** Aceita
- **Data:** 2026-11-03

## Contexto

O KanjiLens vai ser feito por vários desenvolvedores, com agentes do Claude Code trabalhando em paralelo. O primeiro documento de design ([ARCHITECTURE.md](../ARCHITECTURE.md)) já misturava temas decididos e em aberto numa tabela só, sem registro das alternativas nem dos trade-offs de cada escolha. Sem esse registro, uma mudança posterior pode desfazer uma decisão sem saber por que ela foi tomada, e um agente não tem como distinguir uma escolha deliberada de um acaso.

## Alternativas consideradas

- **Decisões só no ARCHITECTURE.md** — um lugar só para ler; mas ele descreve o estado atual, não o porquê, e o raciocínio se perde quando o estado muda.
- **Decisões nas issues e nas descrições dos PRs** — já estão escritas lá; mas são difíceis de achar depois e não são versionadas com o código.
- **ADRs no repositório** — um arquivo curto por decisão, versionado com o código, com um modelo que obriga a listar alternativas e consequências negativas; custa um pouco de escrita em toda mudança significativa.

## Decisão

Registramos cada decisão técnica significativa como uma ADR em `docs/adr/`, a partir do modelo `0000-template.md`, no mesmo PR da mudança. O ARCHITECTURE.md descreve o estado atual e aponta para as ADRs quando o assunto é o porquê.

## Consequências

- **Positivas:** o porquê sobrevive à troca de pessoas e às conversas resumidas; revisores e agentes conseguem conferir uma mudança contra as decisões Aceitas; as decisões em aberto têm um lugar claro para serem fechadas.
- **Negativas:** toda mudança significativa traz um arquivo a mais para escrever e revisar; o índice em `docs/adr/README.md` é mantido à mão; as ADRs retroativas (0002, 0003, 0005 a 0007) têm contexto *inferido*.
- **Na prática:** siga os critérios de [docs/adr/README.md](README.md) e os passos do `CLAUDE.md`, "Decisões de arquitetura (ADRs) — obrigatório". Nunca apague uma ADR: substitua.
