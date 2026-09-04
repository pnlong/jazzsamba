"""Stereo mapping matches JazzSAMBA mixture.flac left/right rules."""

from pathlib import Path

import numpy as np

from jazzsamba.audio import stereo_map_tracks, track_name_from_stem_path


def test_track_name_strips_debleeded_suffix():
    path = Path("piano_left.debleeded.derived.flac")
    assert track_name_from_stem_path(path) == "piano_left"


def test_stereo_map_left_right_and_dual_mono():
    left = np.array([0.5, 0.0])
    right = np.array([0.0, 0.25])
    bass = np.array([0.1, 0.1])
    stereo = stereo_map_tracks(
        ["piano_left", "piano_right", "bass"],
        [left, right, bass],
    )
    np.testing.assert_allclose(stereo[:, 0], [0.6, 0.1])
    np.testing.assert_allclose(stereo[:, 1], [0.1, 0.35])
