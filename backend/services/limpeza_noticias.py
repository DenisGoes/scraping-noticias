from datetime import UTC, datetime

from sqlalchemy import select

from backend.bot.telegram import ID_CANAL, bot, telegram_message_not_found
from backend.database.models import Noticias
from backend.database.session import Session


def clean_dados():
    """Delete expired news from Telegram and the database.

    If Telegram confirms that the publication is already missing, the database
    row is still removed. Other Telegram errors leave the row for a retry.
    Rows without ``remover_em`` are never selected.
    """
    agora = datetime.now(UTC)
    removidas = 0

    with Session() as session:
        try:
            vencidas = session.scalars(
                select(Noticias).where(
                    Noticias.remover_em.is_not(None),
                    Noticias.remover_em <= agora,
                )
            ).all()

            for noticia in vencidas:
                if noticia.telegram_message_id:
                    try:
                        bot.delete_message(ID_CANAL, noticia.telegram_message_id)
                    except Exception as error:
                        if not telegram_message_not_found(error):
                            print(
                                f"Falha ao apagar publicação da notícia {noticia.id}; "
                                f"registro mantido: {error}"
                            )
                            continue

                session.delete(noticia)
                session.commit()
                removidas += 1

            return removidas
        except Exception:
            session.rollback()
            raise
