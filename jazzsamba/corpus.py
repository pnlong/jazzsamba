"""Corpus entry point: JazzSamba(root)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import pandas as pd

from jazzsamba.constants import (
    MUSICIANS_CSV,
    SONGS_CSV,
    SONGS_DIRNAME,
    SPLIT_NAMES,
    SPLITS_DIRNAME,
)
from jazzsamba.song import Song, _as_bool


def read_split_file(path: Path) -> list[int]:
    """Parse a JazzSAMBA ``*.txt`` split file (``#`` comments allowed)."""
    if not path.is_file():
        raise FileNotFoundError(path)
    ids: list[int] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        ids.append(int(line))
    return ids


def is_release_layout(root: Path) -> bool:
    return (root / "async" / "songs").is_dir() or (root / "sync" / "songs").is_dir()


def split_file_path(root: Path, name: str) -> Path:
    """Resolve ``async_test`` → ``async/splits/test.txt`` or ``splits/async_test.txt``."""
    if name not in SPLIT_NAMES:
        raise KeyError(f"Unknown split {name!r}; expected one of {list(SPLIT_NAMES)}")
    protocol, partition = name.split("_", 1)
    release = root / protocol / SPLITS_DIRNAME / f"{partition}.txt"
    working = root / SPLITS_DIRNAME / f"{name}.txt"
    if release.is_file() or is_release_layout(root):
        return release
    return working


def _root_from_env() -> str | None:
    for key in ("JAZZSAMBA_DIR", "JAZZ_SAMBA_ROOT"):
        raw = (os.environ.get(key) or "").strip()
        if raw and not raw.startswith("<"):
            return raw
    return None


def _load_dotenv_for_root() -> None:
    """Pick up ``JAZZSAMBA_DIR`` from a nearby ``.env`` if python-dotenv is installed."""
    if _root_from_env():
        return
    try:
        from dotenv import find_dotenv, load_dotenv
    except ImportError:
        return
    path = find_dotenv(filename=".env", usecwd=True)
    if path:
        load_dotenv(path)


class JazzSamba:
    """Root accessor for a JazzSAMBA dataset directory."""

    def __init__(self, root: str | Path | None = None):
        if root is None:
            _load_dotenv_for_root()
            root = _root_from_env()
            if not root:
                raise ValueError(
                    "Pass root=... or set JAZZSAMBA_DIR / JAZZ_SAMBA_ROOT "
                    "to the assembled JazzSAMBA directory."
                )
        self.root = Path(root).expanduser().resolve()
        songs_csv = self.root / SONGS_CSV
        if not songs_csv.is_file():
            raise FileNotFoundError(
                f"Expected {SONGS_CSV} under {self.root}. "
                "Point root at the assembled JazzSAMBA tree."
            )
        self._songs = pd.read_csv(songs_csv)
        musicians_csv = self.root / MUSICIANS_CSV
        self._musicians = (
            pd.read_csv(musicians_csv) if musicians_csv.is_file() else pd.DataFrame()
        )
        self.songs_dir = self.root / SONGS_DIRNAME
        self.splits_dir = self.root / SPLITS_DIRNAME

    @property
    def songs_table(self) -> pd.DataFrame:
        return self._songs.copy()

    @property
    def musicians_table(self) -> pd.DataFrame:
        return self._musicians.copy()

    def __len__(self) -> int:
        return len(self._songs)

    def song(self, song_id: int) -> Song:
        matches = self._songs.loc[self._songs["song_id"] == song_id]
        if matches.empty:
            raise KeyError(f"Unknown song_id={song_id}")
        return Song.from_row(matches.iloc[0], self.root)

    def songs(
        self,
        *,
        synchronous: bool | None = None,
        genre: str | None = None,
        song_ids: list[int] | None = None,
    ) -> Iterator[Song]:
        frame = self._songs
        if song_ids is not None:
            id_set = set(song_ids)
            frame = frame.loc[frame["song_id"].isin(id_set)]
        if synchronous is not None:
            mask = frame["synchronous"].map(_as_bool) == synchronous
            frame = frame.loc[mask]
        if genre is not None:
            frame = frame.loc[frame["genre"].astype(str) == genre]
        for _, row in frame.sort_values("song_id").iterrows():
            song = Song.from_row(row, self.root)
            if not song.song_dir.is_dir():
                continue
            yield song

    def song_ids(self, *, synchronous: bool | None = None) -> list[int]:
        return [s.song_id for s in self.songs(synchronous=synchronous)]

    def split_ids(self, name: str) -> list[int]:
        """Load frozen benchmark ``song_id``s (``async_test`` reads ``async/splits/test.txt``)."""
        if name not in SPLIT_NAMES:
            raise KeyError(
                f"Unknown split {name!r}; expected one of {list(SPLIT_NAMES)}"
            )
        path = split_file_path(self.root, name)
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing benchmark split file {path}."
            )
        return read_split_file(path)

    def songs_in_split(self, name: str) -> Iterator[Song]:
        """Songs whose ``song_id`` is in the named split and whose directory exists."""
        for song_id in self.split_ids(name):
            song = self.song(song_id)
            if song.song_dir.is_dir():
                yield song

    def list_splits(self) -> list[str]:
        """Return split names that exist on disk."""
        found = []
        for name in SPLIT_NAMES:
            path = split_file_path(self.root, name)
            if path.is_file():
                found.append(name)
        return found
