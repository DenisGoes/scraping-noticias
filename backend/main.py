from fastapi import FastAPI
from backend.api.routes.noticias import router_noti


app = FastAPI()

app.include_router(router_noti)

