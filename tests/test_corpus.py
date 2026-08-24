"""Minimal tests for jazz_samba (run with JAZZSAMBA_DIR or DATA_DIR set)."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("jazz_samba")

from jazz_samba import JazzSamba


@pytest.fixture(scope="module")
def ds():
    root = (
        os.environ.get("JAZZSAMBA_DIR")
        or os.environ.get("JAZZ_SAMBA_ROOT")
        or os.environ.get("DATA_DIR")
    )
    if not root:
        pytest.skip("JAZZSAMBA_DIR / JAZZ_SAMBA_ROOT / DATA_DIR not set")
    return JazzSamba(root)


def test_corpus_counts(ds):
    assert len(ds) == 76
    assert len(ds.song_ids(synchronous=False)) == 50
    assert len(ds.song_ids(synchronous=True)) == 26


def test_async_take_stems(ds):
    song = ds.song(0)
    assert not song.synchronous
    take = song.recording.take("better")
    assert take.mixture_path() is not None
    assert len(take.stems()) >= 1


def test_lead_sheet_paths(ds):
    paths = ds.song(0).lead_sheet.paths()
    assert isinstance(paths, dict)


def test_take_level_structure_on_take(ds):
    song = ds.song(1)
    better = song.recording.take("better")
    worse = song.recording.take("worse")
    # Public release derives order/sequence from soloists.csv and bars.csv.
    assert better.solo_order == worse.solo_order == song.solo_order
    assert better.measure_sequence == worse.measure_sequence == song.measure_sequence
    assert better.solo_order
    soloists = better.annotation("soloists")
    assert soloists is not None
    assert "instrument" in soloists.load().columns


def test_song_level_meta(ds):
    song = ds.song(0)
    meta = song.song_level_meta
    assert meta["song_id"] == 0
    assert "title" in meta


def test_benchmark_splits(ds):
    async_train = ds.split_ids("async_train")
    async_val = ds.split_ids("async_val")
    async_test = ds.split_ids("async_test")
    assert len(async_train) == 40
    assert len(async_val) == 5
    assert len(async_test) == 5
    assert set(async_train) | set(async_val) | set(async_test) == set(
        ds.song_ids(synchronous=False)
    )
    assert set(async_train).isdisjoint(async_val)
    assert set(async_train).isdisjoint(async_test)
    assert set(async_val).isdisjoint(async_test)

    sync_train = ds.split_ids("sync_train")
    sync_val = ds.split_ids("sync_val")
    sync_test = ds.split_ids("sync_test")
    assert len(sync_train) == 20
    assert len(sync_val) == 3
    assert len(sync_test) == 3
    assert set(sync_train) | set(sync_val) | set(sync_test) == set(
        ds.song_ids(synchronous=True)
    )
    assert "async_test" in ds.list_splits()
