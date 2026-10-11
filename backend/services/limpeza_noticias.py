from backend.database.session import Session
from backend.database.models import Noticias
from sqlalchemy import delete
from datetime import datetime, UTC

def clean_dados():
    agora = datetime.now(UTC)
    with Session() as session:
        try:
            resultado = session.execute(
                delete(Noticias).where(
                    Noticias.status.in_(("LIDA", "REJEITADA")),
                    Noticias.remover_em.is_not(None),
                    Noticias.remover_em <= agora,
                )
            )
            session.commit()
            return resultado.rowcount or 0

        except Exception as e:
            session.rollback()
            raise
