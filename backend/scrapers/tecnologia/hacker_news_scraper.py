from backend.bot.telegram import enviar_noticias
from backend.database.crud.noticias import salvar_noticia
from backend.scrapers.rss_reader import ler_feed_rss


LIMITE_NOTICIAS = 10
URL_FEED = "https://thehackernews.com/feeds/posts/default?alt=rss"


def run_scraper_the_hacker_news():
    noticias = ler_feed_rss(URL_FEED)[:LIMITE_NOTICIAS]
    print(
        f"Notícias encontradas no The Hacker News: {len(noticias)} "
        f"(limite: {LIMITE_NOTICIAS})"
    )

    for noticia in noticias:
        titulo = noticia["titulo"]
        fonte = "hacker news"
        data_publicacao = noticia["data_publicacao"]
        resumo = noticia["resumo"]
        link = noticia["link"]
        mensagem = (
            "🔥 <b>Nova notícia encontrada!</b>\n\n"
            f"📌 <b>{titulo}</b>\n"
            f"🏢 {fonte}\n"
            f"📍 {data_publicacao or 'Data não informada'}\n"
            f"🔗 {link}\n"
        )

        print(f"Título: {titulo} | Publicação: {data_publicacao} | Link: {link}")
        salvar_noticia(
            titulo=titulo,
            fonte=fonte,
            data_publicacao=data_publicacao,
            resumo=resumo,
            link=link,
            mensagem=mensagem,
        )

    enviar_noticias()
