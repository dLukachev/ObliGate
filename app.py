from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.backend import router as backend

from src.data.db.base import init_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"]
)

app.include_router(backend)
init_db()