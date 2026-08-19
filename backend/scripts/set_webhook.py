from backend.bot.telegram import bot
from dotenv import load_dotenv
import os

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")


bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

print(f"WebHook configurado: {WEBHOOK_URL}")