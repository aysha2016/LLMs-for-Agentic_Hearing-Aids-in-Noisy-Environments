"""Integration tests."""

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
