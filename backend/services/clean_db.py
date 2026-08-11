from backend.database.session import Session
from backend.database.models import Noticias
from sqlalchemy import select, or_
from datetime import datetime, UTC

def clean_dados():
    agora = datetime.now(UTC)
    with Session() as session:
        try:
            noticias = session.execute(
                select(Noticias).where(Noticias.remover_em <= agora)
            ).scalars().all()

            if noticias:
                for noticia in noticias:
                    session.delete(noticia)

                session.commit()

            return len(noticias)

        except Exception as e:
            session.rollback()
            raise