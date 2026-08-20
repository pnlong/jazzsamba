# jazzsamba

Python API for the **JazzSAMBA** multitrack jazz-standards dataset.

Install the package, point it at a local `JazzSAMBA/` directory (after unzipping the Zenodo archives into one folder), and load songs, takes, and stems.

## Related repos

| | |
|--|--|
| **Dataset download** | Zenodo (DOI forthcoming) |
| **Project page** | [`pnlong/jazzsamba-demo`](https://github.com/pnlong/jazzsamba-demo) — [listen / explore](https://pnlong.github.io/jazzsamba-demo/) |
| **Processing / release pipeline** | [`pnlong/jazz-standard-dataset`](https://github.com/pnlong/jazz-standard-dataset) (authoring only; not required to use this package) |

## Install

```bash
pip install -e .
# later: pip install jazz-samba
```

From the processing monorepo (submodule):

```bash
pip install -e packages/jazz-samba
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

`reference.url` / `youtube_id` come from `songs.csv` (pointers only; commercial/YouTube audio is not in JazzSAMBA).

## Object model

See [docs/ER.md](docs/ER.md). Canonical layout and song- vs take-level fields are also in the JazzSAMBA dataset `README.md` (shipped on Zenodo).

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

## License

MIT — see [LICENSE](LICENSE).
