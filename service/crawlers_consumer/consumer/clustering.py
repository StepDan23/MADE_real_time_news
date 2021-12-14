import logging
import pandas as pd
import torch

from sklearn.manifold import TSNE


TABLE = 'posts'
TABLE_OUTPUT = 'tsne'
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
    text = str(text).strip().replace("\n", " ").replace("\xa0", " ").lower()
    return text


def cluster_job(db, tokenizer, model):
    logger.info('start cluster')
    cursor = db[TABLE] \
        .aggregate([{"$sample": {"size": LIMIT}}])  # select random samples

    df = pd.DataFrame.from_records(cursor)
    # Могут проскакивать дубли
    df = df.drop_duplicates('link')
    # df['full_text'] = df['title'] + ' ____ ' + df['summary']
    transformed_titles = df['title'].apply(lambda x: embed_bert_cls(preprocess(x), model, tokenizer))
    tsne = TSNE(n_components=2, perplexity=170, random_state=0)
    items_tsne = tsne.fit_transform(transformed_titles.tolist())
    df['tsne_x'] = items_tsne[:, 0]
    df['tsne_y'] = items_tsne[:, 1]
    df = df[['title', 'source', 'tsne_x', 'tsne_y']]
    records = df.to_dict(orient='records')
    collection = db[TABLE_OUTPUT]
    collection.insert_many(records)
    logging.info(f'clustered with TSNE records: {len(records)}')
