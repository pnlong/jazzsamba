"""jazzsamba: public API for the JazzSAMBA dataset."""

from jazzsamba.corpus import JazzSamba
from jazzsamba.lead_sheet import LeadSheet, ReferenceAudio
from jazzsamba.recording import AsyncRecording, Recording, SyncRecording
from jazzsamba.song import Song
from jazzsamba.stem import AnnotationTable, Stem
from jazzsamba.take import Take

__all__ = [
    "AnnotationTable",
    "AsyncRecording",
    "JazzSamba",
    "LeadSheet",
    "Recording",
    "ReferenceAudio",
    "Song",
    "Stem",
    "SyncRecording",
    "Take",
]

__version__ = "0.1.1"
