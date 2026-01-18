"""Integration tests for ORAL loop decision making."""

import pytest
import json
from src.llm.decision_engine import DecisionEngine, ObservationContext
from src.llm.safety import SafetyValidator, SafetyCheck


class TestORALLoop:
    """Test the Observe-Reason-Act-Learn loop."""
    
    def setup_method(self):
        """Initialize test fixtures."""
        self.engine = DecisionEngine(enable_safety=True)
        self.validator = SafetyValidator()
    
    def test_observe_phase_no_raw_audio(self):
        """Test that OBSERVE phase never receives raw audio."""
        # Valid observation context - high-level descriptors only
        observation = ObservationContext(
            acoustic_scene="restaurant",
            noise_level_db=75.0,
            speech_confidence=0.65,
            speech_presence=True,
            asr_transcript="Can you pass the... [unclear] ...please",
            noise_type="environmental",
            hearing_loss_profile={"mid": 15.0, "high": 25.0},
            user_preference="clarity",
            listening_intent="conversation",
            recent_actions=[],
            feedback_history=[],
            temporal_context={"time_of_day": "12:30", "day_of_week": "Monday"},
            device_state={"battery_percent": 85, "temperature_celsius": 25.0, "processing_load": 35}
        )
        
        # Should successfully create observation without raw audio
        assert observation.acoustic_scene == "restaurant"
        assert observation.speech_confidence == 0.65
        # NO waveform data should be present
        assert not hasattr(observation, 'waveform')
        assert not hasattr(observation, 'samples')
    
    def test_reason_phase_low_confidence_default(self):
        """Test that REASON phase uses conservative strategy when uncertain."""
        observation = ObservationContext(
            acoustic_scene="unknown",
            noise_level_db=70.0,
            speech_confidence=0.35,  # Low confidence
            speech_presence=True,
            asr_transcript="[unintelligible]",
            noise_type="unknown",
            hearing_loss_profile={},
            user_preference="balanced",
            listening_intent="unknown",  # Unclear intent
            recent_actions=[],
            feedback_history=[],
            temporal_context={"time_of_day": "15:30", "day_of_week": "Wednesday"},
            device_state={"battery_percent": 50, "temperature_celsius": 26.0, "processing_load": 45}
        )
        
        user_profile = {
            "hearing_loss_profile": {},
            "preference": "balanced",
            "listening_intent": "unknown"
        }
        
        decision = self.engine._reason(observation, user_profile)
        
        # With low confidence, should prefer conservative strategy
        assert decision.confidence < 0.6, "Low confidence should result in lower decision confidence"
        # Conservative = lower aggressiveness values
        assert decision.primary_action['noise_suppression_strength'] <= 0.5
        assert decision.primary_action['speech_enhancement_strength'] <= 0.3
    
    def test_act_phase_safety_validation(self):
        """Test that ACT phase validates all safety constraints."""
        # Invalid strategy with violations
        invalid_strategy = {
            'noise_suppression_strength': 1.5,  # VIOLATION: > 0.95
            'speech_enhancement_strength': 0.4,
            'compression_ratio': 10.0,  # VIOLATION: > 8.0
            'high_freq_boost_db': 0.0,
            'low_freq_reduction_db': 0.0,
            'frequency_profile': 'neutral',
            'confidence': 0.9,
            'rationale': 'Test strategy',
            'duration_seconds': 30,
            'is_reversible': True
        }
        
        safety_check = self.validator.validate_strategy(invalid_strategy)
        
        assert not safety_check.is_safe
        assert len(safety_check.violations) > 0
        # Should report bounds violations
        violations_str = str(safety_check.violations)
        assert any('noise_suppression' in v.lower() for v in safety_check.violations)
        assert any('compression' in v.lower() for v in safety_check.violations)
    
    def test_act_phase_parameter_bounds(self):
        """Test that all parameters respect strict bounds."""
        # Test each parameter at boundaries
        test_cases = [
            {
                'name': 'ns_at_min',
                'strategy': {'noise_suppression_strength': 0.0},
                'valid': True
            },
            {
                'name': 'ns_at_max',
                'strategy': {'noise_suppression_strength': 0.95},
                'valid': True
            },
            {
                'name': 'ns_exceed_max',
                'strategy': {'noise_suppression_strength': 0.96},
                'valid': False
            },
            {
                'name': 'se_at_max',
                'strategy': {'speech_enhancement_strength': 0.9},
                'valid': True
            },
            {
                'name': 'se_exceed_max',
                'strategy': {'speech_enhancement_strength': 0.91},
                'valid': False
            },
        ]
        
        for test in test_cases:
            # Build complete strategy for each test
            strategy = {
                'noise_suppression_strength': test['strategy'].get('noise_suppression_strength', 0.5),
                'speech_enhancement_strength': test['strategy'].get('speech_enhancement_strength', 0.0),
                'compression_ratio': 3.5,
                'high_freq_boost_db': 0.0,
                'low_freq_reduction_db': 0.0,
                'frequency_profile': 'neutral',
                'confidence': 0.7,
                'rationale': f"Test: {test['name']}",
                'duration_seconds': 30,
                'is_reversible': True
            }
            
            safety_check = self.validator.validate_strategy(strategy)
            assert safety_check.is_safe == test['valid'], f"Failed: {test['name']}"
    
    def test_act_phase_no_waveform_requests(self):
        """Test that safety validation detects waveform requests."""
        strategy_with_prohibited = {
            'rationale': 'I need the raw waveform data for processing',  # Prohibited!
            'noise_suppression_strength': 0.5,
            'speech_enhancement_strength': 0.0,
            'compression_ratio': 1.0,
            'high_freq_boost_db': 0.0,
            'low_freq_reduction_db': 0.0,
            'frequency_profile': 'neutral',
            'confidence': 0.7,
            'duration_seconds': 30,
            'is_reversible': True
        }
        
        safety_check = self.validator.validate_strategy(strategy_with_prohibited)
        
        assert not safety_check.is_safe
        # Should detect the prohibited term
        assert any('prohibited' in v.lower() or 'waveform' in v.lower() for v in safety_check.violations)
    
    def test_act_phase_requires_rationale(self):
        """Test that all decisions must have explicit rationale."""
        strategy_no_rationale = {
            'rationale': '',  # Empty rationale - VIOLATION
            'noise_suppression_strength': 0.5,
            'speech_enhancement_strength': 0.0,
            'compression_ratio': 1.0,
            'high_freq_boost_db': 0.0,
            'low_freq_reduction_db': 0.0,
            'frequency_profile': 'neutral',
            'confidence': 0.7,
            'duration_seconds': 30,
            'is_reversible': True
        }
        
        safety_check = self.validator.validate_strategy(strategy_no_rationale)
        
        assert not safety_check.is_safe
        assert any('rationale' in v.lower() for v in safety_check.violations)
    
    def test_act_phase_minimum_duration(self):
        """Test minimum decision duration constraint (prevent oscillation)."""
        # Too short duration
        strategy_short_duration = {
            'duration_seconds': 5,  # VIOLATION: < 10
            'noise_suppression_strength': 0.5,
            'speech_enhancement_strength': 0.0,
            'compression_ratio': 1.0,
            'high_freq_boost_db': 0.0,
            'low_freq_reduction_db': 0.0,
            'frequency_profile': 'neutral',
            'confidence': 0.7,
            'rationale': 'This duration is too short',
            'is_reversible': True
        }
        
        safety_check = self.validator.validate_strategy(strategy_short_duration)
        
        assert not safety_check.is_safe
        assert any('duration' in v.lower() and 'short' in v.lower() for v in safety_check.violations)
    
    def test_act_phase_reversibility_required(self):
        """Test that all decisions must be reversible."""
        strategy_irreversible = {
            'is_reversible': False,  # CRITICAL VIOLATION
            'noise_suppression_strength': 0.5,
            'speech_enhancement_strength': 0.0,
            'compression_ratio': 1.0,
            'high_freq_boost_db': 0.0,
            'low_freq_reduction_db': 0.0,
            'frequency_profile': 'neutral',
            'confidence': 0.7,
            'rationale': 'This decision is permanent',
            'duration_seconds': 30
        }
        
        safety_check = self.validator.validate_strategy(strategy_irreversible)
        
        assert not safety_check.is_safe
        # Should flag this as critical violation
        assert any('reversible' in v.lower() or 'critical' in v.lower() for v in safety_check.violations)
    
    def test_learn_phase_effectiveness_computation(self):
        """Test LEARN phase effectiveness signal computation."""
        # Create mock decision and outcome
        from datetime import datetime
        from src.llm.decision_engine import Decision
        
        decision = Decision(
            primary_action={'strategy_name': 'moderate_ns_with_speech_boost'},
            confidence=0.82,
            rationale='Test decision',
            duration_seconds=30,
            secondary_adjustments=[],
            is_reversible=True,
            timestamp=datetime.now().isoformat()
        )
        
        self.engine.decision_history.append(decision)
        
        # Positive outcome: ASR confidence improved, user satisfied
        outcome = {
            'asr_confidence_change': 0.15,  # +15% improvement
            'user_override': False,
            'satisfaction': 85  # Out of 100
        }
        
        effectiveness = self.engine._compute_effectiveness(outcome, user_satisfaction=85)
        
        # Should be positive effectiveness
        assert effectiveness > 0.5, "Positive outcome should result in effectiveness > 0.5"
    
    def test_learn_phase_negative_outcome(self):
        """Test LEARN phase with negative outcome."""
        from datetime import datetime
        from src.llm.decision_engine import Decision
        
        decision = Decision(
            primary_action={'strategy_name': 'aggressive_ns'},
            confidence=0.70,
            rationale='Test aggressive decision',
            duration_seconds=30,
            secondary_adjustments=[],
            is_reversible=True,
            timestamp=datetime.now().isoformat()
        )
        
        self.engine.decision_history.append(decision)
        
        # Negative outcome: user overrode after 5 seconds
        outcome = {
            'asr_confidence_change': -0.10,  # -10% decline
            'user_override': True,
            'satisfaction': 25  # Out of 100
        }
        
        effectiveness = self.engine._compute_effectiveness(outcome, user_satisfaction=25)
        
        # Should be negative effectiveness
        assert effectiveness < 0.5, "Negative outcome should result in effectiveness < 0.5"
    
    def test_fallback_conservative_decision(self):
        """Test fallback to conservative strategy on safety failure."""
        observation = ObservationContext(
            acoustic_scene="restaurant",
            noise_level_db=75.0,
            speech_confidence=0.65,
            speech_presence=True,
            asr_transcript="Test",
            noise_type="environmental",
            hearing_loss_profile={},
            user_preference="clarity",
            listening_intent="conversation",
            recent_actions=[],
            feedback_history=[],
            temporal_context={"time_of_day": "12:30", "day_of_week": "Monday"},
            device_state={"battery_percent": 85, "temperature_celsius": 25.0, "processing_load": 35}
        )
        
        fallback = self.engine._fallback_conservative_decision(observation)
        
        # Fallback should have minimal parameters
        assert fallback.primary_action['noise_suppression_strength'] == 0.3
        assert fallback.primary_action['speech_enhancement_strength'] == 0.0
        assert fallback.is_reversible is True
        assert fallback.primary_action['strategy_name'] == 'minimal_intervention_monitoring'
    
    def test_complete_oral_cycle(self):
        """Test complete ORAL loop cycle."""
        # Create observation
        observation = ObservationContext(
            acoustic_scene="quiet_office",
            noise_level_db=50.0,
            speech_confidence=0.88,
            speech_presence=True,
            asr_transcript="Hello, how can I help?",
            noise_type="HVAC",
            hearing_loss_profile={"high": 20.0},
            user_preference="clarity",
            listening_intent="conversation",
            recent_actions=[],
            feedback_history=[],
            temporal_context={"time_of_day": "14:00", "day_of_week": "Tuesday"},
            device_state={"battery_percent": 90, "temperature_celsius": 24.0, "processing_load": 25}
        )
        
        user_profile = {
            "hearing_loss_profile": {"high": 20.0},
            "preference": "clarity",
            "listening_intent": "conversation"
        }
        
        # Execute ORAL cycle
        decision, safety_check = self.engine.decide_strategy(observation, user_profile, [])
        
        # Verify decision structure
        assert decision.primary_action is not None
        assert decision.confidence >= 0.0
        assert decision.confidence <= 1.0
        assert len(decision.rationale) >= 20
        assert decision.is_reversible is True
        assert decision.duration_seconds >= 10
        
        # Verify safety check
        if safety_check.is_safe:
            assert len(safety_check.violations) == 0
        
        # Verify all parameters within bounds
        strategy = decision.primary_action
        assert strategy['noise_suppression_strength'] >= 0.0
        assert strategy['noise_suppression_strength'] <= 0.95
        assert strategy['speech_enhancement_strength'] >= 0.0
        assert strategy['speech_enhancement_strength'] <= 0.9
        assert strategy['compression_ratio'] >= 1.0
        assert strategy['compression_ratio'] <= 8.0
        
        # Integrate feedback
        feedback_outcome = {
            'asr_confidence_change': 0.05,
            'user_override': False,
            'satisfaction': 90
        }
        self.engine.integrate_feedback(feedback_outcome, user_satisfaction=90)
        
        # Should have recorded the decision
        assert len(self.engine.decision_history) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
