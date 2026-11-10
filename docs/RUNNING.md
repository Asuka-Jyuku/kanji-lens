# Como rodar o KanjiLens

Como pôr o KanjiLens de pé numa máquina de desenvolvimento e abrir pelo celular na rede local. Os comandos de teste, lint e build estão no [`CLAUDE.md`, "Comandos"](../CLAUDE.md#comandos).

**O que roda hoje:**
- **API:** recebe o desenho, põe o job na fila e devolve o resultado por `GET` e SSE. O reconhecedor ainda é falso: sempre responde 日, 目 e 白.
- **Frontend:** escolha do modo, canvas e "Reconhecer", que mostra o candidato mais provável. No build de desenvolvimento, também a exportação do desenho em JSON.

A instalação no notebook da escola vem depois ([#62](https://github.com/Asuka-Jyuku/kanji-lens/issues/62), [#63](https://github.com/Asuka-Jyuku/kanji-lens/issues/63)).

## 1. Pré-requisitos

| Ferramenta | Versão | Para quê |
|---|---|---|
| [git](https://git-scm.com/) | recente | clonar o repositório |
| [uv](https://docs.astral.sh/uv/) | a atual | Python do ML e do backend; ele baixa o Python 3.15 sozinho |
| Node.js | **26** (`frontend/.nvmrc`) | frontend |

- **uv:** use o [instalador oficial](https://docs.astral.sh/uv/getting-started/installation/). No Linux e no macOS ele vai para `~/.local/bin`; essa pasta precisa estar no `PATH` (teste com `uv --version` num terminal novo).
- **Node 26:** o do sistema costuma ser outro (no Arch/CachyOS, o `nodejs-lts` é o 22). Use um gerenciador de versões:
  - **[fnm](https://github.com/Schniz/fnm):** `fnm install 26`, e ative no shell com `fnm env --use-on-cd`;
  - **[nvm](https://github.com/nvm-sh/nvm):** `nvm install` e `nvm use` dentro de `frontend/`.
- O `.nvmrc` fica em `frontend/`, não na raiz. Na raiz, use `fnm use 26`. Confira com `node --version` (`v26.x`).

## 2. Instalar

```bash
git clone https://github.com/Asuka-Jyuku/kanji-lens.git
cd kanji-lens
uv sync --all-packages          # Python 3.15, backend e ML (PyTorch só-CPU)
cd frontend
npm ci                          # dependências do frontend
cd ..
```

O `npm ci` avisa `npm warn install-scripts` (para `esbuild`, `lmdb` e outros). Pode ignorar.

## 3. Subir a API

Da raiz:

```bash
uv run --directory backend uvicorn kanjilens.bootstrap.app:create_app --factory --reload
```

A API fica em `http://127.0.0.1:8000`. Rode **um processo só** (sem `--workers`), porque a fila fica em memória.

## 4. Subir o frontend

Noutro terminal, dentro de `frontend/`:

```bash
npm start
```

O frontend fica em `http://localhost:4200`. O `ng serve` passa `/api` para a API em `http://127.0.0.1:8000` (`frontend/proxy.conf.mjs`), então o navegador só fala com a porta 4200 e não há CORS. Se a API estiver noutra porta, use `KANJILENS_API_URL`:

```bash
KANJILENS_API_URL=http://127.0.0.1:8001 npm start
```

O aviso `Locale data for 'pt-BR' cannot be found. Using locale data for 'pt'` é esperado.

## 5. Conferir que está tudo de pé

```bash
curl http://127.0.0.1:8000/api/health
# {"status":"ok"}

curl -X POST http://127.0.0.1:8000/api/recognitions \
  -H 'Content-Type: application/json' \
  -d '{"stroke_order_mode":"unordered","canvas":{"width":320,"height":320},"strokes":[[[40,40,0],[200,40,120]],[[120,10,400],[120,300,600]]]}'
# 202 {"job_id":"<id>","status":"queued"}

curl http://127.0.0.1:8000/api/recognitions/<id>          # o estado do job
curl -N http://127.0.0.1:8000/api/recognitions/<id>/events  # o mesmo pelo SSE (Ctrl+C para sair)
```

Pelo proxy do frontend:

```bash
curl http://localhost:4200/api/health
# {"status":"ok"}
```

No navegador, em `http://localhost:4200`: desenhe e toque em "Reconhecer". A tela mostra "Na fila" e depois "Mais provável: 日". Com a API parada, ela diz "Sem conexão com o servidor".

## 6. Referências do KanjiVG (opcional)

A avaliação da ordem compara o desenho com o [KanjiVG](https://kanjivg.tagaini.net/). A API ainda não usa essas referências ([#48](https://github.com/Asuka-Jyuku/kanji-lens/issues/48)); hoje elas servem ao ML e ao benchmark. Da raiz:

```bash
uv run --directory ml python scripts/prepare_kanjivg.py          # baixa o KanjiVG r20260714, confere o SHA-256 e gera as referências
uv run --directory ml python scripts/benchmark_stroke_order.py   # mede a avaliação da ordem em desenhos sintéticos
```

O download fica em `ml/datasets/kanjivg/` (12 MB) e as referências em `ml/artifacts/kanjivg/` (20 MB), fora do git. O KanjiVG é © Ulrich Apel, sob [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/); o `README.md` gerado junto mantém a atribuição. Detalhes no [MODEL.md](MODEL.md#avaliação-da-ordem-dos-traços).

## 7. Abrir pelo celular na rede local

O celular e a máquina precisam estar na mesma rede. Qualquer um nessa rede alcança o app, sem login ([SECURITY.md](SECURITY.md)).

1. **Suba o frontend escutando na rede.** A API continua só em `127.0.0.1`: o celular chega a ela pelo proxy do frontend.

   ```bash
   uv run --directory backend uvicorn kanjilens.bootstrap.app:create_app --factory --reload   # da raiz, como na seção 3
   npm start -- --host 0.0.0.0      # dentro de frontend/
   ```

   O `ng serve` mostra os endereços em `Network:`. Use o da rede local (Wi‑Fi ou cabo, por exemplo `192.168.15.114`), não o do Docker.
2. **Libere só a porta 4200 no firewall**, só para a rede local. No Linux com `ufw`:

   ```bash
   sudo ufw allow from 192.168.15.0/24 to any port 4200 proto tcp   # troque pela faixa da sua rede
   ```

   Ao terminar, tire a regra:

   ```bash
   sudo ufw delete allow from 192.168.15.0/24 to any port 4200 proto tcp
   ```

   No Windows, o firewall pergunta na primeira vez que o Node escuta na rede: libere só para **redes privadas**.
3. **No celular**, abra `http://<IP da máquina>:4200`. O "Reconhecer" chama `http://<IP da máquina>:4200/api/...`, e o `ng serve` repassa à API.

## 8. Problemas comuns

- **`node --version` não mostra a 26:** o gerenciador não foi ativado nesse shell ou não achou o `.nvmrc`. Rode `fnm use 26` (ou `nvm use` dentro de `frontend/`). Num terminal novo, a ativação depende da linha do fnm ou do nvm na configuração do shell.
- **`uv: command not found`:** `~/.local/bin` não está no `PATH`. Abra um terminal novo ou acrescente a pasta.
- **`warning: VIRTUAL_ENV=... does not match the project environment path`:** há outro ambiente Python ativo no shell. O uv o ignora; para o aviso sumir, rode `deactivate`.
- **`Address already in use`:** a porta está ocupada. Pare o servidor antigo ou use outra porta: `--port 8001` no Uvicorn (com `KANJILENS_API_URL=http://127.0.0.1:8001` no `npm start`) ou `npm start -- --port 4201`.
- **A tela diz "Sem conexão com o servidor":** o proxy não alcança a API. Confira se ela está de pé (`curl http://127.0.0.1:8000/api/health`) e se o `KANJILENS_API_URL` aponta para a porta certa.

**O celular não abre a página** (`ERR_CONNECTION_TIMED_OUT`, `ERR_TOO_MANY_RETRIES` ou carrega para sempre):
1. **O básico:** na própria máquina, `http://<IP da máquina>:4200` abre? O frontend subiu com `--host 0.0.0.0`? A regra do firewall cobre a porta e a faixa da rede?
2. **O pedido chega à máquina?** No Linux, enquanto o celular tenta abrir:
   - com `ufw`: `sudo ufw logging on` e `sudo journalctl -kf | grep 'UFW BLOCK'`. Uma linha com `DPT=4200` é o firewall barrando: a regra não cobre a faixa do celular;
   - ou, com `tcpdump`: `sudo tcpdump -ni any tcp port 4200`.

   Nem bloqueio nem pacote? O problema está na rede ou no celular:
   - **outra rede:** o IP do celular precisa estar na mesma faixa (por exemplo `192.168.15.x`). Rede de convidados é outra faixa;
   - **isolamento de clientes** (*client isolation* / *AP isolation*): muitas redes de convidados, e algumas de escola, impedem um aparelho de falar com outro. Teste noutra rede ou peça para desligar;
   - **VPN, DNS privado ou dados móveis** no celular desviam o tráfego: desligue os três para testar.
3. **Contorno pelo cabo USB (Android):** com a depuração USB ligada e o `adb` instalado (pacote `android-tools`), `adb reverse tcp:4200 tcp:4200` faz o `http://localhost:4200` do celular chegar à máquina, sem passar pela rede. Serve para testar o toque, não a rede da escola.

## O que ainda não está aqui

- Quem serve o build em produção e como a API roda como serviço no Windows: [#62](https://github.com/Asuka-Jyuku/kanji-lens/issues/62).
- Instalação no notebook da escola, com firewall e IP reservado: [#63](https://github.com/Asuka-Jyuku/kanji-lens/issues/63).
- Acesso pelo Wi‑Fi da escola: [#64](https://github.com/Asuka-Jyuku/kanji-lens/issues/64).
