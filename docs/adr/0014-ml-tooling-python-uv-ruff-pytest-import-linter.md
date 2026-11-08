# 0014. Ferramentas do ML: Python 3.15, uv, Ruff, mypy, pytest e Import Linter

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0002](0002-monorepo-for-frontend-backend-and-ml.md), [0004](0004-clean-and-hexagonal-architecture.md), [0006](0006-cnn-with-pytorch.md), [0011](0011-school-notebook-as-server-with-cpu-first-inference.md), [0012](0012-ordered-mode-as-stroke-order-evaluation.md), [0013](0013-run-directly-on-the-school-notebook-without-docker.md)

## Contexto

Nenhum código de ML entra antes das ferramentas da etapa (`CLAUDE.md`, "Comandos"; [#12](https://github.com/Asuka-Jyuku/kanji-lens/issues/12)). A escolha precisa servir a três ambientes:

- **o notebook da escola:** Windows, só CPU ([ADR 0011](0011-school-notebook-as-server-with-cpu-first-inference.md), [ADR 0013](0013-run-directly-on-the-school-notebook-without-docker.md));
- **a máquina de treino:** potente, possivelmente com GPU;
- **o CI:** runners Linux e Windows ([#32](https://github.com/Asuka-Jyuku/kanji-lens/issues/32)).

O backend também vai importar o `kanjilens_ml`, então esta ADR precisa dizer como os dois projetos Python se enxergam.

Foi pedida a versão mais recente do Python, a 3.15 (3.15.2). O suporte a ela, conferido no PyPI em 2026-11-08:

| Pacote | Versão | Pacote para 3.15 | Pacote para 3.15 no Windows |
|---|---|---|---|
| PyTorch | 2.15.0 | sim (inclusive no índice só-CPU) | sim |
| NumPy | 2.5.4 | sim | sim |
| Ruff, mypy, pytest, Import Linter, uv | 0.17.4, 2.4.1, 9.2.0, 2.16, 0.13.7 | sim | sim |
| ONNX Runtime | 1.31.1 | **não** (até 3.14) | **não** |
| OpenVINO | 2026.4.1 | **não** (até 3.14) | **não** |

## Alternativas consideradas

- **Versão do Python:**
  - **3.14:** tudo tem pacote, inclusive os runtimes candidatos ao benchmark (ONNX Runtime e OpenVINO). Não é a mais recente.
  - **3.15:** é a mais recente, e o PyTorch e o NumPy já a suportam no Windows. ONNX Runtime e OpenVINO ainda não, e eles só entram no benchmark, depois do modelo e do código.
- **Gerenciador de pacotes e ambientes:**
  - **pip + venv (+ pip-tools):** padrão e sem nada a instalar além do Python. Não instala o próprio Python, e o lock entre plataformas e o índice do PyTorch exigem trabalho manual.
  - **Poetry:** maduro e com lock. Mais lento, e índices por pacote (o do PyTorch só-CPU) são mais trabalhosos.
  - **conda:** forte em pacotes binários. É pesado, e o PyTorch deixou de publicar no canal do conda.
  - **uv:** rápido. Instala a versão do Python, gera um lock universal (Linux, Windows e macOS num arquivo só), aceita índice por pacote (o PyTorch só-CPU) e tem *workspaces* para vários projetos Python no mesmo repositório. É ferramenta de uma empresa só (Astral), mas o lock e o `pyproject.toml` são padrões abertos.
- **Lint e formatação:**
  - **Black + Flake8 + isort:** três ferramentas e três configurações;
  - **Ruff:** uma ferramenta só, que cobre as três e é muito mais rápida.
- **Tipos:**
  - **pyright:** rápido. Precisa de Node, ou de um wrapper, para rodar no CI;
  - **mypy:** o padrão da comunidade, roda em Python puro e tem modo `strict`.
- **Testes:**
  - **unittest:** já vem com o Python, mas é mais verboso;
  - **pytest:** o padrão de fato, com fixtures e plugins.
- **Teste de arquitetura:**
  - **teste próprio lendo os `import` pela AST:** sem dependência, mas é código para manter;
  - **Import Linter:** contratos declarativos (proibido, camadas), que falham quando um import quebra a regra.
- **Como o backend enxerga o `kanjilens_ml`:**
  - **pacote publicado:** desacopla, mas exige publicar a cada mudança, e o pré-processamento muda junto com o backend;
  - **dependência por caminho, com locks separados:** cada parte tem o seu lock, e o PyTorch e o NumPy podem divergir entre treino e inferência;
  - **workspace do uv com um lock só:** as duas partes usam as mesmas versões de tudo.

## Decisão

- **Python 3.15** (`.python-version` e `requires-python = ">=3.15,<3.16"`).
- **uv** como gerenciador de pacotes e de ambiente, com um **workspace na raiz** e o `uv.lock` versionado. O `pyproject.toml` da raiz não é um pacote: só agrupa os membros. Cada parte mantém o próprio manifesto ([ADR 0002](0002-monorepo-for-frontend-backend-and-ml.md)). Hoje o único membro é o `ml/`; o `backend/` entra na ADR de ferramentas do backend ([#18](https://github.com/Asuka-Jyuku/kanji-lens/issues/18)) e passa a usar o `kanjilens_ml` como dependência do workspace.
- **PyTorch do índice só-CPU** (`https://download.pytorch.org/whl/cpu`), configurado como índice explícito só para o `torch`.
- **Ruff** para lint e formatação, com a configuração na raiz (vale para todas as partes Python).
- **mypy** em modo `strict` no `ml/src` e nos testes.
- **pytest** para os testes, em `ml/tests/`.
- **Import Linter** para o teste de arquitetura, com três contratos no `ml/pyproject.toml`:
  1. o `kanjilens_ml` não importa o backend nem framework web;
  2. a avaliação da ordem (`kanjilens_ml.stroke_order`) não importa o PyTorch ([ADR 0012](0012-ordered-mode-as-stroke-order-evaluation.md));
  3. camadas internas: `preprocessing` é a base; `models`, `data` e `stroke_order` vêm acima; `training` e `evaluation`, no topo.

  O `pytest` roda os contratos (`tests/test_architecture.py`), então o teste falha quando um import quebra a regra.

## Consequências

- **Positivas:**
  - um comando instala o Python certo e todas as dependências, no Linux e no Windows;
  - treino e inferência usam as mesmas versões de PyTorch e NumPy, o que tira uma fonte de *train/serve skew*;
  - o lint, a formatação, os tipos, os testes e a regra de dependência rodam sem ninguém precisar lembrar, e o CI só chama os mesmos comandos;
  - nenhum pacote CUDA de vários GB entra no ambiente.
- **Negativas:**
  - **ONNX Runtime e OpenVINO não têm pacote para o 3.15.** Quando o benchmark acontecer, ou eles já terão, ou o benchmark roda num ambiente 3.14. Se um deles vencer e ainda não suportar o 3.15, a produção volta para o 3.14, numa atualização desta ADR.
  - **Treino em GPU** precisa de outro índice do PyTorch (CUDA). Isso fica para quando o treino começar ([#15](https://github.com/Asuka-Jyuku/kanji-lens/issues/15)), com a versão de CUDA da máquina de treino, provavelmente por *extras* do uv que escolhem o índice.
  - **Todo mundo precisa do uv instalado.** Ele não vem com o Python.
  - **A estrutura não foi testada no Windows nesta ADR:** o lock tem o pacote do PyTorch para Windows, mas a confirmação fica com o CI (#32) e com a primeira instalação no notebook.
  - **O `version` do `ml/pyproject.toml`** precisa acompanhar o `VERSION` a cada release ([ADR 0008](0008-git-flow-and-changelog-by-release.md)). O teste `test_package.py` falha se divergirem.
- **Na prática:**
  - os comandos estão no `CLAUDE.md`, "Comandos";
  - dependência nova entra por `uv add` no membro certo (`--package kanjilens-ml`), com o `uv.lock` no mesmo PR;
  - pacote com índice próprio entra em `[tool.uv.sources]`, com o motivo registrado;
  - mudar a versão do Python pede uma atualização desta ADR.
