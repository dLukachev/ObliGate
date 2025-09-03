import asyncio
import os
from typing import List
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

load_dotenv()

bot = Bot(os.getenv("BOT_TOKEN", "Введите токен в переменное окружение"))
dp = Dispatcher()

async def send_remind_in_telegram(message):
    chat_ids = os.getenv('CHAT_IDS', '')
    
    if ',' in chat_ids:
        chat_id_list = [int(x) for x in chat_ids.split(',') if x.strip()]
    else:
        chat_id_list = [int(chat_ids)] if chat_ids.strip() else []

    if isinstance(chat_id_list, List) != True:
        raise ValueError('Укажите куда следует отправлять напоминание в телеграм!')

    for id in chat_id_list: # type: ignore
        await bot.send_message(chat_id=id, text=message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())