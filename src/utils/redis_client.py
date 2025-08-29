import os
from redis.asyncio import Redis
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def get_redis_session():
    if not os.getenv("HOST_REDIS") or not os.getenv("PORT_REDIS"):
        raise ValueError('Необходимо в переменных окружения указать HOST_REDIS и PORT_REDIS!')
    
    r = Redis(
    host=os.getenv("HOST_REDIS"), # pyright: ignore[reportArgumentType]
    port=int(os.getenv("PORT_REDIS")), # pyright: ignore[reportArgumentType]
    decode_responses=True,
    username=os.getenv("USER_REDIS"),
    password=os.getenv("PASS_REDIS"),
    socket_connect_timeout=5
    )

    try:
        yield r
    finally:
        await r.close()
        await r.connection_pool.disconnect()


# Пример использования
"""
async with get_redis_session() as r:
        await r.set('TEST', 123, ex=10)
        value = await r.get('TEST')
        print(value)
"""