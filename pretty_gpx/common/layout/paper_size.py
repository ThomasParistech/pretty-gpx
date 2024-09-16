#!/usr/bin/python3
"""Paper Size."""
from dataclasses import dataclass


@dataclass
class PaperSize:
    """Paper Size."""
    w_mm: int
    h_mm: int
    margin_mm: int


PAPER_SIZES: dict[str, PaperSize] = {
    "A4": PaperSize(w_mm=210, h_mm=297, margin_mm=10),
    "30x40": PaperSize(w_mm=300, h_mm=400, margin_mm=15),
    "50x70": PaperSize(w_mm=500, h_mm=700, margin_mm=25),
    "40x30": PaperSize(w_mm=400, h_mm=300, margin_mm=15),
}
