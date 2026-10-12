import re
import threading
import unicodedata
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.database.models import Noticias
from backend.database.session import Session


_PARAMETROS_RASTREAMENTO = {
    "fbclid",
    "gclid",
    "dclid",
    "msclkid",
    "ref",
    "source",
    "campaign",
}
_JANELA_DE_TITULO_DUPLICADO = timedelta(days=30)
_LOCK_DEDUPLICACAO = threading.Lock()
_CACHE_CARREGADO = False
_LINKS_EXISTENTES = set()
_TITULOS_EXISTENTES = set()


def _normalizar_link(link):
    partes = urlsplit((link or "").strip())
    esquema = (partes.scheme or "https").casefold()
    if esquema in {"http", "https"}:
        esquema = "https"
    host = (partes.hostname or "").casefold()
    if host.startswith("www."):
        host = host[4:]

    porta = partes.port
    if porta and not ((esquema == "https" and porta == 443) or (esquema == "http" and porta == 80)):
        host = f"{host}:{porta}"

    caminho = re.sub(r"/{2,}", "/", partes.path or "/").rstrip("/") or "/"
    parametros = [
        (chave, valor)
        for chave, valor in parse_qsl(partes.query, keep_blank_values=True)
        if not chave.casefold().startswith("utm_")
        and chave.casefold() not in _PARAMETROS_RASTREAMENTO
    ]
    consulta = urlencode(sorted(parametros))
    return urlunsplit((esquema, host, caminho, consulta, ""))


def _normalizar_titulo(titulo):
    texto = unicodedata.normalize("NFKD", (titulo or "").casefold())
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return " ".join(re.sub(r"[^\w]+", " ", texto).split())


def _carregar_chaves_existentes(session):
    global _CACHE_CARREGADO
    if _CACHE_CARREGADO:
        return

    agora = datetime.now(UTC)
    links = session.scalars(select(Noticias.link)).all()
    titulos = session.scalars(
        select(Noticias.titulo).where(
            Noticias.coletado_em >= agora - _JANELA_DE_TITULO_DUPLICADO
        )
    ).all()

    _LINKS_EXISTENTES.update(_normalizar_link(link) for link in links if link)
    _TITULOS_EXISTENTES.update(
        chave
        for chave in (_normalizar_titulo(titulo) for titulo in titulos)
        if len(chave) >= 25
    )
    _CACHE_CARREGADO = True


def salvar_noticia(titulo, fonte, data_publicacao, resumo, link, mensagem):
    link_normalizado = _normalizar_link(link)
    titulo_normalizado = _normalizar_titulo(titulo)

    with _LOCK_DEDUPLICACAO:
        with Session() as session:
            try:
                _carregar_chaves_existentes(session)

                if link_normalizado in _LINKS_EXISTENTES:
                    print("Notícia duplicada ignorada: link já cadastrado.")
                    return False

                if len(titulo_normalizado) >= 25 and titulo_normalizado in _TITULOS_EXISTENTES:
                    print("Notícia duplicada ignorada: título já cadastrado nos últimos 30 dias.")
                    return False

                nova_noticia = Noticias(
                    titulo=titulo,
                    fonte=fonte,
                    data_publicacao=data_publicacao,
                    resumo=resumo,
                    link=link,
                    mensagem=mensagem,
                )
                session.add(nova_noticia)
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    if session.scalar(select(Noticias.id).where(Noticias.link == link)):
                        _LINKS_EXISTENTES.add(link_normalizado)
                        print("Notícia duplicada ignorada: link já cadastrado.")
                        return False
                    raise

                _LINKS_EXISTENTES.add(link_normalizado)
                if len(titulo_normalizado) >= 25:
                    _TITULOS_EXISTENTES.add(titulo_normalizado)

                print("Notícia salva com sucesso!")
                return True

            except Exception as erro:
                session.rollback()
                print(f"Algo inesperado aconteceu ao salvar a notícia: {erro}")
                raise


def deletar_noticia(id):
    with Session() as session:
        try:
            noticia = session.get(Noticias, id)

            if noticia is None:
                return "Notícia não encontrada."

            session.delete(noticia)
            session.commit()

            return "Notícia deletada com sucesso."

        except Exception as erro:
            session.rollback()
            print(f"Algo inesperado aconteceu! {erro}")
            raise
