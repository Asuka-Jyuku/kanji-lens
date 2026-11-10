# Segurança

O KanjiLens fica **acessível a qualquer um na rede local, sem login** ([ADR 0007](adr/0007-local-execution-over-the-lan.md)). Não há conta, senha nem dado pessoal: o que se protege é o próprio servidor (memória, CPU, o processo de inferência) e os desenhos dos alunos. Este documento diz o que fica exposto, o que limita cada entrada e o que nunca sai da máquina. Muda junto com portas, CORS, limites de entrada e qualquer fronteira de rede nova (`CLAUDE.md`, "Documentos nascem com o assunto").

Nasceu com a [#58](https://github.com/Asuka-Jyuku/kanji-lens/issues/58), o primeiro PR em que a tela no celular chama a API pela rede local.

## O que fica exposto

| Onde | Porta | Escuta em | Quem chega |
|---|---|---|---|
| **Desenvolvimento:** `ng serve` (a página e o proxy de `/api`) | 4200 | `0.0.0.0` só para testar pelo celular; senão, `localhost` | a rede local |
| **Desenvolvimento:** a API (Uvicorn) | 8000 | `127.0.0.1` | só a própria máquina: o celular chega pelo proxy da porta 4200 |
| **Produção** (notebook da escola) | uma porta só, a definir na [#62](https://github.com/Asuka-Jyuku/kanji-lens/issues/62) | `0.0.0.0` | a rede local da escola |

- **Firewall:** libera na rede local só a porta em uso, e só da sub-rede local (no desenvolvimento, a 4200). A 8000 não precisa ser aberta, porque o celular nunca fala com ela direto.
- **Uma origem só, sem CORS.** A página chama a API por URL relativa (`/api`). No desenvolvimento, o proxy do `ng serve` (`frontend/proxy.conf.mjs`) encaminha `/api` para a API; em produção, o build estático e a API ficam na mesma origem (#62). Por isso a API **não liga o CORS**. Se um dia o frontend e a API ficarem em origens diferentes, o CORS libera só a origem do frontend, nunca `*`, e isso entra aqui no mesmo PR.
- **O `ng serve` é só de desenvolvimento.** Ele não é servidor de produção ([ADR 0011](adr/0011-school-notebook-as-server-with-cpu-first-inference.md)) e não vai para o notebook da escola.

## Limites de entrada

Conferidos no adapter HTTP antes de qualquer coisa chegar à fila. Um `POST` sem limite pode esgotar a memória ou travar o processo de inferência.

| Limite | Valor | Onde | Resposta |
|---|---|---|---|
| Corpo da requisição | 1 MiB, conferido **antes** de qualquer parsing, inclusive em envio *chunked* | `BodySizeLimitMiddleware` | `413 drawing_too_large` |
| Traços por desenho | 40 | schema e domínio ([ADR 0016](adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md)) | `413 drawing_too_large` |
| Pontos por traço | 1.000 | schema e domínio | `413 drawing_too_large` |
| Pontos no desenho | 10.000 | domínio | `413 drawing_too_large` |
| Formato (números, canvas de 64 a 4.096 px, pontos até 10% fora do canvas, `t` que não volta) | ADR 0016 | schema e domínio | `400 invalid_drawing` |
| Campo desconhecido ou corpo que não é JSON | — | schema (`extra="forbid"`) | `400 invalid_request` |

O frontend aplica os mesmos limites de traços e pontos enquanto o aluno desenha (`frontend/src/app/domain/drawing.ts`), para ele saber na hora; quem garante é a API.

## Fila e processamento

- **Fila limitada a 16 jobs** ([ADR 0019](adr/0019-in-memory-job-queue-with-one-inference-process.md)). Cheia, a API responde `503 queue_full` com `Retry-After` (5 s) em vez de aceitar mais trabalho. A tela mostra o tempo e só reativa "Reconhecer" depois dele.
- **Um processo de inferência**, um job por vez. Se ele cair, o job falha (`inference_failed`) e o processo é recriado.
- **Um job por vez por aparelho:** "Reconhecer" fica desligado enquanto o job anterior não termina (#58).
- **O SSE** mantém uma conexão aberta por job, só até o estado final, com keep-alive a cada 15 s ([ADR 0020](adr/0020-result-notification-by-server-sent-events.md)). Se ele falhar repetidamente, a tela consulta o `GET` uma vez por segundo, e desiste depois de 60 s sem resposta final.

## Dados dos alunos

- **Os desenhos não são guardados** depois que o resultado do job expira (5 minutos depois do fim; ADR 0019), a menos que uma ADR diga o contrário. Coletar desenhos de alunos (por exemplo, para testar a avaliação da ordem) precisa de ADR antes.
- **Nada de log com o desenho.** O log de acesso do Uvicorn registra rota e status, não o corpo.
- **A exportação de desenhos para os conjuntos de teste** (#66) existe só no build de desenvolvimento.

## Nenhuma saída de rede

O app em execução não chama nada fora da máquina: nem telemetria, nem CDN (as fontes japonesas são do sistema; [ADR 0009](adr/0009-portuguese-ui-first-then-japanese.md)), nem download de modelo em tempo de execução. Chamada nova para fora precisa de ADR. Os scripts de preparação do `ml/` (o dataset ETL e o KanjiVG) baixam dados, mas rodam à parte, antes, e conferem o checksum; não fazem parte do app em execução.

## Ao mudar algo daqui

Porta, CORS, limite de entrada ou fronteira de rede nova mudam este documento no mesmo PR, e a decisão vai para uma ADR se mudar a exposição (`CLAUDE.md`, "Decisões de arquitetura").
