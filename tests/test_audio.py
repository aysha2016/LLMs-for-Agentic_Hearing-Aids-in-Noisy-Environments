"""Tests for audio module."""

import sys
from pathlib import Path
# make sure src directory is on import path when running tests directly
sys.path.insert(0, str(Path(__file__).parent.parent))

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

    def test_controller_multispeaker_synthetic(self):
        """Controller should handle synthetic multi-speaker input when separation enabled."""
        import numpy as np
        from src.hearing_aid.controller import HearingAidController
        from src.hearing_aid.profiles import UserProfile

        # generate mixture of two sine waves
        sr = 8000
        t = np.linspace(0, 1, sr, endpoint=False)
        s1 = np.sin(2 * np.pi * 200 * t).astype(np.float32)
        s2 = 0.5 * np.sin(2 * np.pi * 600 * t).astype(np.float32)
        mix = s1 + s2

        profile = UserProfile(name="Test", preference="clarity")
        controller = HearingAidController(
            sample_rate=sr,
            user_profile=profile,
            enable_neural_denoising=False
        )

        result = controller.process_audio(
            mix,
            use_llm_decision=False,
            use_speaker_separation=True,
            sep_n_sources=2,
            sep_preference="loudest",
        )
        assert isinstance(result.get("processed_streams"), list)
        assert len(result["processed_streams"]) == 2
        assert "chosen_audio" in result
        assert len(result["chosen_audio"]) > 0
