#!/usr/bin/python3
"""NiceGUI Shutdown."""

from nicegui import app
from nicegui import ui


def add_exit_button() -> None:
    """Add Exit Button to the Page."""
    with ui.dialog() as exit_dialog, ui.card():
        ui.label('Confirm exit?')
        with ui.row():
            ui.button('Yes', on_click=lambda: shutdown_app_and_close_tab(), color='red-9')
            ui.button('Cancel', on_click=exit_dialog.close)

    async def confirm_exit() -> None:
        """Display a confirmation dialog before exiting."""
        await exit_dialog

    with ui.page_sticky(position='top-right', x_offset=10, y_offset=10):
        ui.button('Exit',
                  on_click=confirm_exit,
                  color='red-9',
                  icon='logout').props('fab')


def shutdown_app_and_close_tab() -> None:
    """Shutdown the app and close the tab."""
    ui.run_javascript("window.close();")
    app.shutdown()
