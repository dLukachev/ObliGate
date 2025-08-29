import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

app = Celery(
    "my_async_app",
    broker=f"redis://:{os.getenv('PASS_REDIS')}@{os.getenv('HOST_REDIS')}:{os.getenv('PORT_REDIS')}/0",
    backend=f"redis://:{os.getenv('PASS_REDIS')}@{os.getenv('HOST_REDIS')}:{os.getenv('PORT_REDIS')}/0",
    include=["src.utils.celery_tasks"]
)
