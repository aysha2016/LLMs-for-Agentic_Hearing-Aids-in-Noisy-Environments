"""Utility modules."""

from .logger import setup_logger
from .helpers import normalize_audio, denormalize_audio
from .audio_ops import (
    compute_rms,
    amplitude_to_db,
    db_to_amplitude,
    compute_rfft,
    compute_spectral_centroid,
    compute_zero_crossing_rate,
    normalize_peak,
    normalize_signal,
    mix_audio_at_offset,
    add_noise_at_snr,
    resample_linear,
)

__all__ = [
    "setup_logger",
    "normalize_audio",
    "denormalize_audio",
    "compute_rms",
    "amplitude_to_db",
    "db_to_amplitude",
    "compute_rfft",
    "compute_spectral_centroid",
    "compute_zero_crossing_rate",
    "normalize_peak",
    "normalize_signal",
    "mix_audio_at_offset",
    "add_noise_at_snr",
    "resample_linear",
]
