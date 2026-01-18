"""LLM decision engine for hearing aid control - Observe-Reason-Act-Learn loop."""

import json
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from src.audio.features import AudioFeatureSet
from .prompts import PromptBuilder
from .safety import SafetyValidator, SafetyCheck


logger = logging.getLogger(__name__)


@dataclass
class ObservationContext:
    """Encapsulates all observed context without raw audio."""
    
    acoustic_scene: str
    noise_level_db: float
    speech_confidence: float
    speech_presence: bool
    asr_transcript: Optional[str]
    noise_type: str
    hearing_loss_profile: Dict
    user_preference: str
    listening_intent: str
    recent_actions: List[Dict]
    feedback_history: List[Dict]
    temporal_context: Dict
    device_state: Dict


@dataclass
class Decision:
    """Structured decision output from reasoning phase."""
    
    primary_action: Dict
    confidence: float
    rationale: str
    duration_seconds: int
    secondary_adjustments: List[Dict]
    is_reversible: bool
    timestamp: str


class DecisionEngine:
    """
    LLM-based decision engine for hearing aid audio processing.
    
    Implements Observe-Reason-Act-Learn (ORAL) loop for safe, agentic control.
    Makes decisions without direct access to waveforms, maintaining safety
    and user privacy through abstraction layers.
    """
    
    # Minimum decision duration to prevent rapid oscillation
    MIN_ACTION_DURATION_SECONDS = 10
    
    def __init__(
        self,
        model_name: str = "gpt-4",
        api_key: Optional[str] = None,
        enable_safety: bool = True
    ):
        """
        Initialize decision engine.
        
        Args:
            model_name: LLM model to use
            api_key: API key for LLM service
            enable_safety: Whether to enforce safety constraints
        """
        self.model_name = model_name
        self.api_key = api_key
        self.enable_safety = enable_safety
        self.prompt_builder = PromptBuilder()
        self.safety_validator = SafetyValidator()
        self.decision_history: List[Decision] = []
        self.strategy_effectiveness_map: Dict = {}
        self.last_decision_time: Optional[datetime] = None
    
    def decide_strategy(
        self,
        features: AudioFeatureSet,
        user_profile: Dict,
        recent_feedback: Optional[List[Dict]] = None
    ) -> Tuple[Decision, SafetyCheck]:
        """
        Execute full Observe-Reason-Act-Learn cycle for audio processing strategy.
        
        Follows a strict loop:
        1. OBSERVE: Gather all context (no raw waveforms)
        2. REASON: Analyze situation and trade-offs
        3. ACT: Generate bounded, reversible decision
        4. LEARN: Prepare for feedback integration
        
        Args:
            features: Extracted audio features (high-level descriptors only)
            user_profile: User preferences and hearing profile
            recent_feedback: Recent outcome feedback for learning
        
        Returns:
            Tuple of (Decision object, SafetyCheck validation result)
        """
        # Phase 1: OBSERVE - Gather context without raw audio
        observation = self._observe(features, user_profile, recent_feedback or [])
        
        # Phase 2: REASON - Analyze and recommend strategy
        decision = self._reason(observation, user_profile)
        
        # Phase 3: ACT - Validate and prepare for execution
        safety_check = self.safety_validator.validate_strategy(decision.primary_action)
        
        if not safety_check.is_safe:
            logger.error(f"Safety violations detected: {safety_check.violations}")
            decision = self._fallback_conservative_decision(observation)
            safety_check = self.safety_validator.validate_strategy(decision.primary_action)
        
        # Record for learning
        self.decision_history.append(decision)
        self.last_decision_time = datetime.now()
        
        # Phase 4: LEARN - Ready for feedback integration
        logger.info(f"Decision made: {decision.primary_action['strategy_name']} "
                    f"(confidence: {decision.confidence:.2f})")
        
        return decision, safety_check
    
    def _observe(
        self,
        features: AudioFeatureSet,
        user_profile: Dict,
        feedback_history: List[Dict]
    ) -> ObservationContext:
        """
        OBSERVE Phase: Gather all relevant context without raw audio.
        
        Assumes all inputs may be uncertain or noisy.
        Never requests or processes raw waveforms.
        """
        logger.debug("OBSERVE: Gathering context...")
        
        # Extract safe, high-level features
        acoustic_scene = features.get('acoustic_scene', 'unknown')
        noise_level = features.get('noise_level_db', 60.0)
        speech_confidence = features.get('speech_confidence', 0.5)
        speech_present = features.get('speech_present', False)
        asr_transcript = features.get('asr_transcript', None)
        noise_type = features.get('noise_type', 'unknown')
        
        # Gather user context
        hearing_loss_profile = user_profile.get('hearing_loss_profile', {})
        user_preference = user_profile.get('preference', 'balanced')
        listening_intent = user_profile.get('listening_intent', 'conversation')
        
        # Temporal context
        temporal_context = {
            'time_of_day': datetime.now().strftime('%H:%M'),
            'day_of_week': datetime.now().strftime('%A')
        }
        
        # Device state (not waveform data)
        device_state = {
            'battery_percent': features.get('battery_level', 100),
            'temperature_celsius': features.get('device_temp', 25.0),
            'processing_load': features.get('cpu_usage', 30)
        }
        
        # Recent actions for stability checking
        recent_actions = self.decision_history[-5:] if self.decision_history else []
        
        observation = ObservationContext(
            acoustic_scene=acoustic_scene,
            noise_level_db=noise_level,
            speech_confidence=speech_confidence,
            speech_presence=speech_present,
            asr_transcript=asr_transcript,
            noise_type=noise_type,
            hearing_loss_profile=hearing_loss_profile,
            user_preference=user_preference,
            listening_intent=listening_intent,
            recent_actions=[asdict(a) if isinstance(a, Decision) else a for a in recent_actions],
            feedback_history=feedback_history,
            temporal_context=temporal_context,
            device_state=device_state
        )
        
        logger.debug(f"  Scene: {acoustic_scene}, Noise: {noise_level:.1f}dB, "
                    f"Speech: {speech_confidence:.0%}, Intent: {listening_intent}")
        
        return observation
    
    def _reason(
        self,
        observation: ObservationContext,
        user_profile: Dict
    ) -> Decision:
        """
        REASON Phase: Analyze situation and generate strategy recommendation.
        
        Evaluates trade-offs between clarity, comfort, stability, and power.
        Prefers conservative actions when uncertain.
        """
        logger.debug("REASON: Analyzing situation...")
        
        # Build reasoning prompt
        prompt = self.prompt_builder.build_decision_prompt(observation, user_profile)
        
        # Get LLM reasoning (mock for now, would call actual LLM)
        reasoning_output = self._call_llm_reasoning(prompt)
        
        # Parse strategy recommendation from LLM
        strategy_dict = self._parse_strategy_recommendation(reasoning_output)
        
        # Assess confidence
        confidence = self._assess_confidence(observation, strategy_dict)
        
        # Generate decision object
        decision = Decision(
            primary_action=strategy_dict,
            confidence=confidence,
            rationale=reasoning_output.get('rationale', 'Strategy selected based on context'),
            duration_seconds=max(self.MIN_ACTION_DURATION_SECONDS, 
                               reasoning_output.get('duration_seconds', 30)),
            secondary_adjustments=reasoning_output.get('secondary_adjustments', []),
            is_reversible=True,
            timestamp=datetime.now().isoformat()
        )
        
        logger.debug(f"  Strategy: {strategy_dict['strategy_name']}, "
                    f"Confidence: {confidence:.0%}")
        
        return decision
    
    def _call_llm_reasoning(self, prompt: str) -> Dict:
        """
        Call LLM for reasoning (stub - implement with actual API).
        
        Must never expose raw waveforms to external system.
        Must validate all outputs against safety constraints.
        """
        # TODO: Integrate with actual LLM API (OpenAI, local model, etc.)
        # For now, return deterministic strategy based on prompt analysis
        
        logger.debug("Calling LLM reasoning module...")
        
        # Mock implementation - replace with actual LLM call
        return {
            'strategy_name': 'moderate_noise_suppression_with_speech_boost',
            'noise_suppression_strength': 0.65,
            'speech_enhancement_strength': 0.4,
            'compression_ratio': 3.5,
            'high_freq_boost_db': 2.0,
            'frequency_profile': 'speech_optimized',
            'rationale': 'Moderate noise with clear user preference for clarity',
            'duration_seconds': 30,
            'secondary_adjustments': []
        }
    
    def _parse_strategy_recommendation(self, llm_output: Dict) -> Dict:
        """Parse and validate LLM strategy output."""
        return {
            'strategy_name': llm_output.get('strategy_name', 'neutral'),
            'noise_suppression_strength': float(llm_output.get('noise_suppression_strength', 0.5)),
            'speech_enhancement_strength': float(llm_output.get('speech_enhancement_strength', 0.0)),
            'compression_ratio': float(llm_output.get('compression_ratio', 1.0)),
            'high_freq_boost_db': float(llm_output.get('high_freq_boost_db', 0.0)),
            'frequency_profile': llm_output.get('frequency_profile', 'neutral')
        }
    
    def _assess_confidence(
        self,
        observation: ObservationContext,
        strategy: Dict
    ) -> float:
        """
        Assess confidence in the recommended strategy.
        
        Considers:
        - Speech confidence score
        - Consistency with historical effectiveness
        - Recency of similar situations
        - User feedback alignment
        """
        base_confidence = observation.speech_confidence
        
        # Adjust for clarity when intent requires it
        if observation.listening_intent in ['conversation', 'speech_recovery']:
            base_confidence = min(1.0, base_confidence + 0.1)
        
        # Reduce confidence for uncertain scenes
        if observation.acoustic_scene == 'unknown':
            base_confidence = max(0.4, base_confidence - 0.2)
        
        return min(1.0, max(0.3, base_confidence))
    
    def _fallback_conservative_decision(self, observation: ObservationContext) -> Decision:
        """
        Return minimal intervention strategy if safety check fails.
        
        Ensures system always has a safe fallback.
        """
        logger.warning("Fallback: Using conservative minimal intervention strategy")
        
        return Decision(
            primary_action={
                'strategy_name': 'minimal_intervention_monitoring',
                'noise_suppression_strength': 0.3,
                'speech_enhancement_strength': 0.0,
                'compression_ratio': 1.0,
                'high_freq_boost_db': 0.0,
                'frequency_profile': 'neutral'
            },
            confidence=0.6,
            rationale='Safety check failed. Using minimal intervention while monitoring.',
            duration_seconds=self.MIN_ACTION_DURATION_SECONDS,
            secondary_adjustments=[
                {
                    'condition': 'if_safety_cleared',
                    'adjustment': 'return_to_previous_strategy'
                }
            ],
            is_reversible=True,
            timestamp=datetime.now().isoformat()
        )
    
    def integrate_feedback(
        self,
        outcome: Dict,
        user_satisfaction: Optional[float] = None
    ) -> None:
        """
        LEARN Phase: Integrate feedback to improve future decisions.
        
        Args:
            outcome: Objective metrics (ASR confidence change, noise level, etc.)
            user_satisfaction: Subjective feedback (0-100 scale)
        """
        logger.debug("LEARN: Integrating feedback...")
        
        if not self.decision_history:
            return
        
        last_decision = self.decision_history[-1]
        
        # Update strategy effectiveness
        strategy_name = last_decision.primary_action['strategy_name']
        effectiveness_signal = self._compute_effectiveness(outcome, user_satisfaction)
        
        self._update_strategy_rankings(strategy_name, effectiveness_signal)
        
        logger.info(f"Learning: {strategy_name} effectiveness = {effectiveness_signal:.2f}")
    
    def _compute_effectiveness(
        self,
        outcome: Dict,
        user_satisfaction: Optional[float] = None
    ) -> float:
        """
        Compute effectiveness signal from objective and subjective feedback.
        
        Range: -1.0 (harmful) to 1.0 (highly beneficial)
        """
        effectiveness = 0.5  # Neutral baseline
        
        # Objective improvement
        asr_confidence_change = outcome.get('asr_confidence_change', 0)
        effectiveness += asr_confidence_change * 0.5
        
        # Subjective satisfaction
        if user_satisfaction is not None:
            satisfaction_normalized = (user_satisfaction - 50) / 50  # Convert 0-100 to -1 to 1
            effectiveness += satisfaction_normalized * 0.3
        
        # User override penalty
        if outcome.get('user_override', False):
            effectiveness -= 0.3
        
        return max(-1.0, min(1.0, effectiveness))
    
    def _update_strategy_rankings(self, strategy_name: str, effectiveness: float) -> None:
        """
        Incrementally update internal rankings (placeholder for learning).
        
        Updates are incremental and reversible.
        """
        # TODO: Implement persistent learning mechanism
        logger.debug(f"Strategy {strategy_name} ranking adjustment: {effectiveness:+.2f}")
    
    def decide_strategy(
        self,
        features: AudioFeatureSet,
        user_profile: Dict
    ) -> Dict:
        """
        Decide on audio processing strategy based on audio features.
        
        Args:
            features: Extracted audio features
            user_profile: User preferences and hearing profile
        
        Returns:
            Processing strategy as dictionary
        """
        # Build prompt
        prompt = self.prompt_builder.build_audio_context_prompt(features, user_profile)
        
        # Get LLM decision (mock for now)
        decision = self._get_llm_decision(prompt)
        
        # Validate safety
        if self.enable_safety:
            safety_check = self.safety_validator.validate_strategy(decision)
            if not safety_check.is_safe:
                logger.warning(f"Safety violations detected: {safety_check.violations}")
                decision = self.safety_validator.apply_safety_bounds(decision)
            
            if safety_check.warnings:
                logger.info(f"Safety warnings: {safety_check.warnings}")
        
        # Record decision
        self._record_decision(features, decision, user_profile)
        
        return decision
    
    def refine_strategy(
        self,
        features: AudioFeatureSet,
        user_profile: Dict,
        user_feedback: str,
        previous_strategy: Dict
    ) -> Dict:
        """
        Refine strategy based on user feedback.
        
        Args:
            features: Current audio features
            user_profile: User preferences
            user_feedback: User's feedback on previous strategy
            previous_strategy: Strategy that was applied
        
        Returns:
            Refined processing strategy
        """
        # Build feedback prompt
        prompt = self.prompt_builder.build_feedback_prompt(
            features,
            user_profile,
            user_feedback,
            previous_strategy
        )
        
        # Get refined decision
        decision = self._get_llm_decision(prompt)
        
        # Validate safety
        if self.enable_safety:
            safety_check = self.safety_validator.validate_strategy(decision)
            if not safety_check.is_safe:
                logger.warning(f"Safety violations in refined strategy: {safety_check.violations}")
                decision = self.safety_validator.apply_safety_bounds(decision)
        
        # Record decision
        self._record_decision(features, decision, user_profile, user_feedback)
        
        return decision
    
    def _get_llm_decision(self, prompt: str) -> Dict:
        """
        Get decision from LLM.
        
        In production, this would call an actual LLM API.
        For now, returns a mock decision.
        
        Args:
            prompt: Prompt for LLM
        
        Returns:
            Decision as dictionary
        """
        # TODO: Implement actual LLM API call
        # This is a mock implementation
        
        mock_decision = {
            "noise_suppression_strength": 0.6,
            "speech_enhancement_level": 0.5,
            "dynamic_range_compression_ratio": 3.0,
            "high_frequency_boost": 2.0,
            "low_frequency_reduction": -3.0,
            "adaptive_gain": 1.0,
            "noise_gate_threshold": -40.0,
            "rationale": "Moderate processing for typical office environment with some background noise",
            "confidence": 0.85
        }
        
        return mock_decision
    
    def _record_decision(
        self,
        features: AudioFeatureSet,
        decision: Dict,
        user_profile: Dict,
        feedback: Optional[str] = None
    ):
        """Record decision in history for analysis."""
        record = {
            "timestamp": features.timestamp,
            "audio_context": features.to_llm_context(),
            "noise_level": features.noise_level_db,
            "decision": decision,
            "user_profile": user_profile,
            "feedback": feedback
        }
        self.decision_history.append(record)
        
        # Keep history size manageable
        if len(self.decision_history) > 10000:
            self.decision_history = self.decision_history[-5000:]
    
    def get_decision_summary(self) -> Dict:
        """Get summary of recent decisions."""
        if not self.decision_history:
            return {"message": "No decisions recorded yet"}
        
        recent = self.decision_history[-100:]
        
        # Calculate averages
        avg_noise_suppression = sum(d['decision'].get('noise_suppression_strength', 0) 
                                   for d in recent) / len(recent)
        avg_speech_enhancement = sum(d['decision'].get('speech_enhancement_level', 0) 
                                    for d in recent) / len(recent)
        avg_confidence = sum(d['decision'].get('confidence', 0.5) for d in recent) / len(recent)
        
        return {
            "decisions_recorded": len(self.decision_history),
            "recent_decisions": len(recent),
            "avg_noise_suppression": avg_noise_suppression,
            "avg_speech_enhancement": avg_speech_enhancement,
            "avg_confidence": avg_confidence
        }
