# Import libraries
# import os
import json
import requests

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import math

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
from dash import Dash, dcc, html, Input, Output, State, ctx, dash_table
from dash.exceptions import PreventUpdate
from dash.dash_table.Format import Format, Scheme, Symbol

# Data preprocessing function
import data_preprocessing
# Functions for plots creation
import plot_functions

# Load and preprocess the data
PATH = 'https://raw.githubusercontent.com/GhostOfMadness/dash-groceries-and-household-items-exp/main/data/'

df = pd.read_csv(PATH + 'Products.csv', delimiter=';')
preprocessing = data_preprocessing.data_preprocessing
subcat_cat, prod_subcat, cost, quantity, cost_others, quantity_others, period_len_df = preprocessing(df)

# List of dates that cannot be selected as a start or an end
disabled_days = [
    d for d in pd.date_range(
        datetime.strptime('2021-02-13', '%Y-%m-%d'),
        datetime.strptime('2022-07-01', '%Y-%m-%d'),
        freq='d'
        ).tolist() if d not in period_len_df.index
]

# Download dictionaries with labels and items values
labels_file = requests.get(PATH + 'labels_vocabulary.txt').text.split('\n')
items_file = requests.get(PATH + 'items_vocabulary.txt').text.split('\n')

# Create app layout
app = Dash(__name__, eager_loading=True)
app.title = 'Expenses Overview'

server = app.server

app.layout = html.Div(
    [
        dcc.Store(id='dictionaries', storage_type='session'),
        dcc.Store(id='translated-tables', storage_type='session'),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Img(
                                    alt='Plotly logo',
                                    src=app.get_asset_url('plotly_logo.png'),
                                    style={'height' : '60px'}
                                )
                            ], id='plotly-logo'
                        ),
                        html.Div(id='header-text'),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    ['English', 'Русский'],
                                    'English',
                                    clearable=False,
                                    id='language-selector'
                                    ),
                                html.Span(className='tooltip-text', id='language-tooltip')
                            ], id='language-seletor-container'
                        )
                    ], id='logo-header-lang'
                ),
                html.Div(id='header-description')
            ], id='header-container', className='pretty-container'
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Store(id='menu-working-table', storage_type='session'),
                        html.Button(id='tooltip-button', n_clicks=0),
                        html.Div(id='tooltip-container'),
                        html.Div(id='date-picker-range-label', className='menu-label'),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            start_date=date(2021, 2, 13),
                            end_date=date(2022, 7, 1),
                            min_date_allowed=date(2021, 2, 13),
                            max_date_allowed=date(2022, 7, 1),
                            start_date_placeholder_text='2021-02-13',
                            end_date_placeholder_text='2022-07-01',
                            display_format='YYYY-MM-DD',
                            month_format='YYYY-MM',
                            first_day_of_week=1,
                            minimum_nights=0,
                            updatemode='singledate',
                            disabled_days=disabled_days
                        ),
                        html.Div(id='store-kind-label', className='menu-label'),
                        dcc.RadioItems(id='store-kind'),
                        html.Div(id='product-type-label', className='menu-label'),
                        dcc.RadioItems(id='product-type'),
                        html.Div(id='category-choose-label', className='menu-label'),
                        dcc.Dropdown(id='category-choose', multi=True),
                        html.Div(id='item-choose-label', className='menu-label'),
                        dcc.Dropdown(id='item-choose', multi=True),
                        html.Div(
                            [
                                html.Button(
                                    n_clicks=0,
                                    id='submit-button',
                                    className='button-container'
                                ),
                                html.Button(
                                    n_clicks=0,
                                    id='clear-button',
                                    className='button-container'
                                )
                            ], id='full-button-container'
                        ),
                        html.Div(id='err'),
                        dcc.Store(id='tables-storage', storage_type='session'),
                    ], id='menu-container', className='pretty-container'
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    id='total-items',
                                                    className='aggregation-value'
                                                ),
                                                html.Div(
                                                    id='total-items-label',
                                                    className='aggregation-label'
                                                )
                                            ], className='aggregation-info'
                                        ),
                                        html.Div(
                                            html.I(className='bi bi-cart4'),
                                            className='aggregation-icon'
                                        ),
                                    ],
                                    className='aggregation-point pretty-container'
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    id='total-days',
                                                    className='aggregation-value'
                                                ),
                                                html.Div(
                                                    id='total-days-label',
                                                    className='aggregation-label'
                                                )
                                            ], className='aggregation-info'
                                        ),
                                        html.Div(
                                            html.I(className='bi bi-calendar3'),
                                            className='aggregation-icon'
                                        )
                                    ],
                                    className='aggregation-point pretty-container'
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    id='rub-per-day',
                                                    className='aggregation-value',
                                                ),
                                                html.Div(
                                                    id='rub-per-day-label',
                                                    className='aggregation-label'
                                                )
                                            ], className='aggregation-info'
                                        ),
                                        html.Div(
                                            html.I(className='bi bi-cash-coin'),
                                            className='aggregation-icon'
                                        )
                                    ],
                                    className='aggregation-point pretty-container'
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    id='volume-per-day',
                                                    className='aggregation-value two-values',
                                                ),
                                                html.Div(
                                                    id='volume-per-day-label',
                                                    className='aggregation-label'
                                                )
                                            ], className='aggregation-info'
                                        ),
                                        html.Div(
                                            html.I(className='bi bi-boxes'),
                                            className='aggregation-icon'
                                        )
                                    ],
                                    className='aggregation-point pretty-container'
                                )
                            ], id='aggregation-container'
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='graph-1-title', className='graph-name'),
                                        html.Div(
                                            html.Button(
                                                '?',
                                                n_clicks=0,
                                                id='help-button-graph-1',
                                                className='help-button'
                                            ),
                                            className='help-button-container'
                                        ),
                                        html.Div(id='graph-1-help-container'),
                                    ], className='graph-title-container'
                                ),
                                dcc.Graph(id='graph-1', config={'displayModeBar' : False})
                            ], id='graph-1-container', className='pretty-container'
                        )
                    ], id='first-row-right-side-container'
                )
            ], id='first-row-container'
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(id='sync-title'),
                        dcc.RadioItems(
                            inline=True,
                            id='sync-switch'
                        )
                    ], id='sync-switch-container'
                ),
                html.Div(
                    html.Button(
                        '?',
                        n_clicks=0,
                        id='help-button-sync',
                        className='help-button'
                    ), id='help-button-sync-container', className='help-button-container'
                ),
                html.Div(id='graph-2-3-4-help-container')
            ], id='full-sync-switch-container', className='pretty-container'
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(id='graph-2-title', className='graph-name'),
                            ], className='graph-title-container'
                        ),
                        dcc.Graph(id='graph-2', config={'displayModeBar' : False})
                    ], id='graph-2-container', className='pretty-container'
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(id='graph-3-title', className='graph-name'),
                            ], className='graph-title-container'
                        ),
                        html.Div(
                            [
                                dcc.Store(id='sunburst-data-storage', storage_type='session'),
                                dcc.Graph(id='graph-3', config={'displayModeBar' : False}),
                                dcc.Graph(id='graph-4', config={'displayModeBar' : False})
                            ], id='plot-3-4-container'
                        )
                    ], id='graph-3-4-container', className='pretty-container'
                )
            ], id='second-row-container'
        ),
        html.Div(
            [
                dcc.Store(id='others-table-storage', storage_type='session'),
                html.Div(
                    [
                        html.Button(
                            n_clicks=0,
                            id='others-table-button'
                        ),
                        html.Button(
                            '?',
                            n_clicks=0,
                            id='help-button-others-table',
                            className='help-button'
                        ),
                        html.Div(id='help-others-table-container')
                    ], id='others-table-button-container'
                ),
                html.Div(
                    [
                        html.Div(id='others-table-container'),
                        html.Div(
                            id='pic-container'
                        )
                    ], id='table-pic-container'
                )
            ], id='full-others-table-container', className='pretty-container'
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Store(id='graph-5-data', storage_type='session'),
                                html.Div(
                                    [
                                        html.Div(id='graph-5-title', className='graph-name'),
                                        html.Div(
                                            html.Button(
                                                '?',
                                                n_clicks=0,
                                                id='graph-5-help-button',
                                                className='help-button'
                                            ), className='help-button-container'
                                        ),
                                        html.Div(id='graph-5-help-container')
                                    ], id='graph-5-title-container', className='graph-title-container'
                                ),
                                dcc.Graph(
                                    id='graph-5',
                                    clear_on_unhover=True,
                                    config={'displayModeBar' : False}
                                )
                            ], id='graph-5-container', className='pretty-container'
                        ),
                        html.Div(
                            [
                                dcc.Store(id='graph-6-data', storage_type='session'),
                                html.Div(
                                    [
                                        html.Div(id='graph-6-title', className='graph-name'),
                                        html.Div(
                                            html.Button(
                                                '?',
                                                n_clicks=0,
                                                id='graph-6-help-button',
                                                className='help-button',
                                            ), className='help-button-container'
                                        ),
                                        html.Div(id='graph-6-help-container')
                                    ], id='graph-6-title-container', className='graph-title-container'
                                ),
                                dcc.Graph(
                                    id='graph-6',
                                    clear_on_unhover=True,
                                    config={'displayModeBar' : False}
                                )
                            ], id='graph-6-container', className='pretty-container'
                        )
                    ], id='third-row-container'
                ),
                html.Div(
                    [
                        html.Div(
                            html.Img(
                                alt='Сurved right arrow',
                                src=app.get_asset_url('arrow_left.png'),
                                style={
                                    'height' : '180px',
                                    'position' : 'absolute',
                                    'top' : '50px',
                                    'right' : '0',
                                }
                            ),
                            id='arrow-1-container'
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='graph-7-title', className='graph-name'),
                                        html.Div(
                                            html.Button(
                                                '?',
                                                n_clicks=0,
                                                id='graph-7-help-button',
                                                className='help-button'
                                            ), className='help-button-container'
                                        ),
                                        html.Div(id='graph-7-help-container')
                                    ], id='graph-7-title-container', className='graph-title-container'
                                ),
                                dcc.Graph(id='graph-7', config={'displayModeBar' : False})
                            ], id='graph-7-container', className='pretty-container'
                        ),
                        html.Div(
                            html.Img(
                                alt='Curved left arrow',
                                src=app.get_asset_url('arrow_right.png'),
                                style={
                                    'height' : '180px',
                                    'position' : 'absolute',
                                    'top' : '50px',
                                    'left' : '0'
                                    }
                                ),
                            id='arrow-2-container'
                        )
                    ], id='fourth-row-container'
                )
            ], id='third-fourth-row-container'
        ),
        html.Div(
            [
                html.Div(id='thanks', className='footer-block'),
                html.Div(
                    [
                        html.Div(
                            'Email: ',
                            style={
                                'display' : 'inline-block',
                                'height' : '20px',
                                'lineHeight' : '20px',
                                'marginRight' : '1px'
                            }
                        ),
                        html.A(
                            'GhostofMadnessNN@yandex.ru',
                            href='mailto: GhostofMadnessNN@yandex.ru',
                            style={
                                'height' : '20px',
                                'lineHeight' : '20px',
                                'display' : 'inline-block'
                            }
                        )
                    ], id='email', className='footer-block'
                ),
                html.Div(
                    [
                        html.A(
                            children=html.Img(
                                alt='github_logo',
                                src=app.get_asset_url('github_icon.png'),
                                style={'height' : '20px'}
                            ),
                            href='https://github.com/GhostOfMadness',
                            target='_blank',
                            style={
                                'display' : 'inline-block',
                                'marginRight' : '5px'
                            }
                        ),
                        html.A(
                            children=html.Img(
                                alt='telegram_logo',
                                src=app.get_asset_url('telegram_icon.png'),
                                style={'height' : '20px'}
                            ),
                            href='https://t.me/GhostOfMadness',
                            target='_blank',
                            style={'display' : 'inline-block'}
                        )
                    ],
                    id='social-media', className='footer-block'),
                html.Div(id='name', className='footer-block')
            ],
            id='footer', className='pretty-container'),
        html.Div(id='margin-footer')
    ], id='body-container'
)

# Create a help to an object (the menu. a graph, the table, etc.)
def create_tooltip(n_clicks, title, items_list, add_style={}):
    general_style = {
        'backgroundColor' : '#FAEAD9',
        'borderRadius' : '10px',
        'border' : '0.9px solid #7C6A5B',
        'boxShadow' : '2px 2px 2px #8C7969',
        'zIndex' : '2'
    }
    for k, v in add_style.items():
        general_style[k] = v
    if n_clicks % 2 == 1:
        return html.Div(
            [
                html.Div(
                    title,
                    style={
                        'marginTop' : '10px',
                        'marginLeft' : '30px',
                        'fontFamily' : '"Oswald", sans-serif',
                        'fontSize' : '1.125rem',
                        'fontWeight' : '600'
                    }
                ),
                html.Ul(
                    [html.Li(item) for item in items_list],
                    style={
                        'textAlign' : 'justify',
                        'paddingRight' : '10px',
                        'paddingInlineStart' : '30px',
                        'fontSize' : '0.9375rem',
                        'listStyle' : 'circle'
                    }
                )
            ],
            style=general_style
        )
    else:
        return None

# Selected language -> dictionaries
@app.callback(
    Output('dictionaries', 'data'),
    Input('language-selector', 'value')
)
def update_dictionaries(lang):
    lang_num = 1 if lang == 'English' else 2
    labels_dict = {}
    for line in labels_file[:-1]:
        split_line = line.strip().split('*')
        labels_dict[split_line[0]] = split_line[lang_num]
    items_dict = {}
    for line in items_file[:-1]:
        split_line = line.strip().split('*')
        items_dict[split_line[0]] = split_line[lang_num]
    dictionaries = {
        'labels' : labels_dict,
        'items' : items_dict
    }
    return json.dumps(dictionaries)

# Dictionaries -> translated tables
@app.callback(
    Output('translated-tables', 'data'),
    Input('dictionaries', 'data')
)
def translate_tables(dicts):
    dictionaries = json.loads(dicts)
    items_dict = dictionaries['items']
    period_len_df_copy = period_len_df.copy()
    cost_copy = cost.copy()
    cost_copy.columns = [items_dict[col] for col in cost.columns]
    quantity_copy = quantity.copy()
    quantity_copy.columns = [items_dict[col] for col in quantity.columns]
    prod_subcat_copy = prod_subcat.copy()
    prod_subcat_copy.index = [items_dict[idx] for idx in prod_subcat.index]
    prod_subcat_copy['subcategory'] = prod_subcat_copy['subcategory'].apply(lambda x: items_dict[x])
    subcat_cat_copy = subcat_cat.copy()
    subcat_cat_copy.index = [items_dict[idx] for idx in subcat_cat.index]
    subcat_cat_copy['category'] = subcat_cat_copy['category'].apply(lambda x: items_dict[x])
    cost_others_copy = cost_others.copy()
    cost_others_copy.columns = [items_dict[col] for col in cost_others.columns]
    quantity_others_copy = quantity_others.copy()
    quantity_others_copy.columns = [items_dict[col] for col in quantity_others.columns]
    datasets = {
        'period_len_df' : period_len_df_copy.to_json(date_format='epoch', orient='split'),
        'cost' : cost_copy.to_json(date_format='epoch', orient='split'),
        'quantity' : quantity_copy.to_json(date_format='epoch', orient='split'),
        'prod_subcat' : prod_subcat_copy.to_json(date_format='iso', orient='split'),
        'subcat_cat' : subcat_cat_copy.to_json(date_format='iso', orient='split'),
        'cost_others' : cost_others_copy.to_json(date_format='epoch', orient='split'),
        'quantity_others' : quantity_others_copy.to_json(date_format='epoch', orient='split')
    }
    return json.dumps(datasets)

# Dictionaries -> translated labels (that are not depend on any other callbacks)
@app.callback(
    Output('header-text', 'children'),
    Output('header-description', 'children'),
    Output('date-picker-range-label', 'children'),
    Output('store-kind-label', 'children'),
    Output('product-type-label', 'children'),
    Output('category-choose-label', 'children'),
    Output('category-choose', 'placeholder'),
    Output('item-choose-label', 'children'),
    Output('item-choose', 'placeholder'),
    Output('submit-button', 'children'),
    Output('clear-button', 'children'),
    Output('rub-per-day-label', 'children'),
    Output('volume-per-day-label', 'children'),
    Output('tooltip-button', 'title'),
    Output('language-tooltip', 'children'),
    Output('graph-1-title', 'children'),
    Output('help-button-graph-1', 'title'),
    Output('sync-title', 'children'),
    Output('help-button-sync', 'title'),
    Output('graph-2-title', 'children'),
    Output('graph-3-title', 'children'),
    Output('others-table-button', 'children'),
    Output('others-table-button', 'title'),
    Output('help-button-others-table', 'title'),
    Output('graph-5-title', 'children'),
    Output('graph-6-title', 'children'),
    Output('graph-5-help-button', 'title'),
    Output('graph-6-help-button', 'title'),
    Output('graph-7-title', 'children'),
    Output('graph-7-help-button', 'title'),
    Output('thanks', 'children'),
    Output('name', 'children'),
    Input('dictionaries', 'data')
)
def set_labels(dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    labels = [
        labels_dict['header'],
        labels_dict['header_description'],
        labels_dict['date_range'],
        labels_dict['store_type'],
        labels_dict['items_type'],
        labels_dict['items_category'],
        labels_dict['items_category_placeholder'],
        labels_dict['items_name'],
        labels_dict['items_name_placeholder'],
        labels_dict['submit_button_label'],
        labels_dict['clear_button_label'],
        labels_dict['rub_per_day_label'],
        labels_dict['volume_per_day_label'],
        labels_dict['help_button_title'],
        labels_dict['language_tooltip'],
        labels_dict['graph_1_title'],
        labels_dict['help_button_title'],
        labels_dict['sync_title'],
        labels_dict['help_button_title'],
        labels_dict['graph_2_title'],
        labels_dict['graph_3_4_title'],
        labels_dict['others_button_label'],
        labels_dict['others_button_title'],
        labels_dict['help_button_title'],
        labels_dict['graph_5_title'],
        labels_dict['graph_6_title'],
        labels_dict['help_button_title'],
        labels_dict['help_button_title'],
        labels_dict['graph_7_title'],
        labels_dict['help_button_title'],
        labels_dict['thanks'],
        labels_dict['name']
    ]
    return labels

# Dictionaries -> increase clicks of menu help button on 2
# (As a result, the state (visible/ hidden) of help will not be changed)
@app.callback(
    Output('tooltip-button', 'n_clicks'),
    Input('dictionaries', 'data'),
    State('tooltip-button', 'n_clicks'),
)
def update_help_button_clicks(dicts, n_clicks):
    return n_clicks + 2

# Click on the menu help button -> show or hide the menu help
@app.callback(
    Output('tooltip-container', 'children'),
    Input('tooltip-button', 'n_clicks'),
    State('dictionaries', 'data')
)
def show_tooltip(n_clicks, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    items_list = [
        labels_dict['help_menu_1'],
        labels_dict['help_menu_2'],
        labels_dict['help_menu_3'],
        labels_dict['help_menu_4'],
        labels_dict['help_menu_5']
    ]
    return create_tooltip(n_clicks, labels_dict['help_menu_title'], items_list)

# Start date, click on the clear button, dictionaries -> start date
@app.callback(
    Output('date-picker-range', 'start_date'),
    Input('date-picker-range', 'start_date'),
    Input('clear-button', 'n_clicks'),
    Input('dictionaries', 'data')
)
def update_start_date(start_date, n_clicks, dicts):
    comp_id = ctx.triggered_id
    if comp_id == 'date-picker-range':
        delta = period_len_df.loc[datetime.strptime(start_date, '%Y-%m-%d'), 0]
        start = datetime.strptime(start_date, '%Y-%m-%d')
        correct_start = start - timedelta(days=int(delta))
        return correct_start.date()
    elif comp_id == 'clear-button':
        if n_clicks == 0:
            raise PreventUpdate
        else:
            return date(2021, 2, 13)
    elif comp_id == 'dictionaries':
        return date(2021, 2, 13)

# Click on the clear button, dictionaries -> end date
@app.callback(
    Output('date-picker-range', 'end_date'),
    Input('clear-button', 'n_clicks'),
    Input('dictionaries', 'data')
)
def update_end_date(n_clicks, dicts):
    return date(2022, 7, 1)

# Create one option for dcc.Radioitems
def create_option(label, disabled=False, color='#000000'):
    return {
        'label' : html.Div(
            label,
            style={
                'display' : 'inline-block',
                'marginRight' : '10px',
                'color' : color,
                'height' : '20px',
                'lineHeight' : '20px'
            }
        ),
        'value' : label,
        'disabled' : disabled
    }

# Start date, end date -> store kind options, store kind value
@app.callback(
    Output('store-kind', 'options'),
    Output('store-kind', 'value'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    State('dictionaries', 'data')
)
def update_store_kind(start_date, end_date, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    mask = (period_len_df.index <= end) & (period_len_df.index >= start)
    period_len_dff = period_len_df[mask]
    store_kind_options = [
        create_option(labels_dict['store_kind_option_all']),
        create_option(labels_dict['store_kind_option_hyper']),
        create_option(labels_dict['store_kind_option_super'])
    ]
    value = store_kind_options[0]['value']
    if period_len_dff.shape[0] == 1:
        if period_len_dff[0].values[0] == 0:
            store_kind_options = [
                create_option(labels_dict['store_kind_option_all'], disabled=True, color='#B1B1B0'),
                create_option(labels_dict['store_kind_option_hyper']),
                create_option(labels_dict['store_kind_option_super'], disabled=True, color='#B1B1B0')
            ]
            value = store_kind_options[1]['value']
        else:
            store_kind_options = [
                create_option(labels_dict['store_kind_option_all'], disabled=True, color='#B1B1B0'),
                create_option(labels_dict['store_kind_option_hyper'], disabled=True, color='#B1B1B0'),
                create_option(labels_dict['store_kind_option_super'])
            ]
            value = store_kind_options[2]['value']
    elif period_len_dff.shape[0] == 0:
        store_kind_options = [
            create_option(labels_dict['store_kind_option_all'], disabled=True, color='#B1B1B0'),
            create_option(labels_dict['store_kind_option_hyper'], disabled=True, color='#B1B1B0'),
            create_option(labels_dict['store_kind_option_super'], disabled=True, color='#B1B1B0')
        ]
    return store_kind_options, value

# Store kind value -> list of available items
@app.callback(
    Output('menu-working-table', 'data'),
    Input('store-kind', 'value'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
    State('dictionaries', 'data'),
    State('translated-tables', 'data')
)
def update_current_table_after_sk(store_kind_value, start_date, end_date, dicts, ts_tables):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    datasets = json.loads(ts_tables)
    ts_cost = pd.read_json(datasets['cost'], orient='split')
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    mask = (period_len_df.index <= end) & (period_len_df.index >= start)
    dates = period_len_df[mask]
    if store_kind_value == labels_dict['store_kind_option_hyper']:
        dates = dates[dates[0] == 0]
    elif store_kind_value == labels_dict['store_kind_option_super']:
        dates = dates[dates[0] != 0]
    items = ts_cost.loc[dates.index]
    items_values = items.replace(0, np.nan).dropna(axis=1, how='all').columns
    return json.dumps(items_values.tolist())

# List of available items -> product type options, product type value
@app.callback(
    Output('product-type', 'options'),
    Output('product-type', 'value'),
    Input('menu-working-table', 'data'),
    State('dictionaries', 'data'),
    State('translated-tables', 'data')
)
def update_product_type(jsonified_data, dicts, ts_tables):
    items_values = json.loads(jsonified_data)
    dictionaries = json.loads(dicts)
    datasets = json.loads(ts_tables)
    labels_dict = dictionaries['labels']
    ts_prod_subcat = pd.read_json(datasets['prod_subcat'], orient='split')
    ts_subcat_cat = pd.read_json(datasets['subcat_cat'], orient='split')
    product_type_options = [
        create_option(labels_dict['product_type_option_all']),
        create_option(labels_dict['product_type_option_food']),
        create_option(labels_dict['product_type_option_goods'])
    ]
    value = product_type_options[0]['value']
    unique_categories = ts_subcat_cat.loc[
        ts_prod_subcat.loc[items_values].subcategory.unique()
        ].category.unique()
    if len(unique_categories) == 1:
        if unique_categories[0] == labels_dict['product_type_option_food']:
            product_type_options = [
                create_option(labels_dict['product_type_option_all'], disabled=True, color='#B1B1B0'),
                create_option(labels_dict['product_type_option_food']),
                create_option(labels_dict['product_type_option_goods'], disabled=True, color='#B1B1B0')
            ]
            value = product_type_options[1]['value']
        if unique_categories[0] == labels_dict['product_type_option_goods']:
            product_type_options [
                create_option(labels_dict['product_type_option_all'], disabled=True, color='#B1B1B0'),
                create_option(labels_dict['product_type_option_food'], disabled=True, color='#B1B1B0'),
                create_option(labels_dict['product_type_option_goods'])
            ]
            value = product_type_options[2]['value']
    elif len(unique_categories) == 0:
            product_type_options = [
                create_option(labels_dict['product_type_option_all'], disabled=True, color='#B1B1B0'),
                create_option(labels_dict['product_type_option_food'], disabled=True, color='#B1B1B0'),
                create_option(labels_dict['product_type_option_goods'], disabled=True, color='#B1B1B0')
            ]
    return product_type_options, value

# Product type value -> items' category options
@app.callback(
    Output('category-choose', 'options'),
    Input('product-type', 'value'),
    State('menu-working-table', 'data'),
    State('dictionaries', 'data'),
    State('translated-tables', 'data')
)
def update_categories(type_value, jsonified_data, dicts, ts_tables):
    items_values = json.loads(jsonified_data)
    dictionaries = json.loads(dicts)
    datasets = json.loads(ts_tables)
    labels_dict = dictionaries['labels']
    items_dict = dictionaries['items']
    ts_prod_subcat = pd.read_json(datasets['prod_subcat'], orient='split')
    ts_subcat_cat = pd.read_json(datasets['subcat_cat'], orient='split')
    if type_value != labels_dict['product_type_option_all']:
        items_values = [
            i for i in items_values if ts_subcat_cat.loc[ts_prod_subcat.loc[i].subcategory].category == type_value
        ]
    categories = np.sort(ts_prod_subcat.loc[items_values].subcategory.unique()).tolist()
    if len(categories) > 1:
        categories.insert(0, items_dict['Все'])
    return categories

# Items' category values, product type value -> items' category values
@app.callback(
    Output('category-choose', 'value'),
    Input('category-choose', 'value'),
    Input('product-type', 'value'),
    State('dictionaries', 'data')
)
def correct_category_value(category_value, product_value, dicts):
    comp_id = ctx.triggered_id
    if comp_id == 'product-type':
        return []
    elif comp_id == 'category-choose':
        dictionaries = json.loads(dicts)
        items_dict = dictionaries['items']
        if len(category_value) > 1 and items_dict['Все'] in category_value:
            category_value.remove(items_dict['Все'])
        return category_value

# Items' category values -> items options
@app.callback(
    Output('item-choose', 'options'),
    Input('category-choose', 'value'),
    State('menu-working-table', 'data'),
    State('product-type', 'value'),
    State('dictionaries', 'data'),
    State('translated-tables', 'data')
)
def update_items(category_value, jsonified_data, type_value, dicts, ts_tables):
    items_options = json.loads(jsonified_data)
    dictionaries = json.loads(dicts)
    datasets = json.loads(ts_tables)
    items_dict = dictionaries['items']
    ts_prod_subcat = pd.read_json(datasets['prod_subcat'], orient='split')
    ts_subcat_cat = pd.read_json(datasets['subcat_cat'], orient='split')
    if len(category_value) >= 1 and category_value[0] != items_dict['Все']:
        items_options = [
            i for i in items_options if ts_prod_subcat.loc[i, 'subcategory'] in category_value
        ]
    else:
        if type_value != items_dict['Все']:
            items_options = [
                i for i in items_options if ts_subcat_cat.loc[ts_prod_subcat.loc[i, 'subcategory'], 'category'] == type_value
            ]
    items_options = sorted(items_options)
    if len(items_options) > 1:
        items_options.insert(0, items_dict['Все'])
    return items_options

# Items' values, items' category values -> items' values
@app.callback(
    Output('item-choose', 'value'),
    Input('item-choose', 'value'),
    Input('category-choose', 'value'),
    State('dictionaries', 'data')
)
def correct_item_value(item_value, category_value, dicts):
    comp_id = ctx.triggered_id
    if comp_id == 'category-choose':
        return []
    else:
        dictionaries = json.loads(dicts)
        items_dict = dictionaries['items']
        if len(item_value) > 1 and items_dict['Все'] in item_value:
            item_value.remove(items_dict['Все'])
        return item_value

# Click on the submit button, selected language -> the error message
# (if the date range is incorrect or no items are selected)
@app.callback(
    Output('err', 'children'),
    Input('submit-button', 'n_clicks'),
    Input('language-selector', 'value'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
    State('item-choose', 'value'),
    State('dictionaries', 'data')
)
def show_error_message(n_clicks, lang, start_date, end_date, items, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    comp_id = ctx.triggered_id
    if comp_id == 'submit-button':
        if n_clicks == 0:
            raise PreventUpdate

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        if start > end:
            return labels_dict['error_message_1']
        elif items == [] or items is None:
            return labels_dict['error_message_2']
    else:
        return ''

# Translated tables -> clicks on the submit button
@app.callback(
    Output('submit-button', 'n_clicks'),
    Input('translated-tables', 'data')
)
def update_submit_n_clicks(ts_tables):
    return 0

# Clicks on the submit button -> translated slices of tables
@app.callback(
    Output('tables-storage', 'data'),
    Input('submit-button', 'n_clicks'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
    State('store-kind', 'value'),
    State('item-choose', 'value'),
    State('item-choose', 'options'),
    State('dictionaries', 'data'),
    State('translated-tables', 'data')
)
def clean_data(n_clicks, start_date, end_date, sk_value, items_value, items_options, dicts, ts_tables):
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    if n_clicks != 0 and (start > end or items_value == [] or items_value is None):
        raise PreventUpdate

    dictionaries = json.loads(dicts)
    datasets = json.loads(ts_tables)
    labels_dict = dictionaries['labels']
    items_dict = dictionaries['items']
    ts_cost = pd.read_json(datasets['cost'], orient='split')
    ts_quantity = pd.read_json(datasets['quantity'], orient='split')
    ts_prod_subcat = pd.read_json(datasets['prod_subcat'], orient='split')
    ts_subcat_cat = pd.read_json(datasets['subcat_cat'], orient='split')
    ts_cost_others = pd.read_json(datasets['cost_others'], orient='split')
    ts_quantity_others = pd.read_json(datasets['quantity_others'], orient='split')
    if n_clicks != 0:
        mask = (period_len_df.index <= end) & (period_len_df.index >= start)
        period_len_dff = period_len_df[mask]
        if sk_value == labels_dict['store_kind_option_hyper']:
            period_len_dff = period_len_dff[period_len_dff[0] == 0]
        elif sk_value == labels_dict['store_kind_option_super']:
            period_len_dff = period_len_dff[period_len_dff[0] != 0]
        dates = period_len_dff.index
        if items_dict['Все'] in items_value:
            columns = [opt for opt in items_options if opt != items_dict['Все']]
        else:
            columns = items_value
        cost_cleaned = ts_cost.loc[dates, columns]
        quantity_cleaned = ts_quantity.loc[dates, columns]
        prod_subcat_cleaned = ts_prod_subcat.loc[columns]
        subcat_cat_cleaned = ts_subcat_cat.loc[list(set(prod_subcat_cleaned.subcategory))]
        datasets = {
            'period_len_df' : period_len_dff.to_json(orient='split', date_format='epoch'),
            'cost' : cost_cleaned.to_json(orient='split', date_format='epoch'),
            'quantity' : quantity_cleaned.to_json(orient='split', date_format='epoch'),
            'prod_subcat' : prod_subcat_cleaned.to_json(orient='split', date_format='iso'),
            'subcat_cat' : subcat_cat_cleaned.to_json(orient='split', date_format='iso'),
        }
        if items_dict['Остальные расходы'] in subcat_cat_cleaned.index:
            cost_others_cleaned = ts_cost_others.loc[dates].replace(0, np.nan).dropna(axis=1, how='all')
            cost_others_cleaned.fillna(0, inplace=True)
            quantity_others_cleaned = ts_quantity_others.loc[dates, cost_others_cleaned.columns]
            datasets['cost_others'] = cost_others_cleaned.to_json(orient='split', date_format='epoch')
            datasets['quantity_others'] = quantity_others_cleaned.to_json(orient='split', date_format='epoch')
    vol, pack = [], []
    for pos in ts_cost.columns:
        if np.all(ts_quantity[pos].astype('int') == ts_quantity[pos]) and pos not in items_dict['Мука']:
            pack.append(pos)
        else:
            vol.append(pos)
    datasets['kg_l'] = json.dumps(vol)
    datasets['packs'] = json.dumps(pack)
    return json.dumps(datasets)

# Translated slices of tables -> aggregation values
@app.callback(
    Output('total-items', 'children'),
    Output('total-days', 'children'),
    Output('rub-per-day', 'children'),
    Output('volume-per-day', 'children'),
    Input('tables-storage', 'data'),
    State('dictionaries', 'data'),
    State('translated-tables', 'data')
)
def update_aggregation_values(jsonified_data, dicts, ts_tables):
    full_datasets = json.loads(ts_tables)
    slice_datasets = json.loads(jsonified_data)
    dictionaries = json.loads(dicts)
    period_len_df_slice = pd.read_json(slice_datasets['period_len_df'], orient='split')
    cost_slice = pd.read_json(slice_datasets['cost'], orient='split')
    quantity_slice = pd.read_json(slice_datasets['quantity'], orient='split')
    quantity_full = pd.read_json(full_datasets['quantity'], orient='split')
    items_dict = dictionaries['items']
    items = len(cost_slice.columns)
    days = int(period_len_df_slice[0].sum() + len(period_len_df_slice))
    rub_per_day = round(cost_slice.sum().sum() / days, 2)
    vol, pack = [], []
    for item in quantity_slice.columns:
        if np.all(quantity_full[item].astype('int') == quantity_full[item]) and item != items_dict['Мука']:
            pack.append(item)
        else:
            vol.append(item)
    vol_per_day = round(quantity_slice[vol].sum().sum() / days, 1)
    pack_per_day = int(math.ceil(quantity_slice[pack].sum().sum() / days))
    total_volume_per_day = f'{vol_per_day}/ {pack_per_day}'
    return items, days, rub_per_day, total_volume_per_day

# Total items count -> total items count label
@app.callback(
    Output('total-items-label', 'children'),
    Input('total-items', 'children'),
    State('dictionaries', 'data'),
    State('language-selector', 'value')
)
def set_total_items_label(value, dicts, lang):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    if lang == 'Русский':
        if str(value)[-1] == '1' and str(value)[-2:] != '11':
            return 'Наименование'
        elif str(value)[-1] in ['2', '3', '4'] and str(value)[-2:] not in ['12', '13', '14']:
            return 'Наименования'
        return labels_dict['total_items_label']
    if lang == 'English':
        return labels_dict['total_items_label'] if value != 1 else 'Item'

# Total days count -> total days count label
@app.callback(
    Output('total-days-label', 'children'),
    Input('total-days', 'children'),
    State('dictionaries', 'data'),
    State('language-selector', 'value')
)
def set_total_days_label(value, dicts, lang):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    if lang == 'Русский':
        if str(value)[-1] == '1' and str(value)[-2:] != '11':
            return 'День'
        elif str(value)[-1] in ['2', '3', '4'] and str(value)[-2:] not in ['12', '13', '14']:
            return 'Дня'
        return labels_dict['total_days_label']
    if lang == 'English':
        return labels_dict['total_days_label'] if value != 1 else 'Day'

# Translated slices of tables -> graph-1 (total expenses by period)
@app.callback(
    Output('graph-1', 'figure'),
    Input('tables-storage', 'data'),
    State('translated-tables', 'data'),
    State('dictionaries', 'data'),
    State('store-kind', 'value'),
    State('language-selector', 'value')
)
def update_figure_1(cleaned_ts_tables, ts_tables, dicts, sk_value, lang):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    full_datasets = json.loads(ts_tables)
    cleaned_datasets = json.loads(cleaned_ts_tables)
    full_ts_cost = pd.read_json(full_datasets['cost'], orient='split')
    full_period_len_df = pd.read_json(full_datasets['period_len_df'], orient='split')
    cleaned_ts_cost = pd.read_json(cleaned_datasets['cost'], orient='split')
    start = cleaned_ts_cost.index[0]
    end = cleaned_ts_cost.index[-1]
    items_names = cleaned_ts_cost.columns
    return plot_functions.linear_graph(
        full_ts_cost, full_period_len_df, start, end, start, end, items_names, lang, sk_value, labels_dict, 'cost_count'
        )

# Dictionaries -> increase clicks of the graph-1 help button on 2
@app.callback(
    Output('help-button-graph-1', 'n_clicks'),
    Input('dictionaries', 'data'),
    State('help-button-graph-1', 'n_clicks'),
)
def update_help_button_clicks_graph_1(dicts, n_clicks):
    return n_clicks + 2

# Click on the graph-1 help button -> show or hide the graph-1 help
@app.callback(
    Output('graph-1-help-container', 'children'),
    Input('help-button-graph-1', 'n_clicks'),
    State('dictionaries', 'data')
)
def show_tooltip_graph_1(n_clicks, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    items_list = [
        labels_dict['graph_1_help_1'],
        labels_dict['graph_1_help_2'],
        labels_dict['graph_1_help_3']
    ]
    add_style = {
        'position' : 'absolute',
        'top' : '0',
        'left' : '0',
        'width' : '400px',
    }

    return create_tooltip(n_clicks, labels_dict['graph_1_help_title'], items_list, add_style=add_style)

# Translated slices of tables -> data for sunburst plots
@app.callback(
    Output('sunburst-data-storage', 'data'),
    Input('tables-storage', 'data'),
    State('dictionaries', 'data')
)
def create_sunburst_tables(cleaned_ts_tables, dicts):
    cleaned_datasets = json.loads(cleaned_ts_tables)
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    cleaned_ts_cost = pd.read_json(cleaned_datasets['cost'], orient='split')
    cleaned_ts_quantity = pd.read_json(cleaned_datasets['quantity'], orient='split')
    cleaned_ts_prod_subcat = pd.read_json(cleaned_datasets['prod_subcat'], orient='split')
    cleaned_ts_subcat_cat = pd.read_json(cleaned_datasets['subcat_cat'], orient='split')
    items_kg_l = json.loads(cleaned_datasets['kg_l'])
    items_packs = json.loads(cleaned_datasets['packs'])
    sunburst_data_cost = plot_functions.sunburst_dataframe(
        cleaned_ts_cost, cleaned_ts_quantity, cleaned_ts_cost.columns,
        cleaned_ts_prod_subcat, cleaned_ts_subcat_cat,
        labels_dict['total'], labels_dict['of_total_sum'], 'cost', labels_dict)
    sunburst_data_kg_l = plot_functions.sunburst_dataframe(
        cleaned_ts_cost, cleaned_ts_quantity, items_kg_l,
        cleaned_ts_prod_subcat, cleaned_ts_subcat_cat,
        labels_dict['total'], labels_dict['of_total_vol'], 'vol', labels_dict)
    sunburst_data_packs = plot_functions.sunburst_dataframe(
        cleaned_ts_cost, cleaned_ts_quantity, items_packs,
        cleaned_ts_prod_subcat, cleaned_ts_subcat_cat,
        labels_dict['total'], labels_dict['of_total_vol'], 'pack', labels_dict)
    items_list = []
    for idx in sunburst_data_cost.index:
        if not idx in sunburst_data_cost['parent'].values:
            items_list.append(idx)
            items_list.append(sunburst_data_cost.loc[idx, 'showing_label'])
    sunburst_data = {
        'cost' : sunburst_data_cost.to_json(orient='split', date_format='iso'),
        'vol' : sunburst_data_kg_l.to_json(orient='split', date_format='iso'),
        'pack' : sunburst_data_packs.to_json(orient='split', date_format='iso'),
        'items_list' : json.dumps(items_list)
    }
    return json.dumps(sunburst_data)

# Data for sunburst plots -> graph-2 (items' cost shares)
@app.callback(
    Output('graph-2', 'figure'),
    Input('sunburst-data-storage', 'data')
)
def update_figure_2(sunburst_tables):
    plot_tables = json.loads(sunburst_tables)
    cost_plot_table = pd.read_json(plot_tables['cost'], orient='split')
    return plot_functions.sunburst_plot_cost(cost_plot_table)

# Dictionaries -> synchronization state options, synchronization state
@app.callback(
    Output('sync-switch', 'options'),
    Output('sync-switch', 'value'),
    Input('dictionaries', 'data')
)
def enable_synchronization(dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    options = [labels_dict['yes'], labels_dict['no']]
    value = labels_dict['yes']
    return options, value

# Data for sunburst plots, graph-2 clickData -> graph-3
# (items' quantity shares (in kilograms or litres))
@app.callback(
    Output('graph-3', 'figure'),
    Input('sunburst-data-storage', 'data'),
    Input('graph-2', 'clickData'),
    Input('sync-switch', 'value'),
    State('dictionaries', 'data')
)
def update_figure_3(sunburst_tables, click_data, sync_value, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    plot_tables = json.loads(sunburst_tables)
    vol_plot_table = pd.read_json(plot_tables['vol'], orient='split')
    items = json.loads(plot_tables['items_list'])
    comp_id = ctx.triggered_id
    if comp_id == 'sunburst-data-storage':
        return plot_functions.sunburst_plot_quantity(vol_plot_table)
    elif comp_id == 'sync-switch':
        if sync_value == labels_dict['no']:
            return plot_functions.sunburst_plot_quantity(vol_plot_table)
        if sync_value == labels_dict['yes']:
            if click_data:
                return plot_functions.update_quantity_sunburst(
                    vol_plot_table, click_data, items)
            else:
                return plot_functions.sunburst_plot_quantity(vol_plot_table)
    elif comp_id == 'graph-2':
        if click_data:
            if sync_value == labels_dict['yes']:
                return plot_functions.update_quantity_sunburst(
                    vol_plot_table, click_data, items)
            else:
                raise PreventUpdate
        else:
            return plot_functions.sunburst_plot_quantity(vol_plot_table)

# Data for sunburst plots, graph-2 clickData -> graph-4
# (items' quantity shares (in packs))
@app.callback(
    Output('graph-4', 'figure'),
    Input('sunburst-data-storage', 'data'),
    Input('graph-2', 'clickData'),
    Input('sync-switch', 'value'),
    State('dictionaries', 'data')
)
def update_figure_4(sunburst_tables, click_data, sync_value, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    plot_tables = json.loads(sunburst_tables)
    pack_plot_table = pd.read_json(plot_tables['pack'], orient='split')
    items = json.loads(plot_tables['items_list'])
    comp_id = ctx.triggered_id
    if comp_id == 'sunburst-data-storage':
        return plot_functions.sunburst_plot_quantity(pack_plot_table)
    elif comp_id == 'sync-switch':
        if sync_value == labels_dict['no']:
            return plot_functions.sunburst_plot_quantity(pack_plot_table)
        if sync_value == labels_dict['yes']:
            if click_data:
                return plot_functions.update_quantity_sunburst(
                    pack_plot_table, click_data, items)
            else:
                return plot_functions.sunburst_plot_quantity(pack_plot_table)
    elif comp_id == 'graph-2':
        if click_data:
            if sync_value == labels_dict['yes']:
                return plot_functions.update_quantity_sunburst(
                    pack_plot_table, click_data, items)
            else:
                raise PreventUpdate
        else:
            return plot_functions.sunburst_plot_quantity(pack_plot_table)

# Dictionaries -> increase clicks of the synchronization help button on 2
@app.callback(
    Output('help-button-sync', 'n_clicks'),
    Input('dictionaries', 'data'),
    State('help-button-sync', 'n_clicks'),
)
def update_help_button_clicks_graph_2_3_4(dicts, n_clicks):
    return n_clicks + 2

# Click on the synchronization help button -> show or hide the synchronization help
@app.callback(
    Output('graph-2-3-4-help-container', 'children'),
    Input('help-button-sync', 'n_clicks'),
    State('dictionaries', 'data'),
    State('language-selector', 'value')
)
def show_tooltip_graph_2_3_4(n_clicks, dicts, lang):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    block_width = 429 if lang == 'Русский' else 464
    block_right = -(block_width + 28.79)
    pic_left = 198.86 if lang == 'Русский' else 170.64
    items_list = [
        labels_dict['graph_3_4_help_1'],
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            labels_dict['graph_3_4_help_2_1'],
                            style={
                                'display' : 'inline-block',
                                'lineHeight' : '19px'
                            }
                        ),
                        html.Img(
                            alt='Cursor icon',
                            src=app.get_asset_url('cursor_icon.png'),
                            style={
                                'height' : '17px',
                                'margin' : '0px 1px',
                                'display' : 'inline-block',
                                'position' : 'absolute',
                                'bottom' : '0',
                                'left' : f'{pic_left}px'
                            }
                        ),
                        html.Div(
                            labels_dict['graph_3_4_help_2_2'],
                            style={
                                'display' : 'inline-block',
                                'lineHeight' : '19px',
                                'position' : 'absolute',
                                'top' : '0',
                                'right' : '0'
                            }
                        )
                    ],
                    style={
                        'position' : 'relative'
                    }
                ),
                html.Div(labels_dict['graph_3_4_help_2_3'])
            ]
        ),
        labels_dict['graph_3_4_help_3']
    ]
    add_style = {
        'position' : 'absolute',
        'top' : '0',
        'right' : f'{block_right}px',
        'width' : f'{block_width}px',
    }
    return create_tooltip(n_clicks, labels_dict['graph_3_4_help_title'], items_list, add_style=add_style)

# Translated slices of tables -> state of the other expenses table button
@app.callback(
    Output('others-table-button', 'disabled'),
    Input('tables-storage', 'data')
)
def on_off_others_table_button(cleaned_ts_tables):
    cleaned_datasets = json.loads(cleaned_ts_tables)
    return cleaned_datasets.get('cost_others', '') == ''

# Translated slices of tables -> data for the other expenses table
@app.callback(
    Output('others-table-storage', 'data'),
    Input('tables-storage', 'data'),
    State('store-kind', 'value'),
    State('dictionaries', 'data')
)
def create_others_table(cleaned_ts_tables, sk_value, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    cleaned_datasets = json.loads(cleaned_ts_tables)
    if cleaned_datasets.get('cost_others', '') != '':
        cleaned_ts_cost_others = pd.read_json(cleaned_datasets['cost_others'], orient='split')
        cleaned_ts_quantity_others = pd.read_json(cleaned_datasets['quantity_others'], orient='split')
        cleaned_ts_period_df = pd.read_json(cleaned_datasets['period_len_df'], orient='split')
        if sk_value == labels_dict['store_kind_option_all']:
            others_table, hyper_part, super_part, all_part = plot_functions.create_full_table(
                cleaned_ts_cost_others, cleaned_ts_quantity_others, cleaned_ts_period_df
            )
            others_table_data = {
                'table' : others_table.to_json(orient='split', date_format='iso'),
                'hyper_part' : json.dumps(hyper_part),
                'super_part' : json.dumps(super_part),
                'all_part' : json.dumps(all_part),
                'sk_value' : json.dumps([sk_value])
            }
        else:
            others_table, all_part = plot_functions.create_one_table(
                cleaned_ts_cost_others, cleaned_ts_quantity_others
            )
            others_table_data = {
                'table' : others_table.to_json(orient='split', date_format='iso'),
                'all_part' : json.dumps(all_part),
                'sk_value' : json.dumps([sk_value])
            }
        return json.dumps(others_table_data)

# Data for the other expenses table -> zeroing clicks on the other expenses table button
@app.callback(
    Output('others-table-button', 'n_clicks'),
    Input('others-table-storage', 'data')
)
def update_others_n_clicks(others_table):
    return 0

# Click on the other expenses table button ->
# containers' style inside the block for the other expenses table
@app.callback(
    Output('full-others-table-container', 'style'),
    Output('others-table-button-container', 'style'),
    Output('others-table-button', 'style'),
    Output('help-button-others-table', 'style'),
    Output('table-pic-container', 'style'),
    Output('others-table-container', 'style'),
    Output('pic-container', 'style'),
    Output('pic-container', 'children'),
    Input('others-table-button', 'n_clicks'),
    State('others-table-storage', 'data'),
    State('tables-storage', 'data'),
    State('dictionaries', 'data')
)
def change_style(n_clicks, others_table, cleaned_ts_tables, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    cleaned_datasets = json.loads(cleaned_ts_tables)
    if cleaned_datasets.get('cost_others', '') != '':
        cleaned_ts_cost_others = pd.read_json(cleaned_datasets['cost_others'], orient='split')
        items_count = cleaned_ts_cost_others.shape[1]
        others_table_data = json.loads(others_table)
        sk_value = json.loads(others_table_data['sk_value'])[0]
    else:
        items_count = 0
    full_others_table_style = {
        'position' : 'absolute',
        'top' : '1241.2px',
        'left' : '0'
    }
    others_button_container_style = {
        'position' : 'absolute',
        'top' : '0',
        'left' : '10px',
        'height' : '45px',
    }
    others_button_style = {
        'position' : 'absolute',
        'top' : '0',
        'left' : '0',
        'width' : 'calc(100% - 25px)',
        'fontFamily' : '"Oswald", sans-serif',
        'fontWeight' : '600',
        'fontSize' : '1.0625rem',
        'height' : '45px',
        'lineHeight' : '45px',
        'textAlign' : 'left',
        'padding' : '0',
        'border' : '0',
        'backgroundColor' : '#F3F3F3',
        'textDecoration' : 'underline',
        'textDecorationStyle' : 'dashed'
    }
    help_others_button_style = {
        'position' : 'absolute',
        'top' : '10px',
        'right' : '0',
        'width' : '25px',
        'height' : '25px',
    }
    table_pic_style = {
        'position' : 'absolute',
        'top' : '45px',
        'left' : '10px',
        'width' : 'calc(100% - 20px)',
        'backgroundColor' : 'white'
    }
    others_table_style = {
        'position' : 'absolute',
        'top' : '0',
        'left' : '0'
    }
    pic_style = {
        'position' : 'absolute',
        'top' : '0',
        'right' : '0'
    }
    if n_clicks % 2 == 0:
        full_others_table_style['height'] = '49px'
        full_others_table_style['width'] = '31.9449782%'
        others_button_container_style['width'] = 'calc(100% - 20px)'
        table_pic_style['height'] = '0'
        others_table_style['height'] = '0'
        others_table_style['width'] = '0'
        pic_style['height'] = 0
        pic_style['width'] = 0
        others_img = None
    else:
        coef = 2 if sk_value == labels_dict['store_kind_option_all'] else 1
        menu_height = 37 if items_count > 10 else 0
        full_height = 49 + 31 * coef + 30 * 10 + menu_height + 10
        table_height = full_height - 49 - 10
        full_others_table_style['width'] = '100%'
        full_others_table_style['height'] = f'{full_height}px'
        others_button_container_style['width'] = '30.2965381%'
        table_pic_style['height'] = f'{table_height}px'
        others_table_style['height'] = f'{table_height}px'
        pic_style['height'] = f'{table_height}px'
        if sk_value == labels_dict['store_kind_option_all']:
            others_table_style['width'] = '100%'
            pic_style['width'] = '0'
            others_img = None
        else:
            others_table_style['width'] = '50%'
            pic_style['width'] = '50%'
            others_img = html.Img(
                alt='Others items iamge',
                src=app.get_asset_url('others_image.jpeg'),
                style={
                    'height' : f'{table_height}px',
                    'position' : 'absolute',
                    'top' : '0',
                    'left' : '13.4128386%'
                }
            )
    return full_others_table_style, others_button_container_style, others_button_style, help_others_button_style, table_pic_style, others_table_style, pic_style, others_img

# Click on the other expenses table button -> show or hide the other expenses table
@app.callback(
    Output('others-table-container', 'children'),
    Input('others-table-button', 'n_clicks'),
    State('others-table-storage', 'data'),
    State('dictionaries', 'data')
)
def show_others_table(n_clicks, others_table, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    if n_clicks % 2 != 0:
        others_table_data = json.loads(others_table)
        sk_value = json.loads(others_table_data['sk_value'])[0]
        show_table = pd.read_json(others_table_data['table'], orient='split')
        all_part = json.loads(others_table_data['all_part'])
        if sk_value == labels_dict['store_kind_option_all']:
            hyper_part = json.loads(others_table_data['hyper_part'])
            super_part = json.loads(others_table_data['super_part'])
            return plot_functions.create_full_datatable(
                show_table, hyper_part, super_part, all_part, labels_dict)
        else:
            return plot_functions.create_one_datatable(show_table, all_part, labels_dict)

# Dictionaries -> increase clicks of the other expenses table help button on 2
@app.callback(
    Output('help-button-others-table', 'n_clicks'),
    Input('dictionaries', 'data'),
    State('help-button-others-table', 'n_clicks'),
)
def update_others_help_button_clicks(dicts, n_clicks):
    return n_clicks + 2

# Click on the other expenses table help button -> show or hide the other expenses table help
@app.callback(
    Output('help-others-table-container', 'children'),
    Input('help-button-others-table', 'n_clicks'),
    State('dictionaries', 'data')
)
def show_tooltip_others_table(n_clicks, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    items_list = [
        labels_dict['others_help_1'],
        labels_dict['others_help_2']
    ]
    add_style = {
        'position' : 'absolute',
        'top' : '0',
        'left' : 'calc(100% + 38.796875px)',
        'width' : '400px'
    }
    return create_tooltip(n_clicks, labels_dict['others_help_title'], items_list, add_style=add_style)

# The other expenses table container style -> the third and fourth rows' container style
@app.callback(
    Output('third-fourth-row-container', 'style'),
    Input('full-others-table-container', 'style')
)
def update_row_position(table_style):
    top = 1241.2 + int(table_style['height'][:-2]) + 20
    row_style = {
        'position' : 'absolute',
        'top' : f'{top}px',
        'left' : '0',
        'width' : '100%',
        'height' : '898px',
        'border' : '0',
        'backgroundColor' : 'transparent'
    }
    return row_style

# Translated slices of tables -> data for the graph-5 (items' number by period)
@app.callback(
    Output('graph-5-data', 'data'),
    Input('tables-storage', 'data'),
    State('translated-tables', 'data'),
    State('store-kind', 'value')
)
def update_data_graph_5(cleaned_ts_tables, ts_tables, sk_value):
    full_datasets = json.loads(ts_tables)
    full_ts_cost = pd.read_json(full_datasets['cost'], orient='split')
    cleaned_datasets = json.loads(cleaned_ts_tables)
    cleaned_ts_cost = pd.read_json(cleaned_datasets['cost'], orient='split')
    items_names = cleaned_ts_cost.columns
    dff = full_ts_cost[items_names].apply(np.count_nonzero, axis=1).to_frame()
    graph_data = {
        'to_plot' : dff.to_json(orient='split', date_format='epoch'),
        'sk_value' : json.dumps([sk_value])
    }
    return json.dumps(graph_data)

# Data for the graph-5, graph-6 hoverData -> graph-5
@app.callback(
    Output('graph-5', 'figure'),
    Input('graph-5-data', 'data'),
    Input('graph-6', 'hoverData'),
    State('tables-storage', 'data'),
    State('translated-tables', 'data'),
    State('dictionaries', 'data'),
    State('language-selector', 'value')
)
def update_graph_5(graph_tables, hover_data, cleaned_ts_tables, ts_tables, dicts, lang):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    full_datasets = json.loads(ts_tables)
    cleaned_datasets = json.loads(cleaned_ts_tables)
    graph_data = json.loads(graph_tables)
    dff = pd.read_json(graph_data['to_plot'], orient='split')
    sk_value = json.loads(graph_data['sk_value'])[0]
    full_period_len_df = pd.read_json(full_datasets['period_len_df'], orient='split')
    cleaned_ts_cost = pd.read_json(cleaned_datasets['cost'], orient='split')
    start = cleaned_ts_cost.index[0]
    end = cleaned_ts_cost.index[-1]
    items_names = cleaned_ts_cost.columns
    comp_id = ctx.triggered_id
    if comp_id == 'graph-5-data' or (comp_id == 'graph-6' and hover_data is None):
        return plot_functions.linear_graph(
            dff, full_period_len_df, start, end, start, end, items_names, lang, sk_value, labels_dict, 'items_count'
            )
    elif comp_id == 'graph-6':
        point_x = datetime.strptime(hover_data['points'][0]['x'], '%Y-%m-%d')
        if '-' not in hover_data['points'][0]['text']:
            raise PreventUpdate
        else:
            return plot_functions.update_linear_graph_on_hover(point_x, dff, full_period_len_df, start, end, start, end, items_names, lang, sk_value, labels_dict, 'items_count')

# Translated slices of tables -> data for the graph-6 (median cost per item by period)
@app.callback(
    Output('graph-6-data', 'data'),
    Input('tables-storage', 'data'),
    State('translated-tables', 'data'),
    State('store-kind', 'value')
)
def update_data_graph_6(cleaned_ts_tables, ts_tables, sk_value):
    full_datasets = json.loads(ts_tables)
    full_ts_cost = pd.read_json(full_datasets['cost'], orient='split')
    cleaned_datasets = json.loads(cleaned_ts_tables)
    cleaned_ts_cost = pd.read_json(cleaned_datasets['cost'], orient='split')
    items_names = cleaned_ts_cost.columns
    dff = full_ts_cost[items_names].apply(
        lambda x: np.median(x[x != 0]) if np.any(x != 0) else 0, axis=1).to_frame()
    graph_data = {
        'to_plot' : dff.to_json(orient='split', date_format='epoch'),
        'sk_value' : json.dumps([sk_value])
    }
    return json.dumps(graph_data)

# Data for the graph-6, graph-5 hoverData -> graph-6
@app.callback(
    Output('graph-6', 'figure'),
    Input('graph-6-data', 'data'),
    Input('graph-5', 'hoverData'),
    State('tables-storage', 'data'),
    State('translated-tables', 'data'),
    State('dictionaries', 'data'),
    State('language-selector', 'value')
)
def update_graph_6(graph_tables, hover_data, cleaned_ts_tables, ts_tables, dicts, lang):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    full_datasets = json.loads(ts_tables)
    cleaned_datasets = json.loads(cleaned_ts_tables)
    graph_data = json.loads(graph_tables)
    dff = pd.read_json(graph_data['to_plot'], orient='split')
    sk_value = json.loads(graph_data['sk_value'])[0]
    full_period_len_df = pd.read_json(full_datasets['period_len_df'], orient='split')
    cleaned_ts_cost = pd.read_json(cleaned_datasets['cost'], orient='split')
    start = cleaned_ts_cost.index[0]
    end = cleaned_ts_cost.index[-1]
    items_names = cleaned_ts_cost.columns
    comp_id = ctx.triggered_id
    if comp_id == 'graph-6-data' or (comp_id == 'graph-5' and hover_data is None):
        return plot_functions.linear_graph(
            dff, full_period_len_df, start, end, start, end, items_names, lang, sk_value, labels_dict, 'medians_count'
            )
    elif comp_id == 'graph-5':
        point_x = datetime.strptime(hover_data['points'][0]['x'], '%Y-%m-%d')
        if '-' not in hover_data['points'][0]['text']:
            raise PreventUpdate
        else:
            return plot_functions.update_linear_graph_on_hover(point_x, dff, full_period_len_df, start, end, start, end, items_names, lang, sk_value, labels_dict, 'medians_count')

# Dictionaries -> increase clicks of the graph-5 help button on 2
@app.callback(
    Output('graph-5-help-button', 'n_clicks'),
    Input('dictionaries', 'data'),
    State('graph-5-help-button', 'n_clicks'),
)
def update_help_button_clicks_graph_5(dicts, n_clicks):
    return n_clicks + 2

# Click on the graph-5 help button -> show or hide the graph-5 help
@app.callback(
    Output('graph-5-help-container', 'children'),
    Input('graph-5-help-button', 'n_clicks'),
    State('dictionaries', 'data')
)
def show_tooltip_graph_5(n_clicks, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    items_list = [
        labels_dict['graph_1_help_1'],
        ' '.join([
            labels_dict['graph_5_help_2_1'],
            labels_dict['graph_5_help_2_2']
        ]),
        labels_dict['graph_5_help_3'],
        labels_dict['graph_1_help_3']
    ]
    add_style = {
        'position' : 'absolute',
        'top' : '45px',
        'right' : '0',
        'width' : '500px',
    }
    return create_tooltip(n_clicks, labels_dict['graph_5_help_title'], items_list, add_style=add_style)

# Dictionaries -> increase clicks of the graph-6 help button on 2
@app.callback(
    Output('graph-6-help-button', 'n_clicks'),
    Input('dictionaries', 'data'),
    State('graph-6-help-button', 'n_clicks'),
)
def update_help_button_clicks_graph_6(dicts, n_clicks):
    return n_clicks + 2

# Click on the graph-6 help button -> show or hide the graph-6 help
@app.callback(
    Output('graph-6-help-container', 'children'),
    Input('graph-6-help-button', 'n_clicks'),
    State('dictionaries', 'data')
)
def show_tooltip_graph_6(n_clicks, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    items_list = [
        labels_dict['graph_1_help_1'],
        ' '.join([
            labels_dict['graph_6_help_2_1'],
            labels_dict['graph_6_help_2_2']
        ]),
        labels_dict['graph_5_help_3'],
        labels_dict['graph_1_help_3']
    ]
    add_style = {
        'position' : 'absolute',
        'top' : '45px',
        'right' : '0',
        'width' : '500px',
    }
    return create_tooltip(n_clicks, labels_dict['graph_6_help_title'], items_list, add_style=add_style)

# Translated slices of tables -> graph-7
# (interralation between items' number and median cost per item)
@app.callback(
    Output('graph-7', 'figure'),
    Input('tables-storage', 'data'),
    State('dictionaries', 'data'),
    State('store-kind', 'value')
)
def update_graph_7(cleaned_ts_tables, dicts, sk_value):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    cleaned_datasets = json.loads(cleaned_ts_tables)
    cleaned_ts_cost = pd.read_json(cleaned_datasets['cost'], orient='split')
    cleaned_ts_period_df = pd.read_json(cleaned_datasets['period_len_df'], orient='split')
    return plot_functions.scatter_graph(cleaned_ts_cost, cleaned_ts_period_df, sk_value, labels_dict)

# Dictionaries -> increase clicks of the graph-7 help button on 2
@app.callback(
    Output('graph-7-help-button', 'n_clicks'),
    Input('dictionaries', 'data'),
    State('graph-7-help-button', 'n_clicks'),
)
def update_help_button_clicks_graph_7(dicts, n_clicks):
    return n_clicks + 2

# Click on the graph-7 help button -> show or hide the graph-7 help
@app.callback(
    Output('graph-7-help-container', 'children'),
    Input('graph-7-help-button', 'n_clicks'),
    State('dictionaries', 'data')
)
def show_tooltip_graph_7(n_clicks, dicts):
    dictionaries = json.loads(dicts)
    labels_dict = dictionaries['labels']
    items_list = [
        labels_dict['graph_7_help_1'],
        labels_dict['graph_1_help_3'],
        labels_dict['graph_7_help_3'],
        [
            labels_dict['graph_7_help_4'][:1],
            html.Sup('2'),
            labels_dict['graph_7_help_4'][1:],
        ]
    ]
    add_style = {
        'position' : 'absolute',
        'top' : '45px',
        'right' : '0',
        'width' : '500px'
    }
    return create_tooltip(n_clicks, labels_dict['graph_7_help_title'], items_list, add_style=add_style)

# The other expenses table container style -> the footer style
@app.callback(
    Output('footer', 'style'),
    Output('margin-footer', 'style'),
    Input('full-others-table-container', 'style')
)
def update_footer_position(style):
    height = 1241.2 + int(style['height'][:-2]) + 20 + 898 + 20
    footer_style = {
        'position' : 'absolute',
        'top' : f'{height}px',
        'left' : '0',
        'width' : '100%',
        'height' : '115px',
        'padding' : '10px'
    }
    margin_footer = {
        'position' : 'absolute',
        'top' : f'{height+115}px',
        'left' : '0',
        'width' : '100%',
        'height' : '7.2px'
    }
    return footer_style, margin_footer

if __name__ == "__main__":
    app.run_server(debug=True)
