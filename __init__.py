from typing import Type

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from .dependencies import root_required, auth_required, login_required
from .exceptions import CrudException
from .models import DbModelBase, TokenDetail, AddResult, CountResult
from .utils import add, add_name, add_name_list, find, find_one, make_query, update, remove, raise_if_exists, count

__version__ = "0.1.0"
db_client = AsyncIOMotorClient(settings.DB_URL)


def init_crud(app: FastAPI, db_models: list[Type["DbModelBase"]]):
    @app.on_event("startup")
    async def on_startup():
        global db_client
        await init_beanie(db_client[settings.DB_NAME], document_models=db_models)

    @app.on_event("shutdown")
    def on_shutdown():
        global db_client
        db_client.close()
