"""
This app is voting classifier asking several NLU models with user text message, receiving answer of each model,
weighting them and giving final answer
"""
import os
import json
from cachetools import TTLCache
import pymongo
import logging
import aiohttp
import pika
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from api.http_dto.res import ResponseOut


TIMEOUT = 60
MONGO_HOSTNAME = os.environ.get('MONGO_HOSTNAME', 'localhost')
RABBIT_HOSTNAME = os.environ.get('RABBIT_HOSTNAME', 'localhost')
CONNECTIONS_STRING = f'mongodb://{MONGO_HOSTNAME}:27017'
DATABASE = 'test'

cache = TTLCache(maxsize=1, ttl=60)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


def _get_last_news():
    mongo = pymongo.MongoClient(CONNECTIONS_STRING, serverSelectionTimeoutMS=5000)
    database = mongo.get_database("test")
    collection = database.get_collection("posts")
    result = list(collection.find().limit(10).sort([("_id", pymongo.DESCENDING)]))
    logger.info(result)
    mongo.close()
    [elem.pop('_id') for elem in result]
    return result


def get_news_from_api():
    # q_len = 0
    # if q_len < 10:
    #     logger.info("Not enough items in queue %s" % q_len)
    #     if not cache.get('mongo_news'):
    #         logger.info("Query to mongo.")
    #         cache['mongo_news'] = _get_last_news()
    #     logger.info("Return cached.")
    #     return cache['mongo_news']
    
    return _get_last_news()


@app.get('/api/get_news')
async def get_latest_news():
    news = get_news_from_api()
    return news


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    news = await get_latest_news()
    buffer = []
    processed_news = []
    for idx, post in enumerate(news):
        if idx % 2 == 0 and idx != 0:
            processed_news.append(buffer[:])
            buffer.clear()
        buffer.append([post['title'], post['predicted_class'], post['source'], post['link']])

    logger.info(news)
    return templates.TemplateResponse("index.html", {'request': request, 'news': processed_news})
