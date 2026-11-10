# kanjilens-ml

Biblioteca de ML do KanjiLens: pré-processamento compartilhado, modelo, treino, avaliação e avaliação da ordem dos traços. É usada pelos scripts de treino e pelos adapters outbound do backend; não sobe servidor nem fila.

As ferramentas estão na [ADR 0014](../docs/adr/0014-ml-tooling-python-uv-ruff-pytest-import-linter.md); os comandos, no [`CLAUDE.md`](../CLAUDE.md#comandos); como preparar o KanjiVG, no [`docs/RUNNING.md`](../docs/RUNNING.md#6-referências-do-kanjivg-opcional); as regras de ML, na skill `ml-conventions`.

Os scripts de `scripts/` preparam dados e medem: `prepare_kanjivg.py` gera as referências do KanjiVG (CC BY-SA 3.0, © Ulrich Apel) fora do git, e `benchmark_stroke_order.py` mede a avaliação da ordem ([docs/MODEL.md](../docs/MODEL.md#avaliação-da-ordem-dos-traços)).
