"""Audio / MIDI path helpers and optional array loading."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


_STEM_AUDIO_SUFFIXES = (
    ".debleeded.derived.flac",
    ".debleeded.flac",
    ".flac",
    ".wav",
)


def load_audio(path: Path, always_2d: bool = True) -> tuple[NDArray[np.floating], int]:
    """Load an audio file with soundfile. Returns ``(samples, sample_rate)``."""
    import soundfile as sf

    data, sr = sf.read(str(path), always_2d=always_2d)
    return np.asarray(data, dtype=np.float64), int(sr)


def track_name_from_stem_path(path: Path) -> str:
    """Canonical track id for stereo mapping (``piano_left``, ``bass``, …)."""
    name = path.name
    lower = name.lower()
    for suffix in _STEM_AUDIO_SUFFIXES:
        if lower.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def stereo_map_tracks(
    track_names: list[str],
    channels: list[np.ndarray],
) -> np.ndarray:
    """Map mono stems to stereo: ``*_left`` → L, ``*_right`` → R, else dual-mono.

    Same rule as ``preprocessing.utils.mixing.stereo_map_tracks`` (JazzSAMBA
    ``mixture.flac``).
    """
    if len(track_names) != len(channels):
        raise ValueError("track_names and channels length mismatch")
    if not channels:
        raise ValueError("No channels to stereo-map")

    max_len = max(len(c) for c in channels)
    left = np.zeros(max_len, dtype=np.float64)
    right = np.zeros(max_len, dtype=np.float64)
    for tn, ch in zip(track_names, channels, strict=True):
        ch_p = np.pad(np.asarray(ch, dtype=np.float64).reshape(-1), (0, max_len - len(ch)))
        if tn.endswith("_left"):
            left += ch_p
        elif tn.endswith("_right"):
            right += ch_p
        else:
            left += ch_p
            right += ch_p
    return np.column_stack([left, right])


def sum_audio_paths(
    paths: list[Path],
    *,
    target_sr: int | None = None,
) -> tuple[NDArray[np.floating], int]:
    """Load and sum mono/stereo stems to a common length (zero-pad shorter)."""
    if not paths:
        raise ValueError("paths must be non-empty")
    arrays: list[NDArray[np.floating]] = []
    sr_out: int | None = None
    for path in paths:
        audio, sr = load_audio(path, always_2d=True)
        if target_sr is not None and sr != target_sr:
            raise ValueError(f"sample rate mismatch for {path}: {sr} != {target_sr}")
        if sr_out is None:
            sr_out = sr
        elif sr != sr_out:
            raise ValueError(f"sample rate mismatch for {path}: {sr} != {sr_out}")
        arrays.append(audio)
    assert sr_out is not None
    n_ch = max(a.shape[1] for a in arrays)
    n_samp = max(a.shape[0] for a in arrays)
    out = np.zeros((n_samp, n_ch), dtype=np.float64)
    for a in arrays:
        out[: a.shape[0], : a.shape[1]] += a
    return out, sr_out


def sum_audio_paths_stereo_mapped(
    paths: list[Path],
    *,
    target_sr: int | None = None,
) -> tuple[NDArray[np.floating], int]:
    """Load mono stems and sum with JazzSAMBA left/right stereo mapping."""
    if not paths:
        raise ValueError("paths must be non-empty")
    names: list[str] = []
    channels: list[np.ndarray] = []
    sr_out: int | None = None
    for path in paths:
        audio, sr = load_audio(path, always_2d=True)
        if target_sr is not None and sr != target_sr:
            raise ValueError(f"sample rate mismatch for {path}: {sr} != {target_sr}")
        if sr_out is None:
            sr_out = sr
        elif sr != sr_out:
            raise ValueError(f"sample rate mismatch for {path}: {sr} != {sr_out}")
        names.append(track_name_from_stem_path(path))
        channels.append(audio[:, 0])
    assert sr_out is not None
    return stereo_map_tracks(names, channels), sr_out
