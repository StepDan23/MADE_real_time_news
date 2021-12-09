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

COLORS = ["red", "green", "blue", "orange", "purple", "cyan", "magenta", "lime", "pink"]
MAX_TICKS_IN_GRAPH = 30

def get_source_for_time_split(df, time_limit_minutes):
    """ for given time limits (maximum number of minutes from current moment) get dataframe for plotting"""
    df = df.assign(minutes_ago = (pd.Timestamp.now() - pd.to_datetime(df["posted_time"], 
                                                           format="%d/%m/%Y %H:%M:%S")
                                  ).dt.total_seconds().round(0) // 60
                   )
    
    df = df.loc[df.minutes_ago < time_limit_minutes]
    df = df.assign(posted_time_minutes = df.posted_time.str[-8: -3])
    minutes_ago_all = pd.Series(np.arange(0, time_limit_minutes, 1), name="minutes_ago_all").to_frame()
    df = pd.merge(minutes_ago_all, df, how="left", left_on = "minutes_ago_all", right_on = "minutes_ago")
    
    df = df.drop_duplicates(["minutes_ago_all", "minutes_ago", "label", "source"], keep="last")
    
    if time_limit_minutes > MAX_TICKS_IN_GRAPH:
        # get intervals of minutes
        df = df.assign(minutes_ago_all = pd.cut(df.minutes_ago_all, MAX_TICKS_IN_GRAPH))
        # convert intervals to timestamps
        df = df.assign(minutes_ago_all = df.minutes_ago_all.apply(lambda x: (int(x.left) + int(x.right)
                                                                            ) / 2
                                                                  )\
                                                           .apply(lambda x: pd.Timestamp.now() - pd.Timedelta(minutes=x)
                                                                  )\
                                                           .astype("datetime64[ns]")
                      )
        # group by timestamps and get mean count for every interval-timestamp/label/source
        df = df.groupby(["minutes_ago_all", "label", "source"])["count"].mean()
        df = df.unstack(["label", "source"])
        df = df.fillna(0)
    else:
        # get actual count for every minute
        df = df.assign(minutes_ago_all = df.minutes_ago_all.apply(lambda x: pd.Timestamp.now() - pd.Timedelta(minutes=x)
                                                                  )\
                                                           .astype("datetime64[ns]")
                      )
        df = df.set_index(["minutes_ago_all", "label", "source"])[["count"]]
        df = df.unstack(["label", "source"])
        df = df.fillna(0)
        df.columns = df.columns.droplevel(0)
    
    df = df.sort_index()
    return df

def update_graph_df(input_df, time_limit_minutes):
    """update graphs based on given dataframe from database
    """
    graph_params = {
                    'layout': {
                        'margin': {
                                    'l': 30,
                                    'r': 20,
                                    'b': 30,
                                    't': 20,
                                  }
                              }
                    }

    df = get_source_for_time_split(input_df, time_limit_minutes)
    
    graph_params.update({
                        'data': [{
                                'x': df.index,
                                'y': df[col],
                                'line': {
                                       'width': 3,
                                       'shape': 'spline',
                                       "color": COLORS[ind % len(COLORS)]
                                         },
                                 'name': str(col)
                                 } for ind, col in enumerate(df.columns.tolist())
                                ],
                        }
                        )
    
    return graph_params

# TO DO сделать multi select
def create_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
    server = flask.Flask(__name__)

    external_stylesheets = ['https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.5/css/bulma.min.css']
    app = dash.Dash(__name__, server=server,
                    requests_pathname_prefix=requests_pathname_prefix,
                    external_stylesheets=external_stylesheets)

    app.scripts.config.serve_locally = False
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    app.layout = html.Div([
        html.Nav(className="navbar is-dark", children=[
            html.Div(id="navbarTransparent", className="navbar-menu", children=[
                html.Div(className="navbar-start", children=[
                    html.A('News feed', className="navbar-item", href='/'),
                    html.A('Statistic', className="navbar-item", href='/dash')
                ])
            ])
        ]),
    html.H1('Comparison of sources:'),
    html.Div([html.H3("time limit"), 
              dcc.Slider(id="time limits slider",
                         min=0,
                         max=10,
                         step=None,
                         marks={
                             0: '5 min',
                             3: '30 min',
                             5: '6 hours',
                             7.65: '24 hours',
                             10: '3 days'
                         },
                         value=0
                        ),
              ],
             style={
                 "margin-left": "25px",
                 "margin-right": "75px",
                 "margin-bottom": "45px",}
            ),
    dcc.Dropdown(
        id='source dropdown',
        options=SOURCES,
        value='__all__',
        multi=True
    ),
    dcc.Dropdown(
        id='label dropdown',
        options=LABELS,
        value='society',
        multi=True
    ),
    dcc.Graph(id='my-graph')
    ], className="container")

    @app.callback(Output('my-graph', 'figure'),
                  [Input('source dropdown', 'value'), 
                   Input('label dropdown', 'value'),
                   Input("time limits slider", "value"),
                  ])
    def update_graph_sources(source_value, label_value, time_limit):
        """
        main function to filter source and labels and time_limit to inner function
        """
        logger.info(f"label: {label_value}")
        logger.info(f'source: {source_value}')
        
        # time limits location values to time limit in minutes from now
        time_limit_dict = {
                             0: 5 ,
                             3: 30,
                             5: 360,
                             7.65: 1440,
                             10: 4320
                         }
        
        time_limit_minutes = time_limit_dict[time_limit]
        logger.info(f'time limit: {time_limit_minutes}')
        
        # convert source to list
        if not isinstance(source_value, list):
            source_list = [source_value]
        else:
            source_list = source_value
        
        # convert label to list
        if not isinstance(label_value, list):
            label_list = [label_value]
        else:
            label_list = label_value
            
        if 'all' in source_list or "__all__" in source_list:
            source_list = [d["label"] for d in SOURCES if d["label"] not in ["all", "__all__"]]
        
        cursor = database_connection['time_splits'] \
            .find({'source': {"$in": source_list}, 
                   'label': {"$in": label_list}
                   }) \
            .sort("_id", pymongo.ASCENDING) \
            .limit(400)
        df = pd.DataFrame.from_records(cursor)
        return update_graph_df(df, time_limit_minutes)

    return app
