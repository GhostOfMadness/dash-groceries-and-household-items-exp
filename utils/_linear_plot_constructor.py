from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go


@dataclass
class BasePlot:
    """Base figure class."""

    bg_color: str = 'rgb(30, 30, 30)'
    main_text_color: str = 'rgb(238, 238, 238)'
    sup_text_color: str = 'rgb(189, 189, 189)'
    weekend_color: str = 'rgb(100, 181, 246)'
    weekend_out_color: str = 'rgba(100, 181, 246, 0.5)'
    workweek_color: str = 'rgb(246, 166, 100)'
    workweek_out_color: str = 'rgba(246, 166, 100, 0.5)'
    grid_color: str = 'rgba(255, 255, 255, 0.16)'
    font_family: str = 'Source Sans Pro, sans-serif'


class LinearPlot(BasePlot):
    """A linear plot constructor."""

    FIG_NAME_VALUE_FMT: dict[str, str] = {
        'total_expenses': '%{y:,.2f} rub.',
        'item_count': '%{y:,.0f}',
        'median_cost': '%{y:,.2f} rub.',
    }
    RANGE_TYPE_START_DATE: dict[str, str] = {
        'weekend': '',
        'workweek': '<i>%{customdata|%Y-%m-%d}</i> - ',
    }

    def __init__(
        self,
        df: pd.DataFrame,
        user_settings: dict[str, Any],
        fig_name: str,
        yaxis_title: str,
        end_start_map: dict[tuple[str, pd.Timestamp], pd.Timestamp],
    ) -> None:
        """
        Initialize linear plot constructor.

        Args:
        - df - `pd.DataFrame` with the data to display.
        - user_settings - `dict` with the user input.
        - fig_name - the figure name, one of options: 'total_expenses',
          'item_count', 'median_cost'.
        - yaxis_title - a title to the figure Y axis.
        - end_start_map - `dict` of pairs 'df index value - start of the
        period'.
        """
        super().__init__()
        self.df = df
        self.user_settings = user_settings
        self.fig_name = fig_name
        self.yaxis_title = yaxis_title
        self.end_start_map = end_start_map

    def __set_data_filters(self, range_type: str) -> dict[str, np.ndarray]:
        """
        Set base filters to the data.

        Create 3 filters to the data:
        - in_range - data for the given range_type inside the interval;
        - left_out_of_range - data for the given range_type before the
          start date;
        - right_out_of_range - data for the given range_type after the
          end date.
        """
        start_date = self.user_settings['start_date']
        end_date = self.user_settings['end_date']

        range_cond = self.df.index.get_level_values(0) == range_type
        start_cond = self.df.index.get_level_values(1) >= start_date
        end_cond = self.df.index.get_level_values(1) <= end_date

        in_range = (range_cond) & (start_cond) & (end_cond)
        left_out_of_range = (range_cond) & ~(start_cond)
        right_out_of_range = (range_cond) & ~(end_cond)
        return {
            'in_range': in_range,
            'left_out_of_range': left_out_of_range,
            'right_out_of_range': right_out_of_range,
        }

    def __set_hoverlabel_prop(self, border_color: str) -> dict[str, Any]:
        """Set the hoverlabel properties."""
        return dict(
            font_size=14,
            bgcolor=self.bg_color,
            bordercolor=border_color,
            font_color=self.main_text_color,
            font_family=self.font_family,
        )

    def __set_hovertemplate(self, range_type: str) -> str:
        """Set a hovertemplate based on the figure name and range type."""
        value_fmt = self.FIG_NAME_VALUE_FMT[self.fig_name]
        start_date = self.RANGE_TYPE_START_DATE[range_type]
        return (
            f'<b> {value_fmt} </b><extra></extra><br> '
            f'for {start_date} <i>%{{x|%Y-%m-%d}}</i>'
        )

    def _create_in_range_trace(
        self,
        range_filter: np.ndarray,
        range_type: str,
    ) -> go.Scatter:
        """
        Create a scatter plot for the data inside the given interval.

        Custom data are the start dates of the periods.
        """
        filter_df: pd.DataFrame = self.df.loc[range_filter]
        color: str = getattr(self, range_type + '_color')

        return go.Scatter(
            x=filter_df.index.get_level_values(1),
            y=filter_df.values,
            mode='lines+markers',
            showlegend=False,
            marker=dict(size=4, color=color),
            line=dict(width=1.2, color=color),
            hoverlabel=self.__set_hoverlabel_prop(border_color=color),
            hovertemplate=self.__set_hovertemplate(
                range_type=range_type,
            ),
            customdata=[self.end_start_map[idx] for idx in filter_df.index],
        )

    def _create_out_of_range_trace(
        self,
        range_filter: np.ndarray,
        range_type: str,
    ) -> go.Scatter:
        """
        Create a scatter plot outside the given interval.

        The plot contains only low opacity dashed line without any
        data visible on hover.
        """
        filter_df: pd.DataFrame = self.df.loc[range_filter]
        color: str = getattr(self, range_type + '_out_color')

        return go.Scatter(
            x=filter_df.index.get_level_values(1),
            y=filter_df.values,
            mode='lines',
            showlegend=False,
            hoverinfo='skip',
            line=dict(color=color, width=1.2, dash='3px'),
        )

    def _create_legend_trace(self, range_type: str) -> go.Scatter:
        """
        Create an empty trace to be displayed in the legend.

        A trace contains only a square marker that is visible in
        the figure legend.
        """
        color: str = getattr(self, range_type + '_color')

        return go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(
                color=color,
                size=10,
                symbol='square',
            ),
            name=range_type.capitalize(),
        )

    def _set_range_type_traces(self, range_type: str) -> list[go.Scatter]:
        """
        Set figure traces for the given range type.

        Create 4 scatter traces:
        - the solid line with hover info for the data inside the interval.
        - two faded dashed lines for the data outside the interval.
        - the empty trace with square marker to the legend.
        """
        filters = self.__set_data_filters(range_type=range_type)
        method_args_map = {
            '_create_in_range_trace': [
                dict(range_filter=filters['in_range']),
            ],
            '_create_out_of_range_trace': [
                dict(range_filter=filters['left_out_of_range']),
                dict(range_filter=filters['right_out_of_range']),
            ],
            '_create_legend_trace': [dict()],
        }
        return [
            getattr(self, method)(range_type=range_type, **arg)
            for method, args in method_args_map.items()
            for arg in args
        ]

    def _set_traces(self) -> list[go.Scatter]:
        """Set figure traces."""
        user_range_type = self.user_settings['range_type']
        if user_range_type is None or user_range_type == 'all':
            range_types = ['weekend', 'workweek']
        else:
            range_types = [user_range_type]

        data = []
        for range_type in range_types:
            data.extend(self._set_range_type_traces(range_type))
        return data

    def __set_axis_ticks_prop(self) -> dict[str, Any]:
        """Set axis ticks properties."""
        return dict(
            ticks='outside',
            tickwidth=1,
            ticklen=5,
            tickcolor=self.main_text_color,
            tickfont=dict(
                size=14,
                color=self.main_text_color,
                family=self.font_family,
            ),
        )

    def __set_base_axis_prop(self) -> dict[str, Any]:
        """Set base axis properties."""
        return dict(
            title_font=dict(
                size=16,
                color=self.main_text_color,
                family=self.font_family,
            ),
            linecolor=self.main_text_color,
            linewidth=1,
            **self.__set_axis_ticks_prop(),
        )

    def __set_legend_prop(self) -> dict[str, Any]:
        """Set the figure legend properties."""
        return dict(
            font=dict(
                size=14,
                color=self.main_text_color,
                family=self.font_family,
            ),
            itemclick=False,
            itemdoubleclick=False,
            xanchor='right',
            orientation='h',
            x=1,
            yanchor='bottom',
            y=1,
        )

    def _set_xaxis(self) -> go.layout.XAxis:
        """Set the figure xaxis."""
        return go.layout.XAxis(
            title_text='Date',
            title_standoff=10,
            showgrid=False,
            dtick='M1',
            tickformat='%b\n%Y',
            range=['2021-02-05', '2022-07-10'],
            **self.__set_base_axis_prop(),
        )

    def _set_yaxis(self) -> go.layout.YAxis:
        """Set the figure yaxis."""
        return go.layout.YAxis(
            title_text=self.yaxis_title,
            title_standoff=20,
            showgrid=True,
            gridwidth=1,
            gridcolor=self.grid_color,
            tickformat=',.0f',
            rangemode='nonnegative',
            **self.__set_base_axis_prop(),
        )

    def _set_layout(self) -> go.Layout:
        return go.Layout(
            plot_bgcolor=self.bg_color,
            paper_bgcolor=self.bg_color,
            margin=dict(t=0, r=0, b=0, l=0),
            font=dict(
                family=self.font_family,
                color=self.main_text_color,
            ),
            legend=self.__set_legend_prop(),
            xaxis=self._set_xaxis(),
            yaxis=self._set_yaxis(),
        )

    def create_figure(self) -> go.Figure:
        """Create a linear plot."""
        return go.Figure(
            data=self._set_traces(),
            layout=self._set_layout(),
        )
