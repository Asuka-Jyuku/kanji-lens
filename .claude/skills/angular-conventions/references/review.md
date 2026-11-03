# Revisão de código Angular

Use ao revisar um PR com frontend e no fim do seu próprio trabalho. Cada achado sai com `arquivo:linha`, o que acontece de errado (entrada → resultado) e a fonte da regra; o que for gosto, sem fonte, diga que é julgamento.

## O que a CI já pega (não gaste a revisão nisso)

Build, checagem de tipos, testes, linter e o teste de arquitetura, quando existirem (ADR de ferramentas da etapa 3). Se um deles falhou na CI, a revisão aponta o job; não reexplica a regra.

## O que só a revisão pega

**Camadas (ADR 0004)**
- [ ] `domain/` não importa nada do Angular; `application/` só importa `domain/` e os próprios ports.
- [ ] Nenhum `HttpClient`, `EventSource` ou `fetch` fora de `infrastructure/`.
- [ ] Adapter novo ligado ao port em `app.config.ts`, não instanciado à mão.
- [ ] Nenhuma regra de negócio escondida num componente ou template.

**Regras e testes**
- [ ] Cada regra nova tem teste; use cases testados com port falso, não com `HttpClient` simulado.
- [ ] Bug corrigido com teste que falhava antes.

**Canvas e touch**
- [ ] Pointer Events, `touch-action: none`, `devicePixelRatio` e pointer capture no lugar (`style.md`).
- [ ] O desenho vai como foi desenhado: nada de recortar, redimensionar, inverter ou normalizar no frontend.
- [ ] Limpar o canvas também limpa os resultados e qualquer job pendente.

**Fluxo assíncrono (ADR 0005)**
- [ ] Todo estado do job aparece na tela: `queued`, `processing`, `completed`, `failed`, mais o `503` (fila cheia) e erro de rede.
- [ ] A conexão SSE é fechada no destroy; o polling de `GET /api/recognitions/{id}` assume quando o SSE cai.
- [ ] Um segundo "Recognize" com um job pendente não deixa dois streams abertos.

**Rede local (ADR 0007)**
- [ ] Nenhuma URL com `localhost` fixo; a base da API vem da configuração ou do proxy do servidor de desenvolvimento.

**Acessibilidade**
- [ ] Botões são botões de verdade, com rótulo; o estado de processamento e os resultados são anunciados (`aria-live`).

**Idioma (`CLAUDE.md`, "Idioma")**
- [ ] Código, nomes de arquivos e comentários em inglês.
