"""jazz-samba: public API for the JazzSAMBA dataset."""

from jazz_samba.corpus import JazzSamba
from jazz_samba.lead_sheet import LeadSheet, ReferenceAudio
from jazz_samba.recording import AsyncRecording, Recording, SyncRecording
from jazz_samba.song import Song
from jazz_samba.stem import AnnotationTable, Stem
from jazz_samba.take import Take

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

__version__ = "0.1.0"
