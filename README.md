Сброка ```docker-compose build```

Запуск ```docker-compose up```

---- Обязательно в .env

HOST_REDIS=""
PORT_REDIS=""
USER_REDIS=""
PASS_REDIS=""

DATABASE_URL = ""

---- Локальный запуск

В первом терминале ```uvicorn app:app --host 0.0.0.0 --port 8000```

Во втором ```celery -A src.utils.celery_client worker --pool=solo -l info```