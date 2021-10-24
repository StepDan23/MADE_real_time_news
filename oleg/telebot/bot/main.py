"""
This bot is maintained to be integrated with outsourced ML model
predicting incoming message class. The bot should get message from user,
send it to server with model using POST request, get class prediction and finally
give relevant answer to the user. The current bot name is ruELMo_SVC_bot. Bot owner is
@olegshchegolev
"""
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ParseMode
import aiohttp
from utils import get_back_response, parse_answer

BACK_URL = os.environ['BACK_URL']
TELEGRAM_TOKEN = os.environ['TELEGRAM_BOT_API_TOKEN']
print(TELEGRAM_TOKEN)
START_MESSAGE = "Привет!\nЯ бот real-time агрегатора новостей!"
ERROR_MESSAGE = 'Извините, сейчас мы не можем выполнить ваш запрос'
TIMEOUT = int(os.environ['TIMEOUT'])

MAX_TELEGRAM_MESSAGE_LENGTH = 4096

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply(START_MESSAGE)


@dp.message_handler(commands=['news'])
async def get_news(message: types.Message):
    """
    This handler will give 10 latest news
    """
    try:
        async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=TIMEOUT)
            ) as session:
            response = await asyncio.create_task(get_back_response(session, BACK_URL))
            news = [item['title'] for item in response['news']['articles']]
            logging.info(news[0])
            for text in news:
                answer = parse_answer(text, MAX_TELEGRAM_MESSAGE_LENGTH)
                for part in answer:
                    if len(part) > 0:
                        await message.answer(part)
    except Exception as e:
        logging.error(e)
        await message.answer(ERROR_MESSAGE)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)