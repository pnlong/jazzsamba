"""Recording modes: async vs sync."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jazzsamba.constants import (
    TAKE_QUALITIES,
    canonicalize_take_quality,
    take_quality_folder_names,
)
from jazzsamba.take import Take

_TAKE_FOLDER_MARKERS = ("preferred", "alternate", "better", "worse")


def resolve_take_folder(recording_dir: Path, quality: str) -> tuple[Path, str]:
    """Return ``(folder, canonical_quality)`` for a take quality."""
    canonical = canonicalize_take_quality(quality)
    for name in take_quality_folder_names(canonical):
        folder = recording_dir / name
        if folder.is_dir():
            return folder, canonical
    return recording_dir / canonical, canonical


class Recording:
    """Base recording attached to a song directory."""

    mode: str

    def __init__(
        self,
        song_dir: Path,
        mode: str,
        *,
        song_row: dict[str, Any] | None = None,
    ):
        self.song_dir = Path(song_dir)
        self.mode = mode
        self.song_row = dict(song_row or {})

    @property
    def recording_dir(self) -> Path:
        nested = self.song_dir / self.mode
        if any((self.song_dir / name).is_dir() for name in _TAKE_FOLDER_MARKERS):
            return self.song_dir
        return nested

    def take(self, quality: str = "preferred") -> Take:
        folder, canonical = resolve_take_folder(self.recording_dir, quality)
        return Take(
            quality=canonical,
            folder=folder,
            mode=self.mode,
            song_row=self.song_row,
        )

    def takes(self) -> dict[str, Take]:
        out: dict[str, Take] = {}
        for quality in TAKE_QUALITIES:
            folder, canonical = resolve_take_folder(self.recording_dir, quality)
            if folder.is_dir():
                out[canonical] = Take(
                    quality=canonical,
                    folder=folder,
                    mode=self.mode,
                    song_row=self.song_row,
                )
        return out

    def extras(self) -> Path | None:
        """Async extras folder, if present. Sync recordings have none."""
        return None

    def __getitem__(self, quality: str) -> Take:
        return self.take(quality)


class AsyncRecording(Recording):
    """Async session recording (per-instrument preferred/alternate assembly).

    Take-level structure (measure sequence, solo order, annotations) is
    annotated on ``preferred`` and duplicated onto ``alternate``.
    """

    def __init__(self, song_dir: Path, *, song_row: dict[str, Any] | None = None):
        super().__init__(song_dir=song_dir, mode="async", song_row=song_row)

    def extras(self) -> Path | None:
        """Song-level extras folder (unplanned sax / superseded takes). Not a Take."""
        for path in (self.song_dir / "extras", self.recording_dir / "extras"):
            if path.is_dir():
                return path
        return None


class SyncRecording(Recording):
    """Sync full-band recording (preferred/alternate = whole-take selection).

    Take-level structure may differ between qualities / physical takes.
    """

    def __init__(self, song_dir: Path, *, song_row: dict[str, Any] | None = None):
        super().__init__(song_dir=song_dir, mode="sync", song_row=song_row)
