import subprocess
import sys

# Команда для Celery-воркера
celery_cmd = [
    sys.executable, "-m", "celery", "-A", "src.utils.celery_client.app", "worker", "--loglevel=info"
]

# Команда для Uvicorn
uvicorn_cmd = [
    sys.executable, "-m", "uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
]

# Запускаем оба процесса в фоне
subprocess.Popen(celery_cmd)
subprocess.Popen(uvicorn_cmd)

print("Celery worker и Uvicorn запущены!")