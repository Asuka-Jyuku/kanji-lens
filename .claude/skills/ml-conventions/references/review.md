# Revisão de código de ML

Use ao revisar um PR com código de ML (ou o adapter do recognizer no backend) e no fim do seu próprio trabalho. Cada achado sai com `arquivo:linha`, o que acontece de errado (entrada → resultado) e a fonte da regra; o que for gosto, sem fonte, diga que é julgamento.

## O que a CI já pega (não gaste a revisão nisso)

Formatter, linter, testes e o teste de arquitetura, quando existirem (ADR de ferramentas da etapa 1). Se um deles falhou na CI, a revisão aponta o job; não reexplica a regra.

## O que só a revisão pega

**Consistência entre treino e inferência (`CLAUDE.md`, "Pré-processamento sempre junto")**
- [ ] Continua existindo uma implementação só de pré-processamento; nada em `backend/` ou `frontend/` recorta, redimensiona, inverte ou normaliza por conta própria.
- [ ] Uma mudança no pré-processamento, no tamanho da entrada, na normalização ou na lista de classes também sobe a versão do modelo, retreina e atualiza o adapter do recognizer neste PR.
- [ ] O adapter recusa pesos cuja lista de classes ou versão de pré-processamento não bate.

**Números (`references/experiments.md`)**
- [ ] Top-1/Top-5 antes e depois, no mesmo split de teste fixo, e no conjunto do canvas.
- [ ] Mudou a avaliação da ordem? Erros detectados × falsos alarmes antes e depois, no mesmo conjunto fixo de desenhos com ordem certa e errada.
- [ ] Todo número com o split, a versão do modelo, a configuração e a seed.
- [ ] O split é por pessoa que escreveu, quando o dataset permite; o split de teste não foi usado para ajuste.
- [ ] Uma queda tem um "aceito porque..." explícito.

**Código**
- [ ] `model.eval()` e `torch.inference_mode()` (ou `no_grad`) na avaliação e na inferência.
- [ ] Seeds vindas da configuração; nenhuma aleatoriedade escondida (augmentation sem seed, workers do `DataLoader`).
- [ ] Nada importa de `notebooks/`.
- [ ] Funciona só com CPU: o servidor é o notebook da escola, sem GPU dedicada (ADR 0011). Número de desempenho medido nele, com hardware e versões registrados.
- [ ] A avaliação da ordem não importa PyTorch, e os dados do KanjiVG têm a versão e a licença registradas (ADR 0012).
- [ ] Código copiado de um projeto de referência? A licença permite, e há ADR (spike, seção 11.1).

**Repositório e licença**
- [ ] Nenhum dataset, peso ou binário grande no commit; como obtê-los está documentado.
- [ ] O uso do dataset respeita a licença (cadastro, redistribuição, citação).

**Idioma (`CLAUDE.md`, "Idioma")**
- [ ] Código, nomes de arquivos e comentários em inglês; `docs/MODEL.md` em português.
