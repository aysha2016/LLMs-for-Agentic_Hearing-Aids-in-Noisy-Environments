"""Audio processing implementation based on LLM decisions."""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass
from src.utils.audio_ops import compute_rfft, db_to_amplitude


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
        # Short-time spectral subtraction with overlap-add to reduce musical noise.
        n_fft = 512
        hop_length = 160
        window = np.hanning(n_fft)

        if len(signal) < n_fft:
            return signal

        # Frame the signal
        num_frames = 1 + (len(signal) - n_fft) // hop_length
        frames = np.lib.stride_tricks.as_strided(
            signal,
            shape=(num_frames, n_fft),
            strides=(signal.strides[0] * hop_length, signal.strides[0])
        )
        frames = frames * window

        spec = np.fft.rfft(frames, axis=1)
        magnitude = np.abs(spec)
        phase = np.angle(spec)

        # Estimate noise floor per frequency bin (lower percentile across frames)
        noise_floor = np.percentile(magnitude, 10, axis=0)

        # Spectral subtraction with a conservative floor
        suppressed_mag = magnitude - strength * noise_floor
        suppressed_mag = np.maximum(suppressed_mag, 0.05 * magnitude)

        # Light temporal smoothing to reduce tonal artifacts
        if suppressed_mag.shape[0] > 2:
            kernel = np.array([0.25, 0.5, 0.25], dtype=np.float32)
            suppressed_mag = np.apply_along_axis(
                lambda m: np.convolve(m, kernel, mode='same'),
                axis=0,
                arr=suppressed_mag
            )

        spec_suppressed = suppressed_mag * np.exp(1j * phase)
        frames_out = np.fft.irfft(spec_suppressed, n=n_fft, axis=1) * window

        # Overlap-add reconstruction
        output_len = (num_frames - 1) * hop_length + n_fft
        processed = np.zeros(output_len, dtype=np.float32)
        window_sum = np.zeros(output_len, dtype=np.float32)
        for i in range(num_frames):
            start = i * hop_length
            processed[start:start + n_fft] += frames_out[i]
            window_sum[start:start + n_fft] += window ** 2

        processed = processed / np.maximum(window_sum, 1e-8)
        # pad if the overlap-add output was shorter than original signal
        if len(processed) < len(signal):
            pad = np.zeros(len(signal) - len(processed), dtype=processed.dtype)
            processed = np.concatenate([processed, pad])
        return processed[:len(signal)]
    
    def _apply_noise_gate(self, signal: np.ndarray, threshold_db: float) -> np.ndarray:
        """Apply noise gate to suppress signals below threshold."""
        threshold_linear = 10 ** (threshold_db / 20)

        # Smooth RMS envelope to avoid choppy gating
        window = int(0.02 * self.sample_rate)
        window = max(window, 1)
        rms = np.sqrt(
            np.convolve(signal ** 2, np.ones(window) / window, mode='same')
        )

        # Soft-knee gate with a gentle floor for natural decay
        knee = threshold_linear * 0.5
        gate = np.clip((rms - threshold_linear) / max(knee, 1e-8), 0.0, 1.0)
        min_gain = 0.1
        gate = min_gain + (1.0 - min_gain) * gate

        # Additional smoothing to prevent pumping
        gate = np.convolve(gate, np.ones(200) / 200, mode='same')
        return signal * gate
    
    def _apply_speech_enhancement(
        self,
        signal: np.ndarray,
        level: float
    ) -> np.ndarray:
        """Apply speech enhancement through spectral emphasis."""
        magnitude, phase, freqs = compute_rfft(signal, self.sample_rate)
        spec = magnitude * np.exp(1j * phase)

        emphasis = np.ones_like(freqs)
        speech_band = (freqs >= 300) & (freqs <= 3000)
        emphasis[speech_band] = 1.0 + level * 0.5

        fft_enhanced = spec * emphasis
        return np.fft.irfft(fft_enhanced, n=len(signal))
    
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
        magnitude, phase, freqs = compute_rfft(signal, self.sample_rate)
        spec = magnitude * np.exp(1j * phase)

        emphasis = np.ones_like(freqs)

        for band, gain_db in emphasis_dict.items():
            gain_linear = db_to_amplitude(gain_db)

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

        fft_emphasized = spec * emphasis
        return np.fft.irfft(fft_emphasized, n=len(signal))
    
    def _apply_frequency_adjustments(
        self,
        signal: np.ndarray,
        high_freq_boost_db: float,
        low_freq_reduction_db: float
    ) -> np.ndarray:
        """Apply high/low frequency adjustments."""
        magnitude, phase, freqs = compute_rfft(signal, self.sample_rate)
        spec = magnitude * np.exp(1j * phase)

        if high_freq_boost_db != 0:
            spec[freqs > 4000] *= db_to_amplitude(high_freq_boost_db)

        if low_freq_reduction_db != 0:
            spec[freqs < 200] *= db_to_amplitude(low_freq_reduction_db)

        return np.fft.irfft(spec, n=len(signal))
