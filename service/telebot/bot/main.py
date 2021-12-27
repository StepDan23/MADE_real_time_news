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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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


main_kb = InlineKeyboardMarkup()
main_kb.add(InlineKeyboardButton('последние новости', callback_data=f'last news 30'))
main_kb.add(InlineKeyboardButton('новости по темам', callback_data=f'topic news 30'))
#main_kb.add(InlineKeyboardButton('подписаться на новости', callback_data=f'digest news 30'))

topics = {'sports': 'спорт',
          'society': 'общество',
          'economy': 'экономика',
          'entertaiment': 'развлечения',
          'science': 'наука',
          'technology': 'технологии',
          'not_news': 'остальное'}

topics_kb = InlineKeyboardMarkup()
for key, value in topics.items():
    topics_kb.add(InlineKeyboardButton(value, callback_data='specific: ' + key))

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await bot.send_message(chat_id=message.from_user.id, text=START_MESSAGE, reply_markup=main_kb)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('last news'))
async def get_news(callback_query: types.CallbackQuery):
    """
    This handler will give 10 latest news
    """
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT)
        ) as session:
            response = await asyncio.create_task(get_back_response(session, BACK_URL + 'get_news'))
            logging.info(response)
            logging.info(response[0])
            news = [item['title'] for item in response]
            sources = [item['source'] for item in response]
            links = [item['link'] for item in response]
            logging.info(news[0])
            for i, (text, source, link) in enumerate(zip(news, sources, links)):
                answer = parse_answer(text, MAX_TELEGRAM_MESSAGE_LENGTH)
                for j, part in enumerate(answer):
                    if len(part) > 0:
                        if i == len(news) - 1 and j == len(answer) - 1:
                            await bot.send_message(chat_id=callback_query.from_user.id, 
                                    text=f'Источник: {source}. <a href="{link}">{part}</a>', parse_mode=ParseMode.HTML, reply_markup=main_kb)
                        else:
                            await bot.send_message(chat_id=callback_query.from_user.id, 
                                    text=f'Источник: {source}. <a href="{link}">{part}</a>', parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(e)
        await bot.send_message(chat_id=callback_query.from_user.id, text=ERROR_MESSAGE, reply_markup=main_kb)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('specific:'))
async def get_news_topic(callback_query: types.CallbackQuery):
    """
    This handler will give 10 latest news
    """
    topic = callback_query.data.split()[-1]
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT)
        ) as session:
            response = await asyncio.create_task(get_back_response(session, BACK_URL + f'get_news_topic?topic={topic}'))
            logging.info(response)
            logging.info(response[0])
            news = [item['title'] for item in response]
            sources = [item['source'] for item in response]
            links = [item['link'] for item in response]
            logging.info(news[0])
            for i, (text, source, link) in enumerate(zip(news, sources, links)):
                answer = parse_answer(text, MAX_TELEGRAM_MESSAGE_LENGTH)
                for j, part in enumerate(answer):
                    if len(part) > 0:
                        if i == len(news) - 1 and j == len(answer) - 1:
                            await bot.send_message(chat_id=callback_query.from_user.id, 
                                    text=f'Источник: {source}. <a href="{link}">{part}</a>', parse_mode=ParseMode.HTML, reply_markup=main_kb)
                        else:
                            await bot.send_message(chat_id=callback_query.from_user.id, 
                                    text=f'Источник: {source}. <a href="{link}">{part}</a>', parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(e)
        await bot.send_message(chat_id=callback_query.from_user.id, text=ERROR_MESSAGE, reply_markup=main_kb)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('topic'))
async def choose_topic(callback_query: types.CallbackQuery):
    """
    handler to choose topic
    """
    await bot.send_message(chat_id=callback_query.from_user.id, text='Выберите тему', reply_markup=topics_kb)

 


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
