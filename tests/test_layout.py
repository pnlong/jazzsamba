"""Loader tests that do not require a live DATA_DIR."""

from __future__ import annotations

from pathlib import Path

from jazzsamba.corpus import is_release_layout, split_file_path
from jazzsamba.constants import SPLIT_NAMES, canonicalize_take_quality
from jazzsamba.recording import resolve_take_folder


def test_canonicalize_take_quality():
    assert canonicalize_take_quality("preferred") == "preferred"
    assert canonicalize_take_quality("alternate") == "alternate"
    assert canonicalize_take_quality("better") == "preferred"
    assert canonicalize_take_quality("worse") == "alternate"


def test_resolve_take_folder_prefers_public_name(tmp_path: Path):
    song = tmp_path / "song"
    (song / "preferred").mkdir(parents=True)
    (song / "better").mkdir(parents=True)
    folder, quality = resolve_take_folder(song, "preferred")
    assert quality == "preferred"
    assert folder.name == "preferred"


def test_resolve_take_folder_falls_back_to_legacy(tmp_path: Path):
    song = tmp_path / "song"
    (song / "better").mkdir(parents=True)
    folder, quality = resolve_take_folder(song, "preferred")
    assert quality == "preferred"
    assert folder.name == "better"


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
