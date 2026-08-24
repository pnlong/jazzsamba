"""Song object wrapping catalog metadata and on-disk assets."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from jazz_samba.constants import SONG_LEVEL_COLUMNS
from jazz_samba.lead_sheet import LeadSheet, ReferenceAudio
from jazz_samba.recording import AsyncRecording, Recording, SyncRecording
from jazz_samba.stem import as_plain_dict
from jazz_samba.take import Take


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return str(value).strip().upper() in {"TRUE", "1", "YES"}


@dataclass
class Song:
    """One JazzSAMBA standard: **song-level** catalog + song directory.

    Song-level fields (title, genre, key, lead sheet, references, …) live here.
    **Take-level** fields — ``measure_sequence``, ``solo_order``, timed
    annotations — belong on :class:`~jazz_samba.take.Take` (see the JazzSAMBA README data model).

    Convenience: :meth:`better_take` and the ``solo_order`` /
    ``measure_sequence`` properties delegate to the ``better`` take so callers
    have a short path, but new code should prefer ``recording.take(...)``.
    """

    song_id: int
    row: dict[str, Any]
    song_dir: Path
    _recording: Recording | None = field(default=None, repr=False, compare=False)

    @classmethod
    def from_row(cls, row: pd.Series | dict[str, Any], root: Path) -> Song:
        data = as_plain_dict(row)
        song_id = int(data["song_id"])
        subdir = data.get("song_subdir_basename")
        if subdir is None or (isinstance(subdir, float) and pd.isna(subdir)):
            raise KeyError(f"song_id={song_id} missing song_subdir_basename")
        root = Path(root)
        protocol = "sync" if _as_bool(data.get("synchronous")) else "async"
        release_dir = root / protocol / "songs" / str(subdir)
        working_dir = root / "songs" / str(subdir)
        if release_dir.is_dir():
            song_dir = release_dir
        elif working_dir.is_dir():
            song_dir = working_dir
        else:
            song_dir = release_dir
        return cls(song_id=song_id, row=data, song_dir=song_dir)

    # --- song-level catalog ---------------------------------------------------

    @property
    def title(self) -> str:
        return str(self.row.get("title", ""))

    @property
    def artist(self) -> str:
        return str(self.row.get("artist", ""))

    @property
    def genre(self) -> str:
        return str(self.row.get("genre", ""))

    @property
    def key_signature(self) -> str:
        return str(self.row.get("key_signature", ""))

    @property
    def time_signature(self) -> str:
        return str(self.row.get("time_signature", ""))

    @property
    def bpm(self) -> float | None:
        raw = self.row.get("bpm")
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    @property
    def form(self) -> str:
        return str(self.row.get("form", ""))

    @property
    def synchronous(self) -> bool:
        return _as_bool(self.row.get("synchronous"))

    @property
    def song_level_meta(self) -> dict[str, Any]:
        """Subset of ``row`` for known song-level columns (plus any extras)."""
        out = {k: self.row[k] for k in SONG_LEVEL_COLUMNS if k in self.row}
        return out

    @property
    def lead_sheet(self) -> LeadSheet:
        return LeadSheet(self.song_dir)

    @property
    def references(self) -> ReferenceAudio:
        return ReferenceAudio(self.song_dir)

    @property
    def reference_url(self) -> str | None:
        raw = self.row.get("reference.url")
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            return None
        text = str(raw).strip()
        return text or None

    @property
    def youtube_id(self) -> str | None:
        raw = self.row.get("youtube_id")
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            return None
        text = str(raw).strip()
        return text or None

    def meta(self, key: str, default: Any = None) -> Any:
        return self.row.get(key, default)

    # --- recording / takes ----------------------------------------------------

    @property
    def recording(self) -> Recording:
        if self._recording is None:
            if self.synchronous:
                self._recording = SyncRecording(self.song_dir, song_row=self.row)
            else:
                self._recording = AsyncRecording(self.song_dir, song_row=self.row)
        return self._recording

    def better_take(self) -> Take:
        return self.recording.take("better")

    def worse_take(self) -> Take:
        return self.recording.take("worse")

    # --- take-level convenience (delegates to better) -------------------------

    @property
    def solo_order(self) -> list[str]:
        """Convenience: ``better`` take solo order (from ``soloists.csv``)."""
        return self.better_take().solo_order

    @property
    def measure_sequence(self) -> str | None:
        """Convenience: ``better`` take measure sequence (from ``bars.csv``)."""
        return self.better_take().measure_sequence
