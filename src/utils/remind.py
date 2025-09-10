from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from datetime import datetime
# from src.utils.celery_tasks import remind

def set_reminder(message, remind_at: datetime):
    remind.apply_async( # type: ignore
        args=[message],
        eta=remind_at  # Время, когда задача должна выполниться
    )

# Пример использования:
# remind_time = datetime.now(timezone.utc) + timedelta(seconds=10)
# set_reminder(message="Пора сделать задачу!", time=remind_time, remind_at=remind_time)
# time.sleep(15)