"""Tests for LLM decision engine."""

import pytest
from src.llm.decision_engine import DecisionEngine
from src.llm.safety import SafetyValidator
from src.audio.features import AudioFeatureSet
from src.hearing_aid.profiles import UserProfile


class TestDecisionEngine:
    """Test LLM decision engine."""
    
    @pytest.fixture
    def engine(self):
        """Create decision engine."""
        return DecisionEngine(model_name="gpt-4", enable_safety=True)
    
    @pytest.fixture
    def test_features(self):
        """Create test audio features."""
        features = AudioFeatureSet()
        features.noise_level_db = 45.0
        features.speech_probability = 0.7
        features.is_speech_present = True
        return features
    
    @pytest.fixture
    def user_profile(self):
        """Create test user profile."""
        return UserProfile(preference="clarity")
    
    def test_strategy_decision(self, engine, test_features, user_profile):
        """Test strategy decision making."""
        decision = engine.decide_strategy(test_features, user_profile.to_dict())
        
        assert isinstance(decision, dict)
        assert 'noise_suppression_strength' in decision
        assert 'speech_enhancement_level' in decision
        assert 'adaptive_gain' in decision
        assert 'confidence' in decision


class TestSafetyValidator:
    """Test safety validation."""
    
    @pytest.fixture
    def validator(self):
        """Create safety validator."""
        return SafetyValidator()
    
    def test_valid_strategy(self, validator):
        """Test validation of valid strategy."""
        strategy = {
            'noise_suppression_strength': 0.5,
            'speech_enhancement_level': 0.5,
            'dynamic_range_compression_ratio': 3.0,
            'high_frequency_boost': 2.0,
            'low_frequency_reduction': -3.0,
            'adaptive_gain': 1.0,
            'noise_gate_threshold': -40.0
        }
        
        check = validator.validate_strategy(strategy)
        assert check.is_safe == True
        assert len(check.violations) == 0
    
    def test_invalid_strategy_high_suppression(self, validator):
        """Test detection of invalid noise suppression."""
        strategy = {
            'noise_suppression_strength': 1.5,  # Too high
            'speech_enhancement_level': 0.5,
            'dynamic_range_compression_ratio': 3.0,
            'high_frequency_boost': 2.0,
            'low_frequency_reduction': -3.0,
            'adaptive_gain': 1.0,
            'noise_gate_threshold': -40.0
        }
        
        check = validator.validate_strategy(strategy)
        assert check.is_safe == False
        assert len(check.violations) > 0
    
    def test_apply_safety_bounds(self, validator):
        """Test safety bounds application."""
        strategy = {
            'noise_suppression_strength': 1.5,  # Will be clamped
            'speech_enhancement_level': -0.5,  # Will be clamped
            'dynamic_range_compression_ratio': 15.0,  # Will be clamped
            'high_frequency_boost': 20.0,  # Will be clamped
            'low_frequency_reduction': -20.0,  # Will be clamped
            'adaptive_gain': 0.5,  # Valid
            'noise_gate_threshold': -40.0  # Valid
        }
        
        safe = validator.apply_safety_bounds(strategy)
        
        assert safe['noise_suppression_strength'] <= validator.MAX_NOISE_SUPPRESSION
        assert safe['speech_enhancement_level'] >= 0
        assert safe['dynamic_range_compression_ratio'] <= validator.MAX_COMPRESSION_RATIO
        assert safe['high_frequency_boost'] <= validator.MAX_HIGH_FREQ_BOOST
