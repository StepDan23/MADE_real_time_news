"""Приложение для контроля парсеров. Их добавление, удаление, запуск, остановка."""
import json
import logging
import os
from logging.config import dictConfig
from multiprocessing import Process

from fastapi import FastAPI, Response, status
from pydantic import BaseModel

from app.core.entities.queue import RabbitConfig
from app.core.entities.response import RssConfig
from app.core.feed import Producer
from app.core.entities.log_config import LogConfig
from app.core.entities.spiders import TassNewsSpider, LentaNewsSpider, RiaNewsSpider, GazetaNewsSpider, MeduzaNewsSpider


dictConfig(LogConfig().dict())
logger = logging.getLogger("crawler")
app = FastAPI()
RUNNING_CRAWLERS = {}
SOURCES = {
    'meduza': RssConfig(
        source_name='meduza.io',
        rss_link='https://meduza.io/rss2/all',
        timeout=60,
        spider=MeduzaNewsSpider,
    ),
    'lenta': RssConfig(
        source_name='lenta.ru',
        rss_link='https://lenta.ru/rss/news',
        timeout=75,
        spider=LentaNewsSpider,
    ),
    'ria': RssConfig(
        source_name='ria.ru',
        rss_link='http://static.feed.rbc.ru/rbc/logical/footer/news.rss',
        timeout=65,
        spider=RiaNewsSpider,
    ),
    'tass': RssConfig(
        source_name='tass.ru',
        rss_link='http://tass.ru/rss/v2.xml',
        timeout=50,
        spider=TassNewsSpider,
    ),
    'gazeta': RssConfig(
        source_name='gazeta.ru',
        rss_link='https://www.gazeta.ru/export/rss/first.xml',
        timeout=60,
        spider=GazetaNewsSpider,
    )
}


def run_producers():
    queue_config = RabbitConfig(
        host='rabbitmq',
        login='admin',
        password='admin'
    )
    for name in SOURCES.keys():
        process = Process(target=Producer(SOURCES[name], queue_config, logger))
        logger.info("Start thread")
        process.start()
        RUNNING_CRAWLERS[name] = process.pid


def run_producer(source_name: str):
    queue_config = RabbitConfig(
        host=os.environ.get('RABBIT_HOSTNAME', 'localhost'),
        login='admin',
        password='admin'
    )
    process = Process(target=Producer(
        SOURCES[source_name], queue_config, logger))
    logger.info("Start thread")
    process.start()
    RUNNING_CRAWLERS[source_name] = process.pid


@app.post('/start/all', status_code=status.HTTP_200_OK)
def start_reading():
    return json.dumps(run_producers())


@app.post('/source/create/', status_code=status.HTTP_201_CREATED)
def create_source(source: RssConfig):
    logger.info(f"get object {source}")
    if not SOURCES.get(source.name):
        SOURCES[source.name] = source
    return source


@app.get('/sources/list/')
def get_exist_sources():
    return json.dumps(SOURCES, default=lambda x: dict(x))


@app.delete("/source/delete/{source_name}")
def delete_source(source_name: str, response: Response):
    logger.info(source_name)
    if SOURCES.get(source_name):
        del SOURCES[source_name]
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_404_NOT_FOUND)


@app.get('/running/list/')
def get_running():
    return json.dumps([source.name for source in RUNNING_CRAWLERS])


@app.post('/stop/{source_name}')
async def stop_process(source_name: str, response: Response):
    logger.info(source_name)
    if SOURCES.get(source_name):
        logger.info("Start terminate process %s pid" %
                    RUNNING_CRAWLERS[source_name])
        # Единственный работающий сбособ убить процесс в FastAPI, который я нашел
        os.kill(RUNNING_CRAWLERS[source_name], 9)
        del RUNNING_CRAWLERS[source_name]
        logger.info("End terminate process")
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_404_NOT_FOUND)


@app.post('/start/{source_name}')
def start_process(source_name: str):
    if source_name not in list(RUNNING_CRAWLERS.keys()) and SOURCES.get(source_name):
        run_producer(source_name)
        return Response(status_code=status.HTTP_201_CREATED)
    return Response(status_code=status.HTTP_404_NOT_FOUND)
