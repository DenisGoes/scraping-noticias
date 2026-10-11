from backend.bot.telegram import bot
from dotenv import load_dotenv
import os

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL não configurada.")

WEBHOOK_URL = WEBHOOK_URL.rstrip("/")
if not WEBHOOK_URL.endswith("/telegram/webhook"):
    WEBHOOK_URL += "/telegram/webhook"

bot.remove_webhook()
webhook_configurado = bot.set_webhook(
    url=WEBHOOK_URL,
    allowed_updates=["message", "callback_query"],
)
if not webhook_configurado:
    raise RuntimeError("O Telegram não confirmou a configuração do webhook.")

print(f"WebHook configurado: {WEBHOOK_URL}")
