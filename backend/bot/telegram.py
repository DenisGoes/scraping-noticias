import os
import time
from threading import Lock, Thread

import telebot
from telebot.util import quick_markup

from dotenv import load_dotenv
from sqlalchemy import select
from datetime import datetime, timedelta, UTC

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


def telegram_message_not_found(error):
    """Return True only for Telegram's explicit missing-message errors."""
    description = getattr(error, "description", "") or ""
    result_json = getattr(error, "result_json", None)
    if isinstance(result_json, dict):
        description = f"{description} {result_json.get('description', '')}"
    message = f"{description} {error}".casefold()
    return "message to delete not found" in message or "message not found" in message


def _responder_ao_clique(call, texto, callback_respondido=False, show_alert=False):
    """Confirma rapidamente o callback ou publica o resultado como resposta."""
    if not callback_respondido:
        return bot.answer_callback_query(
            call.id, texto, show_alert=show_alert
        )

    if call.message:
        return bot.send_message(
            ID_CANAL,
            texto,
            reply_to_message_id=call.message.message_id,
        )


def _gerar_relatorio_em_background(noticia_id):
    try:
        with Session() as session:
            noticia = session.get(Noticias, noticia_id)
            if noticia is None:
                bot.send_message(ID_CANAL, "Notícia não encontrada no banco de dados.")
                return
            if noticia.roteiro_gerado_em is not None:
                bot.send_message(ID_CANAL, "O roteiro desta notícia já foi gerado.")
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
                "Não foi possível gerar ou enviar o roteiro. Tente novamente mais tarde.",
            )
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        try:
            bot.send_message(
                ID_CANAL,
                "O Gemini não conseguiu gerar o roteiro agora. Tente novamente mais tarde.",
            )
        except Exception as send_error:
            print(f"Erro ao avisar sobre a falha do relatório: {send_error}")
    finally:
        _relatorio_lock.release()


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    callback_respondido = False
    try:
        dados = call.data or ""
        if dados.startswith("LIDA:"):
            confirmacao = "Registrando como lida…"
        elif dados.startswith("REJEITADA:"):
            confirmacao = "Removendo notícia…"
        elif dados.startswith(("GERAR_ROTEIRO", "GERAR_RELATORIO")):
            confirmacao = "Preparando o roteiro…"
        else:
            confirmacao = "Processando clique…"
        bot.answer_callback_query(call.id, confirmacao)
        callback_respondido = True
    except Exception as e:
        # Continua o processamento mesmo se a confirmação imediata falhar.
        print(f"Erro ao confirmar callback imediatamente: {e}")

    try:
        _processar_callback(call, callback_respondido)
    except Exception as e:
        print(f"❌ Falha ao processar callback {call.data!r}: {e}")
        try:
            _responder_ao_clique(
                call,
                "Não foi possível processar o botão. Tente novamente.",
                callback_respondido,
                show_alert=True,
            )
        except Exception as answer_error:
            print(f"Erro ao responder callback do Telegram: {answer_error}")


def _processar_callback(call, callback_respondido=False):
    callback_data = call.data or ""
    print(f"Callback do Telegram recebido: {callback_data}")

    if callback_data.startswith(("GERAR_ROTEIRO:", "GERAR_RELATORIO:")):
        try:
            noticia_id = int(callback_data.split(":", 1)[1])
        except ValueError:
            _responder_ao_clique(
                call,
                "Botão de roteiro inválido.",
                callback_respondido,
                show_alert=True,
            )
            return
    elif callback_data in ("GERAR_ROTEIRO", "GERAR_RELATORIO"):
        # Compatibilidade com mensagens antigas sem ID no callback_data.
        with Session() as session:
            noticia = session.scalar(
                select(Noticias).where(
                    Noticias.telegram_message_id == call.message.message_id
                )
            ) if call.message else None
            noticia_id = noticia.id if noticia else None
        if noticia_id is None:
            _responder_ao_clique(
                call,
                "Não encontrei a notícia desta mensagem.",
                callback_respondido,
                show_alert=True,
            )
            return
    else:
        noticia_id = None

    if noticia_id is not None:
        with Session() as session:
            noticia = session.get(Noticias, noticia_id)
            if noticia is None:
                _responder_ao_clique(
                    call,
                    "Notícia não encontrada.",
                    callback_respondido,
                    show_alert=True,
                )
                return
            if noticia.roteiro_gerado_em is not None:
                _responder_ao_clique(
                    call,
                    "O roteiro desta notícia já foi gerado.",
                    callback_respondido,
                    show_alert=True,
                )
                return

        if not _relatorio_lock.acquire(blocking=False):
            _responder_ao_clique(
                call,
                "Um relatório já está sendo gerado.",
                callback_respondido,
            )
            return

        worker = Thread(
            target=_gerar_relatorio_em_background,
            args=(noticia_id,),
            daemon=True,
        )
        try:
            worker.start()
        except Exception:
            _relatorio_lock.release()
            raise
        return

    with Session() as session:
        try:
            acao, noticia_id = callback_data.split(":", 1)
            if acao in ("APLICADA", "SALVA"):
                # Compatibilidade com botões de versões anteriores.
                acao = "LIDA"
            noticia = session.scalar(
                select(Noticias).where(Noticias.id == int(noticia_id))
            )

            if not noticia:
                _responder_ao_clique(
                    call, "Notícia não encontrada!", callback_respondido
                )
                return

            if acao == "LIDA":
                if (noticia.status or "").casefold() == "lida":
                    _responder_ao_clique(
                        call,
                        "Essa notícia já foi lida.",
                        callback_respondido,
                    )
                    return
                noticia.status = "lida"
                noticia.remover_em = datetime.now(UTC) + timedelta(days=3)

            elif acao == "REJEITADA":
                telegram_message_id = noticia.telegram_message_id
                if telegram_message_id:
                    try:
                        bot.delete_message(ID_CANAL, telegram_message_id)
                    except Exception as e:
                        print(f"Erro ao deletar mensagem do Telegram: {e}")
                        if not telegram_message_not_found(e):
                            _responder_ao_clique(
                                call,
                                "Não consegui apagar a publicação; notícia mantida para nova tentativa.",
                                callback_respondido,
                                show_alert=True,
                            )
                            return
                session.delete(noticia)
                session.commit()
                return

            else:
                _responder_ao_clique(
                    call, "Ação inválida!", callback_respondido
                )
                return

            session.commit()

            _responder_ao_clique(
                call, "Notícia marcada como lida.", callback_respondido
            )

        except Exception as e:
            session.rollback()
            print(f"❌ Erro no callback: {e}")
            try:
                _responder_ao_clique(
                    call,
                    "Não foi possível processar o botão. Tente novamente.",
                    callback_respondido,
                    show_alert=True,
                )
            except Exception as answer_error:
                print(f"Erro ao responder callback do Telegram: {answer_error}")


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
                mensagem = "🎙️ ROTEIRO DO DIA\n\n" f"{parte}"
                bot.send_message(ID_CANAL, mensagem)

            else:
                bot.send_message(ID_CANAL, parte)

            time.sleep(1)

        markup = quick_markup(
            {"📒 Abrir o NotebookLM": {"url": URL_NOTEBOOKLM}}, row_width=1
        )
        bot.send_message(
            ID_CANAL,
            "📋 Copie o roteiro acima e abra o NotebookLM para gerar o podcast.",
            reply_markup=markup,
        )

        print(f"🎙️ Roteiro enviado para o Telegram em {len(partes)} partes.")
        return True

    except Exception as e:
        print(f"❌ Erro ao enviar roteiro: {e}")
        return False


def enviar_mensagem(noticia):
    markup = quick_markup(
        {
            "✅ JÁ LI": {"callback_data": f"LIDA:{noticia.id}"},
            "❌ REJEITAR": {"callback_data": f"REJEITADA:{noticia.id}"},
            "📝 GERAR ROTEIRO": {"callback_data": f"GERAR_ROTEIRO:{noticia.id}"},
        },
        row_width=1,
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
