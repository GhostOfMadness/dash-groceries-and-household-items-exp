"""Util functions for app callbacks."""
from typing import Any, Sequence

import pandas as pd
from dash import ctx


def get_data_slice(
    df: pd.DataFrame,
    date_range: Sequence[str],
    date_range_type: str | None = None,
) -> pd.DataFrame:
    """
    Slice the initial data.

    Get data slice by the given date range and the range type.
    Then left only non-zero columns.
    """
    if date_range_type is None or date_range_type == 'all':
        date_range_type = df.index.get_level_values(0).unique().tolist()
    df_slice = df.loc(axis=0)[date_range_type, slice(*date_range)]
    return df_slice.loc[:, (df_slice != 0).any(axis=0)]


def set_radio_options(
    option1: str,
    option2: str,
    types_list: list[str],
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Set radio items options and pick the default value.

    Pick first option with `disabled=False` as default value.
    If all options are disabled (when date range in invalid), return None.
    """
    option1_dis_cond = option1 not in types_list
    option2_dis_cond = option2 not in types_list
    value_disabled_status_map = {
        'all': option1_dis_cond or option2_dis_cond,
        option1: option1_dis_cond,
        option2: option2_dis_cond,
    }
    options = [
        {
            'label': key.capitalize(),
            'value': key,
            'disabled': value,
        }
        for key, value in value_disabled_status_map.items()
    ]
    value = next(
        (opt['value'] for opt in options if opt['disabled'] is False),
        None,
    )
    return options, value


def set_dropdown_options(
    df: pd.DataFrame,
    date_range: Sequence[str],
    date_range_type: str | None,
    parent_value: list[str] | None,
    item_cat_map: dict[str, str],
    cat_type_map: dict[str, str] | None,
    is_item_options: bool = False,
) -> list[str]:
    """
    Set dropdown list options.

    Select item categories or item names (depending on `is_item_options`
    argument), sort the result and add the 'All' option to the beginning.
    """
    items = get_data_slice(
        df=df,
        date_range=date_range,
        date_range_type=date_range_type,
    ).columns.tolist()
    options = [
        item if is_item_options else item_cat_map[item]
        for item in items
        if item_cat_map[item] in parent_value
        or cat_type_map[item_cat_map[item]] in parent_value
    ]
    options = list(set(options))
    options.sort()
    if options:
        options.insert(0, 'All')
    return options


def correct_dropdown_value(
    parent_comp_id: str,
    parent_value: Any | None,
    current_value: list[str],
) -> list[str]:
    """
    Correct dropwdown value.

    'All' is the default value for a dropdown list.
    If any other option is chosen, the 'All' option is removed
    from selected ones and cannot be added again
    until the input field is cleared.
    """
    comp_id = ctx.triggered_id
    if comp_id == parent_comp_id:
        return ['All'] if parent_value else []
    if len(current_value) > 1 and 'All' in current_value:
        current_value.remove('All')
    return current_value
