<!-- Título em inglês, no formato do Conventional Commits (vira o commit do squash). O resto em português. -->

Closes #<!-- número da issue -->

## O que muda

<!-- 1 a 3 linhas. -->

## Checklist

- [ ] Uma linha no `CHANGELOG.md`, em `[Não publicado]`
- [ ] Regra nova com teste; bug corrigido com teste que falhava antes
- [ ] Camadas respeitadas, e nenhum port ou use case novo sem uma segunda implementação real
- [ ] Mudou modelo, pré-processamento, classes ou avaliação da ordem? Números antes e depois, no mesmo conjunto
- [ ] Decisão difícil de desfazer? ADR neste PR
- [ ] Mudou tela ou canvas? Cita o princípio do `docs/UI-UX.md` e diz o que não foi testado num celular
- [ ] Mudou porta, CORS, limite ou fila? O `docs/SECURITY.md` continua certo
- [ ] Documentos: só o que ficou falso foi atualizado (e o `README.pt-BR.md` junto com o `README.md`)
- [ ] Nenhum dataset, peso, segredo ou `.env` no commit
