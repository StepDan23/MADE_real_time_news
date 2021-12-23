"""
This app is voting classifier asking several NLU models with user text message, receiving answer of each model,
weighting them and giving final answer
"""
import logging
import os
import re

import pymongo
from api.dashapp import create_dash_app
from cachetools import TTLCache
from fastapi import FastAPI, Request
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta

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
dash_app = create_dash_app(requests_pathname_prefix="/dash/")
app.mount("/dash", WSGIMiddleware(dash_app.server))

templates = Jinja2Templates(directory="templates")


def _get_data_from_mongo(batch_size, n_offset, table_name, db_name="test"):
    mongo = pymongo.MongoClient(CONNECTIONS_STRING, serverSelectionTimeoutMS=3000)
    database = mongo.get_database(db_name)
    collection = database.get_collection(table_name)
    result = list(collection.find().sort([("_id", pymongo.DESCENDING)]).skip(n_offset).limit(batch_size))
    logger.info("Get {} records with offset {} from {}, result {}".format(batch_size, n_offset, table_name, result[0]))
    mongo.close()
    [elem.pop('_id') for elem in result]
    #logger.info(result)
    return result

def _get_data_from_mongo_by_topic(topic, batch_size, n_offset, table_name, db_name="test"):
    mongo = pymongo.MongoClient(CONNECTIONS_STRING, serverSelectionTimeoutMS=3000)
    database = mongo.get_database(db_name)
    collection = database.get_collection(table_name)
    result = list(collection.find({'predicted_class': topic}).sort([("_id", pymongo.DESCENDING)]).skip(n_offset).limit(batch_size))
    logger.info("Get {} records with offset {} from {}, result {}".format(batch_size, n_offset, table_name, result[0]))
    mongo.close()
    [elem.pop('_id') for elem in result]
    return result

def _get_data_from_mongo_by_time(interval, table_name, db_name="test"):
    start_time = datetime.now() - timedelta(minutes=interval)
    mongo = pymongo.MongoClient(CONNECTIONS_STRING, serverSelectionTimeoutMS=3000)
    database = mongo.get_database(db_name)
    collection = database.get_collection(table_name)
    result = list(collection.find({'parsed_datetime': {'$gte': start_time}}).sort([("parsed_datetime", pymongo.DESCENDING)]))
#   logger.info("Get {} records with offset {} from {}, result {}".format(batch_size, n_offset, table_name, result[0]))
    mongo.close()
    [elem.pop('_id') for elem in result]
    return result


def _clean_html_tags(json_data):
    json_data['summary'] = re.sub(r'<[^<]+?>', '', json_data['summary'])
    return json_data


@app.get('/api/get_news')
async def get_news(batch_size: int = 10, n_offset: int = 0):
    news = _get_data_from_mongo(batch_size, n_offset, table_name="posts")
    news = [_clean_html_tags(json_data) for json_data in news]
    return news

@app.get('/api/get_news_topic')
async def get_news(topic: str = 'not_news', batch_size: int = 10, n_offset: int = 0):
    logger.info(topic)
    news = _get_data_from_mongo_by_topic(topic, batch_size, n_offset, table_name="posts")
    return news

@app.get('/api/get_news_clusters')
def get_news_clusters(batch_size: int = 100):
    news = _get_data_from_mongo(batch_size, n_offset=0, table_name="clustering")
    return news


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("news_feed.html",
                                      {'request': request, 'title': 'News feed'})


@app.get("/news_clustering", response_class=HTMLResponse)
async def news_clustering(request: Request):
    return templates.TemplateResponse("news_clustering.html",
                                      {'request': request, 'title': 'News feed'})
