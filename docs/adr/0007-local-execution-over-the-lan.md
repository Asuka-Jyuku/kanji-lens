# 0007. Execução local, acessada pela rede local, sem nuvem

- **Status:** Aceita
- **Data:** 2026-11-03
- **Relacionadas:** [0003](0003-angular-frontend-and-fastapi-backend.md), [0005](0005-asynchronous-recognition-with-queue-and-workers.md), [0011](0011-school-notebook-as-server-with-cpu-first-inference.md), [0013](0013-run-directly-on-the-school-notebook-without-docker.md)

## Contexto

O app é para ser usado por celulares e computadores no mesmo lugar, sem orçamento para hospedagem e sem necessidade de acesso público. A inferência roda no servidor; o celular é só cliente. Decisão registrada depois do fato, a partir do [ARCHITECTURE.md](../ARCHITECTURE.md) (seção 5 do commit `d72a4d4`).

## Alternativas consideradas

- **Hospedagem em nuvem** (VM, PaaS, instância com GPU) — acessível de qualquer lugar; custa dinheiro, exige domínio e TLS, e expõe a API à internet.
- **Inferência no aparelho** (modelo no navegador com ONNX Runtime Web ou TensorFlow.js) — sem servidor de inferência; o modelo precisa ser pequeno o bastante para baixar no celular, e o projeto perderia a parte de fila/assíncrono que quer explorar. *Inferido.*
- **Uma máquina local como servidor, acessada pela rede local** — custo zero, sem exposição à internet; só funciona na mesma rede, e qualquer um nessa rede alcança o app.

## Decisão

Rodamos tudo numa máquina local que faz o papel de servidor, e os clientes a acessam pelo Wi-Fi, pelo IP local. Sem domínio público, sem nuvem, sem exposição à internet.

## Consequências

- **Positivas:** sem custo de hospedagem; sem superfície de ataque na internet; a CPU/GPU do servidor é o único limite de recursos, medido na etapa 4.
- **Negativas:** **qualquer um na rede local alcança a API, sem login**, então limite de entrada, fila limitada e CORS restrito são obrigatórios (`CLAUDE.md`, "Segurança"); os serviços precisam escutar em `0.0.0.0`; o firewall precisa liberar as portas; o IP do servidor deve ser reservado no DHCP do roteador; o frontend não pode chamar `localhost` a partir do celular.
- **Na prática:** `ng serve --host 0.0.0.0` e `uvicorn --host 0.0.0.0`; a URL da API usa o IP do servidor, ou o servidor de desenvolvimento do Angular faz proxy de `/api`; nenhuma saída de rede do app em execução sem ADR; os passos de configuração vão para o `docs/RUNNING.md` quando a primeira parte rodar.
- **Atualização de 2026-11-08 ([ADR 0011](0011-school-notebook-as-server-with-cpu-first-inference.md)):**
  - a máquina local é o notebook da escola (Dell Inspiron 3501, i7-1165G7, 16 GB, sem GPU dedicada);
  - o `ng serve --host 0.0.0.0` vale só no desenvolvimento;
  - em produção, o frontend é servido como build estático.
- **Atualização de 2026-11-08 ([ADR 0013](0013-run-directly-on-the-school-notebook-without-docker.md)):** no notebook, o KanjiLens roda direto, sem Docker, com os processos como serviço do sistema.
- **Atualização de 2026-11-10 ([#58](https://github.com/Asuka-Jyuku/kanji-lens/issues/58)):** das duas formas de o frontend achar a API, ficou o **proxy de `/api` no `ng serve`** (`frontend/proxy.conf.mjs`). Com ele, no desenvolvimento só o `ng serve` escuta em `0.0.0.0`; a API fica em `127.0.0.1`, o firewall abre só a 4200 e o CORS fica desligado. As portas e o resto da exposição estão no [docs/SECURITY.md](../SECURITY.md).
