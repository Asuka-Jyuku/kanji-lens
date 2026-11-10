<!-- Título do PR em inglês, no formato do Conventional Commits (vira o commit do squash). O resto, em português. -->

Closes #<!-- número da issue -->

## O que muda

<!-- Resumo em 1-3 linhas. -->

## Tipo

- [ ] Funcionalidade (`feat`)
- [ ] Correção (`fix`)
- [ ] Refatoração / manutenção (`refactor`, `perf`, `chore`, `style`)
- [ ] Documentação (`docs`)
- [ ] CI (`ci`), sem mudança de produto junto
- [ ] Testes (`test`) ou build (`build`)

## Checklist

- [ ] `CHANGELOG.md`: a entrada em `[Não publicado]`, dentro do título do tipo que já existe ali
- [ ] Regras novas com teste; domínio e use cases testados com adapters falsos; bug corrigido com teste que falhava antes
- [ ] Regra de dependência mantida (ADR 0004): nenhum import de framework em `domain/` ou `application/`; componente não injeta `HttpClient`; teste de arquitetura passa
- [ ] Mudou pré-processamento, tamanho da entrada, normalização ou lista de classes? Treino, inferência e versão do modelo neste PR, com Top-1/Top-5 no mesmo split de teste, antes e depois
- [ ] Mudou o modelo ou o treino? Top-1/Top-5 antes e depois, e a configuração usada
- [ ] Mudou a avaliação da ordem (algoritmo, normalização dos traços, dados do KanjiVG)? Erros detectados × falsos alarmes antes e depois, no mesmo conjunto fixo de desenhos
- [ ] Decisão de arquitetura (dependência, ferramenta, modelo/dataset, segurança, infraestrutura, decisão em aberto, padrão de código)? ADR criada ou atualizada neste PR, ou o motivo de não precisar
- [ ] Mudou tela, canvas ou controle? Cada decisão de desenho cita o princípio de `docs/UI-UX.md` (fonte × julgamento) e diz o que não foi validado num celular de verdade
- [ ] Mudou portas, CORS, limites de entrada ou o tamanho da fila? O `docs/SECURITY.md` continua batendo
- [ ] Documentos em dia (`CLAUDE.md`, "Documentos nascem com o assunto"): ARCHITECTURE.md, ADRs, READMEs, `CLAUDE.md`, `CONTRIBUTING.md` e skills conferidos e atualizados, ou nada a mudar
- [ ] Mudou o `README.md`? O `README.pt-BR.md` também (e vice-versa)
- [ ] Nenhum dataset, peso de modelo, segredo ou `.env` no commit
