"""Take (quality folder) with stems, mixture, and take-level structure."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from jazz_samba.audio import load_audio, sum_audio_paths
from jazz_samba.constants import (
    ANNOTATIONS_DIRNAME,
    ASYNC_GT_MIDI_INSTRUMENTS,
    ASYNC_WAV_TRACKS,
    MEASURE_SEQUENCE_CSV,
    MEASURE_SEQUENCE_FILENAME,
    MIXTURE_DEBLEEDED_DERIVED_FILENAME,
    MIXTURE_DEBLEEDED_FILENAME,
    MIXTURE_FILENAME,
    MIXTURE_SYNTHESIZED_FILENAME,
    SOLO_ORDER_CSV,
    SOLO_ORDER_FILENAME,
    SYNC_GT_MIDI_INSTRUMENTS,
    SYNC_WAV_TRACKS,
    TRACK_TO_INSTRUMENT,
)
from jazz_samba.stem import (
    AnnotationTable,
    Stem,
    discover_annotation_tables,
    resolve_midi_for_instrument,
)


def _parse_solo_order(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, float) and raw != raw:  # NaN
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    text = str(raw).strip()
    if not text or text.upper() == "NA":
        return []
    if "," in text:
        return [part.strip() for part in text.split(",") if part.strip()]
    if "-" in text and text.replace("-", "").isdigit():
        # musician-id form "3-4-2" — keep as tokens for callers that resolve IDs
        return [part.strip() for part in text.split("-") if part.strip()]
    return [text]


@dataclass
class Take:
    """One ``better`` or ``worse`` quality folder under async/ or sync/.

    **Take-level attributes** (see the JazzSAMBA README data model):

    - ``measure_sequence`` — measures played in this take
    - ``solo_order`` — soloist sequence for this take
    - ``annotations`` / ``annotation`` — timed CSV tables
    - stems, mixture, MIDI

    Async: humans annotate ``better``; the same measure sequence, solo order,
    and annotations are **duplicated** onto ``worse``. Sync: takes may diverge.
    """

    quality: str
    folder: Path
    mode: str  # "async" | "sync"
    # Song-sheet row used as fallback until take-local files are always shipped.
    song_row: dict[str, Any] = field(default_factory=dict)
    _stems_cache: dict[str, Stem] | None = field(default=None, repr=False, compare=False)

    @property
    def wav_tracks(self) -> tuple[str, ...]:
        return SYNC_WAV_TRACKS if self.mode == "sync" else ASYNC_WAV_TRACKS

    @property
    def gt_midi_instruments(self) -> frozenset[str]:
        return SYNC_GT_MIDI_INSTRUMENTS if self.mode == "sync" else ASYNC_GT_MIDI_INSTRUMENTS

    # --- take-level structure -------------------------------------------------

    @property
    def annotations_dir(self) -> Path:
        nested = self.folder / ANNOTATIONS_DIRNAME
        return nested if nested.is_dir() else self.folder

    @property
    def measure_sequence_path(self) -> Path:
        csv_path = self.annotations_dir / MEASURE_SEQUENCE_CSV
        if csv_path.is_file():
            return csv_path
        return self.folder / MEASURE_SEQUENCE_FILENAME

    @property
    def solo_order_path(self) -> Path:
        csv_path = self.annotations_dir / SOLO_ORDER_CSV
        if csv_path.is_file():
            return csv_path
        return self.folder / SOLO_ORDER_FILENAME

    def measure_sequence_payload(self) -> dict[str, Any] | None:
        """Load take-local measure sequence JSON if present (working tree)."""
        path = self.folder / MEASURE_SEQUENCE_FILENAME
        if not path.is_file():
            return None
        return json.loads(path.read_text())

    @property
    def measure_sequence(self) -> str | None:
        """Measure-sequence string for this take.

        Prefers ``annotations/measure_sequence.csv``, then take-local JSON,
        then the songs-sheet ``measure_sequence`` column (working DATA_DIR).
        """
        csv_path = self.annotations_dir / MEASURE_SEQUENCE_CSV
        if csv_path.is_file():
            df = pd.read_csv(csv_path)
            if "measure" in df.columns and not df.empty:
                return "_".join(str(int(m)) for m in df["measure"])
        payload = self.measure_sequence_payload()
        if payload is not None:
            base = payload.get("base_measure_sequence")
            if base:
                return str(base)
            measures = payload.get("measures")
            if measures:
                return "_".join(str(m) for m in measures)
        raw = self.song_row.get("measure_sequence")
        if raw is None or (isinstance(raw, float) and raw != raw):
            return None
        text = str(raw).strip()
        return text or None

    @property
    def solo_order(self) -> list[str]:
        """Solo order for this take (instrument names or musician-id tokens).

        Prefers ``annotations/solo_order.csv``; then take-local JSON; then sheet.
        """
        csv_path = self.annotations_dir / SOLO_ORDER_CSV
        if csv_path.is_file():
            df = pd.read_csv(csv_path)
            if "instrument" in df.columns:
                if "position" in df.columns:
                    df = df.sort_values("position")
                return [str(x).strip() for x in df["instrument"].tolist() if str(x).strip()]
        path = self.folder / SOLO_ORDER_FILENAME
        if path.is_file():
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                if "instruments" in data:
                    return _parse_solo_order(data["instruments"])
                if "solo_order" in data:
                    return _parse_solo_order(data["solo_order"])
                if "musician_ids" in data:
                    return _parse_solo_order(data["musician_ids"])
            return _parse_solo_order(data)
        for key in ("solo_order", "solo_order.musician_ids"):
            parsed = _parse_solo_order(self.song_row.get(key))
            if parsed:
                return parsed
        return []

    def annotations(self) -> dict[str, AnnotationTable]:
        """Timed annotation CSVs for this take (``final_*.csv`` preferred)."""
        return discover_annotation_tables(self.folder)

    def annotation(self, name: str) -> AnnotationTable | None:
        return self.annotations().get(name)

    # --- audio / MIDI ---------------------------------------------------------

    def mixture_path(self, *, synthesized: bool = False, debleeded: bool = False) -> Path | None:
        if debleeded:
            for name in (MIXTURE_DEBLEEDED_DERIVED_FILENAME, MIXTURE_DEBLEEDED_FILENAME):
                path = self.folder / name
                if path.is_file():
                    return path
            return None
        if synthesized:
            path = self.folder / MIXTURE_SYNTHESIZED_FILENAME
            return path if path.is_file() else None
        path = self.folder / MIXTURE_FILENAME
        if path.is_file():
            return path
        # Fall back to synthesized mixture during incomplete pipeline runs.
        synth = self.folder / MIXTURE_SYNTHESIZED_FILENAME
        return synth if synth.is_file() else None

    def load_mixture(self, *, synthesized: bool = False, debleeded: bool = False):
        path = self.mixture_path(synthesized=synthesized, debleeded=debleeded)
        if path is None:
            raise FileNotFoundError(f"No mixture under {self.folder}")
        return load_audio(path)

    def _discover_stems(self) -> dict[str, Stem]:
        stems: dict[str, Stem] = {}
        for track in self.wav_tracks:
            audio = self.folder / f"{track}.flac"
            if not audio.is_file():
                continue
            debleeded = None
            for name in (f"{track}.debleeded.derived.flac", f"{track}.debleeded.flac"):
                cand = self.folder / name
                if cand.is_file():
                    debleeded = cand
                    break
            instrument = TRACK_TO_INSTRUMENT[track]
            midi_path, midi_is_gt = resolve_midi_for_instrument(
                self.folder, instrument, self.gt_midi_instruments
            )
            stems[track] = Stem(
                track=track,
                audio_path=audio,
                midi_path=midi_path,
                midi_is_gt=midi_is_gt,
                debleeded_path=debleeded,
            )
        return stems

    def stems(self, *, is_derived: bool | None = None) -> list[Stem]:
        if self._stems_cache is None:
            self._stems_cache = self._discover_stems()
        stems = list(self._stems_cache.values())
        if is_derived is None:
            return stems
        if is_derived:
            return [s for s in stems if s.is_derived]
        return [
            Stem(
                track=s.track,
                audio_path=s.audio_path,
                midi_path=s.midi_path if s.midi_is_gt else None,
                midi_is_gt=s.midi_is_gt,
                debleeded_path=None,
            )
            for s in stems
        ]

    def stem(self, track_or_instrument: str) -> Stem | None:
        """Return a stem by track name, or the first track for an instrument."""
        if self._stems_cache is None:
            self._stems_cache = self._discover_stems()
        if track_or_instrument in self._stems_cache:
            return self._stems_cache[track_or_instrument]
        matches = [
            s for s in self._stems_cache.values() if s.instrument == track_or_instrument
        ]
        return matches[0] if matches else None

    def stems_for_instrument(self, instrument: str) -> list[Stem]:
        return [s for s in self.stems() if s.instrument == instrument]

    def instrument_audio_paths(
        self, instrument: str, *, debleeded: bool = False
    ) -> list[Path]:
        paths: list[Path] = []
        for stem in self.stems_for_instrument(instrument):
            if debleeded and stem.debleeded_path is not None:
                paths.append(stem.debleeded_path)
            else:
                paths.append(stem.audio_path)
        return paths

    def present_instruments(self) -> list[str]:
        seen: list[str] = []
        for stem in self.stems():
            if stem.instrument not in seen:
                seen.append(stem.instrument)
        return seen

    def mix_instruments(
        self,
        instruments: list[str],
        *,
        debleeded: bool = False,
    ):
        """Sum audio for the given instruments (e.g. conditioning mix)."""
        paths: list[Path] = []
        for instrument in instruments:
            paths.extend(self.instrument_audio_paths(instrument, debleeded=debleeded))
        if not paths:
            raise FileNotFoundError(
                f"No stems for instruments {instruments} under {self.folder}"
            )
        return sum_audio_paths(paths)
