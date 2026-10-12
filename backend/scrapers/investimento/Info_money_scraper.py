from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

from backend.bot.telegram import enviar_noticias
from backend.database.crud.noticias import salvar_noticia


URLS = (
    "https://www.infomoney.com.br/onde-investir/",
    "https://www.infomoney.com.br/tudo-sobre/trader/",
    "https://www.infomoney.com.br/mercados/",
    "https://www.infomoney.com.br/tudo-sobre/criptomoedas/",
)
URL_MERCADOS = "https://www.infomoney.com.br/mercados/"
SELETOR_CARDS = ', '.join(
    f'[data-ds-component="{tipo}"]' for tipo in ("card-xl", "card-lg", "card-sm")
)
SELETOR_CARREGAR_MAIS = (
    'section[data-ds-component="load-more-cards"] '
    'button[data-ds-variant="secondary"]'
)
CLICKS_CARREGAR_MAIS = 4
ESPERA_APOS_CLIQUE_MS = 10_000


def _texto(card, seletor, padrao=""):
    elemento = card.locator(seletor).first
    if elemento.count() == 0:
        return padrao
    return elemento.inner_text().strip()


def _clicar_carregar_mais(page, url):
    if url != URL_MERCADOS:
        return

    for numero in range(1, CLICKS_CARREGAR_MAIS + 1):
        botao = page.locator(SELETOR_CARREGAR_MAIS).filter(has_text="Carregar mais").first
        if botao.count() == 0 or not botao.is_enabled():
            print(f"Botão 'Carregar mais' indisponível após {numero - 1} clique(s).")
            break

        try:
            botao.scroll_into_view_if_needed(timeout=10_000)
            botao.click(timeout=10_000)
            print(f"Clique {numero}/{CLICKS_CARREGAR_MAIS} em 'Carregar mais'; aguardando 10 segundos.")
            page.wait_for_timeout(ESPERA_APOS_CLIQUE_MS)
        except Exception as erro:
            print(f"Falha no clique {numero} de 'Carregar mais': {erro}")
            break


def _coletar_pagina(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_selector(SELETOR_CARDS, timeout=30000)
    except Exception as erro:
        print(f"Cards do InfoMoney não apareceram em {url}: {erro}")
        return

    _clicar_carregar_mais(page, url)

    cards = page.locator(SELETOR_CARDS)
    quantidade = cards.count()
    print(f"Cards do InfoMoney em {url}: {quantidade}")

    for i in range(quantidade):
        try:
            card = cards.nth(i)
            categoria = _texto(
                card,
                "div.line-clamp-1 > a > div",
                "Categoria não informada",
            )
            titulo_locator = card.locator("h2 > a").first
            if titulo_locator.count() == 0:
                print(f"Card {i + 1} ignorado: título não encontrado.")
                continue

            titulo = titulo_locator.inner_text().strip()
            link = titulo_locator.get_attribute("href")
            data_publicacao = _texto(
                card,
                "div.mt-3 > div.inline-flex",
                "Data não informada",
            )

            if not titulo or not link:
                print(f"Card {i + 1} ignorado: título ou link ausente.")
                continue

            link = urljoin(url, link)
            fonte = "InfoMoney"
            mensagem = (
                "🔥 <b>Nova notícia encontrada!</b>\n\n"
                f"🏷️ <b>Categoria:</b> {categoria}\n"
                f"📌 <b>{titulo}</b>\n"
                f"🏢 {fonte}\n"
                f"📅 {data_publicacao}\n"
                f"🔗 {link}\n"
            )

            print(
                f"Categoria: {categoria} | Título: {titulo} | "
                f"Data: {data_publicacao} | Link: {link}"
            )
            salvar_noticia(
                titulo=titulo,
                fonte=fonte,
                data_publicacao=data_publicacao,
                resumo=f"Categoria: {categoria}",
                link=link,
                mensagem=mensagem,
            )
        except Exception as erro:
            print(f"Erro ao processar card {i + 1} de {url}: {erro}")


def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for url in URLS:
            _coletar_pagina(page, url)

        browser.close()

    enviar_noticias()

