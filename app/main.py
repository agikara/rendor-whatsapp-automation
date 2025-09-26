from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import create_db_and_tables

from . import models
from .routers import webhook, dashboard

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(webhook.router)
app.include_router(dashboard.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "WhatsApp FAQ Bot is running."}
