from fastapi import APIRouter
from backend.bot.telegram import bot
import telebot
import os
from dotenv import load_dotenv



load_dotenv()

router = APIRouter(prefix="webhook", tags=["webhook"])

API_TOKEN = os.getenv("API_TOKEN")


@router.post("/")
async def iniciar_webhook(update: dict):

    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])

    return {"status": "ok"}


# DESENVOLVIMENTO LOCAL

# Webhook usado com ngrok
# https://xxxxx.ngrok-free.dev/webhook/dev/TOKEN
# @router.post("/webhook/dev/{token}")
# async def webhook_dev(token: str, update: dict):

#     if token != API_TOKEN:
#         return {
#             "status": "error",
#             "message": "token inválido"
#         }

#     if update:
#         update = telebot.types.Update.de_json(update)
#         bot.process_new_updates([update])

#     return {"status": "ok"}