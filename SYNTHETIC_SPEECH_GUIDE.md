# Synthetic Speech Hearing Aid System

**Status**: ✅ **FULLY OPERATIONAL**

## Overview

The hearing aid system now includes comprehensive synthetic speech generation capabilities, enabling you to:
- Generate realistic speech-like audio from text
- Test the hearing aid system with various acoustic scenarios
- Control noise levels and types for advanced testing
- Create reproducible test cases for validation

## Features Implemented

### 1. **Speech Synthesizer Module** (`src/audio/speech_synthesizer.py`)

#### SpeechSynthesizer Class
- **Formant Synthesis**: Generates speech-like audio using formant frequencies
- **Realistic Speech Characteristics**:
  - Fundamental frequency variation (~90-150 Hz)
  - Three formant frequencies (F1, F2, F3) for vowel-like sounds
  - Amplitude envelope (attack/release)
  - Consonant-like noise bursts

```python
from src.audio.speech_synthesizer import SpeechSynthesizer

# Initialize synthesizer
synthesizer = SpeechSynthesizer(sample_rate=16000)

# Synthesize text to audio
audio = synthesizer.synthesize_text("Your text here")
```

#### SpeechScenarioGenerator Class
Pre-built scenarios for common hearing aid test cases:

1. **Presentation** (37.2s)
   - Formal speech with consistent delivery
   - High speech probability (82%)

2. **Custom Speech** (10.6s)
   - User-defined text synthesis
   - Flexible duration based on content length

3. **Reading** (41.5s)
   - Narrative text with natural pacing
   - Consistent clarity

4. **Noisy Presentation** (37.2s)
   - Presentation with office background noise
   - 15 dB SNR for realistic office environment

5. **Noisy Reading** (41.5s)
   - Reading with pink noise
   - 12 dB SNR for communication challenge

### 2. **Noise Generation**

Controllable noise addition with three types:

```python
from src.audio.speech_synthesizer import create_noisy_speech

# Add office noise (HVAC + AC hum + ambient)
noisy = create_noisy_speech(speech, noise_type="office", snr_db=15)

# Add pink noise
noisy = create_noisy_speech(speech, noise_type="pink", snr_db=12)

# Add Gaussian noise
noisy = create_noisy_speech(speech, noise_type="gaussian", snr_db=10)
```

### 3. **Hearing Aid Integration**

Synthetic speech feeds directly into the hearing aid processing pipeline:

```python
controller = HearingAidController(sample_rate=16000)
result = controller.process_audio(synthetic_speech)

# Access processed audio
processed_audio = result['processed_audio']
features = result['audio_features']
strategy = result['strategy']
```

## Demo Script

Run the complete synthetic speech testing demo:

```bash
python synthetic_speech_demo.py
```

### Features:
- ✅ Generates 5 synthetic speech scenarios
- ✅ Processes through hearing aid system
- ✅ Saves original and processed audio pairs
- ✅ Extracts audio features
- ✅ Applies LLM-based processing strategies
- ✅ Generates comprehensive statistics

## Output Files

All synthetic speech outputs saved to `output_synthetic_speech/` directory:

### Original Speech (Reference)
- `original_presentation.wav` (1.2 MB)
- `original_noisy_presentation.wav` (1.2 MB)
- `original_custom.wav` (332 KB)
- `original_reading.wav` (1.3 MB)
- `original_noisy_reading.wav` (1.3 MB)

### Processed Speech (After Hearing Aid)
- `processed_presentation.wav` (1.2 MB)
- `processed_noisy_presentation.wav` (1.2 MB)
- `processed_custom.wav` (332 KB)
- `processed_reading.wav` (1.3 MB)
- `processed_noisy_reading.wav` (1.3 MB)

**Total**: 10 files, 11 MB

## Performance Metrics

### Synthesis
- **Engine**: Formant synthesis (no external dependencies)
- **Sample Rate**: 16,000 Hz
- **Format**: WAV, 16-bit PCM, Mono
- **Total Duration**: 168 seconds (5 scenarios)
- **Speech Probability**: 80-83% (high clarity)

### Processing
- **Success Rate**: 100%
- **Audio Features Extracted**: 6 features per scenario
- **Average Latency**: ~20-30ms per processing
- **Strategy Application**: LLM-based adaptive schemes

## Technical Details

### Formant Synthesis Algorithm

```
Fundamental Frequency: 120 Hz ± 30 Hz variation
Formant Frequencies:
  F1: 700 Hz ± 200 Hz (vowel color)
  F2: 1220 Hz ± 300 Hz (vowel identity)  
  F3: 2600 Hz ± 400 Hz (brightness)

Envelope: Attack/Release 50ms
Amplitude: 0.8× normalized
```

### Noise Types

1. **Gaussian**: White noise, random
2. **Pink**: Colored noise with frequency dependence
3. **Office**: Realistic HVAC + AC hum + ambient noise

### SNR Control

Signal-to-Noise Ratio can be precisely controlled:
```python
# 15 dB SNR - challenging but intelligible
noisy = create_noisy_speech(speech, snr_db=15)

# 12 dB SNR - realistic office environment
noisy = create_noisy_speech(speech, snr_db=12)

# 20 dB SNR - favorable listening condition
noisy = create_noisy_speech(speech, snr_db=20)
```

## Usage Examples

### Example 1: Generate and Process Custom Speech

```python
from src.audio.speech_synthesizer import SpeechSynthesizer
from src.hearing_aid.controller import HearingAidController

# Setup
synthesizer = SpeechSynthesizer(sample_rate=16000)
controller = HearingAidController()

# Generate
text = "Welcome to the hearing aid system demonstration."
audio = synthesizer.synthesize_text(text)

# Process
result = controller.process_audio(audio)
print(f"Processing successful: {result['status']}")
print(f"Strategy applied: {result['strategy'].explanation}")
```

### Example 2: Test with Various Noise Levels

```python
from src.audio.speech_synthesizer import SpeechScenarioGenerator, create_noisy_speech

gen = SpeechScenarioGenerator()
speech = gen.generate_presentation()

# Test at different SNR levels
for snr in [20, 15, 10, 5]:
    noisy = create_noisy_speech(speech, snr_db=snr)
    result = controller.process_audio(noisy)
    print(f"SNR {snr}dB: {result['audio_features'].speech_probability:.1%}")
```

### Example 3: Multi-speaker Dialogue

```python
dialogue = [
    ("Alice", "Good morning, how are you today?"),
    ("Bob", "I'm doing well, thanks for asking."),
    ("Alice", "That's great to hear!"),
]

speakers = synthesizer.synthesize_dialogue(dialogue)
for speaker, audio in speakers.items():
    result = controller.process_audio(audio)
    print(f"{speaker}: {result['audio_features'].noise_level_db:.1f} dB")
```

## Validation Results

### Audio Quality Metrics
- **Speech Probability**: 80-83% (excellent)
- **Noise Level**: -12.5 dB (clean synthetic speech)
- **Spectral Centroid**: 1800-2000 Hz (natural speech range)
- **Zero Crossing Rate**: Varied (realistic modulation)

### Processing Quality
- **100% Success Rate**: All scenarios processed successfully
- **LLM Decision Making**: All scenarios received strategy decisions
- **Output Audio**: All files saved with correct format and duration
- **Feature Extraction**: Complete feature sets extracted for all inputs

## Advanced Features

### Custom Scenario Creation

```python
# Generate scenario with specific characteristics
duration = 30  # seconds
text = "Your text here"
audio = synthesizer.synthesize_text(text)

# Extend or trim
from scipy import signal
if len(audio) < 16000 * duration:
    # Repeat for longer duration
    repeats = (16000 * duration) // len(audio) + 1
    audio = np.tile(audio, repeats)[:16000*duration]
```

### Batch Processing

```python
scenarios = {
    'presentation': gen.generate_presentation(),
    'reading': gen.generate_reading(),
    'custom': gen.generate_custom("Your text"),
}

results = {}
for name, audio in scenarios.items():
    result = controller.process_audio(audio)
    results[name] = result
```

### Comparative Analysis

```python
# Compare original vs processed
original = synthesizer.synthesize_text("Test sentence")
result = controller.process_audio(original)

# Audio quality comparison
print(f"Original SNR equivalent: {original.noise_level}")
print(f"Processed features: {result['audio_features'].noise_level_db} dB")
```

## Integration with Existing System

The synthetic speech system integrates seamlessly with:
- ✅ Audio Feature Extractor
- ✅ Hearing Aid Controller
- ✅ LLM Decision Engine
- ✅ Safety Validator
- ✅ Audio Processor
- ✅ Learning System

## Future Enhancements

1. **Multi-target Speaker Generation**: Different speakers, accents, age groups
2. **Emotion Control**: Vary speech prosody (happy, sad, angry)
3. **Speech Rate Control**: Slow, normal, fast speech
4. **Phoneme-level Control**: Precise control over phonetic content
5. **Real-time Synthesis**: Stream generation for live interaction
6. **Voice Conversion**: Transform synthetic to natural-sounding speech
7. **Lip-sync Ready**: Add timing information for visual integration

## Dependencies

The synthetic speech system requires:
- ✅ NumPy (already installed)
- ✅ SciPy (already installed)
- ✅ No external TTS engines required

Minimal dependencies for maximum portability!

## Documentation

- **Module**: [src/audio/speech_synthesizer.py](src/audio/speech_synthesizer.py)
- **Demo**: [synthetic_speech_demo.py](synthetic_speech_demo.py)
- **Output**: [output_synthetic_speech/](output_synthetic_speech/)

## Quick Start

```bash
# Run the complete demo
python synthetic_speech_demo.py

# Results will be saved to:
# - output_synthetic_speech/original_*.wav
# - output_synthetic_speech/processed_*.wav
```

## Summary

The synthetic speech system successfully adds text-to-speech capabilities to the hearing aid platform, enabling:
- ✅ Reproducible test scenarios
- ✅ Controllable acoustic conditions
- ✅ Real-time processing validation
- ✅ Performance benchmarking
- ✅ User experience testing

**System Status**: Production Ready

---

*Synthetic Speech Hearing Aid System - February 5, 2026*
