# Decision Loop Architecture: Observe → Reason → Act → Learn

## Overview

The hearing aid system operates through a continuous, incremental decision loop that ensures safe, explainable, and user-responsive audio processing. The LLM acts as an agentic decision layer that bridges high-level intent and low-level signal processing.

## 1. OBSERVE Phase

The system gathers contextual information about the acoustic environment and user state without ever receiving raw audio waveforms.

### Input Data

#### Acoustic Context
- **Scene Labels**: Restaurant, traffic, crowd, quiet, office, outdoor
- **Noise Characteristics**: Type (white, pink, environmental), estimated level (dB)
- **Speech Presence**: Binary (speech present/absent), confidence (0-100%)
- **Speech Dominance**: Percentage of audio that is speech vs noise

#### Speech Information
- **ASR Transcripts**: Best-effort automatic speech recognition output
- **ASR Confidence**: Per-word confidence scores (0-100%)
- **Pitch & Prosody**: Estimated speaker characteristics (not waveform data)
- **Speech Rate**: Words per minute estimation

#### System State
- **Recent Actions**: Last N decisions and their parameters
- **Feedback History**: User satisfaction, manual overrides, duration of actions
- **Temporal Context**: Time of day, typical environment for this time
- **Device State**: Battery level, processing load, thermal state

#### User Profile
- **Hearing Loss Profile**: Audiometric thresholds per frequency band
- **Preferences**: Priority (clarity vs comfort vs naturalness)
- **Listening Goals**: Conversation focus, environmental awareness, specific activity
- **Adaptation History**: How user has responded to similar situations

### Key Constraint

**No raw audio waveforms** are provided to the reasoning layer. All information is abstracted to high-level descriptors that preserve privacy and reduce cognitive load on the decision mechanism.

---

## 2. REASON Phase

The LLM analyzes the observed context to understand the situation and develop a strategy recommendation.

### Reasoning Tasks

#### 2.1 Situation Assessment

The LLM must infer:
- **Listening Intent**: What is the user trying to hear?
  - Example: "Conversation in restaurant" (focus on speech)
  - Example: "Walking outdoors" (balanced speech + environment awareness)
  - Example: "Meeting with background noise" (extract speech reliably)

- **Current Intelligibility**: Is speech currently understandable?
  - Input: ASR confidence, noise level, user feedback history
  - Assessment: "Degraded" (noise is interfering) vs "Adequate" (acceptable clarity)

- **Environmental Similarity**: How does this compare to past situations?
  - Match current scene against historical decision effectiveness
  - Identify patterns: e.g., "Restaurant at lunch" works better with strategy X

#### 2.2 Trade-off Analysis

The LLM must evaluate multi-objective constraints:
- **Clarity**: Is speech intelligible enough for the listening intent?
- **Comfort**: Will processing introduce artifacts, fatigue, or unnaturalness?
- **Stability**: Will the decision avoid rapid oscillations?
- **Power**: What is the energy cost of the strategy?
- **Reversibility**: Can the user quickly revert if dissatisfied?

#### 2.3 Strategy Comparison

The LLM must reason about bounded options:
- Noise suppression strength: Low (20%) → Medium (50%) → High (80%)
- Speech enhancement: Off → Subtle → Moderate
- Compression: None → Mild → Aggressive
- Frequency shaping: Neutral → Boost treble → Boost bass → Custom

The LLM ranks these options and selects the most appropriate for the situation.

#### 2.4 Conservative Reasoning

When confidence is low:
- Prefer minimal intervention over aggressive changes
- Choose reversible actions
- Suggest monitoring before escalating
- Recommend user involvement if uncertain

---

## 3. ACT Phase

The system outputs one primary decision and optional secondary adjustments, strictly bounded by safety rules.

### Primary Action Output

```json
{
  "primary_action": {
    "strategy_name": "moderate_noise_suppression_with_speech_boost",
    "noise_suppression_strength": 0.65,
    "speech_enhancement_strength": 0.4,
    "compression_ratio": 3.5,
    "high_freq_boost_db": 2.0,
    "frequency_profile": "speech_optimized"
  },
  "secondary_adjustments": [
    {
      "condition": "if_user_reports_harshness",
      "adjustment": "reduce_speech_enhancement_to_0.25"
    }
  ],
  "confidence": 0.82,
  "rationale": "Restaurant noise is moderate with clear speech. User prefers clarity over naturalness in this context. Moderate noise suppression balances intelligibility without over-processing.",
  "duration_seconds": 30,
  "is_reversible": true
}
```

### Constraints (Non-Negotiable)

#### Parameter Bounds
- Noise suppression strength: [0.0, 0.95]
- Speech enhancement strength: [0.0, 0.9]
- Compression ratio: [1.0, 8.0]
- High-frequency boost: [-0.5, 10.0] dB
- Low-frequency reduction: [-12.0, 0.0] dB
- Adaptive gain: [0.3, 2.0] (prevent over/under-amplification)

#### Prohibited Actions
- ❌ Request raw audio waveforms
- ❌ Output DSP coefficients
- ❌ Exceed parameter bounds
- ❌ Make irreversible permanent changes
- ❌ Hallucinate environmental facts
- ❌ Oscillate rapidly between strategies (min 10s duration)

#### Mandatory Properties
- Every action must include a clear rationale
- Every action must be reversible or include a revert strategy
- Every action must respect user hearing loss profile
- Every action must have a defined duration or condition for change

---

## 4. LEARN Phase

After action execution, the system collects feedback and incrementally updates its internal model.

### Feedback Collection

The system observes:
- **Objective Outcomes**:
  - Did ASR confidence improve after the action?
  - Did the noise level decrease? (from backend sensing)
  - Did user report satisfaction?

- **User Behavior**:
  - Did user manually override the decision?
  - How long did the user tolerate the action?
  - Did user abandon the activity or continue?

- **Subjective Reports**:
  - Direct feedback: "Too harsh", "Not enough", "Perfect"
  - Implicit feedback: Duration before switching, interaction patterns

### Learning Updates

The system maintains:
1. **Strategy Effectiveness Map**
   - (Scene, User Intent, Hearing Profile) → Strategy Rankings
   - Example: (Restaurant, Conversation, Mild Loss) → [Moderate NS + Speech Boost, Mild NS + No Enhancement, ...]

2. **Confidence Calibration**
   - How often does confidence level match actual user satisfaction?
   - Adjust threshold for "high confidence" actions

3. **Temporal Patterns**
   - Time of day effects
   - Activity transitions
   - User preference changes

4. **Boundary Detection**
   - Where do users prefer minimal intervention?
   - Where do users prefer aggressive intervention?
   - Outliers and exceptions

### Learning Constraints

- Learning is **incremental**: Each update is a small adjustment, not a replacement
- Learning is **reversible**: Can revert to previous strategy rankings if needed
- Learning is **explainable**: Each update includes a rationale
- Learning is **transparent**: User can inspect strategy rankings
- Learning is **bounded**: No single session dominates the model

---

## Example: Complete Decision Loop Cycle

### Scenario
User is in a restaurant. Background noise is ~75 dB. ASR detects speech at 60% confidence. Recent history shows user prefers clarity over naturalness in restaurants.

### Observe
```json
{
  "acoustic_scene": "restaurant",
  "noise_level_db": 75,
  "speech_confidence": 0.60,
  "speech_presence": true,
  "asr_transcript": "Can you pass the... [unclear] ...please",
  "recent_actions": ["moderate_ns_with_speech_boost for 45 seconds"],
  "user_preference": "clarity_priority",
  "historical_effectiveness": {
    "moderate_ns_with_speech_boost": 0.78,
    "aggressive_ns": 0.65,
    "light_ns": 0.42
  }
}
```

### Reason
1. **Situation**: Restaurant noise with degraded speech (60% confidence below typical 85%+)
2. **Intent**: User is having a conversation; clarity is critical
3. **History**: Moderate NS has worked well (78% satisfaction)
4. **Trade-off**: Aggressive NS might help (clearer speech) but risks harshness (discomfort)
5. **Decision**: Increase from recent moderate NS to slightly stronger, watch for fatigue

### Act
```json
{
  "primary_action": {
    "strategy_name": "elevated_noise_suppression_with_speech_boost",
    "noise_suppression_strength": 0.75,
    "speech_enhancement_strength": 0.5,
    "compression_ratio": 4.0,
    "high_freq_boost_db": 3.0
  },
  "confidence": 0.85,
  "rationale": "Speech confidence is below typical. Historical data shows moderate NS is effective in restaurants. Slight increase should improve clarity while remaining within user tolerance.",
  "duration_seconds": 30,
  "secondary_adjustments": [
    {
      "condition": "if_user_manual_override",
      "adjustment": "revert_to_moderate_ns_with_speech_boost"
    }
  ]
}
```

### Learn
After 30 seconds:
- User did NOT override (satisfaction signal)
- ASR confidence rose to 85% (objective improvement)
- User reported subjective satisfaction: "Much better"

Update:
```json
{
  "event": "successful_action",
  "scenario": "restaurant_degraded_speech",
  "action_taken": "elevated_ns_with_speech_boost_0.75_0.5",
  "outcome": "positive",
  "update": "Increase confidence ranking of (elevated_ns_with_speech_boost) in restaurant context by +0.05"
}
```

---

## Safety & Compliance Rules (Strict)

### Absolute Prohibitions
1. **No Raw Waveforms**: LLM never receives or requests raw audio data
2. **No DSP Coefficients**: LLM never outputs signal processing coefficients
3. **No Out-of-Bounds**: All parameters must respect hard limits
4. **No Irreversible Changes**: Every action includes a revert strategy
5. **No Hallucination**: Decisions must be grounded in provided data
6. **No Rapid Oscillation**: Minimum 10-second duration per strategy

### Mandatory Decision Properties
- ✅ Clear, honest rationale
- ✅ Confidence level (0-100%)
- ✅ Duration or change condition
- ✅ Reversibility statement
- ✅ Respect for hearing loss profile
- ✅ Trade-off acknowledgment

### Validation Checkpoints
- Safety validator checks all parameters before execution
- Any violation blocks the action and triggers fallback (revert to last safe state)
- All violations are logged for review
- System defaults to minimal intervention if uncertain

---

## Implementation Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Audio Input Stream (No Direct Waveform Access)   │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  Feature Extractor   │
       │  (Safe Abstraction)  │
       └──────────┬───────────┘
                  │
          ┌───────▼────────┐
          │ Observation    │
          │ Context Object │
          └───────┬────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  Decision Engine     │
       │  (ORAL Loop)         │
       │  - Observe Data      │
       │  - Reason Strategy   │
       │  - Act Decision      │
       │  - Learn Feedback    │
       └──────────┬───────────┘
                  │
         ┌────────▼────────────────┐
         │  Safety Validator       │
         │  (Enforce Constraints)  │
         └────────┬─────────────────┘
                  │
         ┌────────▼──────────┐
         │ Bounded Decision  │
         │ (Safe Parameters) │
         └────────┬──────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  Audio Processing    │
       │  (Implements Action) │
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  Output Audio Stream │
       │  (Enhanced)          │
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  Feedback Collector  │
       │  (Observes Outcome)  │
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  Learning System     │
       │  (Updates Ranking)   │
       └──────────────────────┘
```

---

## Summary

The decision loop ensures that:
- **Safety**: All decisions respect hard bounds and never expose raw waveforms
- **Explainability**: Every decision includes clear reasoning
- **Adaptability**: The system learns and improves over time
- **User Control**: Users can override or reject decisions
- **Privacy**: Audio is never exposed to external systems
- **Reliability**: Conservative reasoning when uncertain

This architecture enables LLMs to act as safe, effective decision layers for hearing aids while maintaining privacy, explainability, and user autonomy.
