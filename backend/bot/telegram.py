
import telebot
from telebot.util import quick_markup
from backend.database.session import Session
from dotenv import load_dotenv
import os


load_dotenv()

API_TOKEN= os.getenv("TOKEN_API")
ID_CANAL= os.getenv("ID_CANAL")

bot = telebot.TeleBot(API_TOKEN)


def enviar_mensagem():
    with Session() as session:
        # Botões no Telegram
        markup = quick_markup({
            '✅ Lida': {f"Lida:{id}"},
            '❌ Rejeitada': {f"Rejeitada:{id}"}
        }, row_width=2)
        
        try:
           
        except Exception as e:
            print(f"Algo inesperado aconteceu! {e}")





