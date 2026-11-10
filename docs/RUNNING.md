# Como rodar o KanjiLens

O passo a passo para rodar o KanjiLens numa máquina de desenvolvimento e abrir pelo celular na rede local. Os comandos de teste, lint e build ficam no [`CLAUDE.md`, "Comandos"](../CLAUDE.md#comandos); aqui fica a ordem para pôr tudo de pé.

**O que roda hoje:**
- **API:** recebe o desenho, põe o job na fila e devolve o resultado por `GET` e por SSE, ainda com um reconhecedor falso, que sempre responde 日, 目 e 白 ([ARCHITECTURE.md, seção 5](ARCHITECTURE.md#5-comunicação-entre-frontend-e-backend)).
- **Frontend:** mostra a escolha do modo e o canvas; "Reconhecer" envia o desenho para a API, acompanha o job pelo SSE e mostra o candidato mais provável ([#58](https://github.com/Asuka-Jyuku/kanji-lens/issues/58)). A lista completa de candidatos é a [#59](https://github.com/Asuka-Jyuku/kanji-lens/issues/59). No build de desenvolvimento, há também a exportação do desenho em JSON ([#66](https://github.com/Asuka-Jyuku/kanji-lens/issues/66)).

A instalação no notebook da escola (Windows, serviço do sistema, build estático, IP reservado) entra depois, com a [#62](https://github.com/Asuka-Jyuku/kanji-lens/issues/62) e a [#63](https://github.com/Asuka-Jyuku/kanji-lens/issues/63).

## 1. Pré-requisitos

| Ferramenta | Versão | Para quê |
|---|---|---|
| [git](https://git-scm.com/) | qualquer recente | clonar o repositório |
| [uv](https://docs.astral.sh/uv/) | a atual | Python do ML e do backend; ele mesmo baixa o Python 3.15 (`.python-version`) |
| Node.js | **26** (`frontend/.nvmrc`; `engines` do `package.json`) | frontend Angular |

**uv:** siga o [instalador oficial](https://docs.astral.sh/uv/getting-started/installation/). No Linux e no macOS ele vai para `~/.local/bin`; confira que essa pasta está no `PATH` (`uv --version` num terminal novo).

**Node 26:** a versão do sistema costuma ser outra (no Arch/CachyOS, o pacote `nodejs-lts` é a 22). Use um gerenciador de versões que leia o `.nvmrc`:
- **[fnm](https://github.com/Schniz/fnm)** (Linux, macOS e Windows): `fnm install 26`, e ative no shell conforme o README do fnm (`fnm env --use-on-cd`), para trocar de versão sozinho ao entrar em `frontend/`;
- **[nvm](https://github.com/nvm-sh/nvm):** `nvm install` e `nvm use` dentro de `frontend/`.

O `.nvmrc` fica em `frontend/`, não na raiz. `fnm use` ou `nvm use` rodados na raiz não acham o arquivo; rode dentro de `frontend/` ou diga a versão (`fnm use 26`). Confira com `node --version` (`v26.x`).

## 2. Instalar

```bash
git clone https://github.com/Asuka-Jyuku/kanji-lens.git
cd kanji-lens
uv sync --all-packages          # Python 3.15, backend e ML (PyTorch só-CPU), pelo uv.lock
cd frontend
npm ci                          # dependências do frontend, pelo package-lock.json
cd ..
```

O `npm ci` avisa que alguns pacotes têm scripts de instalação que não foram aprovados (`npm warn install-scripts`, para `esbuild`, `lmdb` e outros). É só um aviso: o servidor de desenvolvimento e o build funcionam assim.

## 3. Subir a API

Da raiz do repositório:

```bash
uv run --directory backend uvicorn kanjilens.bootstrap.app:create_app --factory --reload
```

A API fica em `http://127.0.0.1:8000`. O Uvicorn roda com **um processo só**, sem `--workers`, porque a fila fica em memória ([ADR 0019](adr/0019-in-memory-job-queue-with-one-inference-process.md)).

## 4. Subir o frontend

Noutro terminal, dentro de `frontend/`:

```bash
npm start
```

O frontend fica em `http://localhost:4200`. O `ng serve` encaminha `/api` para a API em `http://127.0.0.1:8000` (`frontend/proxy.conf.mjs`), então o navegador fala só com a porta 4200 e não há CORS. API noutro endereço ou porta? Aponte o proxy com a variável `KANJILENS_API_URL`:

```bash
KANJILENS_API_URL=http://127.0.0.1:8001 npm start
```

O aviso `Locale data for 'pt-BR' cannot be found. Using locale data for 'pt'` é esperado e não muda nada na tela.

## 5. Conferir que está tudo de pé

```bash
curl http://127.0.0.1:8000/api/health
# {"status":"ok"}

curl -X POST http://127.0.0.1:8000/api/recognitions \
  -H 'Content-Type: application/json' \
  -d '{"stroke_order_mode":"unordered","canvas":{"width":320,"height":320},"strokes":[[[40,40,0],[200,40,120]],[[120,10,400],[120,300,600]]]}'
# 202 {"job_id":"<id>","status":"queued"}

curl http://127.0.0.1:8000/api/recognitions/<id>          # o estado do job, com as previsões do reconhecedor falso
curl -N http://127.0.0.1:8000/api/recognitions/<id>/events  # o mesmo pelo SSE (Ctrl+C para sair)
```

Pelo proxy do frontend, a mesma API responde na porta 4200:

```bash
curl http://localhost:4200/api/health
# {"status":"ok"}
```

Abra `http://localhost:4200` no navegador: o título, a escolha "Ordem dos traços" e o canvas aparecem. Desenhe e toque em "Reconhecer": a tela mostra "Na fila" e depois "Mais provável: 日", a resposta do reconhecedor falso. Com a API parada, ela diz "Sem conexão com o servidor".

## 6. Referências do KanjiVG (opcional)

A avaliação da ordem dos traços compara o desenho com o [KanjiVG](https://kanjivg.tagaini.net/). A API ainda não usa essas referências (a ligação é a [#48](https://github.com/Asuka-Jyuku/kanji-lens/issues/48)); elas servem hoje para o ML e o benchmark. Da raiz:

```bash
uv run --directory ml python scripts/prepare_kanjivg.py          # baixa o KanjiVG r20260714, confere o SHA-256 e gera as referências
uv run --directory ml python scripts/benchmark_stroke_order.py   # mede a avaliação da ordem em desenhos sintéticos
```

O arquivo baixado fica em `ml/datasets/kanjivg/` (12 MB), e as referências em `ml/artifacts/kanjivg/` (20 MB), as duas pastas fora do git. O KanjiVG é © Ulrich Apel, sob [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/); o `README.md` gerado junto das referências mantém a atribuição. Detalhes e números no [docs/MODEL.md](MODEL.md#avaliação-da-ordem-dos-traços).

## 7. Abrir pelo celular na rede local

O celular e a máquina precisam estar na mesma rede. Qualquer um nessa rede alcança o app, sem login ([ARCHITECTURE.md, 6.2](ARCHITECTURE.md#62-exposição-na-rede-local)).

1. **Suba o frontend escutando na rede**, não só em `localhost`. A API continua como na seção 3, só em `127.0.0.1`: o celular chega a ela pelo proxy de `/api` do frontend, e ela fica fechada para a rede ([docs/SECURITY.md](SECURITY.md)).

   ```bash
   uv run --directory backend uvicorn kanjilens.bootstrap.app:create_app --factory --reload   # da raiz, como na seção 3
   npm start -- --host 0.0.0.0      # dentro de frontend/
   ```

   O `ng serve` mostra os endereços em `Network:`; use o da interface da rede local (Wi‑Fi ou cabo, por exemplo `192.168.15.114`), não o de redes virtuais do Docker.
2. **Libere a porta 4200 no firewall**, só para a rede local; a 8000 não precisa. No Linux com o `ufw`:

   ```bash
   sudo ufw allow from 192.168.15.0/24 to any port 4200 proto tcp   # troque pela faixa da sua rede
   ```

   Ao terminar, tire a regra:

   ```bash
   sudo ufw delete allow from 192.168.15.0/24 to any port 4200 proto tcp
   ```

   No Windows, o Firewall do Windows pergunta na primeira vez que o Node escuta na rede: libere só para **redes privadas**.
3. **No celular**, abra `http://<IP da máquina>:4200`.

Desenhe e toque em "Reconhecer" no celular: o pedido vai para `http://<IP da máquina>:4200/api/...`, e o `ng serve` o repassa à API na própria máquina.

## 8. Problemas comuns

**`node --version` não mostra a 26:** o gerenciador de versões não foi ativado nesse shell ou não achou o `.nvmrc` (ele fica em `frontend/`). Rode `fnm use 26` (ou `nvm use` dentro de `frontend/`) e confira de novo. Num terminal novo, a ativação depende da linha do fnm ou do nvm no arquivo de configuração do shell.

**`uv: command not found` depois de instalar:** `~/.local/bin` não está no `PATH` desse shell. Abra um terminal novo ou acrescente a pasta ao `PATH`.

**`warning: VIRTUAL_ENV=... does not match the project environment path`:** há outro ambiente Python ativado no shell (de outro clone, por exemplo). O uv ignora esse ambiente e usa o `.venv` do projeto; para o aviso sumir, rode `deactivate`.

**`Address already in use`:** outro processo já usa a porta. Pare o servidor antigo ou suba noutra porta (`--port 8001` no Uvicorn, com `KANJILENS_API_URL=http://127.0.0.1:8001` no `npm start`; `npm start -- --port 4201`).

**A tela diz "Sem conexão com o servidor":** o frontend abriu, mas o proxy não alcança a API. Confira se a API está de pé (`curl http://127.0.0.1:8000/api/health`) e, se ela estiver noutra porta, se o `KANJILENS_API_URL` aponta para ela.

**O celular não abre a página** (`ERR_CONNECTION_TIMED_OUT`, `ERR_TOO_MANY_RETRIES`, ou carrega para sempre):
1. **Confira o básico:** na própria máquina, `http://<IP da máquina>:4200` abre? O frontend foi subido com `--host 0.0.0.0`? A regra do firewall cobre a porta e a faixa da rede?
2. **Confira se o pedido chega à máquina.** No Linux, enquanto o celular tenta abrir:
   - com o `ufw`, `sudo ufw logging on` e depois `sudo journalctl -kf | grep 'UFW BLOCK'`: uma linha com `DPT=4200` é o firewall barrando, então a regra da seção 7 não cobre a faixa do celular;
   - ou, com o `tcpdump` instalado, `sudo tcpdump -ni any tcp port 4200`.

   Nem bloqueio nem pacote? O problema está antes da máquina, na rede ou no celular:
   - **o celular está noutra rede:** o IP dele precisa estar na mesma faixa da máquina (por exemplo `192.168.15.x`). Rede de convidados é outra faixa;
   - **isolamento de clientes** (*client isolation* / *AP isolation*): muitas redes de convidados, e algumas redes de escola, impedem que um aparelho fale com outro. Teste noutra rede ou peça para desligar;
   - **VPN, DNS privado ou dados móveis** no celular desviam o tráfego: desligue os três para testar.
3. **Contorno pelo cabo USB (Android):** com a depuração USB ligada no celular e o `adb` instalado (pacote `android-tools`), `adb reverse tcp:4200 tcp:4200` faz o `http://localhost:4200` do celular chegar à máquina, sem passar pela rede. Serve para testar o toque, não a rede da escola.

## O que ainda não está aqui

- **Quem serve o build estático em produção e como a API roda como serviço no Windows:** [#62](https://github.com/Asuka-Jyuku/kanji-lens/issues/62).
- **Instalação no notebook da escola**, com o Firewall do Windows e o IP reservado: [#63](https://github.com/Asuka-Jyuku/kanji-lens/issues/63).
- **Acesso pelo Wi‑Fi da escola:** [#64](https://github.com/Asuka-Jyuku/kanji-lens/issues/64).
