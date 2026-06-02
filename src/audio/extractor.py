"""Audio feature extraction module."""

import numpy as np
from typing import Optional, Tuple
from .features import AudioFeatureSet
from src.utils.audio_ops import (
    compute_rms,
    amplitude_to_db,
    compute_rfft,
    compute_spectral_centroid,
    compute_zero_crossing_rate,
)


class AudioFeatureExtractor:
    """Extracts audio features without processing raw waveforms directly."""
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize feature extractor.
        
        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
    
    def extract_features(
        self,
        audio_signal: np.ndarray,
        duration_ms: Optional[float] = None
    ) -> AudioFeatureSet:
        """
        Extract audio features from signal.
        
        Args:
            audio_signal: Audio waveform as numpy array
            duration_ms: Duration of audio in milliseconds
        
        Returns:
            AudioFeatureSet containing extracted features
        """
        features = AudioFeatureSet(sample_rate=self.sample_rate)
        
        # Calculate duration if not provided
        if duration_ms is None:
            duration_ms = (len(audio_signal) / self.sample_rate) * 1000
        features.duration_ms = duration_ms
        
        # Extract spectral features
        features.spectral_centroid = self._compute_spectral_centroid(audio_signal)
        features.spectral_rolloff = self._compute_spectral_rolloff(audio_signal)
        
        # Extract temporal features
        features.zero_crossing_rate = self._compute_zcr(audio_signal)
        features.onset_strength = self._compute_onset_strength(audio_signal)
        
        # Estimate semantic descriptors
        features.noise_level_db = self._estimate_noise_level(audio_signal)
        features.speech_probability = self._estimate_speech_probability(audio_signal)
        features.is_silence = features.noise_level_db < 30  # Threshold for silence
        features.is_speech_present = features.speech_probability > 0.5
        
        # Classify noise and sound events
        features.noise_type = self._classify_noise(audio_signal)
        features.sound_event_class = self._classify_sound_event(audio_signal)
        
        return features
    
    def _compute_spectral_centroid(self, signal: np.ndarray) -> float:
        """Compute spectral centroid in Hz."""
        return compute_spectral_centroid(signal, self.sample_rate)
    
    def _compute_spectral_rolloff(self, signal: np.ndarray, threshold: float = 0.85) -> float:
        """Compute frequency below which 85% of energy is concentrated."""
        magnitude, _, freqs = compute_rfft(signal, self.sample_rate)

        cumsum = np.cumsum(magnitude)
        total_energy = cumsum[-1] if len(cumsum) > 0 else 1

        idx = np.where(cumsum >= threshold * total_energy)[0]
        rolloff = freqs[idx[0]] if len(idx) > 0 else 0

        return float(rolloff)
    
    def _compute_zcr(self, signal: np.ndarray) -> float:
        """Compute zero crossing rate."""
        return compute_zero_crossing_rate(signal)
    
    def _compute_onset_strength(self, signal: np.ndarray) -> float:
        """Compute onset detection energy."""
        # Use RMS energy of derivative as proxy for onsets
        derivative = np.diff(signal)
        onset_energy = np.sqrt(np.mean(derivative ** 2))
        return float(onset_energy)
    
    def _estimate_noise_level(self, signal: np.ndarray) -> float:
        """Estimate noise floor in dB."""
        return amplitude_to_db(compute_rms(signal))
    
    def _estimate_speech_probability(self, signal: np.ndarray) -> float:
        """Estimate probability of speech presence."""
        # Simple heuristic based on spectral characteristics
        centroid = self._compute_spectral_centroid(signal)
        zcr = self._compute_zcr(signal)
        
        # Speech typically has centroid in 1-4kHz range and moderate ZCR
        centroid_score = 1 - abs(centroid - 2000) / 4000
        centroid_score = max(0, min(1, centroid_score))
        
        zcr_score = 1 - abs(zcr - 0.5) / 1.0
        zcr_score = max(0, min(1, zcr_score))
        
        return float((centroid_score + zcr_score) / 2)
    
    def _classify_noise(self, signal: np.ndarray) -> str:
        """Classify noise type."""
        spectral_centroid = self._compute_spectral_centroid(signal)
        zcr = self._compute_zcr(signal)
        
        if spectral_centroid < 500:
            return "low_frequency"
        elif spectral_centroid < 2000:
            return "mid_frequency"
        elif spectral_centroid < 8000:
            return "high_frequency"
        else:
            return "very_high_frequency"
    
    def _classify_sound_event(self, signal: np.ndarray) -> str:
        """Classify detected sound event."""
        noise_level = self._estimate_noise_level(signal)
        speech_prob = self._estimate_speech_probability(signal)
        
        if noise_level < 30:
            return "silence"
        elif speech_prob > 0.7:
            return "speech"
        elif noise_level > 60:
            return "loud_noise"
        else:
            return "background_sound"
