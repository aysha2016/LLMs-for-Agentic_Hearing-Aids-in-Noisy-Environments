# Quick Reference: ORAL Loop Decision System

## At a Glance

The system uses **Observe → Reason → Act → Learn** (ORAL) loop to make safe, explainable hearing aid decisions.

```
OBSERVE                REASON                ACT                 LEARN
├─ Scene context      ├─ Assess intent      ├─ Generate decision ├─ Collect feedback
├─ User profile       ├─ Check clarity      ├─ Validate safety   ├─ Compute effect
├─ Speech data        ├─ Trade-off analysis ├─ Output bounds     └─ Update rankings
└─ History            └─ Use history        └─ Include rationale
```

---

## No Raw Audio Policy

### ❌ Never Receive
- Raw audio samples/waveforms
- Spectrograms or frequency matrices
- Audio file data
- Frame-by-frame signal data
- Codec information

### ✅ Only Use
- Scene labels: "restaurant", "traffic", "quiet"
- Noise level: 75 dB
- Speech confidence: 65%
- ASR transcript: "Can you pass the..."
- User profile: Hearing loss, preferences

---

## Decision Parameters (Strict Bounds)

| Parameter | Min | Max | Example |
|-----------|-----|-----|---------|
| Noise Suppression | 0.0 | **0.95** | 0.65 |
| Speech Enhancement | 0.0 | **0.9** | 0.4 |
| Compression Ratio | 1.0 | **8.0** | 3.5 |
| High Freq Boost | -0.5 | **+10** dB | +2 dB |
| Low Freq Reduction | -12 | 0 dB | -3 dB |
| Duration | 10 | 3600 s | 30 s |
| Confidence | 0.0 | 1.0 | 0.82 |

**Exceed these and safety validation FAILS.**

---

## Required Decision Fields

Every decision MUST include:

```json
{
  "strategy_name": "moderate_noise_suppression_with_speech_boost",
  "noise_suppression_strength": 0.65,      // ← Required
  "speech_enhancement_strength": 0.4,      // ← Required
  "compression_ratio": 3.5,                // ← Required
  "high_freq_boost_db": 2.0,              // ← Required
  "low_freq_reduction_db": -3.0,          // ← Required
  "frequency_profile": "speech_optimized", // ← Required
  "confidence": 0.82,                      // ← Required (0-1)
  "rationale": "Restaurant noise with...", // ← Required (≥20 chars)
  "duration_seconds": 30,                  // ← Required (≥10)
  "secondary_adjustments": [...],         // Optional
  "is_reversible": true                    // ← ALWAYS TRUE
}
```

---

## Safety Rules (Absolute)

| Rule | Violation |
|------|-----------|
| ❌ No raw audio | Request waveform = FAIL |
| ❌ No DSP coefficients | Output filter params = FAIL |
| ❌ No out-of-bounds | NS > 0.95 = FAIL |
| ❌ No irreversible | is_reversible=false = FAIL |
| ❌ No hallucinations | Invented facts = FAIL |
| ❌ No rapid switching | Duration < 10s = FAIL |

---

## Confidence Guide

| Confidence | Action | Example |
|-----------|--------|---------|
| < 0.3 | Escalate or fallback | Scene unknown, speech unclear |
| 0.3-0.5 | Conservative strategy | Low speech confidence (35%) |
| 0.5-0.7 | Standard strategy | Moderate confidence (60%) |
| 0.7-0.9 | Assertive strategy | High confidence (80%) |
| > 0.9 | Be cautious | May indicate overconfidence |

**Low confidence → minimal intervention**

---

## Trade-off Framework

When reasoning, consider:

```
┌─ CLARITY ────────────────┐
│ How clear must speech be?│
│ Trade: artifacts/harsh   │
└──────────────────────────┘
           ↓
┌─ COMFORT ────────────────┐
│ Will processing fatigue? │
│ Trade: reduced clarity   │
└──────────────────────────┘
           ↓
┌─ STABILITY ──────────────┐
│ How stable expected?     │
│ Trade: miss improvements │
└──────────────────────────┘
           ↓
┌─ POWER ──────────────────┐
│ How much CPU affordable? │
│ Trade: limited processing│
└──────────────────────────┘
```

Example: Restaurant + User wants clarity
- Clarity: 95% (critical)
- Comfort: 70% (some harshness OK)
- Stability: 60% (can change if needed)
- Power: 80% (battery good)
→ **Moderate-to-strong NS + speech boost**

---

## Fallback Strategy

If safety validation fails, use:

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
  "rationale": "Safety violation detected. Minimal intervention.",
  "duration_seconds": 10,
  "is_reversible": true
}
```

---

## Validation Checklist

**Before execution, verify:**
- [ ] No "raw audio" in rationale
- [ ] No "DSP" or "coefficient" mentioned
- [ ] Noise suppression: 0.0 ≤ x ≤ 0.95
- [ ] Speech enhancement: 0.0 ≤ x ≤ 0.9
- [ ] Compression: 1.0 ≤ x ≤ 8.0
- [ ] Confidence: 0.0 ≤ x ≤ 1.0
- [ ] Duration: x ≥ 10 seconds
- [ ] Rationale: ≥ 20 characters
- [ ] is_reversible: true
- [ ] All required fields present

---

## Learning from Feedback

**Positive (user satisfied, no override):**
```
Effectiveness = +0.5 to +1.0
→ Increase strategy ranking for this scenario
```

**Negative (user overrides, dissatisfied):**
```
Effectiveness = -0.5 to -1.0
→ Decrease strategy ranking for this scenario
```

**Updates are incremental** (not wholesale changes):
- Each update: ±0.05 to ±0.15
- Historical data provides stability
- Single session doesn't dominate

---

## Common Mistakes to Avoid

### ❌ WRONG: Requesting waveform data
```json
{
  "rationale": "I need the FFT spectrum for analysis"
  // VIOLATION: Prohibited waveform request
}
```

### ✅ CORRECT: Using scene descriptors
```json
{
  "rationale": "High noise level (75dB) with moderate speech (65% confidence). Restaurant context suggests environmental noise. Using moderate NS to prevent background interference."
  // OK: Uses provided high-level descriptors
}
```

---

### ❌ WRONG: Out-of-bounds parameter
```json
{
  "noise_suppression_strength": 1.2  // VIOLATION: > 0.95
}
```

### ✅ CORRECT: Respect bounds
```json
{
  "noise_suppression_strength": 0.85  // OK: Within 0.0-0.95 range
}
```

---

### ❌ WRONG: Rapid decision changes
```json
{
  "duration_seconds": 5  // VIOLATION: < 10 seconds (causes oscillation)
}
```

### ✅ CORRECT: Stable duration
```json
{
  "duration_seconds": 30  // OK: Allows stable evaluation
}
```

---

### ❌ WRONG: Irreversible decision
```json
{
  "rationale": "Permanently optimize for this user",
  "is_reversible": false  // CRITICAL VIOLATION
}
```

### ✅ CORRECT: Reversible with fallback
```json
{
  "rationale": "Moderate NS with speech boost. If user reports harshness, can reduce enhancement.",
  "is_reversible": true,
  "secondary_adjustments": [
    {
      "condition": "if_user_reports_harshness",
      "adjustment": "reduce_speech_enhancement_to_0.2"
    }
  ]
}
```

---

## Documentation Links

- **Full Architecture**: [docs/decision_loop.md](docs/decision_loop.md)
- **Core Requirements**: [docs/core_requirements.md](docs/core_requirements.md)
- **Implementation Status**: [IMPLEMENTATION.md](IMPLEMENTATION.md)
- **README**: [README.md](README.md)

---

## Testing

Run tests to verify safety:
```bash
pytest tests/test_oral_loop.py -v
```

Key test areas:
- ✅ Parameter bounds enforcement
- ✅ Rationale requirement
- ✅ Reversibility validation
- ✅ Waveform prohibition detection
- ✅ Duration constraints
- ✅ Complete ORAL cycle

---

## Quick Decision Template

```json
{
  "strategy_name": "[name]",
  "noise_suppression_strength": [0.0-0.95],
  "speech_enhancement_strength": [0.0-0.9],
  "compression_ratio": [1.0-8.0],
  "high_freq_boost_db": [-0.5 to +10],
  "low_freq_reduction_db": [-12 to 0],
  "frequency_profile": ["neutral"|"speech_optimized"|"clarity_boost"|"comfort_focus"],
  "confidence": [0.0-1.0],
  "rationale": "[explain reasoning, trade-offs, constraints - minimum 20 characters]",
  "duration_seconds": [≥10],
  "secondary_adjustments": [
    {
      "condition": "[human-readable condition]",
      "adjustment": "[what to change]"
    }
  ],
  "is_reversible": true
}
```

---

**Remember**: Privacy first, safety always, user agency maintained.
