"""Helper utility functions."""

import numpy as np
from typing import Tuple


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
    # Calculate RMS
    rms = np.sqrt(np.mean(signal ** 2))
    
    # Avoid log(0)
    rms = max(rms, 1e-10)
    
    # Calculate gain
    current_db = 20 * np.log10(rms)
    gain_db = target_db - current_db
    gain_linear = 10 ** (gain_db / 20)
    
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
    rms = np.sqrt(np.mean(signal ** 2))
    peak = np.max(np.abs(signal))
    peak_db = 20 * np.log10(max(peak, 1e-10))
    rms_db = 20 * np.log10(max(rms, 1e-10))
    
    return {
        'rms': float(rms),
        'rms_db': float(rms_db),
        'peak': float(peak),
        'peak_db': float(peak_db),
        'crest_factor': float(peak / (rms + 1e-10)),
        'mean': float(np.mean(signal)),
        'std': float(np.std(signal))
    }
