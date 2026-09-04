"""Lead sheet and reference audio accessors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jazzsamba.constants import LEAD_SHEET_STEM


@dataclass(frozen=True)
class LeadSheet:
    """Symbolic lead-sheet exports at the song root."""

    song_dir: Path

    def _path(self, suffix: str) -> Path | None:
        path = self.song_dir / f"{LEAD_SHEET_STEM}{suffix}"
        return path if path.is_file() else None

    @property
    def mscz(self) -> Path | None:
        return self._path(".mscz")

    @property
    def midi(self) -> Path | None:
        return self._path(".mid")

    @property
    def mxl(self) -> Path | None:
        return self._path(".mxl")

    @property
    def pdf(self) -> Path | None:
        return self._path(".pdf")

    def paths(self) -> dict[str, Path]:
        """Present lead-sheet files (empty on the public JazzSAMBA tree)."""
        out: dict[str, Path] = {}
        for key, prop in (
            ("mscz", self.mscz),
            ("midi", self.midi),
            ("mxl", self.mxl),
            ("pdf", self.pdf),
        ):
            if prop is not None:
                out[key] = prop
        return out


@dataclass(frozen=True)
class ReferenceAudio:
    """Reference listening audio at the song root."""

    song_dir: Path

    def paths(self) -> list[Path]:
        patterns = (
            "reference.mp3",
            "reference_original.mp3",
            "reference_cleaned.mp3",
            "reference.original.mp3",
            "reference.cleaned.mp3",
            "reference.warped.mp3",
        )
        found: list[Path] = []
        for name in patterns:
            path = self.song_dir / name
            if path.is_file():
                found.append(path)
        # Also pick up any other reference*.mp3
        for path in sorted(self.song_dir.glob("reference*.mp3")):
            if path not in found:
                found.append(path)
        return found
