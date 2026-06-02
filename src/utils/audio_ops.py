"""Shared low-level audio operations used across the codebase.

Every function is a pure, stateless helper that operates on NumPy arrays.
Centralising these avoids the duplicated RMS / dB / FFT / ZCR / mixing
snippets that previously lived in extractor, processor, evaluator,
multispeaker_dataset, speech_synthesizer, denoising_integration, and helpers.
"""

from typing import Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Level / energy helpers
# ---------------------------------------------------------------------------

def compute_rms(signal: np.ndarray) -> float:
    """Root-mean-square level of *signal*."""
    return float(np.sqrt(np.mean(signal ** 2)))


def amplitude_to_db(value: float, *, min_val: float = 1e-10) -> float:
    """Convert a linear amplitude value to decibels (20·log10)."""
    return float(20 * np.log10(max(value, min_val)))


def db_to_amplitude(db_value: float) -> float:
    """Convert a dB value to linear amplitude."""
    return float(10 ** (db_value / 20))


# ---------------------------------------------------------------------------
# Spectral helpers
# ---------------------------------------------------------------------------

def compute_rfft(
    signal: np.ndarray,
    sample_rate: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the real FFT of *signal*.

    Returns:
        ``(magnitude, phase, freqs)`` — all 1-D arrays of the same length.
    """
    spec = np.fft.rfft(signal)
    magnitude = np.abs(spec)
    phase = np.angle(spec)
    freqs = np.fft.rfftfreq(len(signal), 1 / sample_rate)
    return magnitude, phase, freqs


def compute_spectral_centroid(signal: np.ndarray, sample_rate: int) -> float:
    """Weighted-average frequency (spectral centroid) in Hz."""
    magnitude, _, freqs = compute_rfft(signal, sample_rate)
    total = np.sum(magnitude)
    if total == 0:
        return 0.0
    return float(np.sum(freqs * magnitude) / total)


# ---------------------------------------------------------------------------
# Temporal helpers
# ---------------------------------------------------------------------------

def compute_zero_crossing_rate(signal: np.ndarray) -> float:
    """Fraction of adjacent samples that have a sign change."""
    return float(np.mean(np.abs(np.diff(np.sign(signal)))) / 2)


# ---------------------------------------------------------------------------
# Normalisation / mixing helpers
# ---------------------------------------------------------------------------

def normalize_peak(
    signal: np.ndarray,
    target_peak: float = 0.95,
    epsilon: float = 1e-8,
) -> np.ndarray:
    """Scale *signal* so its peak absolute value equals *target_peak*.

    Returns the original array unchanged when its peak is zero.
    """
    peak = np.max(np.abs(signal))
    if peak < epsilon:
        return signal
    return signal / peak * target_peak


def normalize_signal(signal: np.ndarray, epsilon: float = 1e-8) -> np.ndarray:
    """Scale *signal* to unit peak (max |x| = 1)."""
    peak = np.max(np.abs(signal))
    if peak < epsilon:
        return signal
    return signal / (peak + epsilon)


def mix_audio_at_offset(
    target: np.ndarray,
    source: np.ndarray,
    start_sample: int,
) -> None:
    """Add *source* into *target* starting at *start_sample* (in-place)."""
    end_sample = min(start_sample + len(source), len(target))
    actual_len = end_sample - start_sample
    if actual_len > 0:
        target[start_sample:end_sample] += source[:actual_len]


def add_noise_at_snr(
    signal: np.ndarray,
    noise: np.ndarray,
    snr_db: float,
) -> np.ndarray:
    """Mix *noise* into *signal* at the desired SNR (dB).

    Both arrays must have the same length.  Returns the noisy signal.
    """
    signal_power = np.mean(signal ** 2)
    noise_power = np.mean(noise ** 2)
    if noise_power == 0:
        return signal.copy()
    snr_linear = 10 ** (snr_db / 10)
    scaling = np.sqrt(signal_power / (snr_linear * noise_power))
    return signal + noise * scaling


# ---------------------------------------------------------------------------
# Resampling
# ---------------------------------------------------------------------------

def resample_linear(audio: np.ndarray, ratio: float) -> np.ndarray:
    """Resample *audio* by a given ratio via linear interpolation.

    ``ratio > 1`` lengthens the array (e.g. up-sampling); ``ratio < 1``
    shortens it.
    """
    if ratio == 1.0 or len(audio) == 0:
        return audio
    new_length = int(len(audio) * ratio)
    indices = np.linspace(0, len(audio) - 1, new_length)
    return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
