"""Create app layout."""
from typing import ClassVar

from dash import html


class LayoutConstructor:
    """Create app layout."""

    ASSETS_DIR: ClassVar[str] = '../assets/'
    IMG_DIR: ClassVar[str] = ASSETS_DIR + 'img/'

    def __init__(self) -> None:
        pass

    def __set_header(self):
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

    def create_layout(self):
        return html.Div(
            [
                self.__set_header(),
            ],
            className='content',
        )
