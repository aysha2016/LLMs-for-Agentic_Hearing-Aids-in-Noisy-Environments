"""Integration tests."""

import sys
from pathlib import Path
# make sure project root is discoverable when running tests directly
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from src.hearing_aid.controller import HearingAidController
from src.hearing_aid.profiles import UserProfile


class TestHearingAidIntegration:
    """Integration tests for hearing aid system."""
    
    @pytest.fixture
    def controller(self):
        """Create hearing aid controller."""
        profile = UserProfile(name="Test User", preference="clarity")
        return HearingAidController(
            model_name="gpt-4",
            user_profile=profile
        )
    
    @pytest.fixture
    def test_audio(self):
        """Create test audio signal."""
        # 16kHz sine wave for 1 second
        t = np.linspace(0, 1, 16000)
        signal = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
        # Add some noise
        signal += 0.1 * np.random.randn(len(signal))
        return signal
    
    def test_end_to_end_processing(self, controller, test_audio):
        """Test end-to-end audio processing."""
        result = controller.process_audio(test_audio, use_llm_decision=True)
        
        assert result['status'] == 'success'
        assert 'processed_audio' in result
        assert 'strategy' in result
        assert result['strategy'] is not None
        assert len(result['processed_audio']) == len(test_audio)
    
    def test_strategy_preset_selection(self, controller, test_audio):
        """Test manual strategy preset selection."""
        presets = ['quiet_office', 'busy_office', 'crowded_restaurant']
        
        for preset in presets:
            success = controller.select_strategy_preset(preset)
            assert success == True
            
            result = controller.process_audio(test_audio, use_llm_decision=False)
            assert result['status'] == 'success'
    
    def test_user_profile_update(self, controller):
        """Test user profile update."""
        new_profile = UserProfile(name="Updated User", preference="comfort")
        controller.set_user_profile(new_profile)
        
        status = controller.get_system_status()
        assert status['user_profile'] == "Updated User"
    
    def test_processing_enable_disable(self, controller, test_audio):
        """Test enabling/disabling processing."""
        # Enable
        controller.enable_processing()
        result = controller.process_audio(test_audio)
        assert result['status'] == 'success'
        
        # Disable
        controller.disable_processing()
        result = controller.process_audio(test_audio)
        assert result['status'] == 'disabled'

    def test_speech_separation_integration(self):
        """Run the new separation utility on a real dataset file."""
        import numpy as np
        from scipy.io import wavfile
        from pathlib import Path
        from src.audio.speech_separation import separate_with_preference

        # pick a small scenario from the clean dataset
        path = Path("datasets/multispeaker_audio/clean/office_2speaker.wav")
        if not path.exists():
            pytest.skip("dataset file not available")
        sr, audio = wavfile.read(str(path))
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32767.0

        chosen, components = separate_with_preference(audio, sr, preference="loudest", n_sources=2)
        assert isinstance(components, list)
        assert len(components) == 2
        # check that chosen matches one of the returned components
        assert any(np.allclose(chosen, c, atol=1e-6) for c in components)
        # chosen should not be empty
        assert len(chosen) > 0

    def test_controller_multi_speaker(self):
        """Verify controller can perform multi-speaker enhancement."""
        from pathlib import Path
        from scipy.io import wavfile

        path = Path("datasets/multispeaker_audio/clean/office_2speaker.wav")
        if not path.exists():
            pytest.skip("dataset file not available")

        sr, audio = wavfile.read(str(path))
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32767.0

        # create a simple controller with same profile as fixture
        from src.hearing_aid.controller import HearingAidController
        from src.hearing_aid.profiles import UserProfile
        profile = UserProfile(name="Test User", preference="clarity")
        controller_ms = HearingAidController(
            sample_rate=sr,
            user_profile=profile,
            enable_neural_denoising=False
        )

        result = controller_ms.process_audio(
            audio,
            use_llm_decision=False,
            use_speaker_separation=True,
            sep_n_sources=2,
            sep_preference="loudest",
        )

        # should return list of processed streams
        assert isinstance(result.get("processed_streams"), list)
        assert len(result["processed_streams"]) == 2
        assert "chosen_audio" in result
        assert result["chosen_index"] in [0, 1]
        assert len(result["chosen_audio"]) > 0
