# PWA Album de Figurinhas

App PWA para controle rapido de figurinhas com FastAPI + SQLite e frontend em HTML/Tailwind/Vanilla JS.

## Requisitos

- Python 3.10+

## Como rodar

1. Criar e ativar um ambiente virtual.
2. Instalar dependencias do backend:

   - `pip install -r backend/requirements.txt`

3. Atualizar a lista de selecoes em `backend/data/selections.json` com as 48 selecoes reais.
4. Rodar o seed:

   - `python backend/seed.py`

5. Subir o servidor:

   - `uvicorn backend.main:app --reload`

A aplicacao estara disponivel em `http://localhost:8000`.

## Deploy no Render (Web Service)

1. Suba este repo no GitHub.
2. No Render, crie um Web Service e conecte ao repo.
3. O arquivo `render.yaml` ja contem os comandos de build e start.
4. Configure a env var `DATABASE_URL` (Postgres) no Render.
5. Configure a env var `ADMIN_TOKEN` no Render para habilitar alteracoes protegidas.

Comandos usados:

- Build: `pip install -r backend/requirements.txt`
- Start: `python backend/seed.py && python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

## Banco de dados

- Postgres: defina `DATABASE_URL` (preferido para deploy).
- SQLite: use `ALBUM_DB_PATH` para apontar um arquivo local.
- O seed so roda se a tabela estiver vazia (seguro para re-deploys).

## Notas

- O icone PWA ainda e um placeholder. Substitua em `frontend/icons/icon.svg`.
- O filtro agora usa o campo `group` vindo de `backend/data/selections.json`.
- A bandeira de exemplo esta em `frontend/flags/placeholder.png`.
- A bandeira do Mexico esta em `frontend/flags/mexico.png`.
- Outras bandeiras: `frontend/flags/australia.png`, `frontend/flags/bosnia.png`, `frontend/flags/brasil.png`, `frontend/flags/canada.png`, `frontend/flags/cote.png`, `frontend/flags/czechia.png`, `frontend/flags/ecuador.png`, `frontend/flags/germany.png`, `frontend/flags/haiti.png`, `frontend/flags/japan.png`, `frontend/flags/korea.png`, `frontend/flags/morocco.png`, `frontend/flags/netherlands.png`, `frontend/flags/paraguay.png`, `frontend/flags/qatar.png`, `frontend/flags/scotland.png`, `frontend/flags/south_africa.png`, `frontend/flags/sweden.png`, `frontend/flags/switzerland.png`, `frontend/flags/tunisia.png`, `frontend/flags/turkey.png`, `frontend/flags/usa.png`.
