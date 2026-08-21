from playwright.sync_api import sync_playwright
from backend.database.crud.crud_tecnoblog import salvar_noticia
from backend.bot.telegram import enviar_noticias

def run_scraper_bleeping():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )
        page = browser.new_page()

        page.goto("https://www.bleepingcomputer.com/", wait_until="domcontentloaded")

        cards = page.locator("#bc-home-news-main-wrap > li")

        print(f"Cards encontrados: {cards.count()}")

        for i in range(cards.count()):
            try:
                card = cards.nth(i)

                titulo = card.locator(".bc_latest_news_text h4").inner_text()
                # print(titulo)

                fonte = "bleepingcomputer"

                data_publicacao = card.locator(".bc_news_date").inner_text()
                # print(data_publicacao)

                link = card.locator(".bc_latest_news_text h4 a").get_attribute("href")
                # print(link)

                mensagem = (
                    "🔥 <b>Nova notícia encontrada!</b>\n\n"
                    f"📌 <b>{titulo}</b>\n"
                    f"🏢 {fonte}\n"
                    f"📍 {data_publicacao}\n"
                    f"📅 {link}\n"
                )
                
                print(f"""
                    Titulo: {titulo}
                    Fonte: {fonte}
                    Data publicação: {data_publicacao}
                    Link: {link}
                """)
                
                salvar_noticia(
                    titulo=titulo, 
                    fonte=fonte, 
                    data_publicacao=data_publicacao, 
                    link=link,
                    mensagem=mensagem
                )
            except Exception as e:
                print(f"Algo inesperado aconteceu! {e}")

        browser.close()
    enviar_noticias()