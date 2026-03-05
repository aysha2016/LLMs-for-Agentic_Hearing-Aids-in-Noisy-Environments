# Multi-Speaker Audio Dataset

## Overview

Comprehensive multi-speaker audio dataset with 32 audio files across 4 acoustic conditions.

## Dataset Structure

```
datasets/multispeaker_audio/
├── clean/                      # Noise-free reference audio
│   ├── office_2speaker.wav
│   ├── office_4speaker.wav
│   ├── cafeteria_quiet.wav
│   ├── cafeteria_crowded.wav
│   ├── lecture_small.wav
│   ├── lecture_large.wav
│   ├── phone_3speaker.wav
│   └── phone_5speaker.wav
│
├── office_noise_12db/          # Office ambiance (12 dB SNR)
│   ├── office_2speaker.wav
│   ├── office_4speaker.wav
│   ├── cafeteria_quiet.wav
│   ├── cafeteria_crowded.wav
│   ├── lecture_small.wav
│   ├── lecture_large.wav
│   ├── phone_3speaker.wav
│   └── phone_5speaker.wav
│
├── cafeteria_noise_10db/       # Restaurant/social noise (10 dB SNR)
│   ├── office_2speaker.wav
│   ├── office_4speaker.wav
│   ├── cafeteria_quiet.wav
│   ├── cafeteria_crowded.wav
│   ├── lecture_small.wav
│   ├── lecture_large.wav
│   ├── phone_3speaker.wav
│   └── phone_5speaker.wav
│
├── traffic_noise_8db/          # Vehicle/street noise (8 dB SNR)
│   ├── office_2speaker.wav
│   ├── office_4speaker.wav
│   ├── cafeteria_quiet.wav
│   ├── cafeteria_crowded.wav
│   ├── lecture_small.wav
│   ├── lecture_large.wav
│   ├── phone_3speaker.wav
│   └── phone_5speaker.wav
│
└── dataset_metadata.json       # Complete metadata
```

## Scenarios

### Office Meetings
- **office_2speaker**: 2-person meeting (8 seconds)
- **office_4speaker**: 4-person meeting (10 seconds)

### Crowded Venues
- **cafeteria_quiet**: 3 speakers in background (10 seconds)
- **cafeteria_crowded**: 6 speakers overlapping (15 seconds)

### Educational Settings
- **lecture_small**: Lecturer + 2 audience questions (15 seconds)
- **lecture_large**: Lecturer + 4 audience questions (20 seconds)

### Telecommunications
- **phone_3speaker**: 3-participant conference (10 seconds)
- **phone_5speaker**: 5-participant conference (15 seconds)

## Conditions

| Condition | SNR | Characteristics | Use Case |
|-----------|-----|-----------------|----------|
| **clean** | ∞ | Noise-free baseline | Reference |
| **office_noise_12db** | 12 dB | Low-frequency hum + ambient | Office environments |
| **cafeteria_noise_10db** | 10 dB | Background chatter | Social settings |
| **traffic_noise_8db** | 8 dB | Vehicle/street noise | Outdoor scenarios |

## Audio Specifications

- **Sample Rate**: 16,000 Hz (16 kHz)
- **Bit Depth**: 16-bit PCM
- **Format**: WAV
- **Channels**: Mono
- **Total Scenarios**: 32 files
- **Total Duration**: ~100 seconds

## Usage

### In Python

```python
from scipy.io import wavfile
import numpy as np

# Load audio
sample_rate, audio = wavfile.read('datasets/multispeaker_audio/clean/office_2speaker.wav')

# Convert to float
audio_float = audio.astype(np.float32) / 32767.0

# Process with your hearing aid system
from src.hearing_aid.controller import HearingAidController
controller = HearingAidController()
result = controller.process_audio(audio_float)
```

### In Other Languages

```bash
# MATLAB
[audio, sr] = audioread('datasets/multispeaker_audio/clean/office_2speaker.wav');

# Command line
ffmpeg -i datasets/multispeaker_audio/clean/office_2speaker.wav -f s16le -acodec pcm_s16le audio.raw
```

## Metadata

Complete dataset metadata is available in `dataset_metadata.json`:

```json
{
  "created": "2026-03-01T...",
  "sample_rate": 16000,
  "conditions": {
    "clean": {
      "office_2speaker": {
        "path": "...",
        "duration": 8.0,
        "size_mb": 0.25,
        "speakers": 2
      },
      ...
    },
    ...
  },
  "statistics": {
    "total_files": 32,
    "total_duration_sec": 100.0,
    "total_size_mb": 6.4
  }
}
```

## Statistics

- **Total Files**: 32
- **Total Duration**: ~100 seconds
- **Total Size**: ~6.4 MB
- **Average File Size**: 0.2 MB

## Applications

✅ **Suitable for**:
- Hearing aid testing and development
- Audio enhancement algorithm evaluation
- Speech processing research
- Multi-speaker scenario simulation
- Noise robustness testing
- Signal processing education

## Documentation

See `dataset_metadata.json` for:
- Exact file paths
- Individual file durations
- File sizes
- Condition parameters (SNR, noise type)
- Speaker counts per scenario

## License

Part of the LLMs for Agentic Hearing Aids in Noisy Environments project.

## Generated

Created: 2026-03-01  
Generator: `create_multispeaker_dataset.py`  
Framework: Comprehensive multi-speaker evaluation system
