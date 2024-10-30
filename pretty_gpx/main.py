#!/usr/bin/python3
"""NiceGUI Webapp. Drag&Drop GPX files to create a custom poster."""

from nicegui import app
from nicegui import ui

from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.fly.fly_io_setup import fly_io_setup
from pretty_gpx.ui.pages.page.header import create_rendering_pages
from pretty_gpx.ui.pages.page.homepage import create_homepage

fly_io_setup()

create_homepage()
create_rendering_pages()


app.on_shutdown(lambda: Profiling.export_events())

ui.run(title='Pretty GPX',
       favicon="✨",
       reload=False)
