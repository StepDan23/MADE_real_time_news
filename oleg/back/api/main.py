"""
This app is voting classifier asking several NLU models with user text message, receiving answer of each model,
weighting them and giving final answer
"""
import os
import logging
import aiohttp
from fastapi import FastAPI

# from api.http_dto.req import UserRequestIn
from api.http_dto.res import ResponseOut

NEWSAPI_URL = ('https://newsapi.org/v2/top-headlines?'
       'sources=google-news-ru&'
       'language=ru&'
       'apiKey=3544b46b0b624dd6ba4348770a5136a4')#os.environ.get('NEWSAPI_URL')
TIMEOUT = int(os.environ['TIMEOUT'])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session = aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=TIMEOUT)
)
app = FastAPI()


async def get_news_from_api(model_server_url):
    async with session.get(url=model_server_url, ) as response:
        if response.status == 200:
            return await response.json()
    return Exception


@app.get('/api/get_news', response_model=ResponseOut)
async def get_latest_news():
    news = await get_news_from_api(NEWSAPI_URL)
    print(news['articles'][0]['content'])
    return {'news': news}

