from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
import os
from backend.api.webhook import router as webhook_router
from backend.bot.telegram import bot


load_dotenv()


API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


@asynccontextmanager
async def lifespan(app: FastAPI):

    webhook_url = os.getenv("WEBHOOK_URL")

    print("WEBHOOK:", webhook_url)

    if webhook_url:
        bot.set_webhook(webhook_url)
        print("Webhook configurado")

    yield

    print("Aplicação encerrada")


app = FastAPI(
    lifespan=lifespan
)


app.include_router(webhook_router)

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "API online"}




# DESENVOLVIMENTO LOCAL
# Rodando localmente com ngrok

# ngrok http 8000
# https://xxxxx.ngrok-free.dev
# WEBHOOK_URL = (
#     "https://dazzling-destitute-fragrance.ngrok-free.dev"
#     f"/webhook/dev/{API_TOKEN}"
# )