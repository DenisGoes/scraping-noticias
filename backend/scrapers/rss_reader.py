from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urljoin
from xml.etree import ElementTree

import requests


class _TextoHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []

    def handle_data(self, data):
        texto = data.strip()
        if texto:
            self.partes.append(texto)


def _nome_local(tag):
    return tag.rsplit("}", 1)[-1].casefold()


def _texto_sem_html(valor):
    if not valor:
        return None
    parser = _TextoHTML()
    parser.feed(valor)
    texto = " ".join(parser.partes)
    return " ".join(texto.split()) or None


def _valor(item, nomes):
    for filho in item:
        if _nome_local(filho.tag) in nomes:
            if _nome_local(filho.tag) == "link":
                href = filho.attrib.get("href")
                if href:
                    if filho.attrib.get("rel", "alternate") == "alternate":
                        return href
                    continue
            if filho.text and filho.text.strip():
                return filho.text.strip()
    return None


def ler_feed_rss(url):
    resposta = requests.get(
        url,
        headers={
            "User-Agent": "NT-Scraper/1.0 (+https://github.com/DenisGoes/scraping-noticias)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        },
        timeout=(10, 30),
    )
    resposta.raise_for_status()
    raiz = ElementTree.fromstring(resposta.content)

    itens = [
        elemento
        for elemento in raiz.iter()
        if _nome_local(elemento.tag) in ("item", "entry")
    ]
    noticias = []
    for item in itens:
        titulo = _texto_sem_html(_valor(item, {"title"}))
        link = _valor(item, {"link"})
        if not titulo or not link:
            continue

        resumo = _texto_sem_html(
            _valor(item, {"description", "summary", "content"})
        )
        data_publicacao = _texto_sem_html(
            _valor(item, {"pubdate", "published", "updated", "date"})
        )
        noticias.append(
            {
                "titulo": titulo,
                "link": urljoin(url, link),
                "resumo": resumo,
                "data_publicacao": data_publicacao,
            }
        )

    if not noticias:
        raise ValueError(f"O feed não retornou notícias com título e link: {url}")

    def data_ordenacao(noticia):
        data = noticia["data_publicacao"]
        if not data:
            return datetime.min.replace(tzinfo=UTC)
        try:
            data_convertida = parsedate_to_datetime(data)
        except (TypeError, ValueError):
            try:
                data_iso = data.replace("Z", "+00:00")
                data_convertida = datetime.fromisoformat(data_iso)
            except ValueError:
                return datetime.min.replace(tzinfo=UTC)
        if data_convertida.tzinfo is None:
            data_convertida = data_convertida.replace(tzinfo=UTC)
        return data_convertida.astimezone(UTC)

    return sorted(noticias, key=data_ordenacao, reverse=True)
