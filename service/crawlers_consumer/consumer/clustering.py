import logging
import pandas as pd
import torch

from sklearn.manifold import TSNE
from scipy.cluster import hierarchy

TABLE = 'posts'
TABLE_OUTPUT = 'clustering'
LIMIT = 1500
LOADED = False
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def embed_bert_cls(text, model, tokenizer):
    t = tokenizer(text, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        model_output = model(**{k: v.to(model.device) for k, v in t.items()})
    embeddings = model_output.last_hidden_state[:, 0, :]
    embeddings = torch.nn.functional.normalize(embeddings)
    return embeddings[0].cpu().numpy()


def preprocess(text):
    return str(text).strip().replace("\n", " ").replace("\xa0", " ").lower()


def cluster_job(database, cluster_model, cluster_tokenizer):
    logger.info('start cluster')
    cursor = database[TABLE] \
        .aggregate([{"$sample": {"size": LIMIT}}])  # select random samples

    df = pd.DataFrame.from_records(cursor)
    # Могут проскакивать дубли
    df = df.drop_duplicates(['title', 'source'])
    # df['full_text'] = df['title'] + ' ____ ' + df['summary']
    transformed_titles = df['title'].apply(lambda x: embed_bert_cls(preprocess(x), cluster_model, cluster_tokenizer))
    transformed_titles = transformed_titles.tolist()

    linkage_matrix = hierarchy.linkage(transformed_titles, "average", metric="cosine")
    cluster_ids = hierarchy.fcluster(linkage_matrix, t=0.3, criterion="distance")
    df['cluster_id'] = cluster_ids

    tsne = TSNE(n_components=2, perplexity=170, random_state=0)
    items_tsne = tsne.fit_transform(transformed_titles)
    df['tsne_x'] = items_tsne[:, 0]
    df['tsne_y'] = items_tsne[:, 1]

    records = df[['title', 'source', 'cluster_id', 'tsne_x', 'tsne_y']].to_dict(orient='records')
    collection = database[TABLE_OUTPUT]
    collection.insert_many(records)
    logging.info(f'clustered with TSNE records: {len(records)}')
