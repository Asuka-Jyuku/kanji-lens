# 0015. Ferramentas do backend: FastAPI e Uvicorn no workspace do uv

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0003](0003-angular-frontend-and-fastapi-backend.md), [0004](0004-clean-and-hexagonal-architecture.md), [0005](0005-asynchronous-recognition-with-queue-and-workers.md), [0013](0013-run-directly-on-the-school-notebook-without-docker.md), [0014](0014-ml-tooling-python-uv-ruff-pytest-import-linter.md)

## Contexto

Nenhum código do backend entra antes das ferramentas da etapa ([#18](https://github.com/Asuka-Jyuku/kanji-lens/issues/18)). O framework já está decidido: FastAPI, na [ADR 0003](0003-angular-frontend-and-fastapi-backend.md). As camadas também: ports and adapters, na [ADR 0004](0004-clean-and-hexagonal-architecture.md).

A [ADR 0014](0014-ml-tooling-python-uv-ruff-pytest-import-linter.md) já escolheu as ferramentas Python do ML: Python 3.15, um workspace do uv com lock único, Ruff, mypy, pytest e Import Linter. Ela também deixou para esta ADR a entrada do backend nesse workspace.

O backend roda no notebook Windows, sem Docker ([ADR 0013](0013-run-directly-on-the-school-notebook-without-docker.md)). O suporte das dependências ao Python 3.15, conferido no PyPI em 2026-11-08:
- todas têm pacote para o 3.15 no Windows: FastAPI 0.162, Pydantic 2.14, `pydantic-core` 2.50, Uvicorn 0.54, `httptools` 0.9, `watchfiles` 1.3 (ABI estável) e `websockets` 17.4;
- só o `uvloop` não existe no Windows, e o Uvicorn usa o event loop padrão do `asyncio` ali.

## Alternativas consideradas

- **Ferramentas próprias para o backend** (outro gerenciador, outro linter): deixariam o backend independente do ML, mas com dois jeitos de instalar e de checar, e o PyTorch e o NumPy podendo divergir entre treino e inferência.
- **As mesmas ferramentas da ADR 0014, com o backend como membro do workspace:** um comando instala tudo, a mesma configuração do Ruff vale para as duas partes, e o `kanjilens_ml` entra pelo lock único. Por outro lado, o ambiente do backend carrega o PyTorch só-CPU, mesmo que só o adapter do recognizer o use.
- **Servidor ASGI:**
  - **Hypercorn:** suporta HTTP/2, que não é necessário na rede local;
  - **Uvicorn:** o servidor indicado pelo FastAPI. O extra `standard` traz `httptools`, `watchfiles` e `websockets`; no Linux traz também o `uvloop`, que é deixado de fora no Windows.
- **Cliente de teste:**
  - **`httpx`:** o `TestClient` do Starlette o declara obsoleto;
  - **`httpx2`:** o sucessor, já aceito pelo Starlette, sem aviso.
- **Testes assíncronos:**
  - **`pytest-asyncio`:** mais uma dependência;
  - **o plugin de pytest do `anyio`:** já vem com o `anyio`, que é dependência do Starlette.

## Decisão

- **O backend é o pacote `kanjilens`**, membro do workspace do uv da [ADR 0014](0014-ml-tooling-python-uv-ruff-pytest-import-linter.md): Python 3.15, Ruff configurado na raiz, mypy `strict` (com o plugin do Pydantic), pytest e Import Linter.
- **O `kanjilens_ml` é dependência do workspace** (`kanjilens-ml = { workspace = true }`), com as mesmas versões travadas no `uv.lock`. Só os adapters outbound o importam, e a regra vira contrato.
- **FastAPI** com **Uvicorn** (`uvicorn[standard]`), a aplicação criada por uma fábrica em `bootstrap/` (`create_app`).
- **Testes:**
  - `TestClient` do FastAPI com `httpx2`;
  - para código assíncrono, o plugin do `anyio`, sem dependência extra;
  - testes de domínio e de use case sem framework, com adapters falsos (`CLAUDE.md`, "Testes").
- **Teste de arquitetura:** seis contratos do Import Linter no `backend/pyproject.toml`, rodados pelo `pytest`:
  1. camadas `bootstrap` → `adapters` → `application` → `domain`;
  2. dentro de `application`, `use_cases` → `ports`;
  3. `domain` e `application` não importam FastAPI, Starlette, Pydantic, Uvicorn, httpx, PyTorch, NumPy nem `kanjilens_ml`;
  4. adapters inbound e outbound não se conhecem: só o `bootstrap` os liga;
  5. PyTorch e `kanjilens_ml` não entram no inbound nem no `bootstrap`, que só os alcança pelos adapters outbound;
  6. Pydantic e FastAPI não entram nos adapters outbound.

## Consequências

- **Positivas:**
  - um `uv sync --all-packages` instala o ML e o backend, com as mesmas versões;
  - o `kanjilens_ml` que o backend usa na inferência é o mesmo código, na mesma versão, do treino;
  - as regras da ADR 0004 viram testes que falham, em vez de revisão manual;
  - uma configuração do Ruff e um jeito de rodar as checagens para as duas partes Python.
- **Negativas:**
  - **O ambiente do backend carrega o PyTorch só-CPU** e o NumPy, porque o `kanjilens_ml` depende deles. No notebook isso é necessário de qualquer forma (o processo de inferência roda o modelo), mas o ambiente é maior que o de uma API comum.
  - **Sem `uvloop` no Windows:** o Uvicorn usa o loop padrão do `asyncio`, um pouco mais lento. Para 3–5 alunos isso não deve pesar (*a medir* no teste de carga).
  - **O `version` do `backend/pyproject.toml`** precisa acompanhar o `VERSION` a cada release ([ADR 0008](0008-git-flow-and-changelog-by-release.md)). O `test_package.py` falha se divergirem.
  - **A estrutura não foi testada no Windows nesta ADR.** Isso fica para o CI ([#32](https://github.com/Asuka-Jyuku/kanji-lens/issues/32)), que tem um runner Windows para o backend e o ML.
- **Na prática:**
  - os comandos estão no `CLAUDE.md`, "Comandos";
  - a fila, a notificação (SSE ou WebSocket) e os ports entram nas próprias issues (#19, #20), com as dependências que elas escolherem;
  - rotas e schemas ficam em `adapters/inbound/http/`, e a aplicação é montada em `bootstrap/`;
  - dependência nova entra por `uv add --package kanjilens <pacote>`, com o `uv.lock` no mesmo PR.
