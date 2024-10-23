#!/usr/bin/python3
"""NiceGUI Shutdown."""

from nicegui import app
from nicegui import ui


def shutdown_app_and_close_tab() -> None:
    """Shutdown the app and close the tab."""
    ui.run_javascript("window.close();")
    app.shutdown()
