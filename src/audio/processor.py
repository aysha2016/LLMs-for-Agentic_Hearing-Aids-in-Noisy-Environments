"""Audio processing implementation based on LLM decisions."""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class AudioProcessingStrategy:
    """Strategy for audio processing based on LLM decisions."""
    
    noise_suppression_strength: float  # 0-1
    speech_enhancement_level: float  # 0-1
    dynamic_range_compression_ratio: float  # 1-10
    frequency_emphasis: Optional[Dict[str, float]] = None  # Frequency band adjustments
    high_frequency_boost: float = 0.0  # dB
    low_frequency_reduction: float = 0.0  # dB
    adaptive_gain: float = 1.0  # Linear gain
    noise_gate_threshold: float = -40  # dB
    explanation: str = ""


class AudioProcessor:
    """Applies audio processing strategies determined by LLM."""
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize audio processor.
        
        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
    
    def apply_strategy(
        self,
        signal: np.ndarray,
        strategy: AudioProcessingStrategy
    ) -> np.ndarray:
        """
        Apply processing strategy to audio signal.
        
        Args:
            signal: Input audio waveform
            strategy: Processing strategy from LLM decision
        
        Returns:
            Processed audio signal
        """
        processed = signal.copy()
        
        # Apply noise suppression
        if strategy.noise_suppression_strength > 0:
            processed = self._apply_noise_suppression(
                processed,
                strategy.noise_suppression_strength
            )
        
        # Apply noise gate
        processed = self._apply_noise_gate(processed, strategy.noise_gate_threshold)
        
        # Apply speech enhancement
        if strategy.speech_enhancement_level > 0:
            processed = self._apply_speech_enhancement(
                processed,
                strategy.speech_enhancement_level
            )
        
        # Apply dynamic range compression
        if strategy.dynamic_range_compression_ratio > 1.0:
            processed = self._apply_compression(
                processed,
                strategy.dynamic_range_compression_ratio
            )
        
        # Apply frequency shaping
        if strategy.frequency_emphasis:
            processed = self._apply_frequency_emphasis(
                processed,
                strategy.frequency_emphasis
            )
        
        # Apply high/low frequency adjustments
        processed = self._apply_frequency_adjustments(
            processed,
            strategy.high_frequency_boost,
            strategy.low_frequency_reduction
        )
        
        # Apply adaptive gain
        processed = processed * strategy.adaptive_gain
        
        # Prevent clipping
        processed = np.clip(processed, -1.0, 1.0)
        
        return processed
    
    def _apply_noise_suppression(
        self,
        signal: np.ndarray,
        strength: float
    ) -> np.ndarray:
        """Apply spectral subtraction-based noise suppression."""
        # Simple spectral subtraction
        fft = np.fft.rfft(signal)
        magnitude = np.abs(fft)
        phase = np.angle(fft)
        
        # Estimate noise floor (quietest frames)
        frame_energy = magnitude ** 2
        noise_floor = np.percentile(frame_energy, 10)
        
        # Apply spectral subtraction
        suppressed_mag = magnitude ** 2 - strength * noise_floor
        suppressed_mag = np.maximum(suppressed_mag, 0.1 * (magnitude ** 2))
        suppressed_mag = np.sqrt(suppressed_mag)
        
        # Reconstruct
        fft_suppressed = suppressed_mag * np.exp(1j * phase)
        processed = np.fft.irfft(fft_suppressed, n=len(signal))
        
        return processed
    
    def _apply_noise_gate(self, signal: np.ndarray, threshold_db: float) -> np.ndarray:
        """Apply noise gate to suppress signals below threshold."""
        rms = np.sqrt(np.mean(signal ** 2))
        threshold_linear = 10 ** (threshold_db / 20)
        
        gate = np.where(np.abs(signal) > threshold_linear * 0.1, 1.0, 0.0)
        # Smooth gate to avoid clicks
        gate = np.convolve(gate, np.ones(100) / 100, mode='same')
        
        return signal * gate
    
    def _apply_speech_enhancement(
        self,
        signal: np.ndarray,
        level: float
    ) -> np.ndarray:
        """Apply speech enhancement through spectral emphasis."""
        fft = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(len(signal), 1/self.sample_rate)
        
        # Emphasize speech frequencies (300-3000 Hz)
        emphasis = np.ones_like(freqs)
        speech_band = (freqs >= 300) & (freqs <= 3000)
        emphasis[speech_band] = 1.0 + level * 0.5
        
        fft_enhanced = fft * emphasis
        processed = np.fft.irfft(fft_enhanced, n=len(signal))
        
        return processed
    
    def _apply_compression(
        self,
        signal: np.ndarray,
        ratio: float,
        threshold: float = 0.5
    ) -> np.ndarray:
        """Apply dynamic range compression."""
        abs_signal = np.abs(signal)
        
        # Calculate gain reduction
        gain = np.ones_like(signal)
        above_threshold = abs_signal > threshold
        gain[above_threshold] = threshold / (abs_signal[above_threshold] / (1/ratio - 1 + abs_signal[above_threshold]))
        
        # Smooth gain to avoid artifacts
        gain = np.convolve(gain, np.ones(50) / 50, mode='same')
        
        return signal * gain
    
    def _apply_frequency_emphasis(
        self,
        signal: np.ndarray,
        emphasis_dict: Dict[str, float]
    ) -> np.ndarray:
        """Apply custom frequency band emphasis."""
        fft = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(len(signal), 1/self.sample_rate)
        
        emphasis = np.ones_like(freqs)
        
        # Apply band-specific emphasis
        for band, gain_db in emphasis_dict.items():
            gain_linear = 10 ** (gain_db / 20)
            
            if band == "low":
                mask = freqs < 500
            elif band == "mid_low":
                mask = (freqs >= 500) & (freqs < 2000)
            elif band == "mid_high":
                mask = (freqs >= 2000) & (freqs < 8000)
            elif band == "high":
                mask = freqs >= 8000
            else:
                continue
            
            emphasis[mask] *= gain_linear
        
        fft_emphasized = fft * emphasis
        processed = np.fft.irfft(fft_emphasized, n=len(signal))
        
        return processed
    
    def _apply_frequency_adjustments(
        self,
        signal: np.ndarray,
        high_freq_boost_db: float,
        low_freq_reduction_db: float
    ) -> np.ndarray:
        """Apply high/low frequency adjustments."""
        fft = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(len(signal), 1/self.sample_rate)
        
        # High frequency boost (presence peak)
        if high_freq_boost_db != 0:
            boost_linear = 10 ** (high_freq_boost_db / 20)
            high_freq_mask = freqs > 4000
            fft[high_freq_mask] *= boost_linear
        
        # Low frequency reduction (rumble filter)
        if low_freq_reduction_db != 0:
            reduction_linear = 10 ** (low_freq_reduction_db / 20)
            low_freq_mask = freqs < 200
            fft[low_freq_mask] *= reduction_linear
        
        processed = np.fft.irfft(fft, n=len(signal))
        
        return processed
