import json
import time
from datetime import datetime

import feedparser
import pika
from cachetools import cached, LFUCache
from cachetools.keys import hashkey

from .entities.response import RssConfig
from .entities.queue import RabbitConfig


class Producer:
    def __init__(self, config: RssConfig, queue_config: RabbitConfig, logger):
        self.rss_link = config.rss_link
        self.source = config.source_name
        self.timeout = config.timeout
        self.queue_config = queue_config
        self.logger = logger
        self.logger.info("Init correct!")

    def _queue_connection(self):
        return pika.BlockingConnection(
            pika.ConnectionParameters(
                self.queue_config.host,
                credentials=pika.PlainCredentials(self.queue_config.login, self.queue_config.password))
        )

    def __call__(self, *args, **kwargs):
        """Запуск чтения rss-ленты."""
        self.logger.info("Start parsing process...")
        while True:
            news_feed = feedparser.parse(self.rss_link)
            for news in news_feed.entries:
                self._add_to_queue(
                    json.dumps({
                        'title': news.title.encode('utf-8').decode(),
                        'link': news.link,
                        'id': news.id,
                        'summary': news.summary,
                        'source': self.source,
                        'parsed_datetime': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }),
                    news.id,
                )
            self.logger.info(f"Batch with {len(news_feed.entries)} from {self.source}")
            time.sleep(self.timeout)

    @cached(cache=LFUCache(maxsize=256), key=lambda self, msg, msg_id: hashkey(msg_id))
    def _add_to_queue(self, msg, msg_id):
        """ Добавление сообщения в очередь с хешированием по id. """
        connection = self._queue_connection()
        channel = connection.channel()
        hot_channel = self._queue_connection().channel()
        channel.queue_declare(
            queue='news'
        )
        hot_channel.queue_declare(
            queue='hot',
        )
        self.logger.info("msg with id %s transferred to queus" % msg_id)
        channel.basic_publish(
            exchange='',
            routing_key='news',
            body=msg
        )
        hot_channel.basic_publish(
            exchange='',
            routing_key='hot',
            body=msg,
            properties=pika.BasicProperties(
                expiration='300000',
            ),
        )
        hot_channel.close()
        channel.close()
        connection.close()
       
