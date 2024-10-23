#!/usr/bin/python3
"""UI Header."""
from collections.abc import Callable
from functools import wraps

from nicegui import ui

from pretty_gpx.common.utils.asserts import assert_isfile
from pretty_gpx.rendering_modes import RENDERING_MODES
from pretty_gpx.rendering_modes import RenderingMode


def create_rendering_pages() -> None:
    """Create Rendering Pages."""
    for mode in RENDERING_MODES:
        ui.page(get_page_path(mode))(add_header(mode.ui_page, mode.name))


def add_header(body: Callable[[], None], mode_name: str | None) -> Callable[[], None]:
    """Add Permanent Header to the Page."""

    @wraps(body)
    def wrapper() -> None:
        with ui.header().classes('flex justify-between items-center p-4 text-white shadow'):
            # Left section
            if mode_name is None:
                ui.label("Pretty-GPX").classes('text-black text-3xl font-bold')
            else:
                with ui.link(target='/').classes('mx-2'):
                    ui.tooltip('Homepage').classes('text-lg')
                    ui.label("Pretty-GPX").classes('text-white text-3xl font-bold')

            # Right Section
            icon_shape = "w-8 h-8"
            with ui.row().classes('items-center'):
                for mode in RENDERING_MODES:
                    if mode.name == mode_name:
                        svg_to_html(mode.icon_svg).classes(f"{icon_shape} fill-black")
                    else:
                        with ui.link(target=get_page_path(mode)).classes('mx-2'):
                            ui.tooltip(mode.name.capitalize()).classes('text-lg')
                            svg_to_html(mode.icon_svg).classes(f"{icon_shape} fill-white")
        body()

    return wrapper


def get_page_path(mode: RenderingMode) -> str:
    """Get Page Path of a given rendering mode."""
    return f'/{mode.name.lower()}/'


def svg_to_html(svg_path: str) -> ui.html:
    """Load SVG icon and convert to ui.html."""
    assert_isfile(svg_path)
    with open(svg_path) as f:
        return ui.html(f.read())
