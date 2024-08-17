#!/usr/bin/python3
"""Init."""
import os

MAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(MAIN_DIR, 'data')

EXAMPLES_DIR = os.path.join(MAIN_DIR, 'examples')

ASSETS_DIR = os.path.join(MAIN_DIR, 'assets')
ICONS_DIR = os.path.join(ASSETS_DIR, 'icons')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')
