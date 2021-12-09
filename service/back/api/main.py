"""
This app is voting classifier asking several NLU models with user text message, receiving answer of each model,
weighting them and giving final answer
"""
import logging
import os

import pymongo
from api.dashapp import create_dash_app
from cachetools import TTLCache
from fastapi import FastAPI, Request
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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


def _get_last_news(batch_size, n_offset):
    mongo = pymongo.MongoClient(CONNECTIONS_STRING, serverSelectionTimeoutMS=3000)
    database = mongo.get_database("test")
    collection = database.get_collection("posts")
    result = list(collection.find().sort([("_id", pymongo.DESCENDING)]).skip(n_offset).limit(batch_size))
    logger.info(result[0])
    mongo.close()
    [elem.pop('_id') for elem in result]
    return result


@app.get('/api/get_news')
async def get_news(batch_size: int = 30, n_offset: int = 0):
    logger.info("Get {} news, with offset: {}".format(batch_size, n_offset))
    news = _get_last_news(batch_size, n_offset)
    return news


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("news_feed.html",
                                      {'request': request, 'title': 'News feed'})
