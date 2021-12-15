import logging
import os
import pika
import pymongo
import fasttext
import pyonmttok
from collections import defaultdict
from datetime import datetime
from transformers import AutoTokenizer, AutoModel
from apscheduler.schedulers.background import BackgroundScheduler

from clustering import cluster_job

import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_HOSTNAME = os.environ.get('MONGO_HOSTNAME', 'localhost')
RABBIT_HOSTNAME = os.environ.get('RABBIT_HOSTNAME', 'localhost')
CONNECTIONS_STRING = f'mongodb://{MONGO_HOSTNAME}:27017'
DATABASE = 'test'
BATCH_VALUE = 64

mongo = pymongo.MongoClient(CONNECTIONS_STRING, serverSelectionTimeoutMS=5000)
credentials = pika.PlainCredentials('admin', 'admin')

tokenizer = pyonmttok.Tokenizer("conservative", joiner_annotate=False)
model = fasttext.load_model("ru_cat.ftz")

cluster_tokenizer = AutoTokenizer.from_pretrained("cointegrated/rubert-tiny")
cluster_model = AutoModel.from_pretrained("cointegrated/rubert-tiny")


def preprocess(text):
    text = str(text).strip().replace("\n", " ").replace("\xa0", " ").lower()
    tokens, _ = tokenizer.tokenize(text)
    text = " ".join(tokens)
    return text


def create_timesplite(db, time_split_cache, time):
    records_by_label = []
    records_by_source = []  # А надо ли?
    posted_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    logger.info('Ready to delivery timesplit')
    for label in time_split_cache:
        total = 0
        for source in time_split_cache[label]:
            total += time_split_cache[label][source]
            records_by_label.append({
                'count': time_split_cache[label][source],
                'label': label,
                'source': source,
                'time_split': time,
                'posted_time': posted_time
            })
            logging.info(f'{source} processed')
        records_by_label.append({
            'count': total,
            'label': label,
            'source': "__all__",
            'time_split': time,
            'posted_time': posted_time
        })
        logging.info('total processed')

    collection = db["time_splits"]
    if len(records_by_label) > 0:
        collection.insert_many(records_by_label)
        logging.info(f'insert {time_split_cache}')
        logger.info(f"{len(time_split_cache)} posts to database.")
        time_split_cache.clear()
    else:
        logging.info("empty dict")
    return True


def print_hi():
    logger.info("print hi")


logger.info("print init scheduler")
scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(cluster_job, 'interval', args=[mongo[DATABASE], cluster_model, cluster_tokenizer], minutes=5)


cache = []
time_split_cache = defaultdict(lambda : defaultdict(int))
time_table = set()
transfer_time = None
with pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOSTNAME, credentials=credentials)) as connection:
    channel = connection.channel()
    channel.queue_declare(queue='news')


    def callback(ch, method, properties, body):
        global transfer_time
        body = json.loads(body.decode('utf8'))
        title = preprocess(body['title'])
        predicted_label = model.predict([title])[0][0][0][9:]
        logger.info("P: {} | {}".format(predicted_label, title))
        # Обогащаем предсказанием
        body['predicted_class'] = predicted_label
        cache.append(body)
        logger.info(f"Currently {len(cache) + 1} posts in batch")
        if transfer_time is None:
            transfer_time = datetime.utcnow()
        minutes = int(datetime.utcnow().time().strftime("%M"))
        logger.info(f"print minutes {minutes}")

        curr_time = datetime.utcnow().time().strftime("%H:%M:%S")
        minutes_diff = (datetime.utcnow() - transfer_time).total_seconds() / 60.0
        logging.info(f"diff statistic time {minutes_diff}")

        source = body.get('source', 'unknown')
        time_split_cache[predicted_label][source] += 1

        if (minutes % 5 == 0 and curr_time not in time_table) or (minutes_diff >= 5):
            db = mongo[DATABASE]
            time_table.add(curr_time)
            transfer_time = datetime.utcnow()
            create_timesplite(db, time_split_cache, minutes)

        if len(cache) >= 8:
            db = mongo[DATABASE]
            db.posts.insert_many(cache)
            logger.info(f"{BATCH_VALUE} posts to database.")
            cache.clear()
    
    channel.basic_consume(queue='news', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()



