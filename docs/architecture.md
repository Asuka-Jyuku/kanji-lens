# KanjiLens: Arquitetura

Documento de design do KanjiLens. Registra a arquitetura proposta, as decisões já tomadas e as que ainda estão em aberto. O resumo do projeto está no [README](../README.pt-BR.md).

> Este documento é uma proposta viva. Seções marcadas como **em aberto** ainda não têm decisão.

---

## 1. Visão geral

O KanjiLens reconhece kanjis manuscritos. O usuário desenha um kanji em um canvas, a aplicação envia o desenho para um servidor que executa um modelo de Deep Learning, e o servidor devolve uma lista de possíveis kanjis.

O sistema não precisa acertar o caractere com 100% de precisão. Ele apresenta as principais possibilidades, ordenadas por confiança, para que o usuário identifique qual caractere pretendia escrever.

### Objetivos

- Reconhecer kanjis manuscritos com uma CNN.
- Disponibilizar uma interface de desenho manual, acessível pelo celular.
- Suportar múltiplos usuários simultâneos (estimativa inicial: ~10).
- Processar as solicitações de forma assíncrona.
- Rodar toda a infraestrutura localmente, sem domínio nem hospedagem externa.

---

## 2. Arquitetura

A aplicação tem três componentes, com responsabilidades separadas:

| Componente | Responsabilidade |
|---|---|
| Frontend | Interação com o usuário: canvas, envio e exibição dos resultados |
| Backend | Recebimento das requisições, gerenciamento das tarefas e notificação |
| Machine Learning | Treinamento e inferência do modelo de reconhecimento |

```text
                 CLIENTES
          ┌─────────┬─────────┐
        Mobile    Desktop   Mobile
          └─────────┴─────────┘
                    │
                    ▼
             Angular Frontend
                    │ REST
                    ▼
                 FastAPI
                    │
                    ▼
              Message Queue
                    │
                    ▼
              CNN Worker(s)
                    │
                    ▼
              PyTorch Model
                    │
                    ▼
               Predictions
                    │ SSE / WebSocket
                    ▼
             Angular Frontend
```

### 2.1 Frontend

**Stack:** Angular, TypeScript, HTML, CSS, HTML Canvas API.

Funcionalidades:

- Área de desenho com suporte a mouse e touch.
- Botão para limpar o canvas.
- Botão para enviar o desenho.
- Indicador de processamento.
- Lista dos kanjis previstos, com a confiança de cada um.

```text
┌──────────────────────────────┐
│          KanjiLens           │
│        Draw your Kanji       │
│                              │
│   ┌──────────────────────┐   │
│   │                      │   │
│   │          日          │   │
│   │                      │   │
│   └──────────────────────┘   │
│                              │
│   [Clear]       [Recognize]  │
│                              │
│   Predictions                │
│   日  81%                    │
│   目  12%                    │
│   白   4%                    │
└──────────────────────────────┘
```

### 2.2 Backend

**Stack:** Python, FastAPI, REST, SSE ou WebSocket.

O processamento é assíncrono: o servidor não mantém a requisição HTTP original aberta enquanto a CNN executa a inferência.

Fluxo:

1. O frontend envia o desenho.
2. O FastAPI recebe a solicitação.
3. O backend gera um `job_id`.
4. A tarefa entra na fila de processamento.
5. O backend responde imediatamente com a confirmação de recebimento.
6. Um worker consome a tarefa e executa a inferência.
7. O resultado é armazenado.
8. O backend notifica o frontend que a tarefa terminou.

Resposta inicial:

```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

Resposta após o processamento:

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

> As confianças são probabilidades da saída Softmax. Por isso a soma das previsões top-K nunca passa de 1.

### 2.3 Machine Learning

**Stack:** Python, PyTorch, NumPy, OpenCV (opcional, para pré-processamento).

O modelo é uma CNN treinada para classificar caracteres japoneses manuscritos, a partir de um dataset público (ver [seção 6](#6-dataset-e-treinamento)). O projeto começa com uma arquitetura simples e evolui conforme os resultados.

Arquitetura inicial:

```text
Input Image → Conv2D → ReLU → MaxPooling
            → Conv2D → ReLU → MaxPooling
            → Flatten → Dense → Softmax → Top-K Predictions
```

Pipeline de reconhecimento:

```text
Handwritten Drawing → Image Acquisition → Preprocessing
                    → Normalization → CNN Model → Classification → Top-K Predictions
```

O modelo retorna as K classes mais prováveis, e não apenas a de maior probabilidade.

---

## 3. Processamento assíncrono e concorrência

Para suportar múltiplos usuários simultâneos, a inferência é separada do recebimento das requisições HTTP.

```text
             FastAPI
                │
                ▼
          Message Queue
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
    Worker 1 Worker 2 Worker 3
       │        │        │
      CNN      CNN      CNN
       └────────┼────────┘
                ▼
           Job Results
```

### 3.1 Fila de tarefas (em aberto)

| | `asyncio.Queue` | Redis + Celery ou RQ |
|---|---|---|
| Complexidade | Baixa, sem infraestrutura extra | Exige Redis rodando |
| Persistência | Em memória; tarefas se perdem se o processo cair | Persistente, conforme a configuração |
| Escala | Um único processo | Workers independentes, escaláveis |
| Uso indicado | Validar o fluxo assíncrono na primeira versão | Quando a carga ou a robustez exigirem |

**Direção atual:** começar com `asyncio.Queue` e migrar para Redis + Celery/RQ quando houver necessidade.

### 3.2 Estratégia de inferência

- O modelo é carregado **uma vez por worker** e reutilizado em todas as inferências.
- A quantidade de workers depende dos recursos do computador servidor: CPU, memória e GPU.

### 3.3 Pontos de atenção

- **A inferência bloqueia o event loop.** A inferência do PyTorch é CPU/GPU-bound. Se o worker rodar como corrotina no mesmo event loop do FastAPI, enquanto ele executa a API para de responder, inclusive as conexões SSE. Com `asyncio.Queue`, a inferência precisa rodar fora do loop (`run_in_executor` com thread ou process pool).
- **O estado em memória não é compartilhado entre processos.** Com `asyncio.Queue`, a fila e os resultados vivem na memória de um processo. Se o Uvicorn subir com `--workers > 1`, cada processo terá sua própria fila, e o cliente pode consultar ou escutar um processo que não conhece o seu `job_id`. Na opção 1, rode um único processo do Uvicorn. Esse é o principal motivo para migrar para Redis.
- **Threads do PyTorch.** Por padrão, o PyTorch usa todos os núcleos em cada inferência. Com vários workers no mesmo processo, ajuste `torch.set_num_threads` para que os workers não disputem a CPU.

---

## 4. Comunicação entre frontend e backend

A comunicação principal é REST. SOAP foi descartado por adicionar complexidade sem benefício para esse cenário.

### 4.1 Endpoints

| Método | Endpoint | Responsabilidade |
|---|---|---|
| `POST` | `/api/recognitions` | Enviar um desenho para reconhecimento |
| `GET` | `/api/recognitions/{id}` | Consultar o status de uma tarefa |
| `GET` | `/api/health` | Verificar disponibilidade do backend |

### 4.2 Notificação: SSE vs WebSocket (em aberto)

| | SSE | WebSocket |
|---|---|---|
| Direção | Servidor → cliente | Bidirecional |
| Cliente no browser | `EventSource` nativo, reconexão automática | Reconexão manual |
| Quando faz sentido | Avisar que a tarefa terminou | Progresso detalhado, cancelamento de tarefa, interação contínua |

**Direção atual:** SSE, porque o fluxo principal é o servidor avisando o cliente. WebSocket passa a valer se surgir a necessidade de comunicação bidirecional.

O `GET /api/recognitions/{id}` serve de fallback: se a conexão SSE cair, o frontend consulta o status por polling.

---

## 5. Infraestrutura e execução local

O projeto roda inteiramente em uma máquina local. Não são necessários domínio público, hospedagem em nuvem, servidor externo nem exposição à internet.

O computador que hospeda a aplicação funciona como servidor. Dispositivos na mesma rede Wi-Fi acessam pelo IP local:

```text
Servidor: 192.168.0.10
Angular:  http://192.168.0.10:4200
FastAPI:  http://192.168.0.10:8000
```

O celular é apenas cliente. Toda a inferência roda no servidor.

### 5.1 Configuração necessária

- **Bind dos serviços em `0.0.0.0`.** Por padrão, tanto o `ng serve` quanto o Uvicorn escutam só em `localhost` e ficam invisíveis para o celular. Use `ng serve --host 0.0.0.0` e `uvicorn ... --host 0.0.0.0`.
- **CORS.** O frontend (porta 4200) e a API (porta 8000) são origens diferentes. O FastAPI precisa liberar a origem do frontend.
- **URL da API no frontend.** Se o frontend chamar `http://localhost:8000`, no celular `localhost` é o próprio celular. A URL da API precisa usar o IP do servidor, ou o Angular pode usar um proxy para a API (assim tudo passa pela porta 4200 e o CORS deixa de ser necessário).
- **Firewall.** Liberar as portas 4200 e 8000 na rede local.
- **IP fixo.** O IP do servidor pode mudar a cada conexão ao roteador. Reserve o IP no DHCP do roteador para não precisar reconfigurar.

---

## 6. Dataset e treinamento

### 6.1 Dataset (em aberto)

O projeto usa um dataset público de kanjis manuscritos. Critérios de escolha:

- Quantidade de kanjis disponíveis.
- Quantidade de amostras por caractere.
- Qualidade das imagens.
- Diversidade de estilos de escrita.
- Licença e possibilidade de uso.
- Compatibilidade com o pipeline de treinamento.

Candidatos a avaliar (licenças e números ainda a confirmar nas fontes oficiais):

- **ETL Character Database (AIST)**, em especial o ETL8G e o ETL9B: kanjis modernos escritos à mão por centenas de pessoas. É a referência mais usada para esse problema.
- **Kuzushiji-Kanji**: tem muitas classes, mas é escrita cursiva clássica, bem diferente da escrita moderna. Tende a não servir como base principal.

### 6.2 Quantidade de classes (em aberto)

Começar com algumas centenas de kanjis e depois expandir para o conjunto Jōyō (2.136 kanjis).

### 6.3 Avaliação do modelo

Métricas acompanhadas:

- Accuracy Top-1 e Top-5.
- Precision, Recall e F1-score.
- Matriz de confusão.
- Tempo médio de inferência.

A Top-5 é a métrica mais próxima da experiência do usuário, já que a interface mostra vários candidatos. A matriz de confusão serve principalmente para analisar kanjis visualmente semelhantes (como 日, 目 e 白).

### 6.4 Pontos de atenção

- **O desenho do canvas é diferente das imagens do dataset.** Datasets como o ETL são digitalizações de papel: tons de cinza, traço de caneta, ruído e contraste próprios. O canvas gera traço sintético, geralmente fino e uniforme, com cores e proporção diferentes. Se o pré-processamento da inferência não aproximar o desenho das imagens de treino (inversão de cores, recorte pela bounding box, centralização, padding, espessura do traço e resolução), a acurácia em produção cai bastante em relação à do conjunto de teste. Esse é o principal risco do projeto e deve ser testado com desenhos reais assim que houver um modelo base.
- **O pré-processamento precisa ser o mesmo no treino e na inferência.** Mantenha-o em um único módulo compartilhado entre `ml/` e `backend/`, em vez de duas implementações paralelas.

---

## 7. Estrutura do repositório

Proposta inicial, ajustável conforme o projeto evoluir:

```text
kanji-lens/
├── frontend/
│   ├── src/
│   ├── angular.json
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── workers/
│   │   ├── models/
│   │   └── main.py
│   └── requirements.txt
├── ml/
│   ├── datasets/
│   ├── notebooks/
│   ├── training/
│   ├── evaluation/
│   └── models/
├── infrastructure/
│   └── docker/
├── docs/
├── docker-compose.yml
└── README.md
```

> `ml/datasets/` e os pesos em `ml/models/` tendem a ser grandes. Mantenha-os fora do Git (`.gitignore`) e documente como obtê-los.

---

## 8. Escopo do MVP

A primeira versão prioriza o fluxo completo de reconhecimento, de ponta a ponta.

### Etapa 1: Machine Learning

- [ ] Pesquisar datasets de kanjis manuscritos.
- [ ] Selecionar o dataset.
- [ ] Pré-processar as imagens.
- [ ] Implementar uma CNN inicial.
- [ ] Treinar o modelo.
- [ ] Avaliar os resultados.
- [ ] Implementar inferência top-K.

### Etapa 2: Backend

- [ ] Configurar o projeto FastAPI.
- [ ] Criar o endpoint de reconhecimento.
- [ ] Gerar o `job_id`.
- [ ] Implementar o processamento assíncrono.
- [ ] Integrar o modelo PyTorch.
- [ ] Armazenar os resultados.
- [ ] Implementar a notificação via SSE ou WebSocket.

### Etapa 3: Frontend

- [ ] Criar a aplicação Angular.
- [ ] Implementar o canvas responsivo.
- [ ] Implementar desenho com mouse e touch.
- [ ] Implementar a limpeza do canvas.
- [ ] Integrar com a REST API.
- [ ] Implementar o indicador de processamento.
- [ ] Exibir as previsões.

### Etapa 4: Infraestrutura

- [ ] Configurar a execução local.
- [ ] Configurar o acesso pela rede Wi-Fi.
- [ ] Configurar a comunicação entre frontend e backend.
- [ ] Avaliar o uso de Redis.
- [ ] Testar múltiplos usuários simultâneos.
- [ ] Medir o consumo de CPU, memória e GPU.

---

## 9. Decisões arquiteturais

| Decisão | Escolha | Status |
|---|---|---|
| Frontend | Angular + TypeScript | Decidido |
| Backend | Python + FastAPI | Decidido |
| Comunicação principal | REST | Decidido |
| Machine Learning | PyTorch, CNN | Decidido |
| Processamento | Assíncrono, com workers | Decidido |
| Execução | Local / LAN | Decidido |
| Usuários simultâneos estimados | ~10 | Estimativa |
| Notificação assíncrona | SSE ou WebSocket | Em aberto (tendência: SSE) |
| Fila | `asyncio.Queue` ou Redis + Celery/RQ | Em aberto (começar com `asyncio.Queue`) |
| Dataset | A definir | Em aberto |
| Quantidade de classes | Centenas → 2.136 (Jōyō) | Em aberto |

Quando uma decisão em aberto for fechada, vale registrá-la como ADR em `docs/adr/`, com contexto, alternativas e trade-off.

---

## 10. Objetivo final

Entregar uma aplicação funcional na qual diferentes usuários acessem uma interface web pelo celular ou computador, desenhem kanjis e recebam sugestões de caracteres reconhecidos por um modelo de Deep Learning.

Além do reconhecimento em si, o projeto explora:

- Computer Vision.
- Deep Learning e CNN.
- Processamento assíncrono.
- Arquitetura orientada a eventos.
- REST API.
- Comunicação em tempo real.
- Concorrência e gerenciamento de filas.
- Integração entre frontend e modelos de Machine Learning.

O foco é uma solução modular, com separação clara entre interface, API, processamento e modelo, permitindo que cada componente evolua de forma independente.
