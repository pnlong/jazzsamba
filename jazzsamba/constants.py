"""Constants for JazzSAMBA on-disk layout and instrument vocabularies."""

from __future__ import annotations

TAKE_QUALITIES = ("better", "worse")

INSTRUMENTS = (
    "drums",
    "bass",
    "piano",
    "trumpet",
    "saxophone_alto",
    "saxophone_tenor",
)

RHYTHM_INSTRUMENTS = frozenset({"drums", "bass", "piano"})
SAX_INSTRUMENTS = frozenset({"saxophone_alto", "saxophone_tenor"})
HORN_INSTRUMENTS = frozenset({"trumpet"}) | SAX_INSTRUMENTS

ASYNC_WAV_TRACKS = (
    "drums_left",
    "drums_right",
    "bass",
    "piano_left",
    "piano_right",
    "trumpet",
    "saxophone_alto",
    "saxophone_tenor",
)

SYNC_WAV_TRACKS = (
    "drums_left",
    "drums_right",
    "drums_kick",
    "bass",
    "piano_left",
    "piano_right",
    "trumpet",
    "saxophone_alto",
    "saxophone_tenor",
)

TRACK_TO_INSTRUMENT = {
    "drums_left": "drums",
    "drums_right": "drums",
    "drums_kick": "drums",
    "piano_left": "piano",
    "piano_right": "piano",
    "bass": "bass",
    "trumpet": "trumpet",
    "saxophone_alto": "saxophone_alto",
    "saxophone_tenor": "saxophone_tenor",
}

# Instruments whose MIDI is DAW ground truth (not AMT) when present as ``{name}.mid``.
ASYNC_GT_MIDI_INSTRUMENTS = frozenset({"drums", "piano"})
SYNC_GT_MIDI_INSTRUMENTS = frozenset({"piano"})

MIXTURE_FILENAME = "mixture.flac"
MIXTURE_SYNTHESIZED_FILENAME = "mixture.synthesized.flac"
MIXTURE_DEBLEEDED_FILENAME = "mixture.debleeded.flac"
MIXTURE_DEBLEEDED_DERIVED_FILENAME = "mixture.debleeded.derived.flac"
TRANSCRIBED_MIDI_SUFFIX = ".transcribed.mid"
TRANSCRIBED_MIDI_DERIVED_SUFFIX = ".transcribed.derived.mid"

ANNOTATION_NAMES = (
    "bars",
    "chords",
    "sections",
    "soloists",
    "section_musicians",
    "notes",
)

ANNOTATIONS_DIRNAME = "annotations"

LEAD_SHEET_STEM = "lead_sheet"
SONGS_CSV = "songs.csv"
MUSICIANS_CSV = "musicians.csv"
SONGS_DIRNAME = "songs"
SPLITS_DIRNAME = "splits"
SPLIT_SEED = 1738
SPLIT_VERSION = "v1"
SPLIT_NAMES = (
    "async_train",
    "async_val",
    "async_test",
    "sync_train",
    "sync_val",
    "sync_test",
)

# Song-level catalog columns commonly read from songs.csv (non-exhaustive).
SONG_LEVEL_COLUMNS = (
    "song_id",
    "title",
    "artist",
    "genre",
    "year",
    "key_signature",
    "time_signature",
    "bpm",
    "form",
    "tempo_text",
    "is_swung",
    "synchronous",
    "copyright",
    "song_subdir_basename",
    "playing.musician_ids",
    "reference.url",
    "youtube_id",
    "comment",
)