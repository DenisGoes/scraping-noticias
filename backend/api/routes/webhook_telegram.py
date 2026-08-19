from fastapi import APIRouter
from backend.bot.telegram import bot
import telebot

webhook_router = APIRouter(prefix="/telegram/webhook", tags=["webhook"])


@webhook_router.post("/")
async def receber_webhook(update: dict):

    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])

    return {"status": "ok"}