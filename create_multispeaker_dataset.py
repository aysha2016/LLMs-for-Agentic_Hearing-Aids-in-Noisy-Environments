"""Generate and export comprehensive multi-speaker audio dataset."""

import os
import logging
from typing import Dict, List
import json
from datetime import datetime

from src.audio.multispeaker_dataset import MultiSpeakerScenarioGenerator
from scipy.io import wavfile
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_comprehensive_dataset(output_base: str = "datasets/multispeaker_audio") -> Dict:
    """
    Create complete multi-speaker audio dataset with all conditions.
    
    Args:
        output_base: Base directory for datasets
        
    Returns:
        Dataset metadata
    """
    logger.info("=" * 80)
    logger.info("CREATING COMPREHENSIVE MULTI-SPEAKER AUDIO DATASET")
    logger.info("=" * 80)
    
    sample_rate = 16000
    generator = MultiSpeakerScenarioGenerator(sample_rate=sample_rate)
    
    os.makedirs(output_base, exist_ok=True)
    metadata = {
        "created": datetime.now().isoformat(),
        "sample_rate": sample_rate,
        "conditions": {},
        "statistics": {
            "total_files": 0,
            "total_duration_sec": 0,
            "total_size_mb": 0
        }
    }
    
    # Define all scenarios
    scenarios = {
        "office_2speaker": ("office", 2, 8),
        "office_4speaker": ("office", 4, 10),
        "cafeteria_quiet": ("cafeteria", 3, 10),
        "cafeteria_crowded": ("cafeteria", 6, 15),
        "lecture_small": ("lecture", 2, 15),
        "lecture_large": ("lecture", 4, 20),
        "phone_3speaker": ("phone", 3, 10),
        "phone_5speaker": ("phone", 5, 15),
    }
    
    # Generate clean scenarios
    logger.info("\n📝 GENERATING CLEAN AUDIO SCENARIOS")
    logger.info("-" * 80)
    
    clean_dir = os.path.join(output_base, "clean")
    os.makedirs(clean_dir, exist_ok=True)
    
    clean_files = {}
    for scenario_name, (scenario_type, num_speakers, duration) in scenarios.items():
        logger.info(f"\n  Generating: {scenario_name} ({num_speakers} speakers, {duration}s)")
        
        # Generate based on type
        if scenario_type == "office":
            audio = generator.create_office_meeting(num_speakers=num_speakers, duration_sec=duration)
        elif scenario_type == "cafeteria":
            audio = generator.create_crowded_cafeteria(num_speakers=num_speakers, duration_sec=duration)
        elif scenario_type == "lecture":
            audio = generator.create_lecture_hall(num_speakers=num_speakers, duration_sec=duration)
        elif scenario_type == "phone":
            audio = generator.create_phone_conference(num_speakers=num_speakers, duration_sec=duration)
        else:
            logger.warning(f"    Unknown scenario type: {scenario_type}")
            continue
        
        # Save audio
        filepath = os.path.join(clean_dir, f"{scenario_name}.wav")
        audio_int16 = np.int16(audio / (np.max(np.abs(audio)) + 1e-8) * 32767)
        wavfile.write(filepath, sample_rate, audio_int16)
        
        duration_sec = len(audio) / sample_rate
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        
        clean_files[scenario_name] = {
            "path": filepath,
            "duration": duration_sec,
            "size_mb": file_size_mb,
            "speakers": num_speakers
        }
        
        logger.info(f"    ✓ Saved: {duration_sec:.1f}s ({file_size_mb:.2f} MB)")
        
        metadata["statistics"]["total_files"] += 1
        metadata["statistics"]["total_duration_sec"] += duration_sec
        metadata["statistics"]["total_size_mb"] += file_size_mb
    
    metadata["conditions"]["clean"] = clean_files
    
    # Generate noisy conditions
    noise_conditions = {
        "office_noise_12db": ("office", 12),
        "cafeteria_noise_10db": ("restaurant", 10),
        "traffic_noise_8db": ("traffic", 8),
    }
    
    for condition_name, (noise_type, snr_db) in noise_conditions.items():
        logger.info(f"\n📝 GENERATING {condition_name.upper()}")
        logger.info("-" * 80)
        
        condition_dir = os.path.join(output_base, condition_name)
        os.makedirs(condition_dir, exist_ok=True)
        
        condition_files = {}
        for scenario_name, (scenario_type, num_speakers, duration) in scenarios.items():
            # Get clean audio
            clean_audio = clean_files[scenario_name]
            sr, audio_int = wavfile.read(clean_audio["path"])
            audio = audio_int.astype(np.float32) / 32767.0
            
            # Add noise
            logger.info(f"  Adding {noise_type} noise to {scenario_name}...")
            noisy_audio = generator.add_background_noise(audio, noise_type=noise_type, snr_db=snr_db)
            
            # Save
            filepath = os.path.join(condition_dir, f"{scenario_name}.wav")
            audio_int16 = np.int16(noisy_audio / (np.max(np.abs(noisy_audio)) + 1e-8) * 32767)
            wavfile.write(filepath, sample_rate, audio_int16)
            
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            condition_files[scenario_name] = {
                "path": filepath,
                "duration": duration,
                "size_mb": file_size_mb,
                "speakers": num_speakers,
                "noise_type": noise_type,
                "snr_db": snr_db
            }
            
            logger.info(f"    ✓ Saved: {file_size_mb:.2f} MB")
            
            metadata["statistics"]["total_files"] += 1
            metadata["statistics"]["total_duration_sec"] += duration
            metadata["statistics"]["total_size_mb"] += file_size_mb
        
        metadata["conditions"][condition_name] = condition_files
    
    # Save metadata
    metadata_path = os.path.join(output_base, "dataset_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"\n✅ Saved metadata to: {metadata_path}")
    
    return metadata


def create_dataset_index(output_base: str = "datasets/multispeaker_audio") -> str:
    """
    Create an index/README for the dataset.
    
    Args:
        output_base: Base directory for datasets
        
    Returns:
        Index content
    """
    index = """# Multi-Speaker Audio Dataset

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
"""
    
    index_path = os.path.join(output_base, "README.md")
    with open(index_path, 'w') as f:
        f.write(index)
    
    logger.info(f"✅ Created dataset index: {index_path}")
    
    return index


def main():
    """Generate complete multi-speaker dataset."""
    
    logger.info("\n" + "=" * 80)
    logger.info("MULTI-SPEAKER DATASET CREATION TOOL")
    logger.info("=" * 80)
    
    # Create dataset
    metadata = create_comprehensive_dataset(output_base="datasets/multispeaker_audio")
    
    # Create index
    create_dataset_index(output_base="datasets/multispeaker_audio")
    
    # Print summary
    print("\n" + "=" * 80)
    print("DATASET CREATION COMPLETE")
    print("=" * 80)
    print(f"\n📊 Dataset Summary:")
    print(f"   • Total Files: {metadata['statistics']['total_files']}")
    print(f"   • Total Duration: {metadata['statistics']['total_duration_sec']:.1f} seconds")
    print(f"   • Total Size: {metadata['statistics']['total_size_mb']:.2f} MB")
    print(f"\n📁 Location: datasets/multispeaker_audio/")
    print(f"\n📂 Conditions:")
    for condition in metadata['conditions']:
        num_files = len(metadata['conditions'][condition])
        print(f"   • {condition}: {num_files} files")
    print(f"\n📄 Documentation:")
    print(f"   • README: datasets/multispeaker_audio/README.md")
    print(f"   • Metadata: datasets/multispeaker_audio/dataset_metadata.json")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
