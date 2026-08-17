import os
import time

import telebot
from telebot.util import quick_markup
from telebot.apihelper import ApiTelegramException

from dotenv import load_dotenv
from sqlalchemy import select

from backend.database.session import Session
from backend.database.models import Noticias

from datetime import datetime, timedelta, UTC

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
ID_CANAL = os.getenv("ID_CANAL")

bot = telebot.TeleBot(API_TOKEN)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    with Session() as session:
        try:
            print(f"Callback recebido: {call.data}")

            acao, noticia_id = call.data.split(":")
            noticia = session.scalar(
                select(Noticias).where(
                    Noticias.id == int(noticia_id)
                )
            )

            if not noticia:
                bot.answer_callback_query(
                    call.id,
                    "Notícia não encontrada!"
                )
                return

            if acao == "LIDA":
                noticia.status = "LIDA"
                noticia.remover_em = datetime.now(UTC) + timedelta(days=3)

            elif acao == "REJEITADA":
                noticia.status = "REJEITADA"
                noticia.remover_em = datetime.now(UTC) + timedelta(days=3)

            else:
                bot.answer_callback_query(
                    call.id,
                    "Ação inválida!"
                )
                return

            session.commit()

            if noticia.telegram_message_id:
                try:
                    bot.delete_message(
                        ID_CANAL,
                        noticia.telegram_message_id
                    )

                    print(
                        f"🗑️ Mensagem {noticia.telegram_message_id} "
                        f"deletada do Telegram"
                    )

                except ApiTelegramException as e:
                    print(f"Erro ao deletar mensagem: {e}")

            bot.answer_callback_query(
                call.id,
                f"Notícia marcada como {acao}"
            )

        except Exception as e:
            session.rollback()
            print(f"❌ Erro no callback: {e}")


def enviar_mensagem(noticia):
    markup = quick_markup(
    {
        "✅ LIDA": {
            "callback_data": f"LIDA:{noticia.id}"
        },
        "❌ REJEITADA": {
            "callback_data": f"REJEITADA:{noticia.id}"
        }
    },
    row_width=1
)

    try:
        message = bot.send_message(
            ID_CANAL,
            noticia.mensagem,
            reply_markup=markup,
            parse_mode="HTML"
        )

        noticia.telegram_message_id = message.message_id

        print(
            f"📤 Notícia {noticia.id} enviada. "
            f"Telegram ID: {message.message_id}"
        )

        return True

    except Exception as e:
        print(f"❌ Erro ao enviar notícia {noticia.id}: {e}")
        return False


def enviar_noticias():
    with Session() as session:
        try:
            noticias = session.scalars(
                select(Noticias).where(
                    Noticias.status == "NOVA"
                )
            ).all()

            if not noticias:
                print("Nenhuma notícia nova encontrada.")
                return

            for noticia in noticias:
                sucesso = enviar_mensagem(noticia)

                if sucesso:
                    noticia.status = "ENVIADA"
                    session.commit()

                    print(
                        f"✅ Notícia {noticia.id} marcada como ENVIADA"
                    )

                else:
                    session.rollback()

                time.sleep(2)

        except Exception as e:
            session.rollback()
            print(f"❌ Erro ao enviar notícias: {e}")