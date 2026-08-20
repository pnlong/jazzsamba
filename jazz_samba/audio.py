"""Audio / MIDI path helpers and optional array loading."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def load_audio(path: Path, always_2d: bool = True) -> tuple[NDArray[np.floating], int]:
    """Load an audio file with soundfile. Returns ``(samples, sample_rate)``."""
    import soundfile as sf

    data, sr = sf.read(str(path), always_2d=always_2d)
    return np.asarray(data, dtype=np.float64), int(sr)


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
