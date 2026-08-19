from playwright.sync_api import sync_playwright
from backend.database.crud.crud_tecnoblog import salvar_noticia
from backend.database.models import Noticias
from backend.bot.telegram import enviar_noticias

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://tecnoblog.net/")  # Ir para página da tecnoblog
        # page.wait_for_timeout(5000) #Esperar 5 segundos

        cards = page.locator(".article-destaque")

        for i in range(cards.count()):
            try:
                card = cards.nth(i)

                titulo = card.locator(".texts h2").inner_text()
                print(titulo)

                fonte = "Tecnoblog"

                data_publicacao = card.locator(".info time").inner_text()
                print(data_publicacao)

                link = card.locator("a").get_attribute("href")
                print(link)

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
