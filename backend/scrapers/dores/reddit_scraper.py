from html import escape
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from backend.bot.telegram import enviar_noticias
from backend.database.crud.noticias import salvar_noticia


URL_BUSCA = "https://www.reddit.com/search/?q=programming&kwfEligible=1&sort=new"
SELETOR_CARDS = '[data-testid="search-post-unit"]'
SELETOR_TITULO = 'a[data-testid="post-title-text"]'
SELETOR_PUBLICACAO = 'shreddit-post[view-context="CommentsPage"]'
SELETOR_TEXTO_PUBLICACAO = 'shreddit-post-text-body [slot="text-body"]'
LIMITE_TEXTO_TELEGRAM = 2500
LIMITE_PUBLICACOES = 30
USER_AGENT_REDDIT = "Mozilla/5.0 (compatible; NTScraper/1.0; +https://github.com/)"


def _texto(locator, padrao=""):
    if locator.count() == 0:
        return padrao
    return locator.first.inner_text().strip()


def _aguardar_cards(page, timeout=15000):
    """Espera os resultados sem derrubar todo o workflow se o Reddit bloquear acesso."""
    try:
        page.wait_for_selector(SELETOR_CARDS, state="attached", timeout=timeout)
    except PlaywrightTimeoutError:
        titulo_pagina = page.title()
        trecho_pagina = _texto(page.locator("body"), "")[:300].replace("\n", " ")
        print(
            "Resultados do Reddit não carregaram. "
            f"Título da página: {titulo_pagina!r}; URL: {page.url}; "
            f"conteúdo: {trecho_pagina!r}"
        )
        return False
    return page.locator(SELETOR_CARDS).count() > 0


def _buscar_publicacoes_json():
    """Usa a resposta JSON pública do Reddit quando a página HTML não carrega no Actions."""
    url_json = URL_BUSCA + "&limit=" + str(LIMITE_PUBLICACOES) + "&raw_json=1"
    try:
        resposta = requests.get(
            url_json,
            headers={"User-Agent": USER_AGENT_REDDIT, "Accept": "application/json"},
            timeout=20,
        )
        resposta.raise_for_status()
        itens = resposta.json().get("data", {}).get("children", [])
    except (requests.RequestException, ValueError) as erro:
        print(f"Não foi possível consultar os resultados JSON do Reddit: {erro}")
        return []

    publicacoes = []
    for item in itens[:LIMITE_PUBLICACOES]:
        dados = item.get("data", {})
        permalink = dados.get("permalink")
        if not permalink:
            continue
        data_utc = dados.get("created_utc")
        data_publicacao = (
            datetime.fromtimestamp(data_utc, timezone.utc).isoformat()
            if data_utc
            else None
        )
        publicacoes.append(
            {
                "titulo": dados.get("title") or "Título não informado",
                "link": urljoin("https://www.reddit.com", permalink),
                "publicador": dados.get("author") or "Publicador não informado",
                "subreddit": dados.get("subreddit"),
                "data_publicacao": data_publicacao,
                "texto": dados.get("selftext") or "Texto da publicação não disponível.",
            }
        )
    return publicacoes


def _ler_publicacao(page):
    post = page.locator(SELETOR_PUBLICACAO).first
    post.wait_for(state="attached", timeout=30000)

    titulo = post.get_attribute("post-title") or "Título não informado"
    link = post.get_attribute("content-href") or urljoin(
        "https://www.reddit.com", post.get_attribute("permalink") or page.url
    )
    publicador = post.get_attribute("author") or "Publicador não informado"
    subreddit = post.get_attribute("subreddit-name")
    data_publicacao = post.get_attribute("created-timestamp")

    texto_publicacao = _texto(
        post.locator(SELETOR_TEXTO_PUBLICACAO),
        "Texto da publicação não disponível.",
    )
    if texto_publicacao == "Texto da publicação não disponível.":
        texto_publicacao = _texto(
            post.locator("shreddit-post-text-body"),
            texto_publicacao,
        )

    return {
        "titulo": titulo,
        "link": link,
        "publicador": publicador,
        "subreddit": subreddit,
        "data_publicacao": data_publicacao,
        "texto": texto_publicacao,
    }


def _salvar_publicacao(publicacao):
    titulo = publicacao["titulo"]
    link = publicacao["link"]
    publicador = publicacao["publicador"]
    subreddit = publicacao["subreddit"]
    texto = publicacao["texto"]
    fonte = f"Reddit (r/{subreddit})" if subreddit else "Reddit"
    resumo = f"Publicador: {publicador}\n\n{texto}"

    texto_mensagem = texto
    if len(texto_mensagem) > LIMITE_TEXTO_TELEGRAM:
        texto_mensagem = texto_mensagem[:LIMITE_TEXTO_TELEGRAM].rstrip() + "…"

    mensagem = (
        "💬 <b>Problema ou discussão encontrada no Reddit</b>\n\n"
        f"📌 <b>{escape(titulo)}</b>\n"
        f"👤 <b>Publicador:</b> {escape(publicador)}\n"
        f"🧵 <b>Comunidade:</b> {escape(subreddit or 'não informada')}\n\n"
        f"{escape(texto_mensagem)}\n\n"
        f"🔗 <a href=\"{escape(link, quote=True)}\">Abrir publicação</a>"
    )

    print(
        f"Título: {titulo} | Publicador: {publicador} | "
        f"Comunidade: {subreddit or 'não informada'} | Link: {link}"
    )
    salvar_noticia(
        titulo=titulo,
        fonte=fonte,
        data_publicacao=publicacao["data_publicacao"],
        resumo=resumo,
        link=link,
        mensagem=mensagem,
    )


def run_scraper_dores():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="pt-BR")
        page.goto(URL_BUSCA, wait_until="domcontentloaded", timeout=60000)
        if not _aguardar_cards(page):
            publicacoes_json = _buscar_publicacoes_json()
            if publicacoes_json:
                print(f"Reddit retornou {len(publicacoes_json)} publicações pela resposta JSON.")
                for publicacao in publicacoes_json:
                    _salvar_publicacao(publicacao)
            else:
                print("Reddit indisponível nesta execução; seguindo sem novas publicações.")
            browser.close()
            enviar_noticias()
            return

        quantidade = min(page.locator(SELETOR_CARDS).count(), LIMITE_PUBLICACOES)
        print(f"Publicações mais recentes na busca do Reddit: {quantidade} (limite: {LIMITE_PUBLICACOES})")

        for indice in range(quantidade):
            try:
                card = page.locator(SELETOR_CARDS).nth(indice)
                titulo_busca = _texto(card.locator(SELETOR_TITULO), "Título não informado")
                link_busca = card.locator(SELETOR_TITULO).get_attribute("href")
                if not link_busca:
                    print(f"Card {indice + 1} ignorado: link não encontrado.")
                    continue

                print(f"Abrindo publicação {indice + 1}/{quantidade}: {titulo_busca}")
                card.locator(SELETOR_TITULO).evaluate("element => element.click()")
                page.wait_for_url(lambda url: "/comments/" in url, timeout=30000)
                publicacao = _ler_publicacao(page)
                if not publicacao["titulo"] or publicacao["titulo"] == "Título não informado":
                    publicacao["titulo"] = titulo_busca
                if not publicacao["link"]:
                    publicacao["link"] = urljoin(URL_BUSCA, link_busca)
                _salvar_publicacao(publicacao)
            except PlaywrightTimeoutError as erro:
                print(f"Tempo esgotado ao abrir/processar o card {indice + 1}: {erro}")
            except Exception as erro:
                print(f"Erro ao processar o card {indice + 1}: {erro}")
            finally:
                if "/comments/" in page.url:
                    try:
                        page.go_back(wait_until="domcontentloaded", timeout=30000)
                        if not _aguardar_cards(page):
                            print("A busca do Reddit não voltou a carregar; encerrando a coleta.")
                            break
                    except Exception as erro:
                        print(f"Não foi possível voltar aos resultados: {erro}")
                        try:
                            page.goto(URL_BUSCA, wait_until="domcontentloaded", timeout=60000)
                            if not _aguardar_cards(page):
                                print("Reddit indisponível ao reabrir a busca; encerrando a coleta.")
                                break
                        except Exception as erro_reabertura:
                            print(f"Não foi possível reabrir a busca do Reddit: {erro_reabertura}")
                            break

        browser.close()

    enviar_noticias()




