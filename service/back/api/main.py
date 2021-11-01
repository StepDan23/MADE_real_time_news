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
from fastapi import FastAPI

from api.http_dto.res import ResponseOut

TIMEOUT = 60
MONGO_HOSTNAME = os.environ.get('MONGO_HOSTNAME', 'localhost')
RABBIT_HOSTNAME = os.environ.get('RABBIT_HOSTNAME', 'localhost')
CONNECTIONS_STRING = f'mongodb://{MONGO_HOSTNAME}:27017'
DATABASE = 'test'

cache = TTLCache(maxsize=1, ttl=360)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


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
    parameters = pika.ConnectionParameters(RABBIT_HOSTNAME, credentials=pika.PlainCredentials('admin', 'admin'))
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    # Плохое решение, лучше пересмотреть
    q = channel.queue_declare('hot')
    q_len = q.method.message_count
    
    if q_len < 10:
        logger.info("Not enough items in queue %s" % q_len)
        if not cache.get('mongo_news'):
            logger.info("Query to mongo.")
            cache['mongo_news'] = _get_last_news()
        logger.info("Return cached.")
        return cache['mongo_news']
    
    anws = []
    for method_frame, properties, body in channel.consume('hot'):
        msg = json.loads(body.decode())
        logger.info(msg)
        anws.append(msg)
        channel.basic_ack(method_frame.delivery_tag)

        if method_frame.delivery_tag == 10:
            break

    requeued_messages = channel.cancel()
    channel.close()
    connection.close()
    return anws
    return Exception


@app.get('/api/get_news')
async def get_latest_news():
    news = get_news_from_api()
    return news

