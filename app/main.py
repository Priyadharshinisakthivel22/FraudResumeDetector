from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.candidates import router as candidates_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


setup_logging()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(candidates_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

