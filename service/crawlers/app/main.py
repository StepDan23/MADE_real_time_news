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


dictConfig(LogConfig().dict())
logger = logging.getLogger("crawler")
app = FastAPI()
RUNNING_CRAWLERS = {}
SOURCES = {
    'meduza': RssConfig(
        source_name='meduza.io',
        rss_link='https://meduza.io/rss2/all',
        timeout=60,
    ),
    'lenta': RssConfig(
        source_name='lenta.ru',
        rss_link='https://lenta.ru/rss/news',
        timeout=75
    ),
    'ria': RssConfig(
        source_name='ria.ru',
        rss_link='http://static.feed.rbc.ru/rbc/logical/footer/news.rss',
        timeout=65,
    ),
    'tass': RssConfig(
        source_name='tass.ru',
        rss_link='http://www.itar-tass.com/rss/all.xml',
        timeout=50,
    ),
    'gazeta': RssConfig(
        source_name='gazeta.ru',
        rss_link='https://www.gazeta.ru/export/rss/first.xml',
        timeout=60
    ),
    'rbk': RssConfig(
        source_name='rbk',
        rss_link='http://static.feed.rbc.ru/rbc/internal/rss.rbc.ru/rbc.ru/mainnews.rss',
        timeout=90
    ),
    'russian_rt': RssConfig(
        source_name='russian_rt',
        rss_link='https://russian.rt.com/rss',
        timeout=75
    ),
    'fontanka': RssConfig(
        source_name='fontanka',
        rss_link='http://www.fontanka.ru/fontanka.rss',
        timeout=60
    ),
    'tj': RssConfig(
        source_name='tj',
        rss_link='http://tjournal.ru/rss',
        timeout=60
    ),
    'life': RssConfig(
        source_name='life',
        rss_link='https://life.ru/rss',
        timeout=75
    ),
    'aif': RssConfig(
        source_name='aif',
        rss_link='http://www.aif.ru/rss/news.php',
        timeout=60
    ),
    'yanews': RssConfig(
        source_name='yanews',
        rss_link='http://news.yandex.ru/index.rss',
        timeout=60
    ),
    'bbc': RssConfig(
        source_name='bbc',
        rss_link='http://www.bbc.co.uk/russian/index.xml',
        timeout=60
    ),
    'vz': RssConfig(
        source_name='vz',
        rss_link='http://www.vz.ru/rss.xml',
        timeout=75
    ),
    'vesti': RssConfig(
        source_name='vesti',
        rss_link='http://www.vesti.ru/vesti.rss',
        timeout=60
    ),
    'echo_msk': RssConfig(
        source_name='echo_msk',
        rss_link='http://echo.msk.ru/news.rss',
        timeout=70
    ),
    'interfax': RssConfig(
        source_name='intefrax',
        rss_link='http://www.interfax.ru/rss.asp',
        timeout=60
    ),
    'izvestia': RssConfig(
        source_name='izvestia',
        rss_link='http://izvestia.ru/xml/rss/all.xml',
        timeout=65
    ),
    'rambler': RssConfig(
        source_name='rambler',
        rss_link='http://news.rambler.ru/rss/head/',
        timeout=70
    ),
    'rg': RssConfig(
        source_name='rg',
        rss_link='http://www.rg.ru/xml/index.xml',
        timeout=70
    ),
    'kp': RssConfig(
        source_name='rg',
        rss_link='http://kp.ru/rss/allsections.xml',
        timeout=70
    ),
    'kommersant': RssConfig(
        source_name='kommersant',
        rss_link='http://www.kommersant.ru/rss/main.xml',
        timeout=70
    ),
    'vedomosti': RssConfig(
        source_name='vedomosti',
        rss_link='http://www.vedomosti.ru/newspaper/out/rss.xml"',
        timeout=70
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
