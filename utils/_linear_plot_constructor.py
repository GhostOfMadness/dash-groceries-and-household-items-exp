data = data_handler.cost.sum(1)
start = dt.strptime('2021-06-01', '%Y-%m-%d')
end = dt.strptime('2022-05-15', '%Y-%m-%d')
weekend_cond = (
    (data.index.get_level_values(0) == 'weekend')
    & (data.index.get_level_values(1) >= start)
    & (data.index.get_level_values(1) <= end)
)
not_weekend_cond_1 = (
    (data.index.get_level_values(0) == 'weekend')
    & (data.index.get_level_values(1) < start)
)
not_weekend_cond_2 = (
    (data.index.get_level_values(0) == 'weekend')
    & (data.index.get_level_values(1) > end)
)
workweek_cond = (
    (data.index.get_level_values(0) == 'workweek')
    & (data.index.get_level_values(1) >= start)
    & (data.index.get_level_values(1) <= end)
)
not_workweek_cond_1 = (
    (data.index.get_level_values(0) == 'workweek')
    & (data.index.get_level_values(1) < start)
)
not_workweek_cond_2 = (
    (data.index.get_level_values(0) == 'workweek')
    & (data.index.get_level_values(1) > end)
)
# weekend_cond = data.index.get_level_values(0) == 'weekend'
# workweek_cond = data.index.get_level_values(0) == 'workweek'


dates = pd.date_range(
    start=data.index.get_level_values(1)[0],
    end=data.index.get_level_values(1)[-1],
    freq='MS',
)
year_start = [
    dt for idx, dt in enumerate(dates)
    if idx == 0 or dates[idx - 1].year != dt.year
]


def xaxis_tick_text(idx_date, year_start):
    tick_text = idx_date.strftime('%b').capitalize()
    if idx_date in year_start:
        tick_text += f'<br>{idx_date.year}'
    return tick_text


fig = go.Figure()
fig.add_trace(go.Scatter(
    x=data.loc[weekend_cond].index.get_level_values(1),
    y=data[weekend_cond].values,
    mode='lines+markers',
    showlegend=False,
    marker=dict(
        color='rgb(100, 181, 246)',
        size=4,
    ),
    line=dict(
        color='rgb(100, 181, 246)',
        width=1.2,
    ),
    hoverlabel=dict(
        font_size=16,
        font_family='Source Sans Pro, sans-serif',
        bgcolor='rgb(30, 30, 30)',
        bordercolor='rgb(100, 181, 246)',
        font_color='#bdbdbd',
    ),
    hovertemplate=(
        '<b> %{y:.2f} rub.</b><extra></extra> '
        '<br>'
        ' for <i>%{x|%Y-%m-%d}</i> '
    ),
))
fig.add_trace(go.Scatter(
    x=data[not_weekend_cond_1].index.get_level_values(1),
    y=data[not_weekend_cond_1].values,
    mode='lines',
    showlegend=False,
    line=dict(
        color='rgba(100, 181, 246, 0.5)',
        width=1.2,
        dash='3px',
    ),
    hoverinfo='skip',
))
fig.add_trace(go.Scatter(
    x=data[not_weekend_cond_2].index.get_level_values(1),
    y=data[not_weekend_cond_2].values,
    mode='lines',
    showlegend=False,
    line=dict(
        color='rgba(100, 181, 246, 0.5)',
        width=1.2,
        dash='3px',
    ),
    hoverinfo='skip',
))
fig.add_trace(go.Scatter(
    x=data[workweek_cond].index.get_level_values(1),
    y=data[workweek_cond].values,
    mode='lines+markers',
    showlegend=False,
    marker=dict(
        color='rgb(246, 166, 100)',
        size=4,
    ),
    line=dict(
        color='rgb(246, 166, 100)',
        width=1.2,
    ),
    customdata=[data.index[data.index.get_loc(('workweek', date_idx)) - 1][1] + timedelta(days=1) for date_idx in data[workweek_cond].index.get_level_values(1)],
    hoverlabel=dict(
        font_size=16,
        font_family='Source Sans Pro, sans-serif',
        bgcolor='rgb(30, 30, 30)',
        bordercolor='rgb(246, 166, 100)',
        font_color='#bdbdbd',
    ),
    hovertemplate=(
        '<b> %{y:.2f} rub.</b><extra></extra> '
        '<br>'
        ' for <i>%{customdata|%Y-%m-%d}</i> - <i>%{x|%Y-%m-%d}</i> '
    ),
))
fig.add_trace(go.Scatter(
    x=data[not_workweek_cond_1].index.get_level_values(1),
    y=data[not_workweek_cond_1].values,
    mode='lines',
    showlegend=False,
    line=dict(
        color='rgba(246, 166, 100, 0.5)',
        width=1.2,
        dash='3px',
    ),
    hoverinfo='skip',
))
fig.add_trace(go.Scatter(
    x=data[not_workweek_cond_2].index.get_level_values(1),
    y=data[not_workweek_cond_2].values,
    mode='lines',
    showlegend=False,
    line=dict(
        color='rgba(246, 166, 100, 0.5)',
        width=1.2,
        dash='3px',
    ),
    hoverinfo='skip',
))
fig.add_trace(go.Scatter(
    x=[None],
    y=[None],
    mode='markers',
    marker=dict(
        color='rgb(100, 181, 246)',
        size=10,
        symbol='square',
    ),
    name='Weekend',
))
fig.add_trace(go.Scatter(
    x=[None],
    y=[None],
    mode='markers',
    marker=dict(
        color='rgb(246, 166, 100)',
        size=10,
        symbol='square',
    ),
    name='Workweek',
))
fig.update_xaxes(
    title='Date',
    title_font=dict(
        size=16,
        family='Source Sans Pro, sans-serif',
        color='#eeeeee',
    ),
    title_standoff=10,
    ticks='outside',
    tickwidth=1,
    tickcolor='#eeeeee',
    ticklen=5,
    showgrid=False,
    linecolor='#eeeeee',
    linewidth=1,
    # tickvals=dates,
    # ticktext=[xaxis_tick_text(idx, year_start) for idx in dates],
    tickfont=dict(color='#eeeeee', size=14, family='Source Sans Pro, sans-serif'),
    # range=['2021-01-13 00:04:35.2594', '2022-07-31 23:55:24.7406'],
    range=['2021-02-05', '2022-07-10'],
    dtick='M1',
    tickformat='%b\n%Y',
)
fig.update_yaxes(
    title='Total, ₽',
    title_font=dict(
        size=16,
        family='Source Sans Pro, sans-serif',
        color='#eeeeee',
    ),
    linecolor='#eeeeee',
    linewidth=1,
    ticks='outside',
    tickwidth=1,
    tickcolor='#eeeeee',
    ticklen=5,
    title_standoff=20,
    gridwidth=1,
    gridcolor='rgba(255, 255, 255, 0.16)',
    tickfont=dict(color='#eeeeee', size=14, family='Source Sans Pro, sans-serif'),
    tickformat=',.0f',
    rangemode='nonnegative',
)
fig.update_layout(
    plot_bgcolor='rgb(30, 30, 30)',
    paper_bgcolor='rgb(30, 30, 30)',
    margin=dict(l=0, r=0, b=0, t=0),
    legend=dict(
        font=dict(size=14, family='Source Sans Pro, sans-serif', color='#bdbdbd'),
        itemclick=False,
        itemdoubleclick=False,
        orientation='h',
        xanchor='right',
        x=1,
        yanchor='bottom',
        y=1,
    ),
)

# full_fig = fig.full_figure_for_development()
# print(full_fig.layout.xaxis.range)