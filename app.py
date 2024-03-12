import json
from typing import Any

import pandas as pd
from dash import Dash, Input, Output, State, html
from dash.exceptions import PreventUpdate

from utils import callback_utils
from utils._data_preprocessing import DataFileHandler
from utils._layout_constructor import LayoutConstructor
from utils._linear_plot_constructor import LinearPlot

app = Dash(
    meta_tags=[
        {'name': 'author', 'content': 'Daria Ovechkina'},
        {'name': 'description', 'content': 'Presonal expenses overview'},
        {'name': 'keywords', 'content': 'dash,plotly,data analysis'},
    ],
    title='Expenses Overview',
)

data_handler = DataFileHandler()
data_handler.generate_tables()

active_days = data_handler.cost.index.get_level_values(1)
start_date = active_days[0]
end_date = active_days[-1]
all_days = pd.date_range(start=start_date, end=end_date)
disabled_days = all_days[~all_days.isin(active_days)]

layout_bulder = LayoutConstructor(disabled_days=disabled_days)
app.layout = layout_bulder.create_layout()


@app.callback(
    Output('date-range-type', 'options'),
    Output('date-range-type', 'value'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
)
def set_date_range_type_options(
    start_date: str,
    end_date: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """Set date range type radio items."""
    range_types = callback_utils.get_data_slice(
        df=data_handler.cost,
        date_range=(start_date, end_date),
    ).index.get_level_values(0)
    return callback_utils.set_radio_options(
        option1='workweek',
        option2='weekend',
        types_list=range_types,
    )


@app.callback(
    Output('item-type', 'options'),
    Output('item-type', 'value'),
    Input('date-range-type', 'value'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
)
def set_item_type_options(
    range_type: str | None,
    start_date: str,
    end_date: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """Set item type radio items."""
    items = callback_utils.get_data_slice(
        df=data_handler.cost,
        date_range=(start_date, end_date),
        date_range_type=range_type,
    ).columns.tolist()
    item_types = [
        data_handler.cat_type_map[data_handler.item_cat_map[item]]
        for item in items
    ]
    return callback_utils.set_radio_options(
        option1='foodstuff',
        option2='household',
        types_list=item_types,
    )


@app.callback(
    Output('item-category', 'options'),
    Input('item-type', 'value'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
    State('date-range-type', 'value'),
)
def set_item_category_options(
    item_types: str | None,
    start_date: str,
    end_date: str,
    range_type: str | None,
) -> list[str]:
    """Set item category dropdown list options."""
    item_type_convert_map = {
        None: [],
        'all': ['foodstuff', 'household'],
        'foodstuff': ['foodstuff'],
        'household': ['household'],
    }
    item_types = item_type_convert_map[item_types]
    return callback_utils.set_dropdown_options(
        df=data_handler.cost,
        date_range=(start_date, end_date),
        date_range_type=range_type,
        parent_value=item_types,
        item_cat_map=data_handler.item_cat_map,
        cat_type_map=data_handler.cat_type_map,
    )


@app.callback(
    Output('item-category', 'value'),
    Input('item-type', 'value'),
    Input('item-category', 'value'),
)
def set_item_category_value(item_types, current_value):
    return callback_utils.correct_dropdown_value(
        parent_comp_id='item-type',
        parent_value=item_types,
        current_value=current_value,
    )


@app.callback(
    Output('item-name', 'options'),
    Input('item-category', 'value'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
    State('date-range-type', 'value'),
    State('item-category', 'options'),
)
def set_item_name_options(
    item_cats: list[str] | None,
    start_date: str,
    end_date: str,
    range_type: str | None,
    categories: list[str] | None,
) -> list[str]:
    """Set item name dropdown list options."""
    if not item_cats:
        item_cats = []
    if item_cats and item_cats[0] == 'All':
        if not categories:
            item_cats = list(set(data_handler.item_cat_map.values()))
        else:
            item_cats = categories[1:]
    return callback_utils.set_dropdown_options(
        df=data_handler.cost,
        date_range=(start_date, end_date),
        date_range_type=range_type,
        parent_value=item_cats,
        item_cat_map=data_handler.item_cat_map,
        cat_type_map=data_handler.cat_type_map,
        is_item_options=True,
    )


@app.callback(
    Output('item-name', 'value'),
    Input('item-category', 'value'),
    Input('item-name', 'value'),
)
def set_item_name_value(item_cats, current_value):
    return callback_utils.correct_dropdown_value(
        parent_comp_id='item-category',
        parent_value=item_cats,
        current_value=current_value,
    )


@app.callback(
    Output('sidebar-error', 'children'),
    Input('submit-button', 'n_clicks'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
    State('item-category', 'value'),
    State('item-name', 'value'),
)
def show_sidebar_error(
    n_clicks: int | None,
    start_date: str,
    end_date: str,
    categories: list[str] | None,
    items: list[str] | None,
) -> html.Span | None:
    """
    Show error message if the input is invalid.

    The input is invalid if the start date goes before the end date
    or no categories or items have been selected.
    """
    if not n_clicks:
        raise PreventUpdate

    error_name_mask_map = {
        'invalid-date-range': (
            pd.to_datetime(start_date) > pd.to_datetime(end_date)
        ),
        'invalid-categories': not categories,
        'invalid-items': not items,
    }
    error_messages = json.load(open('app_text_values.json'))['errors']
    for error in error_messages:
        if error_name_mask_map[error['name']]:
            return layout_bulder.sidebar_builder.set_sidebar_error(
                error['message'],
            )


@app.callback(
    Output('date-picker-range', 'start_date'),
    Output('date-picker-range', 'end_date'),
    Input('clear-button', 'n_clicks'),
)
def clear_sidebar_input(n_clicks: int | None) -> tuple[pd.Timestamp]:
    """Return input values to the default ones when click on 'Clear' button."""
    return start_date, end_date


@app.callback(
    Output('working-input', 'data'),
    Input('submit-button', 'n_clicks'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
    State('date-range-type', 'value'),
    State('item-category', 'value'),
    State('item-category', 'options'),
    State('item-name', 'value'),
    State('item-name', 'options'),
)
def save_user_settings(
    n_clicks: int | None,
    start_date: str,
    end_date: str,
    range_type: str | None,
    chosen_categories: list[str] | None,
    categories: list[str] | None,
    chosen_items: list[str] | None,
    items: list[str] | None,
) -> str:
    """Save user input values."""
    error_mask = (
        pd.to_datetime(start_date) > pd.to_datetime(end_date)
        or not chosen_categories
        or not chosen_items
    )
    if error_mask and n_clicks:
        raise PreventUpdate

    if not chosen_categories:
        chosen_categories = list(set(data_handler.item_cat_map.values()))
    if chosen_categories[0] == 'All':
        chosen_categories = categories[1:]

    if not chosen_items:
        chosen_items = list(data_handler.item_cat_map.keys())
    if chosen_items[0] == 'All':
        chosen_items = items[1:]

    user_settings = {
        'start_date': start_date,
        'end_date': end_date,
        'range_type': range_type,
        'categories': chosen_categories,
        'items': chosen_items,
    }
    return json.dumps(user_settings)


@app.callback(
    Output('sum-days', 'children'),
    Output('sum-per-day', 'children'),
    Output('sum-per-day-per-person', 'children'),
    Output('sum-max-spending', 'children'),
    Output('sum-min-spending', 'children'),
    Input('working-input', 'data'),
)
def update_summaries(user_settings: str) -> int:
    """Count total days in the date range."""
    user_data = json.loads(user_settings)
    working_data = callback_utils.get_data_slice(
        df=data_handler.cost,
        date_range=(user_data['start_date'], user_data['end_date']),
        date_range_type=user_data['range_type'],
    )
    if user_data['items']:
        working_data = working_data.loc[:, user_data['items']]

    dates = working_data.index.get_level_values(1)
    period_lengths = callback_utils.count_period_lengths(data_handler.cost)
    total_days = sum(period_lengths[date_value] for date_value in dates)
    total_cost = working_data.sum().sum()
    min_cost = working_data.sum(axis=1).min()
    max_cost = working_data.sum(axis=1).max()
    cost_per_day = total_cost / total_days
    cost_per_day_per_person = cost_per_day / 4
    return (
        total_days,
        f'₽ {cost_per_day:,.2f}'.replace(',', ' '),
        f'₽ {cost_per_day_per_person:,.2f}'.replace(',', ' '),
        f'₽ {max_cost:,.2f}'.replace(',', ' '),
        f'₽ {min_cost:,.2f}'.replace(',', ' '),
    )


@app.callback(
    Output('total-expenses', 'figure'),
    Input('working-input', 'data'),
)
def set_total_expenses_figure(user_settings):
    """Set total expenses plot."""
    user_data = json.loads(user_settings)
    items = user_data['items']
    if not items:
        cost = data_handler.cost.sum(1)
    else:
        cost = data_handler.cost.loc[:, items].sum(1)

    linear_plot_builder = LinearPlot(
        df=cost,
        user_settings=user_data,
        fig_name='total_expenses',
        yaxis_title='Total, ₽',
        end_start_map=data_handler.end_start_map,
    )
    return linear_plot_builder.create_figure()


if __name__ == '__main__':
    app.run_server(debug=True)
