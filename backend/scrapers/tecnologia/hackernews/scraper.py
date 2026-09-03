from playwright.sync_api import sync_playwright
from backend.database.crud.crud_tecnoblog import salvar_noticia
from backend.bot.telegram import enviar_noticias


def run_scraper_hacker():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://thehackernews.com/", wait_until="domcontentloaded")

        cards = page.locator(".clear.home-right")
        print(f"Cards encontrados: {cards.count()}")

        for i in range(cards.count()):
            try:
                card = cards.nth(i)

                titulo = card.locator(".home-title").inner_text()
                fonte = "hacker news"

                resumo = card.locator(".home-desc").inner_text()
                print(resumo)

                link_locator = card.locator("xpath=ancestor::a[1]")

                if link_locator.count() == 0:
                    print(f"Card {i} não possui link válido. Título: {titulo}")
                    continue

                link = link_locator.first.get_attribute("href")

                if not link:
                    print(f"Card {i} sem href. Título: {titulo}")
                    continue

                print(f"""
                    Titulo: {titulo}
                    Fonte: {fonte}
                    Resumo: {resumo}
                    Link: {link}
                    """)

                mensagem = (
                    "🔥 <b>Nova notícia encontrada!</b>\n\n"
                    f"📌 <b>{titulo}</b>\n"
                    f"🏢 {fonte}\n"
                    f"🔗 {link}\n"
                )

                salvar_noticia(
                    titulo=titulo,
                    fonte=fonte,
                    data_publicacao=None,
                    resumo=resumo,
                    link=link,
                    mensagem=mensagem,
                )
            except Exception as e:
                print(f"Erro no card {i}: {e}")

        browser.close()

    enviar_noticias()