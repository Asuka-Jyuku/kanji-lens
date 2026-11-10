# 0013. Execução direta no notebook da escola, sem Docker

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0007](0007-local-execution-over-the-lan.md), [0011](0011-school-notebook-as-server-with-cpu-first-inference.md)

## Contexto

O KanjiLens roda inteiro no notebook da escola: Dell Inspiron 3501, i7-1165G7 com 4 núcleos, 16 GB de RAM e sem GPU dedicada ([ADR 0011](0011-school-notebook-as-server-with-cpu-first-inference.md)). No mesmo notebook rodam:
- o frontend (build estático);
- o FastAPI;
- a fila;
- o processo de inferência com o modelo;
- as referências do KanjiVG.

A estrutura planejada do repositório previa `infrastructure/docker/` e um `docker-compose.yml`, mas nenhuma ADR tinha decidido usar Docker.

O notebook roda **Windows**. Ali, o Docker precisa do Docker Desktop, que roda uma máquina virtual Linux (pelo WSL 2). Essa VM tem memória e disco próprios e, por padrão, pode ocupar até metade da RAM. Os processos do Docker Desktop também ficam rodando o tempo todo.

No Linux o custo seria menor: um container é um processo comum, isolado pelo kernel, e quase não custa CPU. Ainda assim haveria o serviço do Docker, as imagens (a do PyTorch passa de alguns GB) e mais uma camada para operar.

## Alternativas consideradas

- **Docker Compose com um container por serviço:** o ambiente fica igual em qualquer máquina, sobe com um comando e é isolado. Em compensação, é mais um programa para instalar e manter no notebook, e no Windows acrescenta uma VM que custa RAM e disco num notebook que já divide 16 GB com o modelo. Também são mais peças para quem cuida da máquina da escola. Para uma máquina só, o ganho em portabilidade é pequeno.
- **Execução direta, com ambiente Python isolado e os processos como serviço do sistema:** gasta menos memória e disco, tem menos peças, e o profiling de CPU e RAM mede o que roda de fato. Por outro lado, a instalação depende do sistema operacional, e o ambiente pode divergir do de desenvolvimento se as versões não estiverem travadas.

## Decisão

Rodamos o KanjiLens **direto no notebook da escola, sem Docker**:
- **Backend e ML:** num ambiente Python isolado, com versões travadas pelo lock file definido nas ADRs de ferramentas;
- **Frontend:** servido como build estático, na mesma origem da API;
- **Processos:** sobem como serviço do sistema operacional, para iniciar com o notebook e reiniciar se caírem.

A escolha concreta vai para o `docs/RUNNING.md`:
- **Como os processos rodam como serviço no Windows:** um serviço do Windows, um wrapper como o NSSM, ou o Agendador de Tarefas na inicialização;
- **Quem serve o build:** o próprio FastAPI ou um servidor estático.

## Consequências

- **Positivas:**
  - sobra mais RAM e CPU para o modelo e para a carga de 3–5 alunos;
  - menos peças para manter na máquina da escola;
  - o benchmark e o teste de carga medem o processo real, sem uma VM no meio.
- **Negativas:**
  - **sem isolamento:** o KanjiLens divide o sistema com o que mais estiver instalado no notebook;
  - **a instalação é específica do Windows** e precisa de um passo a passo testado;
  - **detalhes do Python no Windows:**
    - o `multiprocessing` usa `spawn`, então um process pool recarrega o modelo em cada processo, e isso pesa na RAM e na partida;
    - o Uvicorn roda sem o `uvloop`, que não existe no Windows;
    - caminhos e fim de linha precisam ser tratados no código e nos scripts;
  - **reprodutibilidade:** só existe se as versões estiverem travadas (lock files de `backend/` e `ml/`, versão do Python e do Node registradas);
  - **desenvolvimento × produção:** quem desenvolve em outra máquina não tem o mesmo ambiente, então diferenças aparecem só no notebook.
- **Na prática:**
  - `infrastructure/docker/` e `docker-compose.yml` saem da estrutura planejada;
  - o `docs/RUNNING.md` nasce com a instalação no notebook Windows: versão do Python, ambiente, serviço, build do frontend, portas, Firewall do Windows e IP reservado;
    - **Atualização de 2026-11-10 ([#61](https://github.com/Asuka-Jyuku/kanji-lens/issues/61)):** o [`docs/RUNNING.md`](../RUNNING.md) nasceu antes, com a parte que já roda: o ambiente de desenvolvimento e o acesso pelo celular na rede local. É a regra do `CLAUDE.md`, "Documentos nascem com o assunto": o documento nasce quando a primeira parte roda. A instalação no notebook Windows entra nele depois, com a [#62](https://github.com/Asuka-Jyuku/kanji-lens/issues/62) e a [#63](https://github.com/Asuka-Jyuku/kanji-lens/issues/63). A decisão desta ADR não muda;
  - **o código de backend e de ML precisa rodar no Windows:** os testes cobrem isso, e o CI (#32) inclui um runner Windows ao menos para o backend e o ML;
  - o teste de carga do épico de Infraestrutura roda no notebook com essa instalação;
  - o CI ([#32](https://github.com/Asuka-Jyuku/kanji-lens/issues/32)) roda os testes num runner do GitHub, o que não exige Docker no notebook;
  - **voltar ao Docker pede uma ADR nova**, com medição de RAM e latência no notebook.
