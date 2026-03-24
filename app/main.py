from fastapi import FastAPI

from app.routers.users import router as users_router
from clickhouse_app.init_db import init_tables

init_tables()

app = FastAPI()
app.include_router(users_router)

