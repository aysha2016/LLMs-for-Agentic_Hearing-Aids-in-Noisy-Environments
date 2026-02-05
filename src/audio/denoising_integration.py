"""Integration of neural denoiser with hearing aid system."""

import numpy as np
from typing import Optional, Dict
import logging
from .neural_denoiser import NeuralDenoiser

logger = logging.getLogger(__name__)


class NeuralDenoisingStrategy:
    """Wrapper to integrate neural denoiser into existing audio processing strategy."""
    
    def __init__(self, denoiser: NeuralDenoiser):
        """
        Initialize neural denoising strategy.
        
        Args:
            denoiser: Initialized NeuralDenoiser instance
        """
        self.denoiser = denoiser
    
    def apply(
        self,
        signal: np.ndarray,
        suppression_strength: float = 1.0
    ) -> np.ndarray:
        """
        Apply neural denoising to signal.
        
        Args:
            signal: Input audio signal
            suppression_strength: Denoising aggressiveness (0-1)
        
        Returns:
            Denoised audio signal
        """
        return self.denoiser.denoise(signal, suppression_strength)


class HybridDenoiser:
    """
    Hybrid denoising combining neural and traditional methods.
    
    Provides fallback mechanism and flexible switching between methods.
    """
    
    def __init__(
        self,
        neural_denoiser: Optional[NeuralDenoiser] = None,
        use_neural: bool = True,
        fallback_to_spectral: bool = True
    ):
        """
        Initialize hybrid denoiser.
        
        Args:
            neural_denoiser: Optional pre-trained NeuralDenoiser
            use_neural: Whether to use neural denoising when available
            fallback_to_spectral: Fallback to spectral subtraction if neural fails
        """
        self.neural_denoiser = neural_denoiser
        self.use_neural = use_neural and neural_denoiser is not None
        self.fallback_to_spectral = fallback_to_spectral
    
    def denoise(
        self,
        signal: np.ndarray,
        noise_profile: Optional[np.ndarray] = None,
        suppression_strength: float = 1.0
    ) -> np.ndarray:
        """
        Apply denoising using available methods.
        
        Args:
            signal: Input audio signal
            noise_profile: Optional noise profile for spectral methods
            suppression_strength: Denoising strength (0-1)
        
        Returns:
            Denoised audio signal
        """
        if self.use_neural:
            try:
                return self.neural_denoiser.denoise(signal, suppression_strength)
            except Exception as e:
                logger.warning(f"Neural denoising failed: {e}. Falling back to spectral subtraction.")
                if self.fallback_to_spectral:
                    return self._spectral_subtraction(signal, noise_profile, suppression_strength)
                return signal
        elif self.fallback_to_spectral:
            return self._spectral_subtraction(signal, noise_profile, suppression_strength)
        else:
            return signal
    
    def _spectral_subtraction(
        self,
        signal: np.ndarray,
        noise_profile: Optional[np.ndarray] = None,
        suppression_strength: float = 1.0
    ) -> np.ndarray:
        """
        Fallback spectral subtraction method.
        
        Args:
            signal: Input audio signal
            noise_profile: Optional noise profile
            suppression_strength: Subtraction strength
        
        Returns:
            Denoised audio
        """
        # Compute STFT
        n_fft = 512
        hop_length = 160
        
        spec = np.fft.rfft(signal)
        mag = np.abs(spec)
        phase = np.angle(spec)
        
        # Estimate noise spectrum if not provided
        if noise_profile is None:
            # Use first 10% as noise estimate
            noise_frames = int(len(mag) * 0.1)
            noise_profile = np.mean(mag[:noise_frames], axis=0) if len(mag.shape) > 1 else mag[:noise_frames].mean()
        
        # Spectral subtraction
        mag_denoised = mag - suppression_strength * noise_profile
        mag_denoised = np.maximum(mag_denoised, 0.1 * mag)  # Floor to prevent over-subtraction
        
        # Reconstruct
        spec_denoised = mag_denoised * np.exp(1j * phase)
        signal_denoised = np.fft.irfft(spec_denoised)
        
        # Match original length
        return signal_denoised[:len(signal)].astype(np.float32)
    
    def estimate_noise_profile(self, signal: np.ndarray, segment_duration_ms: float = 500) -> np.ndarray:
        """
        Estimate noise profile from audio segment.
        
        Args:
            signal: Audio signal
            segment_duration_ms: Duration of segment to analyze
        
        Returns:
            Noise profile
        """
        sample_rate = 16000
        segment_samples = int(sample_rate * segment_duration_ms / 1000)
        segment = signal[:segment_samples]
        
        spec = np.fft.rfft(segment)
        mag = np.abs(spec)
        noise_profile = np.mean(mag)
        
        return noise_profile


class DenoisingAwareFeatureExtractor:
    """
    Feature extractor that incorporates denoising results.
    
    Provides enriched features based on denoised signal analysis.
    """
    
    def __init__(self, base_extractor, denoiser: Optional[NeuralDenoiser] = None):
        """
        Initialize feature extractor with optional denoiser.
        
        Args:
            base_extractor: Base AudioFeatureExtractor instance
            denoiser: Optional NeuralDenoiser for pre-processing
        """
        self.base_extractor = base_extractor
        self.denoiser = denoiser
    
    def extract_with_denoising(
        self,
        audio_signal: np.ndarray,
        denoise: bool = True,
        suppression_strength: float = 1.0
    ) -> Dict:
        """
        Extract features from denoised signal.
        
        Args:
            audio_signal: Input audio signal
            denoise: Whether to apply denoising
            suppression_strength: Denoising strength
        
        Returns:
            Dictionary with base features and denoising info
        """
        result = {}
        
        # Extract base features
        base_features = self.base_extractor.extract_features(audio_signal)
        result['base_features'] = base_features
        
        # Apply denoising if requested
        if denoise and self.denoiser:
            try:
                denoised_audio = self.denoiser.denoise(audio_signal, suppression_strength)
                denoised_features = self.base_extractor.extract_features(denoised_audio)
                result['denoised_features'] = denoised_features
                result['denoised_audio'] = denoised_audio
                
                # Calculate improvement metrics
                result['snr_improvement'] = (
                    denoised_features.noise_level_db - base_features.noise_level_db
                )
                result['speech_preservation'] = denoised_features.speech_probability / (
                    base_features.speech_probability + 1e-8
                )
                
            except Exception as e:
                logger.warning(f"Denoising failed: {e}. Returning base features only.")
                result['denoised_features'] = base_features
                result['denoised_audio'] = audio_signal
        
        return result
