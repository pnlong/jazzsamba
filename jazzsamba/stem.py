"""Stem and annotation path objects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from jazzsamba.audio import load_audio
from jazzsamba.constants import (
    ANNOTATION_NAMES,
    ANNOTATIONS_DIRNAME,
    TRACK_TO_INSTRUMENT,
    TRANSCRIBED_MIDI_DERIVED_SUFFIX,
    TRANSCRIBED_MIDI_SUFFIX,
)


def is_derived_path(path: Path | None) -> bool:
    return path is not None and ".derived." in path.name


@dataclass(frozen=True)
class Stem:
    """One close-mic (or instrument) audio track under a take folder."""

    track: str
    audio_path: Path
    midi_path: Path | None = None
    midi_is_gt: bool = False
    debleeded_path: Path | None = None

    @property
    def instrument(self) -> str:
        return TRACK_TO_INSTRUMENT.get(self.track, self.track)

    @property
    def midi_is_derived(self) -> bool:
        if self.midi_path is None:
            return False
        return is_derived_path(self.midi_path) or not self.midi_is_gt

    @property
    def is_derived(self) -> bool:
        """True when MIDI is AMT or debleeded audio is present as a derived file."""
        return self.midi_is_derived or is_derived_path(self.debleeded_path)

    def load(self, *, debleeded: bool = False):
        path = self.debleeded_path if debleeded and self.debleeded_path else self.audio_path
        if path is None:
            raise FileNotFoundError(f"No audio for stem {self.track}")
        return load_audio(path)


@dataclass(frozen=True)
class AnnotationTable:
    """Timed annotation CSV under a take (or song) folder."""

    name: str
    path: Path

    def load(self) -> pd.DataFrame:
        return pd.read_csv(self.path)


def _annotation_candidates(folder: Path, name: str) -> list[Path]:
    ann = folder / ANNOTATIONS_DIRNAME
    return [
        ann / f"{name}.csv",
        ann / f"final_{name}.csv",
        folder / f"final_{name}.csv",
        folder / f"{name}.csv",
    ]


def discover_annotation_tables(folder: Path) -> dict[str, AnnotationTable]:
    """Find public ``annotations/{name}.csv`` then working-tree ``final_{name}.csv``."""
    found: dict[str, AnnotationTable] = {}
    for name in ANNOTATION_NAMES:
        for candidate in _annotation_candidates(folder, name):
            if candidate.is_file():
                found[name] = AnnotationTable(name=name, path=candidate)
                break
    return found


def resolve_midi_for_instrument(
    folder: Path,
    instrument: str,
    gt_instruments: frozenset[str],
) -> tuple[Path | None, bool]:
    """Return ``(midi_path, is_gt)`` preferring DAW GT over AMT when allowed."""
    gt = folder / f"{instrument}.mid"
    amt_derived = folder / f"{instrument}{TRANSCRIBED_MIDI_DERIVED_SUFFIX}"
    amt = folder / f"{instrument}{TRANSCRIBED_MIDI_SUFFIX}"
    amt_path = amt_derived if amt_derived.is_file() else (amt if amt.is_file() else None)
    if instrument in gt_instruments and gt.is_file():
        return gt, True
    if gt.is_file() and amt_path is None:
        return gt, instrument in gt_instruments
    if amt_path is not None:
        return amt_path, False
    if gt.is_file():
        return gt, instrument in gt_instruments
    return None, False


def as_plain_dict(row: Any) -> dict[str, Any]:
    if hasattr(row, "to_dict"):
        return dict(row.to_dict())
    return dict(row)
