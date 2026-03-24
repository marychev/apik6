from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers.users import router as users_router
from clickhouse_app.init_db import init_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
