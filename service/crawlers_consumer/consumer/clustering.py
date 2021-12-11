from datetime import datetime
import logging
import pymongo
import pandas as pd
import numpy as np
import torch

from sklearn.cluster import DBSCAN


TABLE = 'posts'
TABLE_OUTPUT = 'clusters'
LIMIT = 1000
LOADED = False
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cluster_job(model, tokenizer, db):
    for cat in ['not_news', 'sports', 'society', 'economy', 'entertainment', 'other', 'science', 'technology']:
        cluster(db, cat, tokenizer, model)


def embed_bert_cls(text, model, tokenizer):
    t = tokenizer(text, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        model_output = model(**{k: v.to(model.device) for k, v in t.items()})
    embeddings = model_output.last_hidden_state[:, 0, :]
    embeddings = torch.nn.functional.normalize(embeddings)
    return embeddings[0].cpu().numpy()


def preprocess(text):
    text = str(text).strip().replace("\n", " ").replace("\xa0", " ").lower()
    return text


def cluster(db, label, tokenizer, model):
    logger.info('start cluster')
    cursor = db[TABLE] \
        .find({'predicted_class': label}) \
        .sort("_id", pymongo.DESCENDING) \
        .limit(1000)

    df = pd.DataFrame.from_records(cursor)
    # Могут проскакивать дубли
    df = df.drop_duplicates('link')
    transformed_titles = df.title.apply(lambda x: embed_bert_cls(preprocess(x), model, tokenizer))
    cluster_algo = DBSCAN(min_samples=2, eps=0.15)
    cluster_labels = cluster_algo.fit_predict(transformed_titles.values.tolist(), )
    clusters = []
    for idx_label in range(np.max(cluster_labels) + 1):
        sources_count = df.iloc[np.where(cluster_labels == idx_label)[0].tolist(), :]['source'].unique().shape[0]
        if sources_count > 1:
            clusters.append(idx_label)

    records = []
    for cluster_label in cluster_labels:
        # yanews дубли присылают
        _records = df.iloc[np.where(cluster_labels == cluster_label)[0].tolist(), :].drop_duplicates("source")
        # Иногда dbscan сходит с ума и делает ультра большой кластер
        if len(_records) < 20:
            records.append({
                'time': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'links': _records['link'].values.tolist(),
                'titles': _records['title'].values.tolist(),
                'label': label,
            })
    collection = db[TABLE_OUTPUT]
    collection.insert_many(records)
    logging.info(f'{records}')
