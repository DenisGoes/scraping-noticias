import re
import unicodedata

from backend.bot.telegram import enviar_noticias
from backend.database.crud.noticias import salvar_noticia
from backend.scrapers.rss_reader import ler_feed_rss


URL_FEED = "https://tecnoblog.net/feed/"
LIMITE_NOTICIAS = 20
TERMOS_JOGOS = (
    "videogame",
    "video game",
    "jogo",
    "jogos",
    "game",
    "games",
    "gamer",
    "gaming",
    "nintendo",
    "playstation",
    "xbox",
    "gta",
    "console",
    "consoles",
    "esports",
    "e-sports",
    "steam",
    "game pass",
    "ps5",
    "ps4",
    "ps3",
)


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(caractere for caractere in texto if not unicodedata.combining(caractere))


def _sobre_jogos(titulo):
    titulo_normalizado = _normalizar(titulo)
    return any(
        re.search(rf"\b{re.escape(_normalizar(termo))}\b", titulo_normalizado)
        for termo in TERMOS_JOGOS
    )


def run_scraper_tec():
    noticias_feed = ler_feed_rss(URL_FEED)
    noticias_tecnologia = [
        noticia for noticia in noticias_feed if not _sobre_jogos(noticia["titulo"])
    ]
    noticias = noticias_tecnologia[:LIMITE_NOTICIAS]
    removidas_jogos = len(noticias_feed) - len(noticias_tecnologia)
    print(
        f"Tecnoblog: {len(noticias)} notícias de tecnologia selecionadas; "
        f"{removidas_jogos} notícias sobre jogos filtradas "
        f"(limite: {LIMITE_NOTICIAS})."
    )

    for noticia in noticias:
        titulo = noticia["titulo"]
        fonte = "Tecnoblog"
        data_publicacao = noticia["data_publicacao"]
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
            resumo=noticia["resumo"],
            link=link,
            mensagem=mensagem,
        )

    enviar_noticias()
