# kanjilens-ml

Biblioteca de ML do KanjiLens. Hoje tem o pré-processamento dos traços e a avaliação da ordem contra o KanjiVG; o modelo, o treino e a avaliação do reconhecimento entram com o dataset. É usada pelos scripts de `scripts/` e pelos adapters do backend; não sobe servidor.

- `scripts/prepare_kanjivg.py`: gera as referências do KanjiVG (CC BY-SA 3.0, © Ulrich Apel) fora do git ([RUNNING.md](../docs/RUNNING.md#6-referências-do-kanjivg-opcional)).
- `scripts/benchmark_stroke_order.py`: mede a avaliação da ordem ([MODEL.md](../docs/MODEL.md#avaliação-da-ordem-dos-traços)).

Ferramentas na [ADR 0014](../docs/adr/0014-ml-tooling-python-uv-ruff-pytest-import-linter.md), comandos no [`CLAUDE.md`](../CLAUDE.md#comandos), regras na skill `ml-conventions`.
