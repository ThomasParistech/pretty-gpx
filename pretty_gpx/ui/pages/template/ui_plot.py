#!/usr/bin/python3
"""Ui Plot."""
import base64
import io
from io import BytesIO
from typing import Protocol

import cairosvg
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from nicegui import ui

from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.ui.utils.run import run_cpu_bound_safe
from pretty_gpx.ui.utils.style import BOX_SHADOW_STYLE

W_DISPLAY_PIX = 800  # Display width of the preview (in pix)

LOW_RES_DPI = 100  # DPI of the poster's preview
HIGH_RES_DPI = 400  # DPI of the final poster


class DrawFunctionProtocol(Protocol):
    """Protocol for the Draw Function."""

    def __call__(self, fig: Figure, ax: Axes, *, high_resolution: bool) -> None: ...  # noqa: D102


class UiPlot:
    """Ui Plot Management.

    Create a rasterized view of Matplotlib plot with a shadow around it.
    It is used to display the preview of the poster in the class `UiManager`.

    We could use the `ui.pyplot` element, but when the plot gets too complex, it might become very slow to render and
    make the page unresponsive. On the other hand, the `ui.image` element is guaranteed to be fast and responsive.
    """

    def __init__(self, visible: bool) -> None:
        with ui.card().classes(f'w-[{W_DISPLAY_PIX}px]').style(f'{BOX_SHADOW_STYLE};') as self.card:
            self.img = ui.image()
        self.card.visible = visible
        self.svg_bytes: bytes | None = None

    @staticmethod
    @profile_parallel
    def draw_png(func: DrawFunctionProtocol) -> str:
        """Update the plot."""
        matplotlib.use('Agg')
        fig, ax = plt.subplots()
        func(fig, ax, high_resolution=False)
        base64_image = fig_to_rasterized_base64(fig, dpi=100)
        return f'data:image/png;base64,{base64_image}'

    @staticmethod
    @profile_parallel
    def draw_svg(func: DrawFunctionProtocol) -> bytes:
        """Update the plot."""
        matplotlib.use('Agg')
        fig, ax = plt.subplots()
        func(fig, ax, high_resolution=True)
        return fig_to_svg_bytes(fig, dpi=HIGH_RES_DPI)

    async def update_preview(self, draw_func: DrawFunctionProtocol) -> None:
        """Draw the figure and rasterize it to update the preview."""
        self.svg_bytes = None
        self.img.source = await run_cpu_bound_safe("Updating Preview", UiPlot.draw_png, draw_func)

    async def render_svg(self, draw_func: DrawFunctionProtocol) -> bytes:
        """Draw the figure and return the SVG bytes."""
        if self.svg_bytes is None:
            self.svg_bytes = await run_cpu_bound_safe("Rendering Vectorized Poster", UiPlot.draw_svg, draw_func)

        return self.svg_bytes

    async def svg_to_pdf_bytes(self, svg_bytes: bytes) -> bytes:
        """Convert SVG bytes to PDF bytes."""
        return await run_cpu_bound_safe("Converting to PDF", svg_to_pdf_bytes, svg_bytes)

    def make_visible(self) -> None:
        """Make the layout visible."""
        self.card.visible = True


@profile_parallel
def svg_to_pdf_bytes(svg_bytes: bytes) -> bytes:
    """Convert SVG bytes to PDF bytes."""
    pdf_bytes = io.BytesIO()
    cairosvg.svg2pdf(bytestring=svg_bytes, write_to=pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes.read()


@profile
def fig_to_rasterized_base64(fig: Figure, dpi: int) -> str:
    """Convert a Matplotlib figure to a rasterized PNG in base64."""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi)
    buf.seek(0)
    res = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    return res


@profile
def fig_to_svg_bytes(fig: Figure, dpi: int) -> bytes:
    """Convert a Matplotlib figure to bytes of a vectorized SVG."""
    buf = BytesIO()
    fig.savefig(buf, format="svg", dpi=dpi)
    res = buf.getvalue()
    buf.close()
    plt.close(fig)
    return res
