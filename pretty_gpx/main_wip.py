#!/usr/bin/python3
"""GUI combining all different rendering modes (Work in Progress)."""
from nicegui import ui

from pretty_gpx.ui.pages.header import create_rendering_pages
from pretty_gpx.ui.pages.homepage import create_homepage

create_homepage()
create_rendering_pages()

ui.run(reload=False, port=12345)
