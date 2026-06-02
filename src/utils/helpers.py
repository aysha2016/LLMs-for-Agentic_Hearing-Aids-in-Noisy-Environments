"""Helper utility functions."""

import numpy as np
from typing import Tuple
from src.utils.audio_ops import compute_rms, amplitude_to_db, db_to_amplitude


def normalize_audio(
    signal: np.ndarray,
    target_db: float = -20.0
) -> np.ndarray:
    """
    Normalize audio to target dB level.
    
    Args:
        signal: Audio signal
        target_db: Target level in dB
    
    Returns:
        Normalized signal
    """
    current_db = amplitude_to_db(compute_rms(signal))
    gain_linear = db_to_amplitude(target_db - current_db)
    return signal * gain_linear


def denormalize_audio(
    signal: np.ndarray,
    reference_db: float = -20.0
) -> np.ndarray:
    """
    Denormalize audio from normalized level.
    
    Args:
        signal: Normalized audio signal
        reference_db: Reference level used for normalization
    
    Returns:
        Denormalized signal
    """
    # For now, just return as-is
    # In practice, this would store and restore original levels
    return signal.copy()


def get_audio_statistics(signal: np.ndarray) -> dict:
    """
    Calculate audio statistics.
    
    Args:
        signal: Audio signal
    
    Returns:
        Dictionary with statistics
    """
    rms = compute_rms(signal)
    peak = float(np.max(np.abs(signal)))
    peak_db = amplitude_to_db(peak)
    rms_db = amplitude_to_db(rms)

    return {
        'rms': rms,
        'rms_db': rms_db,
        'peak': peak,
        'peak_db': peak_db,
        'crest_factor': float(peak / (rms + 1e-10)),
        'mean': float(np.mean(signal)),
        'std': float(np.std(signal))
    }
