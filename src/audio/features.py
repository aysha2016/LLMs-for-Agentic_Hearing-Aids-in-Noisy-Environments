"""Audio feature definitions and data structures."""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np


@dataclass
class AudioFeatureSet:
    """Container for extracted audio features."""
    
    # Spectral features
    mfcc: Optional[np.ndarray] = None  # Mel-frequency cepstral coefficients
    mel_spectrogram: Optional[np.ndarray] = None  # Mel-scale spectrogram
    spectral_centroid: Optional[float] = None  # Frequency centroid
    spectral_rolloff: Optional[float] = None  # 85% energy rolloff
    
    # Temporal features
    zero_crossing_rate: Optional[float] = None  # ZCR
    onset_strength: Optional[float] = None  # Onset detection energy
    tempo: Optional[float] = None  # Estimated tempo
    
    # Semantic descriptors
    speech_probability: Optional[float] = None  # 0-1 speech presence
    noise_type: Optional[str] = None  # Background, traffic, machinery, etc.
    noise_level_db: Optional[float] = None  # Estimated noise floor
    
    # Environmental context
    is_speech_present: bool = False
    is_silence: bool = False
    sound_event_class: Optional[str] = None  # Detected sound category
    
    # Metadata
    timestamp: Optional[float] = None
    duration_ms: Optional[float] = None
    sample_rate: int = 16000
    
    def to_dict(self) -> Dict:
        """Convert features to dictionary format."""
        return {
            'spectral': {
                'mfcc': self.mfcc.tolist() if self.mfcc is not None else None,
                'mel_spectrogram': self.mel_spectrogram.tolist() if self.mel_spectrogram is not None else None,
                'spectral_centroid': float(self.spectral_centroid) if self.spectral_centroid is not None else None,
                'spectral_rolloff': float(self.spectral_rolloff) if self.spectral_rolloff is not None else None,
            },
            'temporal': {
                'zero_crossing_rate': float(self.zero_crossing_rate) if self.zero_crossing_rate is not None else None,
                'onset_strength': float(self.onset_strength) if self.onset_strength is not None else None,
                'tempo': float(self.tempo) if self.tempo is not None else None,
            },
            'semantic': {
                'speech_probability': float(self.speech_probability) if self.speech_probability is not None else None,
                'noise_type': self.noise_type,
                'noise_level_db': float(self.noise_level_db) if self.noise_level_db is not None else None,
                'is_speech_present': self.is_speech_present,
                'is_silence': self.is_silence,
                'sound_event_class': self.sound_event_class,
            },
            'metadata': {
                'timestamp': float(self.timestamp) if self.timestamp is not None else None,
                'duration_ms': float(self.duration_ms) if self.duration_ms is not None else None,
                'sample_rate': self.sample_rate,
            }
        }
    
    def to_llm_context(self) -> str:
        """Convert features to natural language context for LLM."""
        context_parts = []
        
        if self.is_silence:
            context_parts.append("Environment: Silent or very quiet")
        else:
            context_parts.append(f"Environment: Sound detected at {self.noise_level_db:.1f}dB")
        
        if self.is_speech_present:
            context_parts.append(f"Speech: Present ({self.speech_probability*100:.0f}% confidence)")
        else:
            context_parts.append(f"Speech: Not detected ({self.speech_probability*100:.0f}% confidence)")
        
        if self.noise_type:
            context_parts.append(f"Noise type: {self.noise_type}")
        
        if self.sound_event_class:
            context_parts.append(f"Sound event: {self.sound_event_class}")
        
        if self.spectral_centroid:
            context_parts.append(f"Spectral profile: {self.spectral_centroid:.0f}Hz centroid")
        
        return " | ".join(context_parts)
