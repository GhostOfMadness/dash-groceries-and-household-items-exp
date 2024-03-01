"""Create app layout."""
import json
from pathlib import Path
from typing import Any, ClassVar

import pandas as pd
from dash import dcc, html


class BaseLayout:
    """Base class for the layout components."""

    LAYOUT_PROP: ClassVar[dict] = json.load(
        open(
            Path(
                Path(__file__).parents[1],
                'initial_data/json_data/layout_properties.json',
            ),
        ),
    )
    ASSETS_DIR: ClassVar[str] = '../assets/'
    IMG_DIR: ClassVar[str] = ASSETS_DIR + 'img/'


class Sidebar(BaseLayout):
    """The sidebar constructor."""

    def __init__(self, disabled_days: list[pd.Timestamp]) -> None:
        self.layout_prop = self.LAYOUT_PROP['sidebar']
        self.calendar_disabled_days = disabled_days

    def __set_sidebar_item(
        self,
        label: str,
        object_class: str,
        object_prop: dict[str, Any],
    ) -> html.Div:
        """Set an item to the app sidebar."""
        if label == 'Date Range':
            object_prop['disabled_days'] = self.calendar_disabled_days
        return html.Div(
            [
                html.H4(label, className='sidebar-item-label'),
                getattr(dcc, object_class)(**object_prop),
            ],
            className='sidebar-item',
        )

    def __set_sidebar_button(
        self,
        label: str,
        btn_id: str,
    ) -> html.Button:
        """Set a button to the app sidebar."""
        return html.Button(
            label,
            className='sidebar-button',
            id=btn_id,
        )

    def set_sidebar(self) -> html.Div:
        """Set the app sidebar."""
        return html.Div(
            [
                html.Div(
                    [
                        self.__set_sidebar_item(**item)
                        for item in self.layout_prop['items']
                    ],
                    id='sidebar-items',
                ),
                html.Div(
                    [
                        self.__set_sidebar_button(**btn)
                        for btn in self.layout_prop['buttons']
                    ],
                    id='sidebar-buttons',
                ),
                html.Div(id='sidebar-error'),
            ],
            className='card',
            id='sidebar',
        )

    def set_sidebar_error(self, error_text: str) -> html.Span:
        return html.Span(error_text, id='error-message')


class Footer(BaseLayout):
    """The footer constructor."""

    def __init__(self) -> None:
        self.layout_prop = self.LAYOUT_PROP['footer']

    def __set_contact_icon(
        self,
        alt: str,
        img_name: str,
        href: str,
    ) -> html.A:
        """Set a contact icon to the footer."""
        return html.A(
            html.Img(
                alt=alt,
                src=self.IMG_DIR + img_name,
                className='contact-icon',
            ),
            href=href,
            target='_blank',
            className='contact-link',
        )

    def set_footer(self) -> html.Footer:
        """Set the footer to the layout."""
        return html.Footer(
            [
                html.Div(
                    [
                        self.__set_contact_icon(**contact)
                        for contact in self.layout_prop['contacts']
                    ],
                    className='contacts'),
                html.Span('Thank you!', className='thank-you'),
            ],
            className='footer',
        )


class LayoutConstructor(BaseLayout):
    """Create app layout."""

    def __init__(self, disabled_days: list[pd.Timestamp]) -> None:
        self.sidebar_builder = Sidebar(disabled_days=disabled_days)
        self.footer_builder = Footer()

    def __set_header(self) -> html.Header:
        """Set the header to the the layout."""
        return html.Header(
            [
                html.H1('Personal expenses overview'),
                html.Button(
                    'Learn more',
                    id='learn-more-button',
                ),
                html.Img(
                    alt='Dash logo',
                    src=self.IMG_DIR + 'dash-logo.png',
                    id='logo',
                ),
            ],
        )

    def __set_summary_item(
        self,
        label: str,
        icon_name: str,
        item_id: str,
    ) -> html.Div:
        """Set an item to figure sumnary."""
        return html.Div(
            [
                html.Div(
                    [
                        html.Span(className='summary-value', id=item_id),
                        html.Img(
                            alt='Summary icon',
                            src=self.IMG_DIR + icon_name,
                            className='summary-icon',
                        ),
                    ],
                    className='summary-value-icon',
                ),
                html.Span(label, className='summary-label'),
            ],
            className='card summary-item',
        )

    def __set_main(self) -> html.Main:
        """Set main block to the layout."""
        return html.Main(
            [
                dcc.Store(id='working-input', storage_type='session'),
                html.Div(
                    [
                        self.sidebar_builder.set_sidebar(),
                        html.Div(className='card linear-plot', id='figure-1'),
                        html.Div(
                            [
                                self.__set_summary_item(**item)
                                for item in self.LAYOUT_PROP['plot_summary']['figure_1']
                            ],
                            className='summary-aside',
                            id='figure-1-summary',
                        ),
                    ],
                    id='first-row-container',
                ),
            ],
        )

    def create_layout(self) -> html.Div:
        return html.Div(
            [
                self.__set_header(),
                self.__set_main(),
                self.footer_builder.set_footer(),
            ],
            className='content',
        )
