# NT Scraper

<!--Badges -->

> NT Scraper é um sistema de busca e coleta automatizada de notícias de tecnologia, de diferentes fontes, como **hacker news**, **Tecnoblog** e outras fontes. <br> Desenvolvido para pessoas que gostam de tecnologia, leitura e que desejam se manter atualizadas sobre as principais notícias do setor.

## 📌 Sobre
O **NT Scraper** é um sistema desenvolvido para buscar, extrair, armazenar e distribuir notícias de tecnologia em um único local: **Telegram**.

Tem por objetivo, diminuir o tempo gasto de pesquisa por notícias, automatizando todo o processo e reunindo as notícias em um canal do Telegram, permitindo a leitura em qualquer lugar que o entusiasta esteja.

O projeto foi criado inicialmente para solucionar uma necessidade pessoal e também como um projeto de estudo e hobby, com foco em **Python, web scraping, automação, APIs, bancos de dados e desenvolvimento backend**.


<!-- ## 🏗 Arquitetura

--- -->

## ✨ Funcionalidades
- Acessar diferentes fontes de notícias de tecnologia
- Extrair automaticamente as informações das notícias
- Armazenar as notícias no banco de dados
- Gerenciamento das notícias
- Enviar notícias formatadas para o Telegram
- Executar o scraper todos os dias, às 06:00
- Disponibilizar um WebHook para integração com o Telegram


## 🛠 Tecnologias
- Python - linguagem principal do projeto
- FastAPI - desenvolvimento da API e do WebHook
- Playwright - automação do navegador e web scraping
- PostgreSQL - armazenamento das notícias
- SQLAlchemy - ORM para comunicação com o banco de dados
- Telegram Bot API - envio de notícias e interação com o Telegram
- GitHub Actions - automação da execução do scraper e integração contínua
- Docker - conteinerização da aplicação
- Render - hospedagem do WebHook
- Supabase - hospedagem do banco de dados PostgreSQL


<!-- ## Versões -->



## 📂 Estrutura do Projeto

```markdown
Projeto
├── backend
│   ├── api
│   │   └── routes
│   ├── bot
│   │   └── telegram.py
│   ├── database
│   │   ├── crud
│   │   ├── models.py
│   │   └── session.py
│   ├── main.py
│   │   └── main.cpython-314.pyc
│   ├── scheduler
│   │   ├── jobs.py
│  
│   ├── scrapers
│   │   ├── investimentos
│   │   └── tecnologia
│   ├── scripts
│   │   ├── run_cleanup.py
│   │   ├── run_create_database.py
│   │   ├── run_tecnoblog.py
│   │   └── set_webhook.py
│   └── services
│       ├── clean_db.py
│ 
├── docker-compose.yml
├── Dockerfile
├── docs
├── estrutura_projeto.txt
├── LICENSE
├── README.md
├── requirements.txt
└── venv
```
>Observação: a pasta **venv** não deve ser versionada no Git. Ela deve ser adicionada no **.gitignore**.


## ⚙ Deploy

- GitHub - Workflow cron, executando o scraper todos os dias às 06:00
- Render - hospedagem da API responsável pelo WebHook
- Supabase - Hospedagem banco de dados postgreSQL

## 🚀 Como usar

### 1. Configurar o Telegram

1. Baixe o Telegram em seu smartphone ou utilize a versão Web/Desktop.
2. Crie uma conta ou faça login.
3. Pesquise por **@BotFather** e inicie uma conversa.
4. Execute o comando `/newbot`.
5. Escolha um nome e um **username** para o bot.
6. Ao final, o BotFather fornecerá um **Token de Acesso**. Guarde esse token.
7. Crie um canal no Telegram.
8. Adicione o bot criado como **Administrador** do canal, concedendo permissão para enviar mensagens.
9. Obtenha o **ID do canal** (utilizado pelo sistema para enviar as notícias).

### 1.1 Obter o id do Canal
1. Envie uma mensagem no canal
2. Abra o navegador e acesse: https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
3. Na resposta JSON, procure pelo campo chat id.

### 2. Configurar as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto.
Utilize o arquivo .env.example como referência para configurar as variáveis necessárias.

### 3. Configurar o sistema

Clone o projeto
```markdown
git clone https://github.com/DenisGoes/scraping-noticias.git
```
Crie o ambiente virtual
```markdown
python -m venv venv
```

Ative o ambiente virtual<br>

Windowns
```markdown
venv\Scripts\activate
```

Linux
```markdown
source venv/bin/activate
```

Instale todas as dependecias
``` markdown
pip install -r requirements.txt
```
Crie o banco de dados:

```bash
python -m backend.scripts.run_create_database
```

Inicie a API:

```bash
uvicorn backend.main:app --reload
```

### 4. Executar os scrapers

```bash
python -m backend.scripts.run_scraper
```

Após a execução, as notícias encontradas serão:

* armazenadas no banco de dados;
* enviadas automaticamente para o canal do Telegram configurado.

## 📖 Documentação

A documentação completa está em: 
```markdown
docs/
```
*A documentação se encontra em desenvolvimento!*

<!-- ## 🤝 Contribuindo -->

## 👨‍💻 Autor

**Denis Goes**

GitHub: https://github.com/DenisGoes

<!-- Portfólio:  -->

## 📄 Licença
*Este projeto está licenciado sob a licença MIT.* 

## Aviso
*Este projeto foi desenvolvido para fins educacionais e de estudo sobre automação e web scraping. O uso da ferramenta deve respeitar os termos de uso e as políticas das plataformas acessadas. O autor não se responsabiliza pelo uso inadequado do software.*

## Agradecimentos

Obrigado por utilizar o NT Scraper!

Este projeto foi desenvolvido com o objetivo de facilitar a busca por notícias de tecnologia e, servir como um projeto de estudo.

Todo feedback é muito bem-vindo.

Se este projeto foi útil para você, considere deixar uma ⭐ no repositório para apoiar seu desenvolvimento.