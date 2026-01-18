# Core Requirements: Observe-Reason-Act-Learn Decision Loop

## Overview

This document specifies the core responsibilities and strict safety rules that govern the LLM-based decision engine for hearing aids. The system must operate within the Observe-Reason-Act-Learn (ORAL) loop framework while respecting absolute safety and privacy constraints.

---

## 1. OBSERVE Phase - Gather Context Without Raw Audio

### 1.1 Input Data Categories

The decision engine receives **only abstract, high-level descriptors** of the acoustic environment. Raw audio waveforms are **never** provided.

#### Acoustic Scene Information
- **Scene Label**: Restaurant, traffic, crowd, quiet, office, outdoor, meeting, etc.
- **Noise Level**: Estimated in dB (e.g., 65 dB, 75 dB)
- **Noise Type**: White, pink, environmental, machinery, voices, traffic
- **Signal-to-Noise Ratio (SNR)**: Estimated ratio in dB

#### Speech Analysis (Never Raw Audio)
- **Speech Presence**: Binary flag (true/false)
- **Speech Dominance**: Percentage of audio that is speech vs noise (0-100%)
- **ASR Confidence**: Per-word or per-frame confidence scores (0-100%)
- **ASR Transcript**: Best-effort text (may be incomplete or noisy)
- **Speech Rate**: Estimated words per minute
- **Pitch/Prosody**: Estimated speaker characteristics (NOT waveform data)

#### User Context
- **Hearing Loss Profile**: Audiometric thresholds per frequency band (dB loss)
- **User Preferences**: Priority ordering (clarity, comfort, naturalness, power efficiency)
- **Listening Intent**: Conversation, environmental awareness, specific speaker focus
- **Activity Type**: Walking, stationary, in vehicle, eating
- **Preference Override History**: Recent user interventions

#### System State
- **Battery Level**: Percentage (0-100%)
- **Device Temperature**: Celsius
- **Processing Load**: CPU usage percentage
- **Recent Decisions**: Last N actions taken (strategy name and parameters)
- **Temporal Context**: Time of day, day of week

#### Historical Context
- **Similar Situation Outcomes**: Effectiveness of strategies in similar past scenes
- **User Feedback History**: Satisfaction ratings, manual overrides, duration of tolerances
- **Strategy Rankings**: Effectiveness ordering for this user in this context
- **Adaptation Patterns**: How user preferences have evolved

### 1.2 Constraint: No Raw Audio Access

The following are **absolutely prohibited**:
- ❌ Raw audio samples or waveforms
- ❌ Spectrograms or frequency representations
- ❌ Sample rate, bit depth, or codec information
- ❌ Frame-by-frame signal data
- ❌ Any audio data that could be reconstructed to sound

All information must be abstracted to semantic, scene-level descriptors.

### 1.3 Uncertainty Assumption

All inputs may be:
- Incomplete or noisy (ASR may misrecognize)
- Noisy or estimated (no ground truth)
- Stale (slight delay from capture to decision)
- Contradictory (e.g., speech detected but ASR confidence low)

The reasoning phase must account for this uncertainty.

---

## 2. REASON Phase - Analyze and Recommend Strategy

### 2.1 Situation Assessment Tasks

The LLM must infer:

#### 2.1.1 Listening Intent
What is the user trying to hear?
- **Conversation Focus**: "I need to hear my conversation partner"
  - Priority: Speech clarity > environmental awareness
  - Action: Emphasize noise suppression and speech enhancement

- **Environmental Awareness**: "I need to stay aware of surroundings"
  - Priority: Balanced hearing of all sounds
  - Action: Preserve ambient cues, minimal processing

- **Specific Speaker Focus**: "Focus on one speaker in a group"
  - Priority: Isolate target speaker > other voices
  - Action: Directional processing, noise suppression

- **Activity-Specific**: "I'm trying to do X and need Y sounds"
  - Examples: Driving (safety sounds), working (background focus), relaxing (comfort)
  - Action: Context-appropriate strategy

#### 2.1.2 Intelligibility Assessment
Is speech currently understandable?

Indicators:
- ASR confidence < 70%: Possibly degraded
- SNR < 5 dB: Likely degraded
- Silence detected: May indicate speech was missed
- User feedback: Previous manual overrides in similar scenes

Decision: "Intelligibility is [Adequate / Degraded / Unknown]"

#### 2.1.3 Historical Context Comparison
How does this situation compare to past similar experiences?

Questions to ask:
- "Have I encountered this scene/user/intent combination before?"
- "What strategy was used? Was the user satisfied?"
- "What was the confidence in that past decision?"
- "Have user preferences changed since then?"

Use historical data to establish baseline expectations.

#### 2.1.4 Trade-Off Analysis
Evaluate multi-objective constraints:

**Clarity** (0-100%)
- How clear must speech be for the listening intent?
- Cost: May introduce artifacts, require more processing

**Comfort** (0-100%)
- Will processing introduce fatigue, harshness, or unnaturalness?
- Cost: May reduce intelligibility if prioritized too high

**Stability** (0-100%)
- How much can we change from the last action?
- Cost: Frequent changes → user frustration, confusion

**Power Efficiency** (0-100%)
- How much processing power can we afford?
- Cost: Battery drain if heavy processing

**Example Trade-off**:
- Restaurant with degraded speech + user prefers clarity
- Clarity: 95% (critical for conversation)
- Comfort: 70% (some harshness acceptable)
- Stability: 60% (can change from previous if needed)
- Power: 80% (battery good, can afford processing)
- → Recommend moderate-to-strong noise suppression with speech enhancement

### 2.2 Conservative Reasoning When Uncertain

**If confidence is low** (< 50%):
- Prefer minimal intervention over aggressive changes
- Choose reversible actions
- Suggest brief trial before escalating
- Recommend user involvement if possible
- Output confidence score explicitly

**Example:**
- ASR confidence is 45%, user intent is unclear
- Decision: Minimal intervention (moderate NS, no enhancement)
- Confidence: 0.42
- Rationale: "Low confidence in speech detection. Applying conservative strategy while monitoring."
- Secondary: "If user reports too much noise, escalate to aggressive NS"

### 2.3 Avoid Rapid Oscillation

**Stability Constraint:** Minimum 10 seconds per decision
- Do NOT rapidly switch between strategies (creates jarring experience)
- If considering change, verify it's stable and justified
- Check recent actions: were we just using something similar?
- If uncertainty, wait and gather more data

**Example Decision History:**
- T=0s: Moderate NS (user in restaurant)
- T=5s: User overrides to aggressive NS
- T=15s: Can consider new strategy (≥10s duration met)
- T=20s: DO NOT revert immediately to moderate NS (causes oscillation)

---

## 3. ACT Phase - Bounded, Reversible Actions

### 3.1 Primary Action Output

Every decision MUST include:

```json
{
  "strategy_name": "descriptive_strategy_name",
  "noise_suppression_strength": <0.0-0.95>,
  "speech_enhancement_strength": <0.0-0.9>,
  "compression_ratio": <1.0-8.0>,
  "high_freq_boost_db": <-0.5 to +10>,
  "low_freq_reduction_db": <-12 to 0>,
  "frequency_profile": <neutral|speech_optimized|clarity_boost|comfort_focus>,
  "confidence": <0.0-1.0>,
  "rationale": "Clear explanation of reasoning",
  "duration_seconds": <minimum 10>,
  "secondary_adjustments": [
    {
      "condition": "human_readable condition",
      "adjustment": "what to change if condition met"
    }
  ],
  "is_reversible": true
}
```

### 3.2 Parameter Constraints (Non-Negotiable)

| Parameter | Min | Max | Notes |
|-----------|-----|-----|-------|
| Noise Suppression | 0.0 | 0.95 | Prevent over-suppression artifacts |
| Speech Enhancement | 0.0 | 0.9 | Prevent harshness above 0.9 |
| Compression Ratio | 1.0 | 8.0 | 1.0=no compression, 8.0=maximum |
| High Freq Boost | -0.5 | +10 dB | Slight attenuation to strong boost |
| Low Freq Reduction | -12 | 0 dB | 0=no reduction, -12=max reduction |
| Duration | 10 | 3600 | Minimum 10s, max 1 hour |
| Confidence | 0.0 | 1.0 | Honest assessment of certainty |

### 3.3 Mandatory Action Properties

Every action MUST include:

1. **Explicit Rationale** (minimum 20 characters)
   - Why this strategy for this situation?
   - What trade-offs were considered?
   - What constraints were respected?

2. **Confidence Level** (0.0-1.0)
   - How certain is this decision?
   - If <0.5: recommend minimal intervention
   - If <0.3: escalate to user or fallback

3. **Duration** (minimum 10 seconds)
   - How long to apply this strategy?
   - When/how to reevaluate?
   - Prevents rapid oscillation

4. **Reversibility Statement**
   - MUST be true (always include revert strategy)
   - What is the revert action?
   - Can user manually override? (yes)

5. **Secondary Adjustments** (optional)
   - Conditional modifications
   - "If user reports harshness, reduce speech enhancement"
   - "If noise increases, escalate to aggressive NS"

### 3.4 Prohibited Actions

The system MUST NEVER:

1. ❌ **Request Raw Audio**
   - "I need the waveform samples"
   - "Can you provide 1-second audio buffers?"
   - "Send me the FFT of the signal"

2. ❌ **Output DSP Coefficients**
   - "Set filter coefficients to [0.1, 0.2, 0.3, ...]"
   - "Use this FIR response: ..."
   - "Apply IIR filter with poles at ..."

3. ❌ **Exceed Parameter Bounds**
   - Noise suppression > 0.95: VIOLATION
   - Negative compression ratio: VIOLATION
   - Frequency boost > 10 dB: VIOLATION

4. ❌ **Make Irreversible Changes**
   - "Disable noise suppression permanently"
   - "Lock user to this strategy forever"
   - All decisions must include revert capability

5. ❌ **Hallucinate Facts**
   - "User prefers X" (without evidence)
   - "Restaurant noise at 100 dB" (without data)
   - "This technique will definitely work" (without basis)

6. ❌ **Cause Rapid Oscillation**
   - Strategy changes every 2 seconds: VIOLATION
   - Minimum 10-second stability required

### 3.5 Example Good Decision

```json
{
  "strategy_name": "balanced_conversation_focus",
  "noise_suppression_strength": 0.65,
  "speech_enhancement_strength": 0.4,
  "compression_ratio": 3.5,
  "high_freq_boost_db": 2.0,
  "low_freq_reduction_db": -3.0,
  "frequency_profile": "speech_optimized",
  "confidence": 0.82,
  "rationale": "Restaurant environment with moderate noise (~75 dB) and clear speech detected. User prefers clarity in conversation scenarios. Balanced strategy: moderate noise suppression prevents background interference without over-processing, mild speech enhancement aids clarity without artifacts. Compression helps with dynamic range. Frequency boost targets speech intelligibility.",
  "duration_seconds": 30,
  "secondary_adjustments": [
    {
      "condition": "if_user_reports_harshness_or_unnatural_sound",
      "adjustment": "reduce_speech_enhancement_to_0.2"
    },
    {
      "condition": "if_noise_increases_above_85_dB",
      "adjustment": "escalate_to_noise_suppression_0.85"
    }
  ],
  "is_reversible": true
}
```

### 3.6 Example Poor Decision (Violations)

```json
{
  "strategy_name": "aggressive_processing",
  "noise_suppression_strength": 1.2,  // ❌ VIOLATION: > 0.95
  "speech_enhancement_strength": 0.95, // ⚠️ WARNING: > 0.9
  "compression_ratio": 12.0,  // ❌ VIOLATION: > 8.0
  "high_freq_boost_db": 15.0,  // ❌ VIOLATION: > 10.0
  "low_freq_reduction_db": -15.0,  // ❌ VIOLATION: < -12.0
  "frequency_profile": "unknown",  // ❌ VIOLATION: not in allowed set
  "confidence": 0.95,  // ⚠️ MISMATCH: too high given poor reasoning
  "rationale": "I think this will be better",  // ❌ VIOLATION: insufficient explanation
  "duration_seconds": 5,  // ❌ VIOLATION: < 10 seconds
  "secondary_adjustments": [],
  "is_reversible": false  // ❌ CRITICAL VIOLATION: must be true
}
```

---

## 4. LEARN Phase - Incremental, Explainable Feedback Integration

### 4.1 Feedback Collection

After action execution, observe outcomes:

#### Objective Metrics
- **ASR Confidence Change**: Did it improve/decline/stay same?
- **Noise Level Change**: Did background noise measurement change?
- **Processing Load**: Did the strategy consume expected CPU?
- **Duration of Action**: How long did user tolerate it?

#### User Behavior
- **Manual Override**: Did user intervene?
- **Override Direction**: Increased aggressiveness? Decreased?
- **Time Until Override**: After how long (seconds)?
- **Session Continuation**: Did user abandon the activity?
- **Revisit Pattern**: Did user return to this activity?

#### Subjective Feedback
- **Direct Report**: "Too harsh", "Not enough", "Perfect", "Too quiet"
- **Implicit Signal**: Duration of use, frequency of use
- **Derived Satisfaction**: Can infer from override patterns

### 4.2 Learning Updates

Update internal knowledge:

```
Scenario: (Scene, User Intent, Hearing Profile, Time of Day)
Strategy: [Effective ranking]
Outcome: (Success / Partial Success / Failure)
Update: ±Δ to strategy ranking

Example:
Scene: Restaurant at lunch
User Intent: Conversation focus
Hearing Profile: Mild high-frequency loss
Time: 12:00-14:00

Strategy: moderate_noise_suppression_with_speech_boost
Outcome: User satisfaction 85%, no override, continued for 45 min
Update: Increase ranking by +0.05

Strategy: aggressive_noise_suppression
Outcome: User overrode after 3 minutes
Update: Decrease ranking by -0.1 for this scenario
```

### 4.3 Learning Constraints

Learning MUST be:

1. **Incremental**
   - Each update is a small adjustment (not replacement)
   - Single session doesn't dominate the model
   - Historical data provides stability

2. **Reversible**
   - Can revert to previous rankings if needed
   - No permanent changes to user profile
   - Can reset if user reports discomfort

3. **Explainable**
   - Every update includes reasoning
   - Can show why a strategy was upgraded/downgraded
   - User can inspect decision history

4. **Transparent**
   - User can request strategy rankings
   - Can see how their feedback affects decisions
   - Can override learning if desired

5. **Bounded**
   - No strategy can dominate completely (at least 3 alternatives always ranked)
   - New situations default to conservative (low confidence)
   - Extreme changes require user confirmation

### 4.4 Adaptation Examples

**Positive Adaptation:**
- User in restaurant scenario consistently chooses moderate NS
- System learns: For this user + scene + intent → moderate NS is preferred
- Increases ranking of moderate NS for similar future situations
- Reduces trial-and-error on next visit

**Negative Adaptation:**
- User in quiet office keeps overriding aggressive strategies
- System learns: For this user + scene + intent → aggressive NS creates discomfort
- Reduces ranking of aggressive strategies
- Suggests gentler alternatives instead

**Edge Case Handling:**
- New activity or hearing changes: Reset confidence to 0.5
- Conflicting feedback from user: Flag for review, don't adapt
- Rare scenarios: Keep low confidence to avoid overfitting

---

## 5. Safety & Compliance Rules (Strict)

### 5.1 Absolute Prohibitions

These are **NEVER permitted**:

1. **No Raw Waveforms**
   - System never receives raw audio
   - LLM never requests raw audio
   - LLM never generates waveform data

2. **No DSP Coefficients**
   - LLM never outputs filter coefficients
   - LLM never specifies FIR/IIR parameters
   - All processing specified via abstract parameters

3. **No Out-of-Bounds Parameters**
   - Every parameter checked against bounds
   - Violations trigger safety alert and fallback
   - No "close enough" - exact bounds enforced

4. **No Irreversible Changes**
   - Every decision includes revert capability
   - No permanent modifications to hearing profile
   - User can always manually override

5. **No Hallucinations**
   - Every statement grounded in provided data
   - No invented facts about user or environment
   - Low confidence when data is limited

6. **No Rapid Oscillation**
   - Minimum 10 seconds per strategy
   - Prevents jarring, confusing changes
   - Stability prioritized when uncertain

### 5.2 Validation Checkpoints

| Checkpoint | Checks | Action if Fail |
|------------|--------|---|
| Pre-Execution | Parameter bounds, reversibility, rationale | Block decision, use fallback |
| During Execution | Duration respected, no waveform requests | Revert to safe baseline |
| Post-Execution | Feedback integration, learning bounds | Rollback update |
| Audit | Violation count, pattern detection | Log and alert |

### 5.3 Fallback Safety Strategy

If any validation fails:

```json
{
  "strategy_name": "conservative_minimal_intervention",
  "noise_suppression_strength": 0.3,
  "speech_enhancement_strength": 0.0,
  "compression_ratio": 1.5,
  "high_freq_boost_db": 0.0,
  "low_freq_reduction_db": 0.0,
  "frequency_profile": "neutral",
  "confidence": 0.6,
  "rationale": "Safety check indicated violation. Reverting to conservative minimal intervention while issue is investigated.",
  "duration_seconds": 10,
  "secondary_adjustments": [],
  "is_reversible": true
}
```

This ensures the system always has a safe, benign action to fall back to.

---

## Summary: The ORAL Loop in Practice

```
┌─ OBSERVE ──────────────────┐
│ Gather scene context        │
│ (NO raw audio)              │
└──────┬──────────────────────┘
       │
       ▼
┌─ REASON ────────────────────┐
│ Analyze situation           │
│ Assess intelligibility      │
│ Evaluate trade-offs         │
│ Prefer conservative if      │
│ uncertain                   │
└──────┬──────────────────────┘
       │
       ▼
┌─ ACT ──────────────────────┐
│ Generate bounded decision   │
│ Validate all parameters     │
│ Check safety constraints    │
│ Output with rationale       │
└──────┬──────────────────────┘
       │
       ▼
┌─ LEARN ────────────────────┐
│ Collect feedback (objective │
│ + subjective)              │
│ Update strategy rankings   │
│ Incremental + reversible   │
└────────────────────────────┘
       │
       └─→ Return to OBSERVE for next decision
```

Every cycle respects user privacy, maintains safety, and aims to improve hearing aid effectiveness while building user trust through transparency and control.
