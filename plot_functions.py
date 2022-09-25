import locale
from math import ceil
import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.exceptions import PreventUpdate
from dash import dash_table
from dash.dash_table.Format import Format, Scheme, Symbol

# Content
# 1. Total expenses by period
# 2. Items' cost shares and Items' quantity shares
# 3. Others expenses table
# 4. Items' number by period and Median cost per item by period (update by hover data)
# 5. Interrelation between an items' number and a median cost per item

# 1. Total expenses by period
## 1.1. Ticks' values and positions on the x-axis
def tick_vals_text_xaxis(df):
    if df.index[0].month == 12:
        start_date = f'{df.index[0].year + 1}-01-01'
    elif df.index[0].month >= 9:
        start_date = f'{df.index[0].year}-{df.index[0].month + 1}-01'
    else:
        start_date = f'{df.index[0].year}-0{df.index[0].month + 1}-01'
    if df.index[-1].month >= 10:
        end_date = f'{df.index[-1].year}-{df.index[-1].month}-01'
    else:
        end_date = f'{df.index[-1].year}-0{df.index[-1].month}-01'
    dates = pd.date_range(start=start_date, end=end_date, freq='MS').tolist()
    unique_years = df.index.year.unique()
    start_year_i = [[d.year for d in dates].index(year) for year in unique_years]
    ticktext = []
    for i in range(len(dates)):
        text = dates[i].strftime('%b').capitalize()
        if i in start_year_i:
            ticktext.append(text + f'<br>{dates[i].year}')
        else:
            ticktext.append(text)
    return dates, ticktext

## 1.2. Determine neighboring values for a date in the array
def find_borders(arr, x):
    low, high, mid = 0, len(arr) - 1, 0
    while high - low > 1:
        mid = (low + high) // 2
        if x < arr[mid]:
            high = mid
        elif x > arr[mid]:
            low = mid
        else:
            low, high = mid, mid
    return low, high

## 1.3. Determine holidays' points positions and the annotation text for them
def add_holidays_dates(df, lang_dict):
    filtered_df = df[df['in_range'] == 1]
    unique_years = df.index.year.unique()
    holidays = {
        lang_dict['christmas_holiday']: '07.01',
        lang_dict['defender_day_holiday']: '23.02',
        lang_dict['iwd_holiday']: '08.03',
        lang_dict['son_birthday_holiday']: '04.04',
        lang_dict['daughter_birthday_holiday']: '17.04',
        lang_dict['worker_holiday'] : '01.05',
        lang_dict['victory_holiday'] : '09.05',
        lang_dict['mom_birthday_holiday']: '19.05',
        lang_dict['dad_birthday_holiday']: '08.10',
        lang_dict['unity_holiday'] : '04.11',
        lang_dict['new_year_holiday']: '31.12'
    }
    holidays_dates = []
    for h, d in holidays.items():
        for year in unique_years:
            date = pd.to_datetime(f'{d}.{year}', format='%d.%m.%Y')
            if filtered_df.index[0] <= date <= filtered_df.index[-1]:
                holidays_dates.append((h, date))
    marker_positions = []
    for hd in holidays_dates:
        low, high = find_borders(filtered_df.index, hd[1])
        b = filtered_df.iloc[low, 0]
        if low != high:
            k = (filtered_df.iloc[high, 0] - filtered_df.iloc[low, 0]) \
            / (filtered_df.index[high] - filtered_df.index[low]).days
        else:
            k = 0
        pos = k * (hd[1] - filtered_df.index[low]).days + b
        marker_positions.append(pos)
    return marker_positions, holidays_dates

## 1.4 Determine a word ending based on the value
def word_ending(word, value):
    ending = ''
    if word == 'наименован':
        if str(value)[-1] == '1' and str(value)[-2:] != '11':
            ending = 'ие'
        elif str(value)[-1] in ['2', '3', '4'] and str(value)[-2:] not in ['12', '13', '14']:
            ending = 'ия'
        else:
            ending = 'ий'
    else:
        if value != 1:
            ending = 's'
    return ending


## 1.5. Create a single linear graph
def one_linear_graph(fig, graph_type, df, start, end, period_df, name, lang_dict, bar_color, holiday_color, row=1, col=1, showlegend=True):
    fig.add_trace(go.Bar(
        x=df.index,
        y=df[0],
        marker_color=bar_color,
        width=345600000,
        hoverinfo='skip',
        hovertemplate=None,
        name=name,
        showlegend=showlegend
    ), row=row, col=col)
    if name == lang_dict['store_kind_option_hyper']:
        if graph_type == 'items_count':
            text = []
            for idx in df[df['in_range'] == 1].index:
                items_word = lang_dict["items"] + word_ending(lang_dict["items"], df.loc[idx, 0])
                line = f'<b>{df.loc[idx, 0]} {items_word}</b> {lang_dict["for"]} <i>{idx.strftime("%Y-%m-%d")}</i><extra></extra>'
                text.append(line)
        else:
            text = [
                f'<b>{df.loc[idx, 0]:.2f} {lang_dict["rubles"]}</b> {lang_dict["for"]} <i>{idx.strftime("%Y-%m-%d")}</i><extra></extra>'
                for idx in df[df['in_range'] == 1].index
            ]
    else:
        start_date_text = [
            (i - timedelta(days=int(period_df.loc[i][0]))).strftime('%Y-%m-%d') for i in df[df['in_range'] == 1].index
        ]
        text = []
        for i in range(len(df[df['in_range'] == 1].index)):
            end_date_i = df[df['in_range'] == 1].index[i].strftime('%Y-%m-%d')
            value = df[df['in_range'] == 1].iloc[i, 0]
            if graph_type == 'items_count':
                items_word = lang_dict["items"] + word_ending(lang_dict["items"], value)
                line = f'<b>{value} {items_word}</b> {lang_dict["for_period"]}<extra></extra><br>{lang_dict["from"]} <i>{start_date_text[i]}</i> {lang_dict["to"]} <i>{end_date_i}</i>'
            else:
                line = f'<b>{value:.2f} {lang_dict["rubles"]}</b> {lang_dict["for_period"]}<extra></extra><br>{lang_dict["from"]} <i>{start_date_text[i]}</i> {lang_dict["to"]} <i>{end_date_i}</i>'
            text.append(line)
    fig.add_trace(go.Scatter(
        x=df[df['in_range'] == 1].index,
        y=df[df['in_range'] == 1][0],
        mode='lines+markers',
        line=dict(color='#382250', dash='dot', width=2),
        hovertemplate='%{text}',
        text=text,
        hoverlabel = {
            'bgcolor' : '#FFFFFF',
            'font_size' : 16,
            'bordercolor' : '#000000',
            'font_family' : 'Source Sans Pro, sans-serif'
        },
        showlegend=False
    ), row=row, col=col)
    marker_positions = add_holidays_dates(df, lang_dict)[0]
    holidays_dates = add_holidays_dates(df, lang_dict)[1]
    fig.add_trace(
        go.Scatter(
            x=[hd[1] for hd in holidays_dates],
            y=marker_positions,
            mode='markers',
            marker_symbol='star',
            marker_line_color='#382250',
            marker_color=holiday_color,
            marker_size=8,
            marker_line_width=1,
            hovertemplate='<b>%{text}</b><br><i>%{x|%Y-%m-%d}</i><extra></extra>',
            text=[hd[0] for hd in holidays_dates],
            hoverlabel = {
                'bgcolor' : '#FFFFFF',
                'font_size' : 16,
                'bordercolor' : '#000000',
                'font_family' : 'Source Sans Pro, sans-serif'
            },
            showlegend=False
        ), row=row, col=col
    )
    max_sum = df[df['in_range'] == 1][0].max()
    max_sum_date = df[(df[0] == max_sum) & (df['in_range'] == 1)].index[0]
    fig.add_vrect(
        x0=max_sum_date - timedelta(days=3),
        x1=max_sum_date + timedelta(days=3),
        fillcolor='#DB311B',
        annotation_text=f'<b>{lang_dict["max"]}</b>',
        annotation_position='outside top right',
        line_width=0,
        opacity=0.4,
        annotation_font_size=12,
        annotation_font_color='#000000',
        annotation_borderwidth=1,
        annotation_bordercolor='#382250',
        annotation_bgcolor='#FFFFFF',
        row=row, col=col
    )
    min_sum = df[df['in_range'] == 1][0].min()
    min_sum_date = df[(df[0] == min_sum) & (df['in_range'] == 1)].index[0]
    fig.add_vrect(
        x0=min_sum_date - timedelta(days=3),
        x1=min_sum_date + timedelta(days=3),
        fillcolor='#0DB268',
        annotation_text=f'<b>{lang_dict["min"]}</b>',
        annotation_position='outside bottom left',
        line_width=0,
        opacity=0.4,
        annotation_font_size=12,
        annotation_font_color='#000000',
        annotation_borderwidth=1,
        annotation_bordercolor='#382250',
        annotation_bgcolor='#FFFFFF',
        row=row, col=col
    )
    if df[df['in_range'] == 1].index[0] != df.index[0]:
        fig.add_vrect(
            x0=df[df.index < start].index[0] - timedelta(days=2),
            x1=df[df.index < start].index[-1] + timedelta(days=2),
            fillcolor='#FFFFFF',
            line_width=0,
            opacity=0.65,
            row=row, col=col
        )
    if df[df['in_range'] == 1].index[-1] != df.index[-1]:
        fig.add_vrect(
            x0=df[df.index > end].index[0] - timedelta(days=2),
            x1=df[df.index > end].index[-1] + timedelta(days=2),
            fillcolor='#FFFFFF',
            line_width=0,
            opacity=0.65,
            row=row, col=col
        )
## 1.6 Modify rounding function
def round_function(k):
    if k < 1:
        return 1
    elif k < 10:
        return k
    elif k < 1000:
        return ceil(k / 10) * 10
    elif k < 100000:
        return ceil(k / 100) * 100

## 1.7. Create full linear graph:
## If the shop kind value is "All", create two single linear graphs with the shared x-axis.
## Draw one single graph in other cases.
def linear_graph(df, period_df, start_date_hyper, end_date_hyper, start_date_super, end_date_super, items, lang, sk_value, lang_dict, graph_type):
    if lang == 'English':
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    N = 4
    dff = df[items].sum(axis=1).to_frame() if graph_type == 'cost_count' else df
    hyper_data = dff.loc[period_df[period_df[0] == 0].index]
    hyper_data['in_range'] = [
        1 if start_date_hyper <= i <= end_date_hyper else 0 for i in hyper_data.index]
    super_data = dff.loc[period_df[period_df[0] != 0].index]
    super_data['in_range'] = [
        1 if start_date_super <= i <= end_date_super else 0 for i in super_data.index]
    hyper_step = round_function(hyper_data[0].max() / N)
    super_step = round_function(super_data[0].max() / N)
    if graph_type == 'cost_count':
        super_name = '/<br>'.join(map(lambda x: x.strip(), lang_dict['store_kind_option_super'].split('/')))
        vertical_spacing=0.02
    else:
        super_name = lang_dict['store_kind_option_super']
        vertical_spacing=0.1
    if sk_value == lang_dict['store_kind_option_all']:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=vertical_spacing)
        one_linear_graph(
            fig, graph_type, hyper_data, start_date_hyper, end_date_hyper, period_df, lang_dict['store_kind_option_hyper'],
            lang_dict, 'rgba(244, 196, 79, 1)', '#0D57B2', row=1, col=1)
        one_linear_graph(
            fig, graph_type, super_data, start_date_super, end_date_super, period_df, super_name,
            lang_dict, 'rgba(179, 112, 112, 1)', '#7E7EE4', row=2, col=1)
        fig.update_xaxes(
            title_text=f'<b>{lang_dict["date"]}</b>',
            tickvals=tick_vals_text_xaxis(super_data)[0],
            ticktext=tick_vals_text_xaxis(super_data)[1],
            tickfont=dict(size=14, color='#000000'),
            title=dict(font_size=16, standoff=10, font_color='#000000'),
            row=2, col=1
            )
        fig.update_yaxes(
            tick0=0,
            dtick=hyper_step,
            row=1, col=1
        )
        fig.update_yaxes(
            tick0=0,
            dtick=super_step,
            row=2, col=1
        )
    elif sk_value == lang_dict['store_kind_option_hyper']:
        fig = make_subplots(rows=1, cols=1)
        one_linear_graph(
            fig, graph_type, hyper_data, start_date_hyper, end_date_hyper, period_df, lang_dict['store_kind_option_hyper'],
            lang_dict, 'rgba(244, 196, 79, 1)', '#0D57B2', row=1, col=1, showlegend=False)
        fig.update_xaxes(
            title_text=f'<b>{lang_dict["date"]}</b>',
            tickvals=tick_vals_text_xaxis(hyper_data)[0],
            ticktext=tick_vals_text_xaxis(hyper_data)[1],
            tickfont=dict(size=14, color='#000000'),
            title=dict(font_size=16, standoff=10, font_color='#000000'),
            row=1, col=1
            )
        fig.update_yaxes(
            tick0=0,
            dtick=hyper_step,
            row=1, col=1
        )
    else:
        fig = make_subplots(rows=1, cols=1)
        one_linear_graph(
            fig, graph_type, super_data, start_date_super, end_date_super, period_df, super_name,
            lang_dict, 'rgba(179, 112, 112, 1)', '#7E7EE4', row=1, col=1, showlegend=False)
        fig.update_xaxes(
            title_text=f'<b>{lang_dict["date"]}</b>',
            tickvals=tick_vals_text_xaxis(super_data)[0],
            ticktext=tick_vals_text_xaxis(super_data)[1],
            tickfont=dict(size=14, color='#000000'),
            title=dict(font_size=16, standoff=10, font_color='#000000'),
            row=1, col=1
            )
        fig.update_yaxes(
            tick0=0,
            dtick=super_step,
            row=1, col=1
        )
    fig.update_xaxes(
        showline=True,
        linecolor='#000000',
    )
    fig.update_yaxes(
        showline=True,
        linecolor='#000000',
        title_text=f'<b>{lang_dict["total"]}</b>',
        tickformat=',.0f',
        showgrid=True,
        gridcolor='#C0C0C0',
        griddash='dash',
        tickfont=dict(size=14, color='#000000'),
        title=dict(font_size=16, font_color='#000000', standoff=20)
    )
    if graph_type == 'cost_count' or graph_type == 'medians_count':
        fig.update_yaxes(ticksuffix='₽')
    if graph_type == 'medians_count':
        fig.update_yaxes(title_text=f'<b>{lang_dict["median"]}</b>')
    elif graph_type == 'items_count':
        fig.update_yaxes(title_text=f'<b>{lang_dict["number"]}</b>')
    fig.update_layout(
        font_family='Source Sans Pro, sans-serif',
        height=380,
        margin=dict(l=0, r=0, b=0, t=10),
        plot_bgcolor='#FFFFFF',
        legend=dict(font_size=14)
    )
    if graph_type != 'cost_count':
        fig.update_layout(legend=dict(
            font_size=14,
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ))
    return fig

# 2. Items' cost shares and Items' quantity shares
## 2.1 Determine labels for a sunburst plot
def labels_for_sunburst(items, prod_subcat_data, subcat_cat_data, last_value):
    categories = prod_subcat_data.loc[items, 'subcategory'].unique().tolist()
    types = subcat_cat_data.loc[
        prod_subcat_data.loc[items, 'subcategory'].unique(), 'category'
    ].unique().tolist()
    labels = [
        *items,
        *categories,
        *types,
        *[last_value]
    ]
    return labels, len(categories), len(types)

## 2.2 Determine displayed labels for a sunburst plot
def showing_labels_for_sunburst(labels, prod_subcat_data, subcat_cat_data):
    showing_labels = []
    for label in labels:
        if label in prod_subcat_data.index:
            showing_labels.append(label if len(label) <= 15 else label[:12] + '...')
        elif label in subcat_cat_data.index:
            space_pos = label.find(' ')
            showing_labels.append(
                label if space_pos == -1 or len(label) <= 10 else label[:space_pos] + '<br>' + label[space_pos+1:])
        else:
            showing_labels.append(label)
    return showing_labels

## 2.3 Determine a "parent" label for each label of a sunburst plot
def parents_for_sunburst(labels, prod_subcat_data, subcat_cat_data):
    parents = []
    for label in labels:
        if label in prod_subcat_data.index:
            parents.append(prod_subcat_data.loc[label, 'subcategory'])
        elif label in subcat_cat_data.index:
            parents.append(subcat_cat_data.loc[label, 'category'])
        elif label in subcat_cat_data['category'].unique():
            parents.append(labels[-1])
        else:
            parents.append('')
    return parents

## 2.4 Determine a value for each label of a sunburst plot
def values_for_sunburst(df, items_in_units, labels, prod_subcat_data, subcat_cat_data):
    values = []
    for label in labels:
        if label in prod_subcat_data.index:
            values.append(df[label].sum())
        elif label in subcat_cat_data.index:
            selected_pos = [
                pos for pos in prod_subcat_data[prod_subcat_data['subcategory'] == label].index \
                if pos in items_in_units
            ]
            values.append(df[selected_pos].sum().sum())
        elif label in subcat_cat_data['category'].unique():
            subcats = subcat_cat_data[subcat_cat_data['category'] == label].index
            selected_pos = []
            for subcat in subcats:
                positions = prod_subcat_data[prod_subcat_data['subcategory'] == subcat].index
                for pos in positions:
                    if pos in items_in_units:
                        selected_pos.append(pos)
            values.append(df[selected_pos].sum().sum())
        else:
            values.append(df[items_in_units].sum().sum())
    return values

## 2.5 Helper function to correct label's hover text
def correct_hovertext(text, explanation):
    colon = text.find(':')
    text = text[:colon] + '*' + text[colon:]
    text += f'<br>* - {explanation}'
    return text

## 2.6 Determine hover text for each label of a sunburst plot
def hovertext_for_sunburst(labels, parents, values, prod_subcat_data,
                           subcat_cat_data, total_text, cat_num, type_num, graph_type,
                           part_quantity, lang_dict):
    hovertext = [''] * len(labels)
    for i in range(len(labels)):
        total_sum = values[-1]
        if graph_type == 'cost':
            value_format = f'{values[i]:,.2f} ' + lang_dict['rubles']
        elif graph_type == 'vol':
            value_format = f'{values[i]:,.3f} ' + lang_dict['kg_l']
        elif graph_type == 'pack':
            value_format = f'{values[i]:} ' + lang_dict['packs']
        if total_sum != 0:
            if labels[i] in prod_subcat_data.index:
                cat_sum = values[labels.index(parents[i])]
                if cat_num == 1:
                    hovertext[i] = '<br>'.join([
                        labels[i] + ':',
                        value_format,
                        f'{(values[i] / cat_sum):.2%} {lang_dict["of_category"]}'
                    ])
                    if graph_type != 'cost' and labels[i] in part_quantity:
                        hovertext[i] = correct_hovertext(hovertext[i], lang_dict['explanation'])
                else:
                    type_sum = values[labels.index(parents[labels.index(parents[i])])]
                    if type_num == 1:
                        hovertext[i] = '<br>'.join([
                            labels[i] + ':',
                            value_format,
                            f'{(values[i] / cat_sum):.2%} {lang_dict["of_category"]}',
                            f'{(values[i] / type_sum):.2%} {lang_dict["of_type"]}',
                        ])
                        if graph_type != 'cost' and labels[i] in part_quantity:
                            hovertext[i] = correct_hovertext(hovertext[i], lang_dict['explanation'])
                    else:
                        hovertext[i] = '<br>'.join([
                            labels[i] + ':',
                            value_format,
                            f'{(values[i] / cat_sum):.2%} {lang_dict["of_category"]}',
                            f'{(values[i] / type_sum):.2%} {lang_dict["of_type"]}',
                            f'{(values[i] / total_sum):.2%} {total_text}'
                        ])
                        if graph_type != 'cost' and labels[i] in part_quantity:
                            hovertext[i] = correct_hovertext(hovertext[i], lang_dict['explanation'])
            elif labels[i] in subcat_cat_data.index:
                if cat_num == 1:
                    hovertext[i] = '<br>'.join([
                            labels[i] + ':',
                            value_format,
                    ])
                    if graph_type != 'cost' and labels[i] in part_quantity:
                        hovertext[i] = correct_hovertext(hovertext[i], lang_dict['explanation'])
                else:
                    type_sum = values[labels.index(parents[i])]
                    if type_num == 1:
                        hovertext[i] = '<br>'.join([
                            labels[i] + ':',
                            value_format,
                            f'{(values[i] / type_sum):.2%} {lang_dict["of_type"]}'
                        ])
                        if graph_type != 'cost' and labels[i] in part_quantity:
                            hovertext[i] = correct_hovertext(hovertext[i], lang_dict['explanation'])
                    else:
                        hovertext[i] = '<br>'.join([
                            labels[i] + ':',
                            value_format,
                            f'{(values[i] / type_sum):.2%} {lang_dict["of_type"]}',
                            f'{(values[i] / total_sum):.2%} {total_text}'
                        ])
                        if graph_type != 'cost' and labels[i] in part_quantity:
                            hovertext[i] = correct_hovertext(hovertext[i], lang_dict['explanation'])
            elif labels[i] in subcat_cat_data['category'].unique():
                if type_num == 1:
                    hovertext[i] = '<br>'.join([
                            labels[i] + ':',
                            value_format,
                    ])
                    if graph_type != 'cost' and labels[i] in part_quantity:
                        hovertext[i] = correct_hovertext(hovertext[i], lang_dict['explanation'])
                else:
                    hovertext[i] = '<br>'.join([
                        labels[i] + ':',
                        value_format,
                        f'{(values[i] / total_sum):.2%} {total_text}'
                    ])
                    if graph_type != 'cost' and labels[i] in part_quantity:
                        hovertext[i] = correct_hovertext(hovertext[i], lang_dict['explanation'])
            else:
                hovertext[i] = '<br>'.join([
                        labels[i] + ':',
                        value_format,
                ])
                if graph_type != 'cost' and labels[i] in part_quantity:
                    hovertext[i] = correct_hovertext(hovertext[i], lang_dict['explanation'])
    return hovertext

## 2.7 Determine a color value for each label of a sunburst plot
def colors_for_sunburst(labels, parents, values):
    colors = [
        values[i] / values[labels.index(parents[i])] if parents[i] != '' else 1 \
        for i in range(len(labels))
    ]
    return colors

## 2.8 Helper function to find all labels from the current one to the node
def find_item_parents(item, df):
    result = []
    if df.loc[item, 'parent'] == '':
        return [item]
    else:
        result += [item]
        result += find_item_parents(df.loc[item, 'parent'], df)
    return result


## 2.9 Create a dataframe for a sunburst plot
def sunburst_dataframe(cleaned_cost_df, cleaned_quantity_df, items_in_units, prod_subcat_data,
    subcat_cat_data, last_label, of_total_text, graph_type, lang_dict):

    # determine which dataframe should be used
    if graph_type == 'cost':
        cleaned_df = cleaned_cost_df
    else:
        cleaned_df = cleaned_quantity_df

    # determine items in the right units
    items = [col for col in cleaned_df.columns if col in items_in_units]

    # determine labels
    labels, cat_num, type_num = labels_for_sunburst(
        items, prod_subcat_data, subcat_cat_data, last_label)
    showing_labels = showing_labels_for_sunburst(labels, prod_subcat_data, subcat_cat_data)

    # determine "parent" labels
    parents = parents_for_sunburst(labels, prod_subcat_data, subcat_cat_data)
    showing_parents = showing_labels_for_sunburst(parents, prod_subcat_data, subcat_cat_data)

    # determine the value for each label
    values = values_for_sunburst(
        cleaned_df, items, labels, prod_subcat_data, subcat_cat_data
    )

    # create the dataframe
    sunburst_data = pd.DataFrame({
        'parent' : parents,
        'value' : values,
        'showing_label' : showing_labels,
        'showing_parent' : showing_parents
    }, index=labels)

    if cat_num == 1:
        sunburst_data = sunburst_data.iloc[:-2, :]
        sunburst_data.iloc[-1, [0, 3]] = ''
    elif type_num == 1:
        sunburst_data = sunburst_data.iloc[:-1, :]
        sunburst_data.iloc[-1, [0, 3]] = ''

    # determine the hover text for each label
    part_quantity_items = [
        item for item in items if not np.all(cleaned_quantity_df[cleaned_cost_df[item] != 0][item] != 0)
    ]
    part_quantity = []
    for i in part_quantity_items:
        part_quantity += find_item_parents(i, sunburst_data)
    part_quantity = list(set(part_quantity))
    hovertext = hovertext_for_sunburst(
        list(sunburst_data.index), sunburst_data['parent'].values, sunburst_data['value'].values,
        prod_subcat_data, subcat_cat_data, of_total_text, cat_num, type_num, graph_type, part_quantity,
        lang_dict
    )
    sunburst_data['hovertext'] = hovertext

    # determine the color value for each label
    colors = colors_for_sunburst(
        list(sunburst_data.index), sunburst_data['parent'].values, sunburst_data['value'].values)
    sunburst_data['color'] = colors

    return sunburst_data


## 2.10 Create sunburst plot's layout
def create_sunburst_object(colorscale='Oranges', **kwargs):
    sunburst = go.Sunburst(
        labels=kwargs['labels'],
        parents=kwargs['parents'],
        values=kwargs['values'],
        insidetextorientation='radial',
        branchvalues='total',
        insidetextfont=dict(size=14, family='Source Sans Pro, sans-serif'),
        sort=True,
        marker=dict(colorscale=colorscale, colors=kwargs['colors'], cmax=1, cmin=0),
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=kwargs['hovertext'],
        hoverlabel={
            'bgcolor' : '#FFFFFF',
            'font_size' : 16,
            'bordercolor' : '#000000',
            'font_family' : 'Source Sans Pro, sans-serif'
        },
        maxdepth=3
    )
    return sunburst


## 2.11 Create items' cost shares plot
def sunburst_plot_cost(sunburst_table):
    fig = go.Figure(
        create_sunburst_object(
            labels=sunburst_table['showing_label'].values,
            parents=sunburst_table['showing_parent'].values,
            values=sunburst_table['value'].values,
            colors=sunburst_table['color'].values,
            hovertext=sunburst_table['hovertext'].values
        )
    )

    fig.update_layout(margin=dict(t=0, b=0, r=0, l=0))

    return fig

## 2.12 Create items' quantity shares plot
def sunburst_plot_quantity(sunburst_table):

    if sunburst_table.shape[0] > 1:
        colorscale = 'Oranges'
    else:
        colorscale = [[0, '#FFF6EC'], [1, '#FFF6EC']]

    fig = go.Figure(create_sunburst_object(
        colorscale=colorscale,
        labels=sunburst_table['showing_label'].values,
        parents=sunburst_table['showing_parent'].values,
        values=sunburst_table['value'].values,
        colors=sunburst_table['color'].values,
        hovertext=sunburst_table['hovertext'].values
        )
    )

    fig.update_layout(margin=dict(t=0, b=0, r=0, l=0))

    return fig

## 2.13 Helper function to find all labels for which the current one is the "parent"
def sunburst_table_slice(label, df, items):
    sunburst_labels = []
    if label in items:
        sunburst_labels.append(label)
    else:
        for idx in df[df['parent'] == label].index:
            sunburst_labels += sunburst_table_slice(idx, df, items)
        sunburst_labels += [label]
    return sunburst_labels

## 2.14 Update an items' quantity shares plot
## based on a click data of the items' cost shares graph
def update_quantity_sunburst(plot_table, click_data, items):
    current_label = click_data['points'][0]['label']
    current_parent = click_data['points'][0]['parent']
    current_entry = click_data['points'][0].get('entry', '')
    if current_label in items or current_parent == '':
        raise PreventUpdate
    else:
        if current_label in plot_table['showing_label'].values:
            working_label = plot_table[plot_table['showing_label'] == current_label].index[0]
            if current_label != current_entry and current_entry != '':
                items_slice = sunburst_table_slice(working_label, plot_table, items)
                slice_data = plot_table.loc[items_slice]
                slice_data.iloc[-1, [0, 3]] = ''
            else:
                if current_parent in plot_table['showing_parent'].values:
                    working_parent = plot_table[plot_table['showing_label'] == current_parent].index[0]
                    items_slice = sunburst_table_slice(working_parent, plot_table, items)
                    slice_data = plot_table.loc[items_slice]
                    slice_data.iloc[-1, [0, 3]] = ''
                else:
                    slice_data = plot_table.copy()
            return sunburst_plot_quantity(slice_data)
        elif current_parent in plot_table['showing_parent'].values and\
            (current_label == current_entry or current_entry == ''):
            working_parent = plot_table[plot_table['showing_label'] == current_parent].index[0]
            items_slice = sunburst_table_slice(working_parent, plot_table, items)
            slice_data = plot_table.loc[items_slice]
            slice_data.iloc[-1, [0, 3]] = ''
            return sunburst_plot_quantity(slice_data)
        else:
            return sunburst_plot_quantity(plot_table)

# 3. Others expenses table
## 3.1 A dataframe if the store kind value is not "All"
def create_one_table(cost_data, quantity_data):
    table = cost_data.sum().to_frame().join(quantity_data.sum().to_frame(), lsuffix='l', rsuffix='r')
    table.reset_index(inplace=True)
    table.columns = ['name', 'cost', 'quantity']
    table['count'] = [np.count_nonzero(cost_data[col]) for col in cost_data.columns]
    table.sort_values(by='name', inplace=True)
    part_quantity = [
        c for c in cost_data.columns if not np.all(quantity_data[cost_data[c] != 0][c] != 0)
    ]
    return table, part_quantity

## 3.2 A dataframe if the store kind value is "All"
def create_full_table(cost_data, quantity_data, period_data):
    hyper_cost_data = cost_data.loc[period_data[period_data[0] == 0].index]
    hyper_quantity_data = quantity_data.loc[period_data[period_data[0] == 0].index]
    super_cost_data = cost_data.loc[period_data[period_data[0] != 0].index]
    super_quantity_data = quantity_data.loc[period_data[period_data[0] != 0].index]
    hyper_table, hyper_part_quantity = create_one_table(hyper_cost_data, hyper_quantity_data)
    super_table, super_part_quantity = create_one_table(super_cost_data, super_quantity_data)
    all_table, all_part_quantity = create_one_table(cost_data, quantity_data)
    table = hyper_table.merge(super_table, on='name').merge(all_table, on='name')
    table.columns = [
        'name',
        'cost_h', 'quantity_h', 'count_h',
        'cost_s', 'quantity_s', 'count_s',
        'cost', 'quantity', 'count'
    ]
    return table, hyper_part_quantity, super_part_quantity, all_part_quantity

## 3.3 A table if the store kind value is not "All"
def create_one_datatable(table, all_part, lang_dict):
    cost_value_format = dict(
        type='numeric',
        format=Format(
            symbol=Symbol.yes, symbol_suffix='₽', precision=2, scheme=Scheme.fixed
            )
    )
    integer_value_format = dict(
        type='numeric',
        format=Format(precision=2, scheme=Scheme.decimal_integer)
    )
    datatable_object = dash_table.DataTable(
        data=table.to_dict('records'),
        columns=[
            dict(id="name", name=lang_dict['items_name']),
            dict(id='cost', name=lang_dict['cost'], **cost_value_format),
            dict(id='quantity', name=lang_dict['quantity'], **integer_value_format),
            dict(id='count', name=lang_dict['period_count'], **integer_value_format),
        ],
        page_size=10,
        sort_action='native',
        sort_mode='single',
        editable=False,
        style_cell={
            'overflow' : 'hidden',
            'textOverflow' : 'ellipsis',
            'fontFamily' : 'Source Sans Pro, sans-serif',
            'fontSize' : '1rem'
        },
        style_cell_conditional=[
            {
                'if' : {'column_id' : 'name'},
                'textAlign' : 'left',
                'width' : '40%'
            },
            {
                'if' : {'column_id' : ['cost', 'quantity', 'count']},
                'textAlign' : 'right',
                'width' : '20%'
            },
        ],
        style_data_conditional=[
            {
                'if' : {
                    'filter_query' : '{} = "{}"'.format('{name}', pos),
                    'column_id' : 'quantity'
                    },
                'textDecoration' : 'underline',
                'textDecorationStyle' : 'double',
                'textDecorationColor' : 'red'
            } for pos in all_part
        ] +
        [
            {
                'if' : {'row_index' : 'odd'},
                'backgroundColor' : '#FFF6EC',
            }
        ],
        tooltip_header={
            'cost' : {'value' : lang_dict['others_cost_exp'], 'type' : 'markdown'},
            'quantity' : {'value' : lang_dict['others_quantity_exp'], 'type' : 'markdown'},
            'count' : {'value' : lang_dict['others_count_exp'], 'type' : 'markdown'}
        },
        tooltip_duration=None,
        css=[
            {'selector' : 'table', 'rule' : 'table-layout: fixed;'},
        ],
    )
    return datatable_object

## 3.4 A table if the store kind value is "All"
def create_full_datatable(table, hyper_part, super_part, all_part, lang_dict):
    cost_value_format = dict(
        type='numeric',
        format=Format(
            symbol=Symbol.yes, symbol_suffix='₽', precision=2, scheme=Scheme.fixed
            )
    )
    integer_value_format = dict(
        type='numeric',
        format=Format(precision=2, scheme=Scheme.decimal_integer)
    )
    datatable_object = dash_table.DataTable(
        data=table.to_dict('records'),
        columns=[
            dict(id="name", name=['', lang_dict['items_name']]),
            dict(id='cost_h', name=[lang_dict['store_kind_option_hyper'], lang_dict['cost']],
                **cost_value_format),
            dict(id='quantity_h', name=[lang_dict['store_kind_option_hyper'], lang_dict['quantity']],
                **integer_value_format),
            dict(id='count_h', name=[lang_dict['store_kind_option_hyper'], lang_dict['period_count']],
                **integer_value_format),
            dict(id='cost_s', name=[lang_dict['store_kind_option_super'], lang_dict['cost']],
                **cost_value_format),
            dict(id='quantity_s', name=[lang_dict['store_kind_option_super'], lang_dict['quantity']],
                **integer_value_format),
            dict(id='count_s', name=[lang_dict['store_kind_option_super'], lang_dict['period_count']],
                **integer_value_format),
            dict(id='cost', name=[lang_dict['store_kind_option_all'], lang_dict['cost']],
                **cost_value_format),
            dict(id='quantity', name=[lang_dict['store_kind_option_all'], lang_dict['quantity']],
                **integer_value_format),
            dict(id='count', name=[lang_dict['store_kind_option_all'], lang_dict['period_count']],
                **integer_value_format),
        ],
        merge_duplicate_headers=True,
        page_size=10,
        sort_action='native',
        sort_mode='single',
        editable=False,
        style_cell={
            'overflow' : 'hidden',
            'textOverflow' : 'ellipsis',
            'fontFamily' : 'Source Sans Pro, sans-serif',
            'fontSize' : '1rem'
        },
        style_cell_conditional=[
            {
                'if' : {'column_id' : 'name'},
                'textAlign' : 'left',
                'width' : '20%'
            },
            {
                'if' : {'column_id' : ['cost_h', 'quantity_h', 'count_h', 'cost_s', 'quantity_s', 'count_s', 'cost', 'quantity', 'count']},
                'textAlign' : 'right',
                'width' : '30%'
            },
        ],
        style_data_conditional=[
            {
                'if' : {
                    'filter_query' : '{} = "{}"'.format('{name}', pos),
                    'column_id' : 'quantity'
                    },
                'textDecoration' : 'underline',
                'textDecorationStyle' : 'double',
                'textDecorationColor' : 'red'
            } for pos in all_part
        ] +
        [
            {
                'if' : {
                    'filter_query' : '{} = "{}"'.format('{name}', pos),
                    'column_id' : 'quantity_h'
                    },
                'textDecoration' : 'underline',
                'textDecorationStyle' : 'double',
                'textDecorationColor' : 'red'
            } for pos in hyper_part
        ] +
        [
            {
                'if' : {
                    'filter_query' : '{} = "{}"'.format('{name}', pos),
                    'column_id' : 'quantity_s'
                    },
                'textDecoration' : 'underline',
                'textDecorationStyle' : 'double',
                'textDecorationColor' : 'red'
            } for pos in super_part
        ] +
        [
            {
                'if' : {'row_index' : 'odd'},
                'backgroundColor' : '#FFF6EC',
            }
        ],
        tooltip_header={
            'cost_h' : [lang_dict['others_hyper'], lang_dict['others_cost_exp']],
            'quantity_h' : [lang_dict['others_hyper'], lang_dict['others_quantity_exp']],
            'count_h' : [lang_dict['others_hyper'], lang_dict['others_count_exp']],
            'cost_s' : [lang_dict['others_super'], lang_dict['others_cost_exp']],
            'quantity_s' : [lang_dict['others_super'], lang_dict['others_quantity_exp']],
            'count_s' : [lang_dict['others_super'], lang_dict['others_count_exp']],
            'cost' : [lang_dict['others_all'], lang_dict['others_cost_exp']],
            'quantity' : [lang_dict['others_all'], lang_dict['others_quantity_exp']],
            'count' : [lang_dict['others_all'], lang_dict['others_count_exp']]
        },
        tooltip_duration=None,
        css=[
            {'selector' : 'table', 'rule' : 'table-layout: fixed;'},
        ],
    )
    return datatable_object

#4. Items' number by period and Median cost per item by period (update by hover data)
def update_linear_graph_on_hover(point, df, period_df, start_date_hyper, end_date_hyper, start_date_super, end_date_super, items, lang, sk_value, lang_dict, graph_type):
    if graph_type == 'medians_count':
        annotation_text = f'<b>{df.loc[point, 0]:.2f} {lang_dict["rubles"]}</b>'
    elif graph_type == 'items_count':
        items_word = lang_dict["items"] + word_ending(lang_dict["items"], df.loc[point, 0])
        annotation_text = f'<b>{df.loc[point, 0]} {items_word}</b>'

    ANNOTATION = {
        'x': point,
        'y' : df.loc[point, 0],
        'text' : annotation_text,
        'showarrow' : True,
        'bgcolor' : '#FFFFFF',
        'font' : dict(size=16, color='#000000', family='Source Sans Pro, sans-serif'),
        'borderwidth' : 1,
        'bordercolor' : '#382250'
    }

    if period_df.loc[point, 0] == 0:
        fig = linear_graph(
            df, period_df, point, point, start_date_super, end_date_super,
            items, lang, sk_value, lang_dict, graph_type
        )
        fig.data = fig.data[:2] + fig.data[3:]
        fig.layout.shapes = fig.layout.shapes[2:]
        fig.layout.annotations = fig.layout.annotations[2:]
        fig.add_annotation(xref='x', yref='y', **ANNOTATION)
    else:
        fig = linear_graph(
            df, period_df, start_date_hyper, end_date_hyper, point, point,
            items, lang, sk_value, lang_dict, graph_type
        )
        if sk_value == lang_dict['store_kind_option_all']:
            fig.data = fig.data[:5]
            fig.layout.shapes = [
                shape for shape in fig.layout.shapes \
                if shape['yref'] == 'y domain' or shape['opacity'] == 0.65]
            fig.layout.annotations = [
                a for a in fig.layout.annotations if a['yref'] == 'y domain'
            ]
            fig.add_annotation(xref='x2', yref='y2', **ANNOTATION)
        else:
            fig.data = fig.data[:2]
            fig.layout.shapes = fig.layout.shapes[2:]
            fig.layout.annotations = []
            fig.add_annotation(xref='x', yref='y', **ANNOTATION)
    return fig

# 5. Interrelation between an items' number and a median cost per item
# 5.1 Create a single scatter plot
def one_scatter_graph(fig, df, period_df, scatter_name, legendgroup_name, color, lang_dict, row=1, col=1):
    x_name, y_name = lang_dict['number_of_items'], lang_dict['median_cost_per_item']
    scatter_text = []
    for i in df.index:
        end_date = i.strftime("%Y-%m-%d")
        start_date = (i - timedelta(days=int(period_df.loc[i, 0]))).strftime('%Y-%m-%d')
        if end_date == start_date:
            date_line = f'<b>{end_date}</b>'
        else:
            date_line = f'<b>{start_date} - {end_date}</b>'
        median_line = f'{y_name} = {df.loc[i, "median"]:.2f} {lang_dict["rubles"]}'
        number_line = f'{x_name} = {df.loc[i, "items"]}<extra></extra>'
        full_line = '<br>'.join([date_line, median_line, number_line])
        scatter_text.append(full_line)
    fig.add_trace(
        go.Scatter(
            x=df['items'],
            y=df['median'],
            mode='markers',
            marker_color=color,
            showlegend=False,
            hovertemplate='%{text}',
            text=scatter_text,
            hoverlabel={
                'bgcolor' : '#FFFFFF',
                'font_size' : 16,
                'bordercolor' : '#000000',
                'font_family' : 'Source Sans Pro, sans-serif'
            }
        ),
        row=row, col=col
    )
    if df['items'].nunique() > 1:
        X = df['items'].values.reshape(-1, 1)
        y = df['median'].values
        model = LinearRegression().fit(X, y)
        coef, intercept, r2 = model.coef_[0], model.intercept_, model.score(X, y)
        coef_line = f'+ {coef:.2f}' if coef >= 0 else f'- {abs(coef):.2f}'
        predictions = pd.DataFrame({'prediction' : model.predict(X)}, index=df.index)
        trend_text = []
        for i in df.index:
            line = '<br>'.join(
                [
                    f'<b>{lang_dict["trend"]}</b><extra></extra>',
                    f'{lang_dict["median"]} = {intercept:.2f} {coef_line} * {lang_dict["number"]}',
                    f'R<sup>2</sup> = {r2:.4f}',
                    '',
                    f'{x_name} = {df.loc[i, "items"]}',
                    f'{lang_dict["predicted"]} = {predictions.loc[i, "prediction"]:.2f} {lang_dict["rubles"]}'
                ]
            )
            trend_text.append(line)
        fig.add_trace(
            go.Scatter(
                x=df['items'],
                y=predictions['prediction'].values,
                mode='lines',
                line=dict(color=color, dash='solid', width=2),
                showlegend=False,
                hovertemplate='%{text}',
                text=trend_text,
                hoverlabel={
                    'bgcolor' : '#FFFFFF',
                    'font_size' : 16,
                    'bordercolor' : '#000000',
                    'font_family' : 'Source Sans Pro, sans-serif'
                }
            ),
            row=row, col=col
        )
    return fig

# 5.2 Create a full scatter plot:
## If the shop kind value is "All", create two single scatter graphs with the shared y-axis.
## Draw one single graph in other cases.
def scatter_graph(df, period_df, sk_value, lang_dict):
    x = df.apply(np.count_nonzero, axis=1).to_frame()
    y = df.apply(lambda x: np.median(x[x != 0]) if np.any(x != 0) else 0, axis=1).to_frame()
    dff = x.join(y, lsuffix='l')
    dff.columns = ['items', 'median']
    dff['is_hyper'] = [1 if period_df.loc[i, 0] == 0 else 0 for i in dff.index]
    dff.drop(dff[(dff['items'] == 0) & (dff['median'] == 0)].index, inplace=True)
    hyper_data = dff[dff['is_hyper'] == 1]
    super_data = dff[dff['is_hyper'] == 0]
    if sk_value == lang_dict['store_kind_option_all']:
        fig = make_subplots(
            rows=1, cols=2,
            shared_yaxes=True, horizontal_spacing=0.05,
            subplot_titles=[lang_dict["store_kind_option_hyper"], lang_dict["store_kind_option_super"]]
        )
        one_scatter_graph(
            fig, hyper_data, period_df, lang_dict['store_kind_option_hyper'],
            'hypermarket', 'rgba(244, 196, 79, 1)', lang_dict, row=1, col=1)
        one_scatter_graph(
            fig, super_data, period_df, lang_dict['store_kind_option_super'],
            'supermarket', 'rgba(179, 112, 112, 1)', lang_dict, row=1, col=2)
    elif sk_value == lang_dict["store_kind_option_hyper"]:
        fig = make_subplots(rows=1, cols=1)
        one_scatter_graph(
            fig, hyper_data, period_df, lang_dict['store_kind_option_hyper'],
            'hypermarket', 'rgba(244, 196, 79, 1)', lang_dict, row=1, col=1)
    else:
        fig = make_subplots(rows=1, cols=1)
        one_scatter_graph(
            fig, super_data, period_df, lang_dict['store_kind_option_super'],
            'supermarket', 'rgba(179, 112, 112, 1)', lang_dict, row=1, col=1)
    fig.update_xaxes(
        title_text=f'<b>{lang_dict["number_of_items"]}</b>',
        title=dict(font_size=16, standoff=10, font_color='#000000'),
        showline=True,
        linecolor='#000000',
        showgrid=True,
        gridcolor='#C0C0C0',
        griddash='dash',
        tickfont=dict(size=14, color='#000000')
    )
    fig.update_yaxes(
        showline=True,
        linecolor='#000000',
        showgrid=True,
        gridcolor='#C0C0C0',
        griddash='dash'
    )
    fig.update_yaxes(
        title_text=f'<b>{lang_dict["median_cost_per_item"]}</b>',
        title=dict(font_size=16, standoff=20, font_color='#000000'),
        tickformat=',.0f',
        ticksuffix='₽',
        tickfont=dict(size=14, color='#000000'),
        row=1, col=1
    )
    fig.for_each_annotation(lambda a: a.update(y=a.y+0.01, font_size=14))
    fig.update_layout(
        font_family='Source Sans Pro, sans-serif',
        height=380,
        margin=dict(l=0, r=0, b=0, t=28),
        plot_bgcolor='#FFFFFF'
    )

    return fig
