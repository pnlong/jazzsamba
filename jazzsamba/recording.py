"""Recording modes: async vs sync."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jazzsamba.constants import TAKE_QUALITIES
from jazzsamba.take import Take


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
        if (self.song_dir / "better").is_dir() or (self.song_dir / "worse").is_dir():
            return self.song_dir
        return nested

    def take(self, quality: str = "better") -> Take:
        if quality not in TAKE_QUALITIES:
            raise ValueError(f"quality must be one of {TAKE_QUALITIES}, got {quality!r}")
        folder = self.recording_dir / quality
        return Take(
            quality=quality,
            folder=folder,
            mode=self.mode,
            song_row=self.song_row,
        )

    def takes(self) -> dict[str, Take]:
        out: dict[str, Take] = {}
        for quality in TAKE_QUALITIES:
            folder = self.recording_dir / quality
            if folder.is_dir():
                out[quality] = Take(
                    quality=quality,
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
    """Async session recording (per-instrument better/worse assembly).

    Take-level structure (measure sequence, solo order, annotations) is
    annotated on ``better`` and duplicated onto ``worse``.
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
    """Sync full-band recording (better/worse = whole-take selection).

    Take-level structure may differ between qualities / physical takes.
    """

    def __init__(self, song_dir: Path, *, song_row: dict[str, Any] | None = None):
        super().__init__(song_dir=song_dir, mode="sync", song_row=song_row)
