# Speech Separation Architecture & Integration

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Speaker Audio Input                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │  Audio Feature Extraction            │
        │  (spectral, temporal characteristics)│
        └──────────────────────────┬───────────┘
                                   │
            ┌──────────────────────┴──────────────────────┐
            │                                             │
            ▼                                             ▼
    ┌───────────────────┐                    ┌────────────────────┐
    │   LLM Decision    │                    │  Speaker           │
    │   Engine (ORAL)   │                    │  Separation (NMF)  │
    │                   │                    │                    │
    │ - Observe context │                    │ - Separate sources │
    │ - Reason tradeoffs│                    │ - Estimate N>1    │
    │ - Act strategy    │                    │   speakers        │
    │ - Learn feedback  │                    └────────┬───────────┘
    └─────────┬─────────┘                             │
              │                                       ▼
              │                          ┌──────────────────────────┐
              │                          │  User Preference Select  │
              │                          │                          │
              │                          │ - Loudest / Quietest    │
              │                          │ - Highest/Lowest Pitch  │
              │                          └────────┬─────────────────┘
              │                                   │
              └───────────────────┬───────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ Audio Processing Layer  │
                    │                         │
                    │ - Noise suppression     │
                    │ - Speech enhancement    │
                    │ - Compression           │
                    │ - Frequency shaping     │
                    └──────────────┬──────────┘
                                   │
                                   ▼
                    ┌─────────────────────────┐
                    │   Processed Audio Out   │
                    │        (single stream)  │
                    └─────────────────────────┘
```

## Component Details

### 1. Speech Separation Module (`src/audio/speech_separation.py`)

**Function: `separate_sources()`**
- Input: Mixed audio (mono waveform)
- Process:
  1. Compute STFT (1024 FFT, 512 hop length)
  2. Extract magnitude spectrogram
  3. Apply NMF (200 iterations)
  4. Generate soft masks from components
  5. Apply phase-aware reconstruction
  6. Inverse STFT to time domain
- Output: List of N separated audio streams

**Function: `select_preferred_source()`**
- Input: List of sources + preference string
- Computes metric for each source:
  - "loudest": RMS energy
  - "quietest": Negative RMS
  - "highest_pitch": Spectral centroid
  - "lowest_pitch": Negative spectral centroid
- Output: Single selected stream (numpy array)

**Function: `separate_with_preference()`**
- Convenience wrapper combining both functions
- Input: Audio + SR + preference + N sources
- Output: (chosen_stream, all_streams) tuple

### 2. Example Tool (`examples/speech_separation_demo.py`)

Command-line interface with arguments:
```bash
python examples/speech_separation_demo.py \
  --condition clean \
  --scenario office_4speaker.wav \
  --preference loudest \
  --output-dir output_separation \
  --n-sources 2
```

Outputs:
- `chosen.wav` - Selected speaker stream
- `component_1.wav` - First separated source
- `component_2.wav` - Second separated source

### 3. Multi-Speaker Dataset Integration

Dataset structure:
```
datasets/multispeaker_audio/
├── clean/
│   ├── office_2speaker.wav
│   ├── office_4speaker.wav
│   ├── cafeteria_quiet.wav
│   ├── cafeteria_crowded.wav
│   ├── lecture_small.wav
│   ├── lecture_large.wav
│   ├── phone_small.wav
│   └── phone_large.wav
├── office_noise_12db/     (8 files, same scenario names)
├── cafeteria_noise_10db/  (8 files, same scenario names)
└── traffic_noise_8db/     (8 files, same scenario names)
```

## Usage Patterns

### Pattern 1: Quick CLI Usage
```bash
# Extract loudest speaker from clean office meeting
python examples/speech_separation_demo.py \
  --condition clean \
  --scenario office_4speaker.wav \
  --preference loudest
```

### Pattern 2: Python API - Basic
```python
from src.audio.speech_separation import separate_with_preference
from scipy.io import wavfile

sr, audio = wavfile.read("audio.wav")
chosen, sources = separate_with_preference(
    audio.astype(float32) / 32767,
    sr,
    preference="loudest"
)
```

### Pattern 3: Python API - Full Pipeline
```python
from src.audio.speech_separation import separate_sources, select_preferred_source
from src.audio.multispeaker_evaluation import MultiSpeakerEvaluator

# Separate
sources = separate_sources(audio, sr, n_sources=2)

# Analyze each component
evaluator = MultiSpeakerEvaluator()
for i, src in enumerate(sources):
    metrics = evaluator.evaluate_audio(src, f"component_{i}", "clean")
    print(f"Component {i} intelligibility: {metrics.intelligibility_estimate:.2%}")

# Select one
chosen = select_preferred_source(sources, sr, preference="loudest")
```

### Pattern 4: Integration with Hearing Aid
```python
from src.hearing_aid.controller import HearingAidController
from src.audio.speech_separation import separate_with_preference

# Separate and select
chosen, _ = separate_with_preference(
    audio, sr, preference="loudest", n_sources=2
)

# Process through hearing aid
controller = HearingAidController(profile="clarity")
result = controller.process_audio(chosen, use_llm_decision=True)
processed = result["processed_audio"]
```

## Feature Relationships

```
┌─────────────────────────────────────┐
│ Multi-Speaker Audio Dataset         │
│ (32 scenarios × 4 conditions)       │
└──────────────────┬──────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   Speech Separation    LLM Decision
   Module (NMF)         Engine (ORAL)
        │                     │
        ├─ separate_sources() ├─ Feature extraction
        ├─ select_preferred_source() ├─ Acoustic context
        └─ separate_with_preference() └─ User profile
        │                     │
        └──────────────┬──────┘
                       │
                       ▼
           Audio Processor (DSP)
           - Noise suppression
           - Speech enhancement
           - Frequency shaping
                       │
                       ▼
              Hearing Aid Output
```

## Performance Characteristics

| Aspect | Value | Notes |
|--------|-------|-------|
| Separation Latency | ~1-2 sec | For 10 sec audio @16kHz |
| Output Length | Varies | ±512 samples vs input (STFT effects) |
| Noise Robustness | Moderate | NMF sensitive to heavy overlap |
| Preference Accuracy | High | RMS/centroid easily computed |
| Audio Quality | Acceptable | Artifacts possible with >2 speakers |

## Safety & Constraints

✅ Operations:
- Non-destructive (can always revert)
- Deterministic (no randomness in inference)
- Privacy-preserving (local processing only)
- Reversible (original audio retained)

⚠️ Limitations:
- No speaker identity
- No temporal tracking
- Modest separation quality
- Requires reasonably clean input

## Testing Strategy

```
Unit Tests (test_speech_separation.py)
├── test_separate_two_sine_waves()     ← Verify separation works
├── test_preference_selection_basic()  ← Verify all 4 preferences
└── test_separate_with_preference()    ← Verify end-to-end

Integration Tests (test_integration.py)
└── test_speech_separation_integration()  ← Test with real dataset

All Tests
├── 28 total passing
├── No regressions
└── Full backward compatibility
```

## Future Enhancements

### Short-term (1-2 sprints)
1. NMF parameter tuning for hearing aid scenarios
2. Confidence scoring for separation quality
3. Better error handling for edge cases
4. Performance profiling and optimization

### Medium-term (3-4 sprints)
1. Deep learning separation (Conv-TasNet, Sinkhorn)
2. Speaker diarization (who spoke when)
3. Adaptive preference selection (context-aware)
4. Real-time streaming support

### Long-term (5+ sprints)
1. Speaker identification/recognition
2. On-device model quantization
3. GPU acceleration
4. Personalized speaker models per user

## See Also

- [SPEECH_SEPARATION_GUIDE.md](SPEECH_SEPARATION_GUIDE.md) - Usage examples
- [SPEECH_SEPARATION_SUMMARY.txt](SPEECH_SEPARATION_SUMMARY.txt) - Implementation details
- [src/audio/speech_separation.py](src/audio/speech_separation.py) - Core module
- [examples/speech_separation_demo.py](examples/speech_separation_demo.py) - CLI tool
- [tests/test_speech_separation.py](tests/test_speech_separation.py) - Unit tests
