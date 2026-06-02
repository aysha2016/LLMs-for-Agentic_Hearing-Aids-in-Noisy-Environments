"""Tests for src.audio.denoising_integration module."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from src.audio.denoising_integration import (
    NeuralDenoisingStrategy,
    HybridDenoiser,
    DenoisingAwareFeatureExtractor,
)


# --------------- NeuralDenoisingStrategy ---------------

class TestNeuralDenoisingStrategy:

    def _make_mock_denoiser(self, return_value=None):
        denoiser = MagicMock()
        if return_value is None:
            return_value = np.zeros(1600, dtype=np.float32)
        denoiser.denoise.return_value = return_value
        return denoiser

    def test_apply_delegates_to_denoiser(self):
        expected = np.random.randn(1600).astype(np.float32)
        denoiser = self._make_mock_denoiser(expected)
        strategy = NeuralDenoisingStrategy(denoiser)
        signal = np.random.randn(1600).astype(np.float32)
        result = strategy.apply(signal, suppression_strength=0.8)
        denoiser.denoise.assert_called_once_with(signal, 0.8)
        assert np.array_equal(result, expected)

    def test_apply_default_strength(self):
        denoiser = self._make_mock_denoiser()
        strategy = NeuralDenoisingStrategy(denoiser)
        signal = np.random.randn(1600).astype(np.float32)
        strategy.apply(signal)
        denoiser.denoise.assert_called_once_with(signal, 1.0)


# --------------- HybridDenoiser ---------------

class TestHybridDenoiser:

    def test_neural_path_when_available(self):
        denoiser = MagicMock()
        expected = np.ones(1600, dtype=np.float32)
        denoiser.denoise.return_value = expected
        hd = HybridDenoiser(neural_denoiser=denoiser, use_neural=True)
        signal = np.random.randn(1600).astype(np.float32)
        result = hd.denoise(signal, suppression_strength=0.5)
        denoiser.denoise.assert_called_once()
        assert np.array_equal(result, expected)

    def test_fallback_to_spectral_when_no_neural(self):
        hd = HybridDenoiser(neural_denoiser=None, use_neural=True, fallback_to_spectral=True)
        signal = np.random.randn(4000).astype(np.float32)
        result = hd.denoise(signal)
        assert result.shape[0] > 0
        assert result.dtype == np.float32

    def test_fallback_to_spectral_on_neural_failure(self):
        denoiser = MagicMock()
        denoiser.denoise.side_effect = RuntimeError("model error")
        hd = HybridDenoiser(neural_denoiser=denoiser, use_neural=True, fallback_to_spectral=True)
        signal = np.random.randn(4000).astype(np.float32)
        result = hd.denoise(signal)
        assert result.shape[0] > 0

    def test_returns_original_on_neural_failure_no_fallback(self):
        denoiser = MagicMock()
        denoiser.denoise.side_effect = RuntimeError("model error")
        hd = HybridDenoiser(neural_denoiser=denoiser, use_neural=True, fallback_to_spectral=False)
        signal = np.random.randn(4000).astype(np.float32)
        result = hd.denoise(signal)
        assert np.array_equal(result, signal)

    def test_returns_original_no_neural_no_spectral(self):
        hd = HybridDenoiser(neural_denoiser=None, use_neural=False, fallback_to_spectral=False)
        signal = np.random.randn(4000).astype(np.float32)
        result = hd.denoise(signal)
        assert np.array_equal(result, signal)

    def test_spectral_subtraction_with_noise_profile(self):
        hd = HybridDenoiser(neural_denoiser=None, use_neural=False, fallback_to_spectral=True)
        signal = np.random.randn(4000).astype(np.float32)
        noise_profile = np.ones(2001) * 0.01  # rfft of len-4000 signal
        result = hd.denoise(signal, noise_profile=noise_profile, suppression_strength=0.5)
        assert result.shape[0] > 0

    def test_estimate_noise_profile(self):
        hd = HybridDenoiser(neural_denoiser=None)
        signal = np.random.randn(16000).astype(np.float32)
        profile = hd.estimate_noise_profile(signal, segment_duration_ms=500)
        assert isinstance(profile, (float, np.floating, np.ndarray))


# --------------- DenoisingAwareFeatureExtractor ---------------

class TestDenoisingAwareFeatureExtractor:

    def _make_mock_extractor(self):
        extractor = MagicMock()
        feature_set = MagicMock()
        feature_set.noise_level_db = -30.0
        feature_set.speech_probability = 0.8
        extractor.extract_features.return_value = feature_set
        return extractor

    def test_extract_without_denoiser(self):
        base = self._make_mock_extractor()
        dafe = DenoisingAwareFeatureExtractor(base_extractor=base, denoiser=None)
        signal = np.random.randn(1600).astype(np.float32)
        result = dafe.extract_with_denoising(signal, denoise=True)
        assert 'base_features' in result
        # No denoiser, so no denoised features
        assert 'denoised_features' not in result

    def test_extract_with_denoiser(self):
        base = self._make_mock_extractor()
        denoiser = MagicMock()
        denoiser.denoise.return_value = np.zeros(1600, dtype=np.float32)
        dafe = DenoisingAwareFeatureExtractor(base_extractor=base, denoiser=denoiser)
        signal = np.random.randn(1600).astype(np.float32)
        result = dafe.extract_with_denoising(signal, denoise=True, suppression_strength=0.7)
        assert 'base_features' in result
        assert 'denoised_features' in result
        assert 'denoised_audio' in result
        assert 'snr_improvement' in result
        assert 'speech_preservation' in result

    def test_extract_denoise_disabled(self):
        base = self._make_mock_extractor()
        denoiser = MagicMock()
        dafe = DenoisingAwareFeatureExtractor(base_extractor=base, denoiser=denoiser)
        signal = np.random.randn(1600).astype(np.float32)
        result = dafe.extract_with_denoising(signal, denoise=False)
        assert 'base_features' in result
        denoiser.denoise.assert_not_called()

    def test_extract_denoiser_failure_falls_back(self):
        base = self._make_mock_extractor()
        denoiser = MagicMock()
        denoiser.denoise.side_effect = RuntimeError("model error")
        dafe = DenoisingAwareFeatureExtractor(base_extractor=base, denoiser=denoiser)
        signal = np.random.randn(1600).astype(np.float32)
        result = dafe.extract_with_denoising(signal, denoise=True)
        assert 'base_features' in result
        assert 'denoised_features' in result
        assert np.array_equal(result['denoised_audio'], signal)
