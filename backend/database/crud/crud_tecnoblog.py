from backend.database.session import Session
from backend.database.models import Noticias
from sqlalchemy import select


def salvar_noticia(titulo, fonte, data_publicacao, link):
    with Session() as session:
        try:
            noticia = session.scalar(select(Noticias).where(Noticias.link == link))

            if noticia:
                print( "Notícia já existe no banco de dados!")
                return False

            nova_noticia = Noticias(
                titulo=titulo, fonte=fonte, data_publicacao=data_publicacao, link=link
            )

            session.add(nova_noticia)
            session.commit()

            print( "Notícia salva com sucesso!")
            return True

        except Exception as e:
            session.rollback() # rollback desfaz qualquer alteração pendente caso a transação falhe, evitando que a sessão fique em estado inconsistente.
            print(f"Algo inesperado aconteceu! {e}")
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

        except Exception as e:
            session.rollback()
            print(f"Algo inesperado aconteceu! {e}")
            raise