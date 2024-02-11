import time

import pandas as pd
from datetime import datetime
import re

# Helper function to correct a date format
def correct_date(str_date):
    day, month, year = re.findall(r'[0-9]+.[0-9]+.[0-9]+', str_date)[0].split('.')
    if len(day) < 2:
        day = '0' + day
    if len(month) < 2:
        month = '0' + month
    if len(year) < 4:
        year = '20' + year
    return '.'.join([day, month, year])

# Helper function to determine an item's position in the index
def find_idx(df, product_name):
    return df[df['product_name'] == product_name].index[0]

# Helper function to unite and delete rows
def unite_and_delete_rows(df, category, product_name, idxs_list):
    new_row = [category, product_name]
    sum_values = df.loc[idxs_list[0], :]
    for i in range(1, len(idxs_list)):
        sum_values += df.loc[idxs_list[i], :]
    new_row += list(sum_values.values[2:])
    df.loc[max(df.index) + 1] = new_row
    df = df.drop(labels=idxs_list, axis=0)
    return df

# Main function to preprocess data
def data_preprocessing(df):

    ## delete "Info" columns
    columns = df.columns.tolist()
    columns_to_delete = [re.findall(r'Info.*', str(col))[0] for col in columns \
                         if len(re.findall(r'Info.*', str(col))) > 0]
    clean_df = df.drop(columns_to_delete, axis=1)

    ## delete intermediate aggregation
    columns = clean_df.columns.tolist()
    columns_to_delete = []
    for i in range(len(columns)):
        col_split = str(columns[i]).split('-')
        if len(col_split) == 2 and col_split[1] != '':
            fmt = '%d.%m.%Y'
            delta = datetime.strptime(correct_date(col_split[1]), fmt) -\
                datetime.strptime(correct_date(col_split[0]), fmt)
            if delta.days > 15:
                columns_to_delete.append(columns[i])
                columns_to_delete.append(columns[i + 1])
    clean_df = clean_df.drop(columns=columns_to_delete)

    ## fill missing values in the product's category column
    clean_df['Unnamed: 0'] = clean_df['Unnamed: 0'].fillna(method='ffill')

    ## delete columns corresponding to dates before 13th February, 2021
    columns_to_keep = [i for i in range(clean_df.shape[1]) if i not in [2, 3, 4, 5]]
    clean_df = clean_df.iloc[:, columns_to_keep]

    ## delete the first and the last two lines
    clean_df = clean_df.drop(clean_df.index[[0, -2, -1]])

    ## correct columns names
    columns_names = clean_df.columns.tolist()
    columns_names[0], columns_names[1] = 'category', 'product_name'
    for i in range(2, len(columns_names)):
        if str(columns_names[i]).count('.') == 2:
            columns_names[i] = datetime.strptime(str(columns_names[i]), '%d.%m.%Y')
        if str(columns_names[i]).count('.') in [3, 5] or 'Unnamed' in str(columns_names[i]):
            columns_names[i] = str(columns_names[i - 1]) + '.q'
    clean_df.columns = columns_names

    ## delete unnecessary spaces from items names
    clean_df['product_name'] = clean_df['product_name'].apply(lambda x: x.strip())

    ## fill missing numeric values by zero
    clean_df = clean_df.fillna(0)

    ## change the category for some items
    clean_df.loc[find_idx(clean_df, 'Ирис') ,'category'] = 'Кондитерские изделия'
    clean_df.loc[
        find_idx(
            clean_df, 'Украшения для выпечки'
        ) ,'category'] = 'Бакалея'

    ## change items names to avoid duplicates
    change_prod_names = {
        ('Консервы', 'Говядина') : 'Говядина (консервированная)',
        ('Консервы', 'Горбуша') : 'Горбуша (консервированная)',
        ('Консервы', 'Свинина') : 'Свинина (консервированная)',
        ('Консервы', 'Скумбрия') : 'Скумбрия (консервированная)',
        ('Консервы', 'Тунец') : 'Тунец (консервированный)'

    }
    for key, value in change_prod_names.items():
        clean_df.loc[clean_df[(clean_df['category'] == key[0]) & (clean_df['product_name'] == key[1])].index[0],
                     'product_name'] = value

    ## correct the format of numeric values
    for col in clean_df.columns[2:]:
        clean_df[col] = clean_df[col].apply(lambda x: float(str(x).replace(',', '.').replace('\xa0', '')))

    ## unite rows that are similar in meaning
    unite_delete_dict = {
        ('Молочные продукты', 'Кисломолочные напитки') : [
            find_idx(clean_df, 'Актимель'),
            find_idx(clean_df, 'Иммуноцея, варенец, ацидофилин'),
            find_idx(clean_df, 'Молочный коктейль'),
            find_idx(clean_df, 'Снежок')
        ],
        ('Молочные продукты', 'Сыр') : [
            find_idx(clean_df, 'Сыр (весовой)'),
            find_idx(clean_df, 'Сыр плавленный, фетакса, рикотта и др.')
        ],
        ('Мясные продукты', 'Копченое мясо') : [
            find_idx(clean_df, 'Бекон'),
            find_idx(clean_df, 'Бекон (весовой), карпаччо'),
            find_idx(clean_df, 'Шпик, грудинка, окорок, сало, корейка')
        ],
        ('Рыба', 'Копченая рыба') : [
            find_idx(clean_df, 'Горбуша (копченая)'),
            find_idx(clean_df, 'Скумбрия (копченая)')
        ],
        ('Консервы', 'Икра красная') : [
            find_idx(clean_df, 'Икра красная'),
            find_idx(clean_df, 'Икра лососевая')
        ],
        ('Рыба', 'Морепродукты') : [
            find_idx(clean_df, 'Мидии'),
            find_idx(clean_df, 'Морской коктейль (в масле), кальмар в рассоле'),
            find_idx(clean_df, 'Паста из морепродуктов'),
            find_idx(clean_df, 'Икра мойвы')
        ],
        ('Соусы', 'Соусы (разные виды)') : [
            find_idx(clean_df, 'Брусничный соус'),
            find_idx(clean_df, 'Сальса, терияки'),
            find_idx(clean_df, 'Соевый соус')
        ],
        ('Бакалея', 'Сухофрукты (кроме изюма, кураги, чернослива)') : [
            find_idx(clean_df, 'Бананы сушеные'),
            find_idx(clean_df, 'Инжир (сушеный)'),
            find_idx(clean_df, 'Клубника (сушеная)'),
            find_idx(clean_df, 'Клюква (сушеная)'),
            find_idx(clean_df, 'Финики')
        ],
        ('Бакалея', 'Ингредиенты для выпечки') : [
            find_idx(clean_df, 'Дрожжи, разрыхлитель'),
            find_idx(clean_df, 'Кокосовая стружка'),
            find_idx(clean_df, 'Мак'),
            find_idx(clean_df, 'Тесто')
        ],
        ('Бакалея', 'Хлебцы') : [
            find_idx(clean_df, 'Галеты (крекеры)'),
            find_idx(clean_df, 'Хлебцы')
        ],
        ('Бакалея', 'Сахар') : [
            find_idx(clean_df, 'Сахар'),
            find_idx(clean_df, 'Пудра сахарная')
        ],
        ('Бакалея', 'Орехи, семечки') : [
            find_idx(clean_df, 'Орехи, семечки'),
            find_idx(clean_df, 'Семечки (подсолнуха, тыквенные)')
        ],
        ('Бакалея', 'Продукты быстрого приготовления') : [
            find_idx(clean_df, 'Лапша быстрого приготовления (пюре)'),
            find_idx(clean_df, 'Смесь для супа, суп быстрого приготовления')
        ],
        ('Кондитерские изделия', 'Зефир, пастила, лукум') : [
            find_idx(clean_df, 'Зефир'),
            find_idx(clean_df, 'Пастила'),
            find_idx(clean_df, 'Лукум')
        ],
        ('Кондитерские изделия', 'Баранки и сушки') : [
            find_idx(clean_df, 'Баранки'),
            find_idx(clean_df, 'Сухари (сладкие)'),
            find_idx(clean_df, 'Сушки, хлебные палочки')
        ],
        ('Кондитерские изделия', 'Десерт') : [
            find_idx(clean_df, 'Десерт (суфле, панна-котта, желе)'),
            find_idx(clean_df, 'Пирог, пирожное, торт')
        ],
        ('Консервы', 'Консервированная рыба') : [
            find_idx(clean_df, 'Горбуша (консервированная)'),
            find_idx(clean_df, 'Сайра (консервированная)'),
            find_idx(clean_df, 'Скумбрия (консервированная)'),
            find_idx(clean_df, 'Тунец (консервированный)'),
            find_idx(clean_df, 'Шпроты')
        ],
        ('Консервы', 'Печень рыбная') : [
            find_idx(clean_df, 'Печень минтая'),
            find_idx(clean_df, 'Печень трески')
        ],
        ('Товары для дома', 'Чистящие средства') : [
            find_idx(clean_df, 'Средство для пола'),
            find_idx(clean_df, 'Чистящее средство (пемолюкс, для туалета и т.д.)')
        ],
        ('Товары для дома', 'Средства для волос') : [
            find_idx(clean_df, 'Средство для волос'),
            find_idx(clean_df, 'Шампунь')
        ]
    }
    others_idx = list(range(find_idx(clean_df, 'Аптечка'), find_idx(clean_df, 'Штора для ванной') + 1))
    useful_others = [
        find_idx(clean_df, 'Канцтовары'),
        find_idx(clean_df, 'Очки'),
        find_idx(clean_df, 'Носки'),
        find_idx(clean_df, 'Одноразовая посуда'),
        find_idx(clean_df, 'Пакет (обычный)'),
        find_idx(clean_df, 'Посуда')
    ]
    others_idx_final = [i for i in others_idx if i not in useful_others]
    unite_delete_dict['Остальные расходы', 'Прочие товары'] = others_idx_final
    others_data = clean_df.loc[others_idx]
    for key, value in unite_delete_dict.items():
        clean_df = unite_and_delete_rows(clean_df, key[0], key[1], value)

    ## create the dataframe "product category -> product type"
    subcat_cat = pd.DataFrame({
        'category' : [
            'Товары' if val in ['Товары для дома', 'Товары для кота', 'Остальные расходы'] else 'Продукты' \
            for val in clean_df['category'].unique()
        ]
    }, index=clean_df['category'].unique()).sort_values(by='category')

    ## create the dataframe "product name -> product category"
    prod_subcat = clean_df[['category', 'product_name']].\
        sort_values(by=['category', 'product_name']).\
        set_index('product_name')
    prod_subcat.columns = ['subcategory']

    ## сreate dataframes with cost values (main and for items in "Other expenses" category)
    cost_columns = [col for col in clean_df.columns.tolist() if '.q' not in str(col)]
    cost = clean_df[cost_columns].drop('category', axis=1).set_index('product_name').T
    cost_others = others_data[cost_columns].drop('category', axis=1).set_index('product_name').T

    ## create dataframes with quantity values (main and for items in "Other expenses" category)
    quantity_columns = [col for col in clean_df.columns.tolist() if '.q' in str(col)]
    quantity_columns.insert(0, 'product_name')
    quantity = clean_df[quantity_columns].set_index('product_name').T
    quantity['Яйца куриные'] = quantity['Яйца куриные'] * 10
    quantity['Яйца перепелиные'] = quantity['Яйца перепелиные'] * 20
    quantity_others = others_data[quantity_columns].set_index('product_name').T

    ## delete columns that are fully consisting of zeros from the cost dataframe
    ## and corresponding columns from the quantity dataframe and rows from the prod_subcat dataframe
    zero_columns = [col for col in cost.columns if cost[col].sum() == 0]
    cost.drop(zero_columns, axis=1, inplace=True)
    quantity.drop(zero_columns, axis=1, inplace=True)
    prod_subcat.drop(zero_columns, axis=0, inplace=True)

    ## create table with lengths of periods
    period_len = {}
    for idx in cost.index:
        if str(idx).count('-') == 1:
            start_date = datetime.strptime(correct_date(idx.split('-')[0]), '%d.%m.%Y')
            end_date = datetime.strptime(correct_date(idx.split('-')[1]), '%d.%m.%Y')
            period_len[end_date] = (end_date - start_date).days
        else:
            period_len[idx] = 1
    period_len_df = pd.DataFrame(period_len.values(), index=period_len.keys())
    period_len_df.replace(1, 0, inplace=True)

    ## set index values for cost dataframes and quantity dataframes
    ## (main and for items in "Other expenses" category)
    cost.index = period_len.keys()
    quantity.index = period_len.keys()
    cost_others.index = period_len.keys()
    quantity_others.index = period_len.keys()

    return subcat_cat, prod_subcat, cost, quantity, cost_others, quantity_others, period_len_df


if __name__ == '__main__':
    df = pd.read_csv('data/Products.csv', delimiter=';')
    total_time = 0
    for _ in range(100):
        start = time.time()
        data_preprocessing(df)
        end = time.time()
        total_time += end - start
    print(total_time/ 100)
