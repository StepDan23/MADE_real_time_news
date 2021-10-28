import logging
import os
import pika
import pymongo

import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_HOSTNAME = os.environ.get('MONGO_HOSTNAME', 'localhost')
RABBIT_HOSTNAME = os.environ.get('RABBIT_HOSTNAME', 'localhost')
CONNECTIONS_STRING = f'mongodb://{MONGO_HOSTNAME}:27017'
DATABASE = 'test'
BATCH_VALUE = 64

mongo = pymongo.MongoClient(CONNECTIONS_STRING, serverSelectionTimeoutMS=5000)
credentials = pika.PlainCredentials('admin', 'admin') # hardcode
cache = []
with pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOSTNAME, credentials=credentials)) as connection:
    channel = connection.channel()
    channel.queue_declare(queue='news')

    def callback(ch, method, properties, body):
        body = json.loads(body.decode('utf8'))
        cache.append(body)
        logger.info(f"Currently {len(cache) + 1} posts in batch")
        if len(cache) >= 64:
            db = mongo[DATABASE]
            db.posts.insert_many(cache)
            logger.info(f"{BATCH_VALUE} posts transfered to database.")
            cache.clear()
    
    channel.basic_consume(queue='news', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()