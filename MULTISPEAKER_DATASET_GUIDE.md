# Multi-Speaker Audio Dataset - Usage Guide

## 🎯 Quick Start

The multi-speaker dataset is ready to use in `datasets/multispeaker_audio/`

**32 audio files** across **4 acoustic conditions**:
- ✅ Clean audio (reference)
- ✅ Office noise (12 dB SNR)
- ✅ Cafeteria noise (10 dB SNR)  
- ✅ Traffic noise (8 dB SNR)

**Total**: 13 MB, ~6.8 minutes of audio

---

## 📂 Dataset Structure

```
datasets/multispeaker_audio/
├── clean/                          # 8 files (noise-free)
│   ├── office_2speaker.wav
│   ├── office_4speaker.wav
│   ├── cafeteria_quiet.wav
│   ├── cafeteria_crowded.wav
│   ├── lecture_small.wav
│   ├── lecture_large.wav
│   ├── phone_3speaker.wav
│   └── phone_5speaker.wav
│
├── office_noise_12db/              # 8 files (office ambiance)
│   └── [same 8 files]
│
├── cafeteria_noise_10db/           # 8 files (social chatter)
│   └── [same 8 files]
│
├── traffic_noise_8db/              # 8 files (vehicle/street)
│   └── [same 8 files]
│
├── dataset_metadata.json           # Complete metadata
└── README.md                       # Dataset documentation
```

---

## 📊 Audio Scenarios

### 1. Office Meetings
| Scenario | Duration | Speakers | Description |
|----------|----------|----------|-------------|
| **office_2speaker** | 8 sec | 2 | Formal business meeting |
| **office_4speaker** | 10 sec | 4 | Team meeting |

### 2. Crowded Venues
| Scenario | Duration | Speakers | Description |
|----------|----------|----------|-------------|
| **cafeteria_quiet** | 10 sec | 3 | Light background conversation |
| **cafeteria_crowded** | 15 sec | 6 | Busy social environment |

### 3. Educational Settings
| Scenario | Duration | Speakers | Description |
|----------|----------|----------|-------------|
| **lecture_small** | 15 sec | 1+2 | Lecturer with audience questions |
| **lecture_large** | 20 sec | 1+4 | Lecture with more interaction |

### 4. Telecommunications
| Scenario | Duration | Speakers | Description |
|----------|----------|----------|-------------|
| **phone_3speaker** | 10 sec | 3 | Small conference call |
| **phone_5speaker** | 15 sec | 5 | Large conference call |

---

## 💻 Usage Examples

### Python with scipy

```python
from scipy.io import wavfile
import numpy as np

# Load clean audio
sample_rate, audio_int = wavfile.read(
    'datasets/multispeaker_audio/clean/office_2speaker.wav'
)

# Convert to float ([-1, 1] range)
audio_float = audio_int.astype(np.float32) / 32767.0

print(f"Sample Rate: {sample_rate} Hz")
print(f"Duration: {len(audio_float) / sample_rate:.1f} seconds")
print(f"Channels: 1 (mono)")
```

### With Hearing Aid System

```python
from scipy.io import wavfile
from src.hearing_aid.controller import HearingAidController

# Load audio
sr, audio_int = wavfile.read('datasets/multispeaker_audio/clean/office_4speaker.wav')
audio = audio_int.astype(np.float32) / 32767.0

# Process with hearing aid
controller = HearingAidController(model_name="gpt-4")
result = controller.process_audio(audio)

# Access results
print(f"Features: {result['audio_features']}")
print(f"Strategy: {result.get('strategy_applied', 'N/A')}")
```

### Compare Conditions

```python
from scipy.io import wavfile
import os

# Load same scenario across all conditions
base_name = "office_4speaker.wav"
conditions = ["clean", "office_noise_12db", "cafeteria_noise_10db", "traffic_noise_8db"]

for condition in conditions:
    path = f"datasets/multispeaker_audio/{condition}/{base_name}"
    sr, audio = wavfile.read(path)
    audio_float = audio / 32767.0
    rms = (audio_float ** 2).mean() ** 0.5
    print(f"{condition}: RMS = {rms:.4f}")
```

### Batch Processing

```python
from scipy.io import wavfile
import glob
import numpy as np

# Get all clean audio files
clean_files = glob.glob('datasets/multispeaker_audio/clean/*.wav')

results = {}
for filepath in sorted(clean_files):
    filename = os.path.basename(filepath)
    sr, audio_int = wavfile.read(filepath)
    audio_float = audio_int / 32767.0
    
    # Your processing here
    rms = np.sqrt(np.mean(audio_float ** 2))
    
    results[filename] = {
        'duration': len(audio_float) / sr,
        'rms': rms,
    }

print(results)
```

### Load from Metadata

```python
import json

# Load dataset metadata
with open('datasets/multispeaker_audio/dataset_metadata.json') as f:
    metadata = json.load(f)

# Get file information
for condition_name, files in metadata['conditions'].items():
    print(f"\n{condition_name}:")
    for scenario, info in files.items():
        print(f"  {scenario}: {info['duration']:.1f}s, {info['speakers']} speakers")

# Overall statistics
stats = metadata['statistics']
print(f"\nTotal: {stats['total_files']} files, {stats['total_duration_sec']:.1f}s")
```

---

## 🎯 Use Cases

### 1. **Testing Hearing Aid Performance**
```python
# Test across all conditions
from src.hearing_aid.controller import HearingAidController
import glob

controller = HearingAidController()

for audio_file in glob.glob('datasets/multispeaker_audio/**/*.wav', recursive=True):
    sr, audio = wavfile.read(audio_file)
    result = controller.process_audio(audio / 32767.0)
    print(f"{audio_file}: {result['audio_features']}")
```

### 2. **Comparing Noise Robustness**
```python
# Compare performance across noise types
from scipy.io import wavfile
from src.audio.multispeaker_evaluation import MultiSpeakerEvaluator

evaluator = MultiSpeaker Evaluator()

for condition in ['clean', 'office_noise_12db', 'cafeteria_noise_10db']:
    sr, audio = wavfile.read(f'datasets/multispeaker_audio/{condition}/office_4speaker.wav')
    metrics = evaluator.evaluate_audio(audio / 32767.0, 'office_4speaker', condition)
    print(f"{condition}: Intelligibility = {metrics.intelligibility_estimate:.3f}")
```

### 3. **Benchmarking Algorithms**
```python
# Run algorithms on all scenarios
import os
import numpy as np
from scipy.io import wavfile

def my_algorithm(audio):
    # Your processing here
    return audio

base_dir = 'datasets/multispeaker_audio'
results = {}

for condition in os.listdir(base_dir):
    condition_dir = os.path.join(base_dir, condition)
    if not os.path.isdir(condition_dir):
        continue
    
    results[condition] = {}
    for filename in os.listdir(condition_dir):
        if filename.endswith('.wav'):
            filepath = os.path.join(condition_dir, filename)
            sr, audio = wavfile.read(filepath)
            output = my_algorithm(audio / 32767.0)
            results[condition][filename] = len(output) / sr

print(results)
```

---

## 📊 Audio File Specifications

- **Sample Rate**: 16,000 Hz (16 kHz)
- **Bit Depth**: 16-bit PCM
- **Format**: WAV
- **Channels**: Mono
- **Duration**: 8-20 seconds per file
- **Total Duration**: 412 seconds (~6.8 minutes)
- **Total Size**: 13 MB

---

## 📈 File Sizes by Scenario

| Scenario | Duration | Size |
|----------|----------|------|
| office_2speaker | 8s | 251 KB |
| office_4speaker | 10s | 313 KB |
| cafeteria_quiet | 10s | 313 KB |
| cafeteria_crowded | 15s | 469 KB |
| lecture_small | 15s | 469 KB |
| lecture_large | 20s | 626 KB |
| phone_3speaker | 10s | 313 KB |
| phone_5speaker | 15s | 469 KB |

(Each scenario appears 4 times: clean + 3 noise conditions, so multiply by 4 for total)

---

## 🔧 Advanced Use

### Custom Processing Pipeline

```python
from scipy.io import wavfile
import numpy as np
from src.hearing_aid.controller import HearingAidController
from src.audio.multispeaker_evaluation import MultiSpeakerEvaluator

# Setup
controller = HearingAidController()
evaluator = MultiSpeakerEvaluator()

# Process and evaluate
audio_path = 'datasets/multispeaker_audio/clean/office_4speaker.wav'
sr, audio = wavfile.read(audio_path)
audio_float = audio / 32767.0

# Step 1: Evaluate original
metrics_orig = evaluator.evaluate_audio(audio_float, 'office_4speaker', 'original')

# Step 2: Process
result = controller.process_audio(audio_float)
audio_processed = result['processed_audio']

# Step 3: Evaluate processed
metrics_proc = evaluator.evaluate_audio(audio_processed, 'office_4speaker', 'processed')

# Step 4: Compare
print(f"Original intelligibility: {metrics_orig.intelligibility_estimate:.3f}")
print(f"Processed intelligibility: {metrics_proc.intelligibility_estimate:.3f}")
print(f"Improvement: {metrics_proc.intelligibility_estimate - metrics_orig.intelligibility_estimate:.3f}")
```

### Extracting Specific Conditions

```python
import shutil
import os

# Create dataset with only office noise
os.makedirs('my_dataset/office_only', exist_ok=True)

src_dir = 'datasets/multispeaker_audio/office_noise_12db'
dst_dir = 'my_dataset/office_only'

for filename in os.listdir(src_dir):
    if filename.endswith('.wav'):
        shutil.copy(
            os.path.join(src_dir, filename),
            os.path.join(dst_dir, filename)
        )
```

---

## 📋 Metadata Structure

```json
{
  "created": "2026-03-01T...",
  "sample_rate": 16000,
  "conditions": {
    "clean": {
      "office_2speaker": {
        "path": "datasets/multispeaker_audio/clean/office_2speaker.wav",
        "duration": 8.0,
        "size_mb": 0.25,
        "speakers": 2
      },
      ...
    },
    "office_noise_12db": {
      "office_2speaker": {
        "path": "datasets/multispeaker_audio/office_noise_12db/office_2speaker.wav",
        "duration": 8.0,
        "size_mb": 0.25,
        "speakers": 2,
        "noise_type": "office",
        "snr_db": 12.0
      },
      ...
    },
    ...
  },
  "statistics": {
    "total_files": 32,
    "total_duration_sec": 412.0,
    "total_size_mb": 12.57
  }
}
```

---

## ✅ Verification

Verify all files are present:

```bash
# Count files
find datasets/multispeaker_audio -name "*.wav" | wc -l
# Should output: 32

# Check sizes
du -sh datasets/multispeaker_audio
# Should output: ~13M

# Verify metadata
jq '.' datasets/multispeaker_audio/dataset_metadata.json | head
```

---

## 📚 Related Documentation

- [Multi-Speaker Evaluation Report](output_multispeaker_evaluation/results/MULTISPEAKER_EVALUATION_REPORT.md)
- [Dataset Generator](src/audio/multispeaker_dataset.py)
- [Evaluation Framework](src/audio/multispeaker_evaluation.py)
- [System Index](MULTISPEAKER_SYSTEM_INDEX.md)

---

## 🚀 Next Steps

1. **Explore the dataset**: Start with `datasets/multispeaker_audio/clean/office_2speaker.wav`
2. **Process with hearing aid**: Use `HearingAidController` to test the system
3. **Evaluate results**: Use `MultiSpeakerEvaluator` to measure performance
4. **Compare conditions**: Analyze performance across noise types
5. **Batch analysis**: Process all scenarios for comprehensive testing

---

Generated: 2026-03-01  
Creator: `create_multispeaker_dataset.py`  
Status: ✅ Ready for Use
