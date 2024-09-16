#!/usr/bin/python3
"""Paths."""
import os

MAIN_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

DATA_DIR = os.path.join(MAIN_DIR, 'data')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')
COLOR_EXPLORATION_DIR = os.path.join(DATA_DIR, 'color_exploration')

EXAMPLES_DIR = os.path.join(MAIN_DIR, 'examples')
CYCLING_DIR = os.path.join(EXAMPLES_DIR, 'cycling')
HIKING_DIR = os.path.join(EXAMPLES_DIR, 'hiking')

ASSETS_DIR = os.path.join(MAIN_DIR, 'assets')
ICONS_DIR = os.path.join(ASSETS_DIR, 'icons')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')
