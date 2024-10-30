#!/usr/bin/python3
"""Ui Plot."""


from matplotlib.axes import Axes
from matplotlib.figure import Figure
from nicegui import ui

from pretty_gpx.ui.utils.style import BOX_SHADOW_STYLE

W_DISPLAY_PIX = 800  # Display width of the preview (in pix)

WORKING_DPI = 50  # DPI of the poster's preview
HIGH_RES_DPI = 400  # DPI of the final poster


class UiPlot:
    """Ui Plot."""

    def __init__(self, visible: bool) -> None:
        with ui.card().classes(f'w-[{W_DISPLAY_PIX}px]').style(f'{BOX_SHADOW_STYLE};') as self.card:
            with ui.pyplot(close=False) as self.plot:
                ax = self.plot.fig.add_subplot()
                ax.axis('off')
        self.card.visible = visible

    @property
    def fig(self) -> Figure:
        """Return the figure."""
        return self.plot.fig

    @property
    def ax(self) -> Axes:
        """Return the figure."""
        return self.fig.gca()

    def update(self) -> None:
        """Update the plot."""
        ui.update(self.plot)

    def make_visible(self) -> None:
        """Make the layout visible."""
        self.card.visible = True
