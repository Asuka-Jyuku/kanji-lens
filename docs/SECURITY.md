# Segurança

O KanjiLens fica **aberto a qualquer um na rede local, sem login** ([ADR 0007](adr/0007-local-execution-over-the-lan.md)). Não há conta nem dado pessoal. O que se protege é o servidor (memória, CPU, o processo de inferência) e os desenhos dos alunos.

## O que fica exposto

| Onde | Porta | Escuta em | Quem chega |
|---|---|---|---|
| Desenvolvimento: `ng serve` (página e proxy de `/api`) | 4200 | `0.0.0.0` só para testar no celular; senão, `localhost` | a rede local |
| Desenvolvimento: API (Uvicorn) | 8000 | `127.0.0.1` | só a própria máquina |
| Produção (notebook da escola) | uma só, a definir na [#62](https://github.com/Asuka-Jyuku/kanji-lens/issues/62) | `0.0.0.0` | a rede da escola |

- **Firewall:** só a porta em uso, só para a sub-rede local. A 8000 nunca precisa abrir.
- **Sem CORS:** a página chama `/api` na mesma origem (pelo proxy no desenvolvimento, pelo build estático em produção). Se um dia forem origens diferentes, o CORS libera só a do frontend, nunca `*`.
- **O `ng serve` é só de desenvolvimento** e não vai para o notebook da escola.

## Limites de entrada

Conferidos na API antes de qualquer coisa chegar à fila.

| Limite | Valor | Onde | Resposta |
|---|---|---|---|
| Corpo | 1 MiB, antes de qualquer parsing (inclusive *chunked*) | `BodySizeLimitMiddleware` | `413 drawing_too_large` |
| Traços | 40 | schema e domínio | `413 drawing_too_large` |
| Pontos por traço | 1.000 | schema e domínio | `413 drawing_too_large` |
| Pontos no total | 10.000 | domínio | `413 drawing_too_large` |
| Formato (canvas de 64 a 4.096 px, pontos até 10% fora, `t` que não volta) | ADR 0016 | schema e domínio | `400 invalid_drawing` |
| Campo desconhecido ou corpo que não é JSON | — | schema (`extra="forbid"`) | `400 invalid_request` |

O frontend aplica os mesmos limites enquanto o aluno desenha, para avisar na hora. Quem garante é a API.

## Fila e processamento

- **Fila de até 16 jobs** ([ADR 0019](adr/0019-in-memory-job-queue-with-one-inference-process.md)). Cheia, a API responde `503 queue_full` com `Retry-After: 5`, e a tela só reativa "Reconhecer" depois disso.
- **Um processo de inferência, um job por vez.** Se ele cair, o job falha (`inference_failed`) e o processo é recriado.
- **Um job por vez por aparelho:** "Reconhecer" fica desligado até o job terminar.
- **SSE:** uma conexão por job, só até o estado final, com keep-alive a cada 15 s ([ADR 0020](adr/0020-result-notification-by-server-sent-events.md)). Se falhar, a tela consulta o `GET` a cada 1 s e desiste depois de 60 s.

## Dados dos alunos

- **Os desenhos não são guardados** depois que o job expira (5 minutos depois do fim). Guardar desenhos de alunos, mesmo para teste, precisa de ADR antes.
- **Nada de desenho no log.** O log do Uvicorn registra rota e status, não o corpo.
- **A exportação de desenhos** (#66) só existe no build de desenvolvimento.

## Nenhuma saída de rede

O app em execução não chama nada fora da máquina: nem telemetria, nem CDN (as fontes japonesas são do sistema), nem download de modelo. Chamada nova para fora precisa de ADR. Os scripts de `ml/` que baixam o ETL e o KanjiVG rodam à parte, antes, e conferem o checksum.

## Ao mudar algo daqui

Porta, CORS, limite de entrada ou fronteira de rede nova mudam este documento no mesmo PR, com ADR se mudar a exposição.
