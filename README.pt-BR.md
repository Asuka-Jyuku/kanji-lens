# KanjiLens

**Reconhecimento de kanjis manuscritos com Deep Learning e Visão Computacional.**

[English](README.md) · [Arquitetura](docs/ARCHITECTURE.md) · [Decisões (ADRs)](docs/adr/README.md) · [Como contribuir](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

> **Status:** fase inicial. A arquitetura, as ferramentas e o CI estão definidos, e as estruturas de `ml/`, `backend/` e `frontend/` existem. O código do produto começa pelo backend.

---

## Visão geral

O KanjiLens é uma aplicação web na qual você desenha um kanji em um canvas e recebe uma lista dos caracteres mais prováveis, ordenada por confiança. Antes de reconhecer, você escolhe se a ordem dos traços deve importar.

O objetivo não é acertar o caractere exato toda vez. É apresentar os **principais candidatos ordenados por confiança**, para que você identifique qual pretendia escrever.

O reconhecimento usa uma CNN 2D compacta treinada em PyTorch, que não depende da ordem dos traços. Quando a ordem importa, o KanjiLens também confere a ordem e a direção dos seus traços contra a referência do KanjiVG e diz quais traços estão fora de ordem. Todo o sistema roda em uma única máquina na rede local (o notebook da escola, com inferência só na CPU): o acesso é feito pelo celular ou pelo computador via Wi-Fi, sem hospedagem em nuvem nem domínio público.

```text
┌──────────────────────────────┐
│          KanjiLens           │
│   Ordem dos traços:          │
│   [ importa | não importa ]  │
│   ┌──────────────────────┐   │
│   │                      │   │
│   │          日          │   │
│   │                      │   │
│   └──────────────────────┘   │
│                              │
│   [Limpar]   [Reconhecer]    │
│                              │
│   Previsões                  │
│   日  81%                    │
│   目  12%                    │
│   白   4%                    │
└──────────────────────────────┘
```

## Como funciona

1. Você escolhe se a ordem dos traços importa e desenha o kanji no canvas (mouse ou touch).
2. O frontend envia os traços (cada um uma lista de pontos, na ordem do desenho) e o modo escolhido para a API.
3. A API gera um `job_id`, coloca a tarefa na fila e responde na hora. A requisição HTTP não fica aberta enquanto o modelo executa.
4. O worker de inferência consome a tarefa e executa o modelo; no modo com ordem, também confere os traços contra a referência do KanjiVG. O modelo e as referências são carregados uma vez, e não a cada requisição.
5. O backend avisa o frontend de cada mudança de estado do job por SSE (Server-Sent Events), com polling como reserva.
6. O frontend exibe as previsões top-K com a confiança de cada uma e, no modo com ordem, quais traços estão fora de ordem. Tocar num candidato abre o verbete num dicionário externo (o Takoboto por padrão; o usuário pode escolher outro).

```text
 Celular / Desktop
       │
       ▼
 Angular frontend ──REST──▶ FastAPI ──▶ Fila ──▶ Worker ──▶ CNN 2D
       ▲                            (+ avaliação da ordem contra o KanjiVG)
       │                                                 │
       └──────────── SSE ─────────── ◀── Resultados ◀────┘
```

## Stack

| Camada | Tecnologias |
|---|---|
| Frontend | Angular, TypeScript, HTML Canvas API |
| Backend | Python, FastAPI, REST, SSE |
| Machine Learning | PyTorch (treino), CNN 2D; avaliação da ordem contra o KanjiVG; runtime de inferência em CPU escolhido por benchmark (PyTorch / OpenVINO / ONNX Runtime) |
| Fila | `asyncio.Queue` limitada, em memória, e um processo de inferência (sem Redis no notebook Windows) |
| Execução | Notebook da escola (Dell Inspiron 3501, i7-1165G7, 16 GB, Windows), direto, sem Docker, acessado pela LAN |

## API

| Método | Endpoint | Responsabilidade |
|---|---|---|
| `POST` | `/api/recognitions` | Enviar os traços e o modo (`ordered` / `unordered`) para reconhecimento |
| `GET` | `/api/recognitions/{id}` | Consultar status e resultado de uma tarefa (reserva do SSE) |
| `GET` | `/api/recognitions/{id}/events` | Receber as mudanças de estado da tarefa por SSE |
| `GET` | `/api/health` | Verificar disponibilidade do backend |

Hoje o `POST` recebe o desenho e põe o job na fila, e o processo de inferência o processa, ainda com um reconhecedor falso no lugar do modelo ([#48](https://github.com/Asuka-Jyuku/kanji-lens/issues/48)). O resultado sai pelo `GET` e pelo SSE, no mesmo formato. Os erros têm sempre um código estável ([ARCHITECTURE.md, seção 5.3](docs/ARCHITECTURE.md#53-erros)).

Exemplo de tarefa concluída:

```json
{
  "job_id": "abc123",
  "status": "completed",
  "stroke_order_mode": "unordered",
  "predictions": [
    { "kanji": "日", "confidence": 0.81 },
    { "kanji": "目", "confidence": 0.12 },
    { "kanji": "白", "confidence": 0.04 }
  ]
}
```

## Estrutura do repositório (planejada)

Clean Architecture com portas e adaptadores, em camadas ([ADR 0004](docs/adr/0004-clean-and-hexagonal-architecture.md)), em um único repositório ([ADR 0002](docs/adr/0002-monorepo-for-frontend-backend-and-ml.md)).

```text
kanji-lens/
├── frontend/                # App Angular, em camadas
│   └── src/app/
│       ├── domain/          # Modelos e regras puras
│       ├── application/     # Casos de uso e portas
│       ├── infrastructure/  # Adaptadores HTTP e SSE
│       └── presentation/    # Canvas e tela de resultados
├── backend/                 # FastAPI, portas e adaptadores
│   └── src/kanjilens/
│       ├── domain/          # RecognitionJob, Prediction, JobStatus, Drawing, StrokeOrderMode
│       ├── application/     # Casos de uso e portas
│       ├── adapters/        # Inbound (HTTP, SSE, consumidor da fila), outbound (reconhecedor, avaliador da ordem, fila, armazenamento)
│       └── bootstrap/       # Composition root
├── ml/
│   ├── src/kanjilens_ml/    # Pré-processamento compartilhado, modelos, treino, avaliação, avaliação da ordem
│   ├── configs/             # Configurações de treino versionadas
│   ├── notebooks/           # Só exploração
│   ├── datasets/            # Fora do git
│   └── artifacts/           # Pesos treinados, fora do git
└── docs/
```

## Roadmap

- [ ] **Machine Learning:** dataset escolhido (ETL9G, com os 1.026 kanji escolares na primeira versão; [ADR 0021](docs/adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md)), pré-processamento compartilhado, treinar a CNN 2D, avaliação da ordem contra o KanjiVG, avaliar (Top-1/Top-5 e acerto da avaliação da ordem), inferência top-K e, depois, medir no notebook da escola
- [ ] **Backend:** projeto FastAPI, endpoint de reconhecimento, processamento assíncrono, integração com o modelo, notificação
- [ ] **Frontend:** app Angular, escolha do modo (ordem dos traços), canvas responsivo com mouse e touch que captura os traços, tela de resultados
- [ ] **Infraestrutura:** acesso pela LAN, CORS e firewall, frontend em build estático, teste com 3–5 alunos (10 clientes como estresse), consumo de CPU/memória/temperatura no notebook da escola

O checklist completo está em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#9-escopo-do-mvp).

## Decisões em aberto

| Tema | Opções | Direção atual |
|---|---|---|
| Runtime de inferência | PyTorch / OpenVINO / ONNX Runtime (CPU), FP32 ou INT8 | Definido por benchmark no notebook da escola |

## Como executar

O app ainda não reconhece kanjis. Para desenvolver, os comandos (instalar, testar, subir a API e o frontend) estão no [`CLAUDE.md`, "Comandos"](CLAUDE.md#comandos). O passo a passo para rodar no notebook da escola e na rede local vai para o `docs/RUNNING.md` quando a primeira versão rodar.

## O que o projeto explora

Visão Computacional, Deep Learning e CNN, correspondência entre traços para avaliar a ordem, processamento assíncrono, arquitetura orientada a eventos, REST API, comunicação em tempo real, concorrência e filas, e integração entre frontend e modelo de Machine Learning.

## Licença

O código-fonte está sob a [licença MIT](LICENSE).

A licença cobre só o código deste repositório. Os datasets usados no treino e os pesos treinados não fazem parte do repositório e não são cobertos por ela: cada dataset mantém os próprios termos, e pesos treinados com ele podem herdá-los. Os dados de referência do KanjiVG, usados na avaliação da ordem e distribuídos com a aplicação, mantêm a própria licença (CC BY-SA 3.0, © Ulrich Apel, [kanjivg.tagaini.net](https://kanjivg.tagaini.net)), com atribuição.

O modelo de reconhecimento é treinado com o ETL Character Database (ETL9G), de uso livre, mas que só pode ser obtido pelo [site oficial](https://etlcdb.db.aist.go.jp/): este repositório não tem nenhuma imagem dele, e cada máquina o baixa de lá ([ADR 0021](docs/adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md)). Referência: Electrotechnical Laboratory, Japanese Technical Committee for Optical Character Recognition, ETL Character Database, 1973-1984.
