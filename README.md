# NT Scraper

O **NT Scraper** coleta notícias de tecnologia de diferentes fontes, organiza os registros em um banco PostgreSQL e publica as novidades em um canal do Telegram. Uma etapa com IA também transforma as notícias pendentes em um roteiro diário, que pode ser aberto no NotebookLM para gerar um áudio.

O projeto é voltado a quem quer acompanhar tecnologia em um só lugar e também serve como estudo de Python, web scraping, APIs, automação, bancos de dados e inteligência artificial.

## Como funciona

1. O GitHub Actions executa os scrapers do **Tecnoblog**, **BleepingComputer** e **The Hacker News** diariamente às 06:00 no horário de Brasília (09:00 UTC).
2. Playwright coleta título, fonte, data, resumo e link. A URL única evita duplicar notícias que ainda estejam no banco.
3. As notícias novas são armazenadas no PostgreSQL e enviadas ao canal do Telegram com os botões **Já li**, **Rejeitar** e **Gerar roteiro**.
4. **Já li** altera o status para `lida` e define a remoção para três dias depois; se clicar novamente, o bot avisa que a notícia já foi lida. **Rejeitar** apaga a publicação e remove o registro. Se a publicação já não existir no Telegram, o registro também é removido; em outros erros, ele fica salvo para nova tentativa.
5. **Gerar roteiro** envia somente a notícia daquele botão ao Gemini, que cria um roteiro de podcast. Ao final do roteiro, o bot publica o botão do NotebookLM para você copiar o roteiro e gerar o podcast manualmente.

O workflow diário faz a coleta sem chamar o Gemini. A geração só começa quando alguém toca em **Gerar roteiro** na notícia desejada. Cada acionamento gera o roteiro usando apenas aquela notícia, que continua salva no banco. Depois de copiar o roteiro e abrir o NotebookLM pelo botão enviado ao final, você inicia a geração do podcast. Se já houver roteiro, o bot informa que ele já foi gerado. Notícias com `remover_em` vencido são apagadas do Telegram e do banco pela limpeza diária; registros sem prazo continuam salvos. Se o Telegram retornar um erro diferente de publicação ausente durante a limpeza, o registro fica salvo para nova tentativa.

## Tecnologias

- Python, FastAPI e SQLAlchemy
- Playwright para coleta das páginas
- PostgreSQL, com suporte ao Supabase
- Telegram Bot API
- Google Gemini API para gerar o roteiro
- GitHub Actions para agendar a rotina
- Docker para executar a API e o PostgreSQL

## Configuração local

### 1. Criar e ativar o ambiente Python

```bash
python -m venv venv
```

No Windows:

```powershell
venv\Scripts\Activate.ps1
```

No Linux ou macOS:

```bash
source venv/bin/activate
```

Instale os pacotes e o Chromium usado pelo Playwright:

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configurar credenciais

Copie `.env.example` para `.env` e substitua os valores de exemplo:

```env
API_TOKEN=token_do_bot_telegram
DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/nt_scraper
GEMINI_API_KEY=sua_chave_google_ai
ID_CANAL=-1001234567890
```

No Windows, use `Copy-Item .env.example .env`; no Linux ou macOS, use `cp .env.example .env`. `DATABASE_URL`, `API_TOKEN`, `ID_CANAL` e `GEMINI_API_KEY` são necessários para os respectivos recursos. `GEMINI_MODEL` é opcional e usa `gemini-3.5-flash` como padrão. `NOTEBOOKLM_URL` é opcional; configure-a no `.env` com o endereço do notebook que deve abrir pelo botão do Telegram.

Para obter o bot e o token, converse com [@BotFather](https://t.me/BotFather), crie um bot e adicione-o como administrador do canal, com permissão para publicar mensagens. Use o ID do canal em `ID_CANAL`.

### 3. Preparar o banco

Configure o PostgreSQL localmente ou use o serviço do Supabase. Para criar as tabelas e atualizar um banco já existente:

```bash
python -m backend.scripts.run_create_database
```

Esse comando cria as tabelas ausentes e adiciona, de forma idempotente, a coluna `roteiro_gerado_em` usada para evitar repetir notícias em roteiros futuros.

### 4. Executar a aplicação

Inicie a API e o endpoint do webhook:

```bash
uvicorn backend.main:app --reload
```

O endpoint de saúde está em `/`. O webhook recebe atualizações em `POST /telegram/webhook`. A variável `WEBHOOK_URL` pode conter o domínio público da aplicação; o script acrescenta `/telegram/webhook` ao configurar o Telegram e habilita os tipos `message` e `callback_query` necessários aos botões. Execute esse script depois de implantar a aplicação ou alterar a configuração do webhook. A raiz também aceita `POST` para manter compatibilidade com webhooks que já foram cadastrados apontando para `/`.

```bash
python -m backend.scripts.set_webhook
```

Execute a coleta, o envio das notícias ou o roteiro manualmente:

```bash
python -m backend.scripts.run_scraper
python -m backend.scripts.run_roteiro
python -m backend.scripts.run_cleanup
```

## Execução automática no GitHub

O workflow `scraper_nt.yml` prepara o banco, coleta e publica notícias e executa a limpeza. Ele roda diariamente às 09:00 UTC (06:00 em Brasília) e também pode ser iniciado manualmente. A geração do relatório é acionada pelo botão no Telegram.

Cadastre nos **Secrets** do repositório:

- `DATABASE_URL`
- `API_TOKEN`
- `ID_CANAL`
- `GEMINI_API_KEY`

`NOTEBOOKLM_URL` e `GEMINI_MODEL` podem ser configuradas como variáveis de repositório ou adicionadas ao workflow se precisar substituir os padrões.

Há também um workflow separado para a limpeza diária às 05:00 no horário de Brasília. Ele pode ser usado independentemente do fluxo principal.

## Estrutura principal

```text
.
├── backend/
│   ├── api/routes/       # Webhook do Telegram
│   ├── bot/              # Envio de mensagens e ações do canal
│   ├── database/
│   │   ├── crud/         # Persistência e consultas das notícias
│   │   ├── models.py     # Modelo da notícia
│   │   └── session.py    # Conexão com PostgreSQL
│   ├── scrapers/tecnologia/
│   │   ├── bleepingcomputer/
│   │   ├── tecnoblog/
│   │   └── the_hacker_news/
│   ├── services/
│   │   ├── gerador_roteiro.py
│   │   └── limpeza_noticias.py
│   ├── scripts/          # Comandos para coleta, roteiro e manutenção
│   └── scheduler/        # Tarefas agendadas pelo backend
├── .github/workflows/    # Rotinas agendadas
└── .env.example          # Modelo das variáveis locais
```

## Observações

- O scraping depende da estrutura das páginas das fontes e pode precisar de ajustes quando elas mudarem.
- Use a ferramenta respeitando os termos de uso e as políticas dos sites consultados.
- Não versione `.env`, tokens, chaves de API ou a pasta `venv`.

## Licença

Este projeto está licenciado sob a licença MIT. Consulte [LICENSE](LICENSE).

## Autor

**Denis Goes** — [GitHub](https://github.com/DenisGoes)
