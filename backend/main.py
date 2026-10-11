from fastapi import FastAPI
from backend.api.routes.webhook_telegram import processar_update, webhook_router

app = FastAPI()


@app.get("/")
def healthz_check():
    return {"status": "ok"}


@app.post("/")
async def webhook_raiz(update: dict):
    # Mantém compatibilidade com o webhook configurado na raiz do domínio.
    return processar_update(update)


app.include_router(webhook_router)
