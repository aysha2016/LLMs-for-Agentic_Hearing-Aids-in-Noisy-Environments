"""Tests for audio module."""

import pytest
import numpy as np
from src.audio.extractor import AudioFeatureExtractor
from src.audio.features import AudioFeatureSet


class TestAudioFeatureExtractor:
    """Test audio feature extraction."""
    
    @pytest.fixture
    def extractor(self):
        """Create feature extractor."""
        return AudioFeatureExtractor(sample_rate=16000)
    
    @pytest.fixture
    def test_signal(self):
        """Create test audio signal."""
        # 1 second of 1kHz sine wave at 16kHz
        t = np.linspace(0, 1, 16000)
        return np.sin(2 * np.pi * 1000 * t).astype(np.float32)
    
    def test_feature_extraction_basic(self, extractor, test_signal):
        """Test basic feature extraction."""
        features = extractor.extract_features(test_signal)
        
        assert isinstance(features, AudioFeatureSet)
        assert features.spectral_centroid is not None
        assert features.spectral_rolloff is not None
        assert features.zero_crossing_rate is not None
        assert features.speech_probability is not None
        assert features.noise_level_db is not None
    
    def test_silence_detection(self, extractor):
        """Test silence detection."""
        silence = np.zeros(16000)
        features = extractor.extract_features(silence)
        
        assert features.is_silence == True
        assert features.noise_level_db < 30
    
    def test_noise_type_classification(self, extractor, test_signal):
        """Test noise type classification."""
        features = extractor.extract_features(test_signal)
        assert features.noise_type in [
            "low_frequency", "mid_frequency", "high_frequency", "very_high_frequency"
        ]
    
    def test_sound_event_classification(self, extractor, test_signal):
        """Test sound event classification."""
        features = extractor.extract_features(test_signal)
        assert features.sound_event_class in [
            "silence", "speech", "loud_noise", "background_sound"
        ]
