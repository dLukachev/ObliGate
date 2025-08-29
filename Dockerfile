FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# По умолчанию ничего не запускаем, команда определяется в docker-compose
CMD ["sleep", "infinity"]