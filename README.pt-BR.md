# KanjiLens

**Reconhecimento de kanjis manuscritos com Deep Learning e Visão Computacional.**

[English](README.md) · [Arquitetura](docs/ARCHITECTURE.md) · [Decisões (ADRs)](docs/adr/README.md) · [Como contribuir](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

> **Status:** fase inicial. A arquitetura está definida; a implementação ainda não começou.

---

## Visão geral

O KanjiLens é uma aplicação web na qual você desenha um kanji em um canvas e recebe uma lista dos caracteres mais prováveis, ordenada por confiança.

O objetivo não é acertar o caractere exato toda vez. É apresentar os **principais candidatos ordenados por confiança**, para que você identifique qual pretendia escrever.

O reconhecimento é feito por uma CNN (Convolutional Neural Network) em PyTorch. Todo o sistema roda em uma única máquina na rede local: o acesso é feito pelo celular ou pelo computador via Wi-Fi, sem hospedagem em nuvem nem domínio público.

```text
┌──────────────────────────────┐
│          KanjiLens           │
│                              │
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

1. Você desenha o kanji no canvas (mouse ou touch).
2. O frontend envia o desenho para a API.
3. A API gera um `job_id`, coloca a tarefa na fila e responde na hora. A requisição HTTP não fica aberta enquanto o modelo executa.
4. Um worker consome a tarefa e executa a inferência da CNN. O modelo é carregado uma vez por worker, e não a cada requisição.
5. O backend notifica o frontend com o resultado (SSE ou WebSocket).
6. O frontend exibe as previsões top-K com a confiança de cada uma.

```text
 Celular / Desktop
       │
       ▼
 Angular frontend ──REST──▶ FastAPI ──▶ Fila ──▶ Worker(s) ──▶ PyTorch CNN
       ▲                                                           │
       └──────────────── SSE / WebSocket ◀── Resultados ◀──────────┘
```

## Stack

| Camada | Tecnologias |
|---|---|
| Frontend | Angular, TypeScript, HTML Canvas API |
| Backend | Python, FastAPI, REST, SSE ou WebSocket |
| Machine Learning | PyTorch, NumPy, OpenCV (opcional) |
| Fila | `asyncio.Queue` no início; Redis + Celery/RQ se necessário |
| Execução | Máquina local, acessada pela LAN |

## API (planejada)

| Método | Endpoint | Responsabilidade |
|---|---|---|
| `POST` | `/api/recognitions` | Enviar um desenho para reconhecimento |
| `GET` | `/api/recognitions/{id}` | Consultar status e resultado de uma tarefa |
| `GET` | `/api/health` | Verificar disponibilidade do backend |

Exemplo de tarefa concluída:

```json
{
  "job_id": "abc123",
  "status": "completed",
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
│       ├── domain/          # RecognitionJob, Prediction, JobStatus
│       ├── application/     # Casos de uso e portas
│       ├── adapters/        # Inbound (HTTP, SSE, consumidor da fila), outbound (reconhecedor, fila, armazenamento)
│       └── bootstrap/       # Composition root
├── ml/
│   ├── src/kanjilens_ml/    # Pré-processamento compartilhado, modelos, treino, avaliação
│   ├── configs/             # Configurações de treino versionadas
│   ├── notebooks/           # Só exploração
│   ├── datasets/            # Fora do git
│   └── artifacts/           # Pesos treinados, fora do git
├── infrastructure/
│   └── docker/
├── docs/
└── docker-compose.yml
```

## Roadmap

- [ ] **Machine Learning:** escolher o dataset, pré-processar, treinar uma CNN base, avaliar (Top-1/Top-5), inferência top-K
- [ ] **Backend:** projeto FastAPI, endpoint de reconhecimento, processamento assíncrono, integração com o modelo, notificação
- [ ] **Frontend:** app Angular, canvas responsivo com mouse e touch, tela de resultados
- [ ] **Infraestrutura:** acesso pela LAN, CORS e firewall, teste com ~10 usuários simultâneos, consumo de CPU/memória/GPU

O checklist completo está em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#9-escopo-do-mvp).

## Decisões em aberto

| Tema | Opções | Direção atual |
|---|---|---|
| Fila de tarefas | `asyncio.Queue` / Redis + Celery ou RQ | Começar com `asyncio.Queue` e migrar para Redis quando necessário |
| Notificação do resultado | SSE / WebSocket | Tendência para SSE (só servidor → cliente) |
| Dataset | A definir | Dataset público de kanjis manuscritos |
| Quantidade de classes | Algumas centenas → 2.136 kanjis Jōyō | Começar pequeno e expandir |

## Como executar

Ainda não disponível. As instruções serão adicionadas quando os primeiros componentes estiverem prontos.

## O que o projeto explora

Visão Computacional, Deep Learning e CNN, processamento assíncrono, arquitetura orientada a eventos, REST API, comunicação em tempo real, concorrência e filas, e integração entre frontend e modelo de Machine Learning.

## Licença

O código-fonte está sob a [licença MIT](LICENSE).

A licença cobre só o código deste repositório. Os datasets usados no treino e os pesos treinados não fazem parte do repositório e não são cobertos por ela: cada dataset mantém os próprios termos, e pesos treinados com ele podem herdá-los.
