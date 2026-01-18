"""Prompt building for LLM decision making - Observe-Reason-Act-Learn loop."""

from typing import Dict, Optional


class PromptBuilder:
    """Constructs prompts for LLM decision making about audio processing."""
    
    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize prompt builder.
        
        Args:
            system_prompt: Custom system prompt (uses default if None)
        """
        self.system_prompt = system_prompt or self._get_default_system_prompt()
    
    def _get_default_system_prompt(self) -> str:
        """
        Get default system prompt - defines agent responsibilities and constraints.
        
        This prompt explicitly encodes the ORAL loop and strict safety rules.
        """
        return """You are an expert audio processing decision agent for hearing aids. Your role is to make \
intelligent, safe, and explainable decisions about audio processing strategies based on environmental context \
and user preferences.

CORE RESPONSIBILITIES (Observe-Reason-Act-Learn):

1. OBSERVE: You receive:
   - Acoustic scene labels (restaurant, traffic, crowd, quiet, etc.)
   - Speech presence and confidence scores (0-100%)
   - ASR transcripts (possibly incomplete or noisy)
   - Noise level estimates
   - User hearing profile and preferences
   - Historical decision outcomes
   
   CONSTRAINT: You never receive raw audio waveforms. All information is abstracted to high-level descriptors.

2. REASON: You must:
   - Infer the listening intent (conversation focus vs environmental awareness)
   - Assess whether speech intelligibility is currently degraded
   - Compare the situation with past similar experiences
   - Evaluate trade-offs between clarity, comfort, stability, and power efficiency
   - Avoid rapid oscillations (prefer consistency when quality is acceptable)

3. ACT: You may recommend only bounded, reversible control actions:
   - Select a noise suppression strength (0.0 to 0.95)
   - Recommend speech enhancement (0.0 to 0.9)
   - Suggest compression ratio (1.0 to 8.0)
   - Propose frequency adjustments (high boost: -0.5 to +10 dB, low reduction: -12 to 0 dB)
   
   You must always:
   - Respect all safety limits
   - Prefer conservative actions when uncertain
   - Never introduce abrupt changes (minimum 10 second duration)
   - Provide a clear rationale for each decision
   - Output one primary action and optional secondary adjustments

4. LEARN: After receiving outcome feedback, you must:
   - Evaluate whether the action improved intelligibility or comfort
   - Detect user overrides or dissatisfaction
   - Update internal preference rankings for similar contexts
   - Learning must be incremental, explainable, and reversible

STRICT SAFETY & COMPLIANCE RULES:

❌ Prohibited Actions:
   - Do NOT request raw audio waveforms or samples
   - Do NOT output DSP coefficients or waveform manipulation instructions
   - Do NOT exceed predefined parameter bounds
   - Do NOT make irreversible permanent changes
   - Do NOT hallucinate environmental facts
   - Do NOT cause rapid strategy oscillation (minimum 10 seconds per decision)

✅ Mandatory Decision Properties:
   - strategy_name: Descriptive name of the strategy
   - noise_suppression_strength: 0.0-0.95
   - speech_enhancement_strength: 0.0-0.9
   - compression_ratio: 1.0-8.0
   - high_freq_boost_db: -0.5 to +10
   - frequency_profile: One of [neutral, speech_optimized, clarity_boost, comfort_focus]
   - confidence: 0.0-1.0 (your confidence in this decision)
   - rationale: Clear explanation of why this strategy is appropriate
   - duration_seconds: How long to apply this strategy (minimum 10)
   - secondary_adjustments: Optional list of conditional adjustments
   - is_reversible: Always true

Always respond with valid JSON containing these properties. If confidence is low (<0.5), choose \
minimal intervention and explain your uncertainty. Balance clarity, comfort, naturalness, and power efficiency \
based on the listening context and user preferences."""
    
    def build_decision_prompt(self, observation, user_profile: Dict) -> str:
        """
        Build comprehensive prompt for decision making.
        
        Includes all observed context and explicit constraints.
        
        Args:
            observation: ObservationContext object with all scene data
            user_profile: User preferences and hearing profile
        
        Returns:
            Complete prompt for LLM decision reasoning
        """
        prompt = f"""
CURRENT SITUATION:

Acoustic Environment:
- Scene: {observation.acoustic_scene}
- Noise Level: {observation.noise_level_db:.1f} dB
- Noise Type: {observation.noise_type}
- Speech Present: {observation.speech_presence}
- Speech Confidence: {observation.speech_confidence:.0%}
- ASR Transcript: {observation.asr_transcript or "(No speech detected)"}

User Context:
- Hearing Loss Profile: {self._format_hearing_profile(observation.hearing_loss_profile)}
- Preference Priority: {observation.user_preference}
- Listening Intent: {observation.listening_intent}
- Device Battery: {observation.device_state.get('battery_percent', 'Unknown')}%

Recent History:
- Recent Actions: {self._format_recent_actions(observation.recent_actions)}
- User Satisfaction Feedback: {self._format_feedback_summary(observation.feedback_history)}

Temporal Context:
- Time of Day: {observation.temporal_context.get('time_of_day', 'unknown')}
- Day: {observation.temporal_context.get('day_of_week', 'unknown')}

DECISION TASK:

Analyze this situation and recommend the BEST audio processing strategy. Your decision must:

1. Consider the listening intent: Is the user trying to have a conversation, maintain environmental awareness, or focus on a specific speaker?

2. Assess intelligibility: Is speech currently understandable given noise level and ASR confidence?

3. Evaluate trade-offs:
   - CLARITY: How clear must speech be for the listening intent?
   - COMFORT: Will processing introduce artifacts or fatigue?
   - STABILITY: Will the decision maintain consistency or avoid rapid changes?
   - EFFICIENCY: What is the power cost?

4. Respect constraints:
   - All parameters must be within specified bounds
   - Never request raw audio or signal coefficients
   - Explain your reasoning clearly
   - If uncertain, prefer minimal intervention

5. Provide a complete decision JSON with:
   - Primary action (strategy name and all parameters)
   - Confidence level (0-1)
   - Clear rationale
   - Duration in seconds (minimum 10)
   - Optional secondary adjustments
   - Whether the action is reversible (always yes)

RECOMMENDATION:

Respond with a JSON object containing your complete decision. Example format:

{{
  "strategy_name": "moderate_noise_suppression_with_speech_boost",
  "noise_suppression_strength": 0.65,
  "speech_enhancement_strength": 0.4,
  "compression_ratio": 3.5,
  "high_freq_boost_db": 2.0,
  "frequency_profile": "speech_optimized",
  "confidence": 0.82,
  "rationale": "Restaurant noise is moderate with clear speech. User prefers clarity. Moderate suppression balances intelligibility without over-processing.",
  "duration_seconds": 30,
  "secondary_adjustments": [
    {{
      "condition": "if_user_reports_harshness",
      "adjustment": "reduce_speech_enhancement_to_0.25"
    }}
  ],
  "is_reversible": true
}}

Now provide your decision:
"""
        return prompt
    
    def _format_hearing_profile(self, profile: Dict) -> str:
        """Format hearing loss profile for readability."""
        if not profile:
            return "Normal hearing"
        
        descriptions = []
        for freq_range, loss_db in profile.items():
            if loss_db > 0:
                descriptions.append(f"{freq_range}: {loss_db}dB loss")
        
        return ", ".join(descriptions) if descriptions else "Normal hearing"
    
    def _format_recent_actions(self, actions: list) -> str:
        """Format recent decision history for context."""
        if not actions:
            return "None"
        
        summaries = []
        for action in actions[-3:]:  # Last 3 actions
            if isinstance(action, dict):
                strategy = action.get('primary_action', {}).get('strategy_name', 'unknown')
                summaries.append(strategy)
        
        return " → ".join(summaries) if summaries else "None"
    
    def _format_feedback_summary(self, feedback: list) -> str:
        """Summarize recent user feedback."""
        if not feedback:
            return "No recent feedback"
        
        recent = feedback[-3:] if len(feedback) > 3 else feedback
        
        positive = sum(1 for f in recent if f.get('satisfaction', 0) > 70)
        negative = sum(1 for f in recent if f.get('satisfaction', 0) < 30)
        
        if positive > negative:
            return f"Generally positive ({positive}/{len(recent)} satisfied)"
        elif negative > positive:
            return f"Generally negative ({negative}/{len(recent)} dissatisfied)"
        else:
            return "Mixed feedback"
    
    def build_audio_context_prompt(
        self,
        features,
        user_profile: Dict
    ) -> str:
        """
        Build prompt analyzing audio context.
        
        Args:
            features: Extracted audio features
            user_profile: User preferences and hearing profile
        
        Returns:
            Complete prompt for LLM
        """
        context = f"""
Analyze the following audio environment and recommend a hearing aid processing strategy.

AUDIO ENVIRONMENT:
- Scene: {features.get('acoustic_scene', 'Unknown')}
- Noise Level: {features.get('noise_level_db', 60.0):.1f} dB
- Speech Probability: {features.get('speech_confidence', 0.5)*100:.0f}%
- Sound Event: {features.get('sound_event_class', 'Unknown')}
- Silence Detected: {features.get('is_silence', False)}

USER PROFILE:
- Hearing Loss Pattern: {user_profile.get('hearing_loss_profile', 'Normal')}
- Preference: {user_profile.get('preference', 'balanced')}
- Power Mode: {user_profile.get('power_mode', 'normal')}
- Background Noise Tolerance: {user_profile.get('noise_tolerance', 'medium')}

DECISION REQUEST:
Recommend an audio processing strategy as JSON with these fields:
{{
    "noise_suppression_strength": <0.0-0.95>,
    "speech_enhancement_strength": <0.0-0.9>,
    "compression_ratio": <1.0-8.0>,
    "high_freq_boost_db": <-0.5 to +10>,
    "low_freq_reduction_db": <-12 to 0>,
    "frequency_profile": <neutral|speech_optimized|clarity_boost|comfort_focus>,
    "rationale": "<explanation of reasoning>",
    "confidence": <0.0-1.0>,
    "duration_seconds": <minimum 10>,
    "is_reversible": true
}}

Ensure your recommendations respect all safety bounds and are appropriate for hearing aid use.
Never request raw audio data or signal coefficients."""
        
        return context
    
    def build_feedback_prompt(
        self,
        features: AudioFeatureSet,
        user_profile: Dict,
        user_feedback: str,
        previous_strategy: Dict
    ) -> str:
        """
        Build prompt incorporating user feedback.
        
        Args:
            features: Extracted audio features
            user_profile: User preferences
            user_feedback: User's feedback on previous processing
            previous_strategy: Previously applied strategy
        
        Returns:
            Prompt for LLM refinement
        """
        context = f"""
Refine the hearing aid processing strategy based on user feedback.

AUDIO ENVIRONMENT:
{features.to_llm_context()}

PREVIOUS STRATEGY APPLIED:
{self._format_strategy(previous_strategy)}

USER FEEDBACK:
{user_feedback}

USER PROFILE:
- Hearing Loss Pattern: {user_profile.get('hearing_loss_pattern', 'Unknown')}
- Preference: {user_profile.get('preference', 'balanced')}

REFINEMENT REQUEST:
Based on the feedback, adjust the processing strategy. Return JSON with:
{{
    "noise_suppression_strength": <0.0-1.0>,
    "speech_enhancement_level": <0.0-1.0>,
    "dynamic_range_compression_ratio": <1.0-10.0>,
    "high_frequency_boost": <-12 to 12 dB>,
    "low_frequency_reduction": <-12 to 0 dB>,
    "adaptive_gain": <0.5-2.0>,
    "noise_gate_threshold": <-60 to -20 dB>,
    "rationale": "<explanation of adjustments>",
    "confidence": <0.0-1.0>
}}

Focus on addressing the user's concerns while maintaining hearing safety."""
        
        return context
    
    def _format_strategy(self, strategy: Dict) -> str:
        """Format strategy dictionary for display."""
        lines = []
        for key, value in strategy.items():
            if isinstance(value, float):
                lines.append(f"  {key}: {value:.2f}")
            else:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)
