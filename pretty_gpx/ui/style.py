#!/usr/bin/python3
"""UI Style."""

from nicegui import ui

BOX_SHADOW_STYLE = 'box-shadow: 0 0 20px 10px rgba(0, 0, 0, 0.2)'


def add_ui_hover_highlight_style() -> None:
    """Darken on idle and highlight on hover."""
    ui.add_head_html("""
    <style>
        .hover-highlight {
            filter: brightness(0.7);  /* Darkens the image by default */
            transition: filter 0.3s ease;
        }
        .hover-highlight:hover {
            filter: brightness(1);  /* Removes darkening on hover */
        }
    </style>
    """)
