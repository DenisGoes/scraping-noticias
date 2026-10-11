import os
import time
from threading import Lock, Thread

import telebot
from telebot.util import quick_markup
from telebot.apihelper import ApiTelegramException

from dotenv import load_dotenv
from sqlalchemy import select

from backend.database.session import Session
from backend.database.models import Noticias
from backend.services.gerador_roteiro import (
    gerar_roteiro,
    marcar_noticias_como_roteirizadas,
)

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
ID_CANAL = os.getenv("ID_CANAL")

bot = telebot.TeleBot(API_TOKEN)
_relatorio_lock = Lock()


def _gerar_relatorio_em_background(noticia_id):
    try:
        with Session() as session:
            noticia = session.get(Noticias, noticia_id)
            if noticia is None:
                bot.send_message(ID_CANAL, "Notícia não encontrada no banco de dados.")
                return
            if noticia.roteiro_gerado_em is not None:
                bot.send_message(ID_CANAL, "O relatório desta notícia já foi gerado.")
                return
            noticia_id = noticia.id
            noticia_para_gerar = noticia

        roteiro = gerar_roteiro([noticia_para_gerar])
        if roteiro and enviar_roteiro(roteiro):
            marcar_noticias_como_roteirizadas([noticia_id])
            print(f"Notícia {noticia_id} marcada como usada no relatório.")
        else:
            bot.send_message(
                ID_CANAL,
                "Não foi possível gerar ou enviar o relatório. Tente novamente mais tarde.",
            )
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        try:
            bot.send_message(
                ID_CANAL,
                "O Gemini não conseguiu gerar o relatório agora. Tente novamente mais tarde.",
            )
        except Exception as send_error:
            print(f"Erro ao avisar sobre a falha do relatório: {send_error}")
    finally:
        _relatorio_lock.release()


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    callback_data = call.data or ""
    print(f"Callback do Telegram recebido: {callback_data}")

    if callback_data == "GERAR_RELATORIO":
        # Compatibilidade com mensagens antigas, cujo botão não carregava o ID.
        with Session() as session:
            noticia = session.scalar(
                select(Noticias).where(
                    Noticias.telegram_message_id == call.message.message_id
                )
            ) if call.message else None
            noticia_id = noticia.id if noticia else None
        if noticia_id is None:
            bot.answer_callback_query(
                call.id, "Não encontrei a notícia desta mensagem.", show_alert=True
            )
            return
    elif callback_data.startswith("GERAR_RELATORIO:"):
        try:
            noticia_id = int(callback_data.split(":", 1)[1])
        except ValueError:
            bot.answer_callback_query(call.id, "Botão de relatório inválido.", show_alert=True)
            return
    else:
        noticia_id = None

    if noticia_id is not None:
        if not _relatorio_lock.acquire(blocking=False):
            bot.answer_callback_query(call.id, "Um relatório já está sendo gerado.")
            return

        bot.answer_callback_query(call.id, "Enviando esta notícia ao Gemini…")
        Thread(
            target=_gerar_relatorio_em_background,
            args=(noticia_id,),
            daemon=True,
        ).start()
        return

    with Session() as session:
        try:
            acao, noticia_id = callback_data.split(":", 1)
            if acao == "LIDA":
                # Botões enviados antes da troca do status LIDA para APLICADA.
                acao = "APLICADA"
            noticia = session.scalar(
                select(Noticias).where(Noticias.id == int(noticia_id))
            )

            if not noticia:
                bot.answer_callback_query(call.id, "Notícia não encontrada!")
                return

            if acao in ("APLICADA", "SALVA"):
                noticia.status = acao
                noticia.remover_em = None

            elif acao == "REJEITADA":
                telegram_message_id = noticia.telegram_message_id
                if telegram_message_id:
                    try:
                        bot.delete_message(ID_CANAL, telegram_message_id)
                    except ApiTelegramException as e:
                        print(f"Erro ao deletar mensagem do Telegram: {e}")
                session.delete(noticia)
                session.commit()
                bot.answer_callback_query(call.id, "Notícia removida do Telegram e do banco.")
                return

            else:
                bot.answer_callback_query(call.id, "Ação inválida!")
                return

            session.commit()

            bot.answer_callback_query(call.id, f"Notícia marcada como {acao}")

        except Exception as e:
            session.rollback()
            print(f"❌ Erro no callback: {e}")


def dividir_texto(texto, limite=4000):
    partes = []

    while len(texto) > limite:
        corte = texto.rfind("\n", 0, limite)

        if corte == -1:
            corte = limite

        partes.append(texto[:corte])
        texto = texto[corte:]

    if texto:
        partes.append(texto)

    return partes


URL_NOTEBOOKLM = os.getenv(
    "NOTEBOOKLM_URL",
    "https://notebooklm.google.com/notebook/932f141b-faa3-42b7-94d7-1d39bf59c8ac",
)


def enviar_roteiro(roteiro):
    partes = dividir_texto(roteiro)

    try:
        for i, parte in enumerate(partes):

            if i == 0:
                markup = quick_markup(
                    {"📒 Abrir no NotebookLM": {"url": URL_NOTEBOOKLM}}, row_width=1
                )

                mensagem = "🎙️ ROTEIRO DO DIA\n\n" f"{parte}"

                bot.send_message(
                    ID_CANAL, mensagem, reply_markup=markup
                )

            else:
                bot.send_message(ID_CANAL, parte)

            time.sleep(1)

        print(f"🎙️ Roteiro enviado para o Telegram em {len(partes)} partes.")
        return True

    except Exception as e:
        print(f"❌ Erro ao enviar roteiro: {e}")
        return False


def enviar_mensagem(noticia):
    markup = quick_markup(
        {
            "✅ APLICADA": {"callback_data": f"APLICADA:{noticia.id}"},
            "💾 SALVA": {"callback_data": f"SALVA:{noticia.id}"},
            "❌ REJEITADA": {"callback_data": f"REJEITADA:{noticia.id}"},
            "📝 GERAR RELATÓRIO": {"callback_data": f"GERAR_RELATORIO:{noticia.id}"},
        },
        row_width=2,
    )

    try:
        message = bot.send_message(
            ID_CANAL, noticia.mensagem, reply_markup=markup, parse_mode="HTML"
        )

        noticia.telegram_message_id = message.message_id

        print(f"📤 Notícia {noticia.id} enviada. " f"Telegram ID: {message.message_id}")

        return True

    except Exception as e:
        print(f"❌ Erro ao enviar notícia {noticia.id}: {e}")
        return False


def enviar_noticias():
    with Session() as session:
        try:
            noticias = session.scalars(
                select(Noticias).where(Noticias.status == "NOVA")
            ).all()

            if not noticias:
                print("Nenhuma notícia nova encontrada.")
                return

            for noticia in noticias:
                sucesso = enviar_mensagem(noticia)

                if sucesso:
                    noticia.status = "ENVIADA"
                    noticia.enviado_telegram = True
                    session.commit()

                    print(f"✅ Notícia {noticia.id} marcada como ENVIADA")

                else:
                    session.rollback()

                time.sleep(2)

        except Exception as e:
            session.rollback()
            print(f"❌ Erro ao enviar notícias: {e}")
