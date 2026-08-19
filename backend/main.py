from fastapi import FastAPI
from backend.api.routes.webhook_telegram import webhook_router



app = FastAPI()


@app.get("/")
def healthz_check():
    return{"status": "ok"}


app.include_router(webhook_router)