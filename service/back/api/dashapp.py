import logging
import os

import dash
import flask
import pandas as pd
import pymongo
from dash import dcc, html
from dash.dependencies import Input, Output

from .consts import SOURCES, LABELS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
MONGO_HOSTNAME = os.environ.get('MONGO_HOSTNAME', 'localhost')
RABBIT_HOSTNAME = os.environ.get('RABBIT_HOSTNAME', 'localhost')
CONNECTIONS_STRING = f'mongodb://{MONGO_HOSTNAME}:27017'
DATABASE = 'test'
COLLECTION = 'time_splits'
database_connection = pymongo.MongoClient(CONNECTIONS_STRING, serverSelectionTimeoutMS=5000)[DATABASE]


# TO DO сделать multi select
def create_dash_app(routes_pathname_prefix: str = None) -> dash.Dash:
    server = flask.Flask(__name__)

    app = dash.Dash(__name__, server=server, routes_pathname_prefix=routes_pathname_prefix)

    app.scripts.config.serve_locally = False
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    app.layout = html.Div([
        html.H1('5-minutes graph from source'),
        dcc.Dropdown(
            id='source dropdown',
            options=SOURCES,
            value='__all__'
        ),
        dcc.Dropdown(
            id='label dropdown',
            options=LABELS,
            value='society',
        ),
        dcc.Graph(id='my-graph')
    ], className="container")

    @app.callback(Output('my-graph', 'figure'),
                  [Input('source dropdown', 'value'), Input('label dropdown', 'value')])
    def update_graph(source_value, label_value):
        logger.info(label_value)
        logger.info(f'run query to {source_value}')
        cursor = database_connection['time_splits'] \
            .find({'source': source_value, 'label': label_value}) \
            .sort("_id", pymongo.ASCENDING) \
            .limit(40)
        df = pd.DataFrame.from_records(cursor)
        return {
            'data': [{
                'x': df.posted_time.str[-8:-3],
                'y': df['count'],
                'line': {
                    'width': 3,
                    'shape': 'spline'
                }
            }],
            'layout': {
                'margin': {
                    'l': 30,
                    'r': 20,
                    'b': 30,
                    't': 20
                }
            }
        }

    return app