#!/usr/bin/python3
"""UI Homepage."""
from nicegui import ui

from pretty_gpx.ui.header import add_header
from pretty_gpx.ui.rendering_pages import RENDERING_PAGES
from pretty_gpx.ui.style import add_ui_hover_highlight_style
from pretty_gpx.ui.style import BOX_SHADOW_STYLE


def homepage() -> None:
    """Homepage."""
    add_ui_hover_highlight_style()
    with ui.row().style("height: 100vh; width: 100%; justify-content: center; align-items: center; gap: 20px;"):
        for mode in RENDERING_PAGES:
            with ui.column().style("align-items: center;"):
                with ui.link(target=mode.page_path).classes('mx-2').classes('hover-highlight'):
                    with ui.card(align_items="center").tight().style("width: 500px; border-radius: 3%; "
                                                                     f"{BOX_SHADOW_STYLE};"):
                        ui.image(mode.example_svg).style("max-width: 100%; height: auto;")

                ui.label(mode.name.capitalize()).style('font-family: "Roboto", sans-serif; font-size: 24px;')


def create_homepage() -> None:
    """Create Homepage."""
    ui.page("/")(add_header(homepage, None))
