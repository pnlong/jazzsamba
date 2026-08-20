"""Loader tests that do not require a live DATA_DIR."""

from __future__ import annotations

from pathlib import Path

from jazz_samba.corpus import is_release_layout, split_file_path
from jazz_samba.constants import SPLIT_NAMES


def test_split_file_path_release_and_working(tmp_path: Path):
    release = tmp_path / "JazzSAMBA"
    (release / "async" / "songs").mkdir(parents=True)
    (release / "async" / "splits").mkdir(parents=True)
    (release / "async" / "splits" / "test.txt").write_text("0\n")
    assert is_release_layout(release)
    assert split_file_path(release, "async_test") == release / "async" / "splits" / "test.txt"

    working = tmp_path / "dataset"
    (working / "splits").mkdir(parents=True)
    (working / "splits" / "async_test.txt").write_text("0\n")
    assert not is_release_layout(working)
    assert split_file_path(working, "async_test") == working / "splits" / "async_test.txt"
    assert "async_test" in SPLIT_NAMES
