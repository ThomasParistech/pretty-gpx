#!/usr/bin/python3
"""Cache handler for data collected over area defined by a GpxBounds."""
import hashlib
import os
from dataclasses import dataclass

from pathvalidate import sanitize_filename

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.utils.paths import CACHE_DIR


@dataclass(kw_only=True)
class GpxDataCacheHandler:
    """Cache handler for data collected over area defined by a GpxBounds."""
    name: str
    extension: str

    def __post_init__(self) -> None:
        assert self.extension.startswith('.')

    def get_path(self, ref: GpxTrack | GpxBounds) -> str:
        """Get path to the corresponding cache file."""
        if isinstance(ref, GpxBounds):
            ref_str = f"{ref.lon_min:.4f},{ref.lon_max:.4f},{ref.lat_min:.4f},{ref.lat_max:.4f}"
        elif isinstance(ref, GpxTrack):
            ref_str = ref.get_overpass_lonlat_str()
        else:
            raise ValueError(f"Unsupported type {type(ref)}")

        hash_str = hashlib.sha256(ref_str.encode('utf-8')).hexdigest()
        parent_folder = os.path.join(CACHE_DIR, sanitize_filename(self.name.lower()))
        basename = f"{hash_str}{self.extension}"

        os.makedirs(parent_folder, exist_ok=True)
        return os.path.join(parent_folder, basename)
