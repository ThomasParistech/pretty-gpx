#!/usr/bin/python3
"""Test Start/End names."""
from pretty_gpx.common.data.examples import CyclingGpx
from pretty_gpx.common.data.examples import HikingGpx
from pretty_gpx.common.data.place_name import get_start_end_named_points
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.utils.asserts import assert_eq


def __core_test_start_end_names(scene: CyclingGpx | HikingGpx, gt_start_name: str, gt_end_name: str | None) -> None:
    """Test Start/End names."""
    # GIVEN
    gpx = GpxTrack.load(scene.path)

    # WHEN
    start, end = get_start_end_named_points(gpx)

    # THEN
    assert_eq(start.name, gt_start_name)
    assert_eq(end.name, gt_end_name)


def test_vanoise_3() -> None:
    """Test Vanoise 3."""
    __core_test_start_end_names(HikingGpx.VANOISE_3,
                                gt_start_name="Aussois",
                                gt_end_name="Pralognan-la-Vanoise")


def test_vanoise() -> None:
    """Test Vanoise."""
    __core_test_start_end_names(HikingGpx.VANOISE,
                                gt_start_name="Pralognan-la-Vanoise",
                                gt_end_name=None)  # Loop


def test_marmotte() -> None:
    """Test Marmotte."""
    __core_test_start_end_names(CyclingGpx.MARMOTTE,
                                gt_start_name="Le Bourg-d'Oisans",
                                gt_end_name="L'Alpe d'Huez")
