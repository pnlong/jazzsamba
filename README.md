# jazz-samba

Python helper for the **JazzSAMBA** jazz-standards multitrack dataset.

This is the **only public consumer API** for the release. Install the package, point it at a JazzSAMBA directory (after unzipping the Zenodo archives into one folder), and load songs / takes / stems.

## Install

```bash
pip install -e path/to/jazz-samba
# later: pip install jazz-samba
```

## Quick start

```python
from jazz_samba import JazzSamba

ds = JazzSamba("/path/to/JazzSAMBA")
# or JazzSamba() if JAZZSAMBA_DIR / JAZZ_SAMBA_ROOT is set (or a nearby .env)
song = ds.song(0)
take = song.recording.take("better")
mixture = take.mixture_path()
bass = take.stem("bass")
print(bass.audio_path, bass.midi_path, bass.midi_is_gt, bass.is_derived)
for stem in take.stems(is_derived=False):
    ...
```

Iterate and filter (rows whose protocol song directory is missing are skipped):

```python
for song in ds.songs(synchronous=False, genre="swing"):
    take = song.recording.take("better")
    extras = song.recording.extras()  # async only; not a Take
```

`reference.url` / `youtube_id` come from `songs.csv` (pointers only; no audio in JazzSAMBA).

## Object model

The entity diagram and the **song-level vs take-level** split are in the JazzSAMBA dataset README (Zenodo / `JazzSAMBA/README.md`; source [`preprocessing/release/JazzSAMBA_README.md`](../../preprocessing/release/JazzSAMBA_README.md)).

```
JazzSamba(root)
  └── Song
        └── AsyncRecording | SyncRecording
              └── Take (better | worse)
              └── extras/   # async only, not a Take
```

Prefer:

```python
take = song.recording.take("better")
take.measure_sequence
take.solo_order
take.annotations()
```

## Dataset root layout

```
JazzSAMBA/
  songs.csv
  musicians.csv
  async/
    splits/{train,val,test}.txt
    songs/<NN-title>/{better,worse,extras}/
  sync/
    splits/{train,val,test}.txt
    songs/<NN-title>/{better,worse}/
```

```python
ids = ds.split_ids("async_test")  # reads async/splits/test.txt
```

During development you may pass the working `DATA_DIR` (legacy `songs/<id>/{async,sync}/` plus `splits/async_test.txt`).

## License

MIT — see [LICENSE](LICENSE).
