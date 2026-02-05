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
        decision, safety_check = engine.decide_strategy(test_features, user_profile.to_dict())
        
        # Check that we get Decision object and SafetyCheck
        assert hasattr(decision, 'primary_action')
        assert hasattr(decision, 'confidence')
        assert isinstance(decision.primary_action, dict)
        assert 'noise_suppression_strength' in decision.primary_action
        assert 'speech_enhancement_strength' in decision.primary_action
        assert 'compression_ratio' in decision.primary_action
        assert 'confidence' in decision.__dict__ or decision.confidence is not None


class TestSafetyValidator:
    """Test safety validation."""
    
    @pytest.fixture
    def validator(self):
        """Create safety validator."""
        return SafetyValidator()
    
    def test_valid_strategy(self, validator):
        """Test validation of valid strategy."""
        strategy = {
            'strategy_name': 'balanced_processing',
            'noise_suppression_strength': 0.5,
            'speech_enhancement_strength': 0.5,
            'compression_ratio': 3.0,
            'high_freq_boost_db': 2.0,
            'low_freq_reduction_db': -3.0,
            'frequency_profile': 'neutral',
            'rationale': 'Standard balanced processing for office environment',
            'confidence': 0.8,
            'duration_seconds': 30,
            'is_reversible': True
        }
        
        check = validator.validate_strategy(strategy)
        assert check.is_safe == True
        assert len(check.violations) == 0
    
    def test_invalid_strategy_high_suppression(self, validator):
        """Test detection of invalid noise suppression."""
        strategy = {
            'strategy_name': 'invalid_high_suppression',
            'noise_suppression_strength': 1.5,  # Too high
            'speech_enhancement_strength': 0.5,
            'compression_ratio': 3.0,
            'high_freq_boost_db': 2.0,
            'low_freq_reduction_db': -3.0,
            'frequency_profile': 'neutral',
            'rationale': 'Test invalid high suppression',
            'confidence': 0.8,
            'duration_seconds': 30,
            'is_reversible': True
        }
        
        check = validator.validate_strategy(strategy)
        assert check.is_safe == False
        assert len(check.violations) > 0
    
    def test_apply_safety_bounds(self, validator):
        """Test safety bounds application."""
        strategy = {
            'strategy_name': 'clipped_bounds',
            'noise_suppression_strength': 1.5,  # Will be clamped
            'speech_enhancement_strength': -0.5,  # Will be clamped
            'compression_ratio': 15.0,  # Will be clamped
            'high_freq_boost_db': 20.0,  # Will be clamped
            'low_freq_reduction_db': -20.0,  # Will be clamped
            'frequency_profile': 'neutral',
            'rationale': 'Test safety bounds application',
            'confidence': 0.7,
            'duration_seconds': 30,
            'is_reversible': True
        }
        
        safe = validator.apply_safety_bounds(strategy)
        
        assert safe['noise_suppression_strength'] <= validator.MAX_NOISE_SUPPRESSION
        assert safe['speech_enhancement_strength'] >= 0
        assert safe['compression_ratio'] <= validator.MAX_COMPRESSION_RATIO
        assert safe['high_freq_boost_db'] <= validator.MAX_HIGH_FREQ_BOOST
