"""Create app layout."""
import json
from pathlib import Path, PosixPath
from typing import ClassVar

from dash import html


class LayoutConstructor:
    """Create app layout."""

    JSON_DATA_PATH: ClassVar[PosixPath] = Path(
        Path(__file__).parent.parent,
        'initial_data/json_data/layout_properties.json',
    )
    ASSETS_DIR: ClassVar[str] = '../assets/'
    IMG_DIR: ClassVar[str] = ASSETS_DIR + 'img/'

    def __init__(self) -> None:
        self.layout_prop = json.load(open(self.JSON_DATA_PATH))

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

    def __set_summary_item(self, label, icon_name, id):
        return html.Div(
            [
                html.Div(
                    [
                        html.Span('10000000000000000000000000000000', className='summary-value', id=id),
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
                html.Div(
                    [
                        html.Div(className='card', id='menu'),
                        html.Div(className='card linear-plot', id='figure-1'),
                        html.Div(
                            [
                                self.__set_summary_item(**item)
                                for item in self.layout_prop['plot_summary']['figure_1']
                            ],
                            className='summary-aside',
                            id='figure-1-summary',
                        ),
                    ],
                    id='first-row-container',
                ),
            ],
        )

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

    def __set_footer(self) -> html.Footer:
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

    def create_layout(self) -> html.Div:
        return html.Div(
            [
                self.__set_header(),
                self.__set_main(),
                self.__set_footer(),
            ],
            className='content',
        )
