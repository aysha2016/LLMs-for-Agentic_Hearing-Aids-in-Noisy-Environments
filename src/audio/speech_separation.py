"""Basic speech/source separation utilities.

This module provides a lightweight, demonstration-quality separation
algorithm leveraging non-negative matrix factorization (NMF) on the
magnitude spectrogram.  It also includes simple user-preference
selection logic to pick one of the estimated sources according to
criteria such as loudness or estimated pitch.

The functions are intentionally kept simple so they can be imported
without introducing heavy dependencies beyond the existing
requirements (librosa, scikit-learn).
"""

from typing import List, Tuple

import numpy as np
import librosa
from sklearn.decomposition import NMF
from src.utils.audio_ops import compute_rms


def separate_sources(
    audio: np.ndarray, sample_rate: int, n_sources: int = 2
) -> List[np.ndarray]:
    """Estimate individual speaker tracks from a mixed signal.

    A basic NMF-based approach is used on the magnitude spectrogram.  The
    returned audio streams will be approximately the same length as the
    input, but may be slightly shorter due to the inverse-STFT overlap
    handling.

    Args:
        audio: Mono waveform array (float32, -1..1).
        sample_rate: Sampling frequency in Hz.
        n_sources: Number of sources to separate.

    Returns:
        List of separated audio arrays, one per estimated source.
    """
    # compute STFT of the mixture
    n_fft = 1024
    hop_length = 512
    D = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
    magnitude = np.abs(D)

    # apply NMF to magnitude spectrogram
    model = NMF(n_components=n_sources, init="random", random_state=0, max_iter=200)
    W = model.fit_transform(magnitude)  # basis vectors (freq x comp)
    H = model.components_  # activations (comp x frames)

    sources = []
    for i in range(n_sources):
        # reconstruct magnitude for this component
        component_mag = np.outer(W[:, i], H[i, :])
        # create soft mask and apply to original complex STFT
        mask = component_mag / (magnitude + 1e-8)
        source_stft = D * mask
        source_audio = librosa.istft(source_stft, hop_length=hop_length)
        sources.append(source_audio.astype(np.float32))

    return sources


def _compute_rms(audio: np.ndarray) -> float:
    return compute_rms(audio)


def _compute_spectral_centroid(audio: np.ndarray, sr: int) -> float:
    # librosa returns a 2D array (1,frames)
    cent = librosa.feature.spectral_centroid(y=audio, sr=sr)
    return float(np.mean(cent))


def select_preferred_source(
    sources: List[np.ndarray], sample_rate: int, preference: str = "loudest"
) -> np.ndarray:
    """Choose a single stream from a list based on user preference.

    Supported preferences:
    - ``loudest``: highest RMS energy
    - ``quietest``: lowest RMS energy
    - ``highest_pitch``: highest spectral centroid
    - ``lowest_pitch``: lowest spectral centroid

    Args:
        sources: List of audio streams returned by :func:`separate_sources`.
        sample_rate: Sampling rate of the streams (needed for pitch).  It is
            assumed that all streams share the same rate.
        preference: One of the supported preference strings.

    Returns:
        The chosen audio stream.  Raises ``ValueError`` if the preference
        string is unrecognized.
    """
    scores: List[float] = []

    for src in sources:
        if preference == "loudest":
            scores.append(_compute_rms(src))
        elif preference == "quietest":
            scores.append(-_compute_rms(src))
        elif preference == "highest_pitch":
            scores.append(_compute_spectral_centroid(src, sample_rate))
        elif preference == "lowest_pitch":
            scores.append(-_compute_spectral_centroid(src, sample_rate))
        else:
            raise ValueError(f"Unknown preference '{preference}'")

    best_idx = int(np.argmax(scores))
    return sources[best_idx]


def separate_with_preference(
    audio: np.ndarray,
    sample_rate: int,
    preference: str = "loudest",
    n_sources: int = 2,
) -> Tuple[np.ndarray, List[np.ndarray]]:
    """Perform source separation then select by preference.

    Args:
        audio: Mixed input audio.
        sample_rate: Sampling rate of ``audio``.
        preference: User preference string passed to
            :func:`select_preferred_source`.
        n_sources: Number of sources to estimate.

    Returns:
        A tuple ``(chosen_stream, all_streams)``.  ``chosen_stream`` is the
        single audio array matching the preference; ``all_streams`` is the
        full list of separated components.
    """
    all_streams = separate_sources(audio, sample_rate, n_sources=n_sources)
    chosen = select_preferred_source(all_streams, sample_rate, preference)
    return chosen, all_streams
