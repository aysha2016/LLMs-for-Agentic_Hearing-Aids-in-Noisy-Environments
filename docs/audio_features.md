# Audio Features

## Overview

The system extracts high-level audio features that describe the sound environment without exposing raw waveforms to the LLM. This maintains privacy and allows for safer, more interpretable decision-making.

## Feature Categories

### Spectral Features
- **MFCC** (Mel-Frequency Cepstral Coefficients): Acoustic modeling, speech recognition
- **Mel-Spectrogram**: Time-frequency representation emphasizing perceptually relevant frequencies
- **Spectral Centroid**: Center of mass of spectrum, indicates "brightness"
- **Spectral Rolloff**: Frequency below which 85% of energy is concentrated

### Temporal Features
- **Zero Crossing Rate (ZCR)**: Number of times signal crosses zero, indicates noise/speech
- **Onset Strength**: Energy of signal derivative, detects sudden changes
- **Tempo**: Estimated rhythm (if applicable)

### Semantic Descriptors
- **Speech Probability**: 0-1 confidence of speech presence
- **Noise Type**: Classification of noise (e.g., traffic, machinery, chatter)
- **Noise Level (dB)**: Estimated sound pressure level
- **Sound Event Class**: High-level classification (silence, speech, loud_noise, background_sound)

### Environmental Context
- **Is Speech Present**: Boolean, speech detected above threshold
- **Is Silence**: Boolean, environment below silence threshold
- **Sound Event Class**: Semantic category of primary sound

## Feature Extraction Process

1. **Preprocessing**: Audio normalized to prevent overflow
2. **FFT Analysis**: Compute frequency domain representation
3. **Feature Calculation**: Extract features from spectral/temporal data
4. **Classification**: Classify noise type and sound events
5. **Thresholding**: Compare against thresholds for semantic features

## LLM Context Format

Features are converted to natural language for LLM processing:

```
Environment: Sound detected at 45.2dB
Speech: Present (72% confidence)
Noise type: mid_frequency
Sound event: background_sound
Spectral profile: 1200Hz centroid
```

This format allows the LLM to understand audio context in intuitive terms.

## Safety Considerations

- No raw waveform data exposed to LLM
- Feature extraction is deterministic and auditable
- All features have defined ranges and meanings
- Easy to validate and explain decisions based on features
