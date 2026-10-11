from fastapi import APIRouter
from backend.bot.telegram import bot
import telebot

webhook_router = APIRouter(prefix="/telegram/webhook", tags=["webhook"])


def processar_update(update: dict):
    if update:
        update = telebot.types.Update.de_json(update)
        if update.callback_query:
            print(
                "Webhook recebeu callback_query: "
                f"{update.callback_query.data}"
            )
        bot.process_new_updates([update])

    return {"status": "ok"}


@webhook_router.post("")
async def receber_webhook(update: dict):
    return processar_update(update)
