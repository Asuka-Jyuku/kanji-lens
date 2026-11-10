# Revisão de ML

Cada achado sai com `arquivo:linha`, o que dá errado (entrada → resultado) e a fonte. Sem fonte, diga que é julgamento.

**O CI já pega** Ruff, mypy strict, pytest e os contratos do Import Linter, no Linux e no Windows. Ele não roda a avaliação do modelo: os números vêm no PR.

## O que só a revisão pega

**Treino e inferência iguais (`CLAUDE.md`, "Arquitetura")**
- [ ] Uma implementação só de pré-processamento; nada em `backend/` ou `frontend/` recorta, redimensiona ou normaliza por conta própria.
- [ ] Mudou o pré-processamento, a entrada, a normalização ou as classes? A versão do modelo sobe, o modelo é retreinado e o recognizer muda neste PR.
- [ ] O recognizer recusa pesos que não batem.

**Números (`references/experiments.md`)**
- [ ] Top-1/Top-5 antes e depois, no mesmo split, e nos desenhos do canvas.
- [ ] Mudou a avaliação da ordem? Erros detectados × falsos alarmes antes e depois, no mesmo conjunto.
- [ ] Todo número com o split, a versão, a configuração e a seed; o split de teste não foi usado para ajuste.
- [ ] Queda com um "aceito porque...".

**Código**
- [ ] `model.eval()` e `torch.inference_mode()` na avaliação e na inferência.
- [ ] Seeds da configuração; nada de aleatoriedade escondida.
- [ ] Funciona só com CPU; desempenho medido no notebook da escola.
- [ ] A avaliação da ordem não importa PyTorch.
- [ ] Nenhum pacote vazio "para o futuro".
- [ ] Código copiado de outro projeto? A licença permite, e há ADR.

**Repositório e licença**
- [ ] Nenhum dataset, peso ou binário grande no commit; como obter está documentado.
- [ ] O uso do dataset respeita a licença (redistribuição, citação).
- [ ] Código e comentários em inglês; `docs/MODEL.md` em português.
