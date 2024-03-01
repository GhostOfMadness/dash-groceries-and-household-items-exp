import json
from typing import Any

import pandas as pd
from dash import Dash, Input, Output, State, html
from dash.exceptions import PreventUpdate

from utils import callback_utils
from utils._data_preprocessing import DataFileHandler
from utils._layout_constructor import LayoutConstructor

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
)
def set_item_name_options(
    item_cats: list[str] | None,
    start_date: str,
    end_date: str,
    range_type: str | None,
) -> list[str]:
    """Set item name dropdown list options."""
    if item_cats and item_cats[0] == 'All':
        item_cats = list(set(data_handler.item_cat_map.values()))
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
    State('item-name', 'value'),
)
def save_user_settings(
    n_clicks: int | None,
    start_date: str,
    end_date: str,
    range_type: str | None,
    categories: list[str] | None,
    items: list[str] | None,
):
    """Save user input values."""
    error_mask = (
        pd.to_datetime(start_date) > pd.to_datetime(end_date)
        or not categories
        or not items
    )
    if error_mask and n_clicks:
        raise PreventUpdate

    user_settings = {
        'start_date': start_date,
        'end_date': end_date,
        'range_type': range_type,
        'categories': categories,
        'items': items,
    }
    return json.dumps(user_settings)


@app.callback(
    Output('sum-days', 'children'),
    Input('working-input', 'data'),
)
def update_sum_days(working_data):
    data = json.loads(working_data)
    print(data)
    return 1


if __name__ == '__main__':
    app.run_server(debug=True)
