import json
import time
from datetime import datetime
from pathlib import Path, PosixPath
from typing import ClassVar

import pandas as pd


class DataFileHandler:
    """
    Handle the initial data file.

    Use `generate_tables` to create 6 data structures
    that are accessible as an object attributes:
    - type_cat_map - python `dict` that links an item type
    to the list of corresponding item categories.
    - cat_item_map - python `dict` that links an item category
    to the list of corresponding item names.
    - cost - `pd.DataFrame` with cost of each item per period.
    - cost_others - `pd.DataFrame` with cost of each 'Other expenses' item
    per period.
    - quantity - `pd.DataFrame` with quantity of each item per period.
    - quantity_others - `pd.DataFrame` with quantity of each 'Other expenses'
    item per period.
    """

    APP_DIR: ClassVar[PosixPath] = Path(__file__).parent.parent

    INITIAL_DATA_DIR: ClassVar[PosixPath] = Path(APP_DIR, 'initial_data')
    CSV_DATA_DIR: ClassVar[PosixPath] = Path(INITIAL_DATA_DIR, 'csv_data')
    JSON_DATA_DIR: ClassVar[PosixPath] = Path(INITIAL_DATA_DIR, 'json_data')

    CSV_FILE: ClassVar[PosixPath] = Path(CSV_DATA_DIR, 'products.csv')
    CAT_TO_CHANGE_FILE: ClassVar[PosixPath] = Path(
        JSON_DATA_DIR,
        'cat_to_change.json',
    )
    ITEMS_TO_UNITE_FILE: ClassVar[PosixPath] = Path(
        JSON_DATA_DIR,
        'items_to_unite.json',
    )
    MEANINGFUL_OTHERS_ITEMS_FILE: ClassVar[PosixPath] = Path(
        JSON_DATA_DIR,
        'meaningful_others.json',
    )
    TRANSLATE_VOC_FILE: ClassVar[PosixPath] = Path(
        JSON_DATA_DIR,
        'translation_dict.json',
    )

    UNNECESSARY_FIRST_ROWS_COUNT: ClassVar[int] = 1
    UNNECESSARY_LAST_ROWS_COUNT: ClassVar[int] = 2
    UNNECESSARY_FIRST_COLS_COUNT: ClassVar[int] = 4

    FOOD_TYPE_NAME: ClassVar[str] = 'Foodstuff'
    NON_FOOD_TYPE_NAME: ClassVar[str] = 'Household'
    NON_FOOD_CATEGORIES: ClassVar[tuple[str]] = (
        'Cat supplies',
        'Household items',
        'Other expenses',
    )

    def __init__(self) -> None:
        """Initialize the dataframe."""
        self.df = pd.read_csv(
            self.CSV_FILE,
            sep=';',
            index_col=[0, 1],
        )

    def __rename_index_values(
        self,
        row: pd.Series,
        name_cat_map: dict[str, str],
    ) -> pd.Series:
        """Rename index category (in combine with reset_index())."""
        if row['name'] in name_cat_map.keys():
            row['category'] = name_cat_map[row['name']]
        return row

    def __handle_others_items(self) -> dict[str, str | list]:
        """
        Find other expenses items that should be united.

        Read the file, find indexes of items to be united
        and save them as key 'items_to_unite' value. Also save the data
        of united items as it's needed in the app.
        """
        others = json.load(open(self.MEANINGFUL_OTHERS_ITEMS_FILE))

        level_0_cond = self.df.index.get_level_values(0) == others['category']
        level_1_cond = ~self.df.index.get_level_values(1).isin(
            others['meaningful_items'],
        )
        others_to_unite = self.df[
            (level_0_cond) & (level_1_cond)
        ].index.tolist()
        others['items_to_unite'] = others_to_unite
        others.pop('meaningful_items')

        self.others_exp = self.df.loc[level_0_cond, :]
        return others

    def __delete_interim_aggregation(self) -> None:
        """
        Delete interim results by month.

        An intermediate result contains 3 columns: a first one with date
        interval for cost sum, a second one for quantity total and last
        'Info' column for additional data. Iterate through column names,
        find this pattern and add it to the list of columns that should
        be deleted.
        """
        col_names = self.df.columns.tolist()
        cols_to_delete: list[str] = []
        for idx, col in enumerate(col_names):
            if col.startswith('Info'):
                cols_to_delete.extend(
                    (col, col_names[idx - 1], col_names[idx - 2]),
                )
        self.df.drop(columns=cols_to_delete, inplace=True)

    def __delete_unnecessary_data(self) -> None:
        """
        Delete excessive rows and columns.

        Remove unnecessary rows from the start and the end of the dataframe.
        Do the same with first columns.
        """
        rows_start = self.UNNECESSARY_FIRST_ROWS_COUNT
        rows_end = self.df.shape[0] - self.UNNECESSARY_LAST_ROWS_COUNT
        cols_start = self.UNNECESSARY_FIRST_COLS_COUNT
        self.df = self.df.iloc[
            rows_start: rows_end,
            cols_start:,
        ]

    def __correct_values(self) -> None:
        """
        Correct values in dataframe.

        Remove whitespaces, replace commas to dots, convert values to
        numeric dtypes and fill missing values with zeros.
        """
        self.df = self.df.apply(
            lambda x: pd.to_numeric(
                x.str.replace('\xa0', '').str.replace(',', '.'),
            ),
            axis=1,
        ).fillna(0)

    def __correct_index(self) -> None:
        """
        Correct the dataframe index.

        Fill missing values in category column by last valid observation,
        strip whitespaces from category and item names and change a category
        value for the given item names.
        """
        cat_to_change_file = json.load(open(self.CAT_TO_CHANGE_FILE))

        name_cat_map = {
            e['item_name']: e['new_category'] for e in cat_to_change_file
        }

        self.df = self.df.reset_index(
            names=['category', 'name'],
        ).ffill().apply(
            lambda x: x.str.strip() if x.name in ['category', 'name'] else x,
        ).apply(
            self.__rename_index_values, name_cat_map=name_cat_map, axis=1,
        ).set_index(
            ['category', 'name'],
        )

    def __unite_items(self) -> None:
        """
        Unite items that are similar in meaning.

        Read the data file and save it to the list. Handle other expenses
        file and add it to the list. For every batch of items
        to be united summarize corresponding rows and add result as
        the new row. After all drop all used items.
        """
        unite_items_list = json.load(open(self.ITEMS_TO_UNITE_FILE))

        other_items = self.__handle_others_items()
        unite_items_list.append(other_items)
        drop_items_list: list[tuple[str, str]] = []

        for elem in unite_items_list:
            new_idx = (elem['category'], elem['new_item'])
            self.df.loc[new_idx, :] = self.df.loc[elem['items_to_unite']].sum()
            drop_items_list.extend(map(tuple, elem['items_to_unite']))
        self.df.drop(drop_items_list, axis=0, inplace=True)

    def __delete_zero_rows(self) -> None:
        """Delete rows that consist of zeros."""
        self.df = self.df.loc[(self.df != 0).any(axis=1)]

    def __translate_index(self) -> None:
        """Translate index values."""
        translate_voc = json.load(open(self.TRANSLATE_VOC_FILE))

        dataframe_names = ('df', 'others_exp')
        for attr in dataframe_names:
            getattr(self, attr).set_index(
                map(
                    lambda x: (translate_voc[x[0]], translate_voc[x[1]]),
                    getattr(self, attr).index.tolist(),
                ),
                inplace=True,
            )

    def __data_preprocess(self) -> None:
        """
        Preprocess the initial data file.

        - delete intermediate aggregation by month.
        - remove unnecessary rows and columns.
        - correct values.
        - correct index values.
        - unite similar items.
        - delete rows that consist of zeros.
        - translate index values.
        """
        self.__delete_interim_aggregation()
        self.__delete_unnecessary_data()
        self.__correct_values()
        self.__correct_index()
        self.__unite_items()
        self.__delete_zero_rows()
        self.__translate_index()

    def __create_cat_item_map(self) -> dict[str, list]:
        """Create dict to link a category to the corresponding item names."""
        cat_item_map = {}
        for cat, item in self.df.index:
            cat_item_map.setdefault(cat, []).append(item)
        return cat_item_map

    def __create_type_category_map(self) -> dict[str, list]:
        """Create dict to link a type to the corresponding categories."""
        type_cat_map = {
            self.FOOD_TYPE_NAME: [],
            self.NON_FOOD_TYPE_NAME: [],
        }
        for cat in self.df.index.get_level_values(0).unique():
            if cat in self.NON_FOOD_CATEGORIES:
                type_cat_map[self.NON_FOOD_TYPE_NAME].append(cat)
            else:
                type_cat_map[self.FOOD_TYPE_NAME].append(cat)
        return type_cat_map

    def __create_new_index(self, current_idx: str):
        """Create tuple (date type, timestamp) for new index."""
        split_idx = current_idx.split(' - ')
        idx_timestamp = datetime.strptime(split_idx[-1], '%d.%m.%Y')
        if split_idx[0] == split_idx[-1]:
            return ('weekend', idx_timestamp)
        return ('workweek', idx_timestamp)

    def __create_final_dataframe(
        self,
        df_idx: list[datetime],
        initial_df_attr: str,
        is_quantity_df: bool,
    ) -> pd.DataFrame:
        """
        Create cost or quantity dataframe.

        Args:
        - df_idx - a `list` of timestamps to be used as the dataframe index.
        - initial_df_attr - a name of the initial dataframe from which
        the new one shoud be created.
        - is quantity_df - a bool value to create either cost or quantity
        dataframe.

        Item names are used as column names, categories are ignored.
        """
        start_col_idx = int(is_quantity_df)
        return pd.DataFrame(
            getattr(self, initial_df_attr).iloc[:, start_col_idx::2].T.values,
            columns=getattr(self, initial_df_attr).index.get_level_values(1),
            index=pd.MultiIndex.from_tuples(df_idx),
        )

    def generate_tables(self):
        """
        Generate clear data to be used in the app.

        Create 6 data structures as the object attributes:
        - type_cat_map - python `dict` that links an item type
        to the list of corresponding item categories.
        - cat_item_map - python `dict` that links an item category
        to the list of corresponding item names.
        - cost - `pd.DataFrame` with cost of each item per period.
        - cost_others - `pd.DataFrame` with cost of each 'Other expenses'
        item per period.
        - quantity - `pd.DataFrame` with quantity of each item per period.
        - quantity_others - `pd.DataFrame` with quantity of each
        'Other expenses' item per period.
        """
        self.__data_preprocess()

        dt_idxs = list(
            map(
                self.__create_new_index,
                self.df.loc[:, ::2].columns,
            ),
        )
        self.cat_item_map = self.__create_cat_item_map()
        self.type_cat_map = self.__create_type_category_map()
        self.cost = self.__create_final_dataframe(
            df_idx=dt_idxs,
            initial_df_attr='df',
            is_quantity_df=False,
        )
        self.quantity = self.__create_final_dataframe(
            df_idx=dt_idxs,
            initial_df_attr='df',
            is_quantity_df=True,
        )
        self.cost_others = self.__create_final_dataframe(
            df_idx=dt_idxs,
            initial_df_attr='others_exp',
            is_quantity_df=False,
        )
        self.quantity_others = self.__create_final_dataframe(
            df_idx=dt_idxs,
            initial_df_attr='others_exp',
            is_quantity_df=True,
        )


if __name__ == '__main__':
    df_handler = DataFileHandler()
    start = time.time()
    df = df_handler.generate_tables()
    end = time.time()
    print(f'Generate clear data for {end - start:.3f}s.')
