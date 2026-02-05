# Using Audio Datasets with the Hearing Aid System

## 📦 Popular Audio Datasets You Can Use

### 1. **LibriSpeech** (Clean Speech)
- **URL**: http://www.openslr.org/12
- **Type**: Clean English speech dataset
- **Size**: 100-1000 hours
- **Use case**: Test speech enhancement in clean conditions

```bash
# Download
wget http://www.openslr.org/resources/12/dev-clean.tar.gz
tar -xzf dev-clean.tar.gz

# Use with system
python examples/use_with_dataset.py --input LibriSpeech/dev-clean/
```

### 2. **DNS Challenge Dataset** (Noisy Speech)
- **URL**: https://github.com/microsoft/DNS-Challenge
- **Type**: Noisy speech with realistic noise
- **Size**: 500+ hours
- **Use case**: Test noise suppression in realistic conditions

```bash
# Download (requires registration)
# Follow instructions at: https://github.com/microsoft/DNS-Challenge

# Use with system
python examples/use_with_dataset.py --input DNS-Challenge/datasets/
```

### 3. **DEMAND** (Environmental Noise)
- **URL**: https://zenodo.org/record/1227121
- **Type**: Environmental background noise recordings
- **Size**: 16 scenarios
- **Use case**: Test adaptive noise handling

### 4. **TIMIT** (Speech Corpus)
- **URL**: https://catalog.ldc.upenn.edu/LDC93S1
- **Type**: Phonetically rich speech
- **Size**: 630 speakers
- **Use case**: Test speech recognition features

### 5. **UrbanSound8K** (Urban Sounds)
- **URL**: https://urbansounddataset.webs.upv.es/urbansound8k.html
- **Type**: Environmental sounds classification
- **Size**: 8732 sound clips
- **Use case**: Test sound event classification

---

## 🚀 Quick Start Examples

### Example 1: Process WAV files from a folder
```python
from pathlib import Path
from src.hearing_aid.controller import HearingAidController
from src.hearing_aid.profiles import UserProfile
import librosa

# Setup
dataset_path = Path("your_dataset/")
controller = HearingAidController(
    model_name="gpt-4",
    user_profile=UserProfile(preference="clarity")
)

# Process all WAV files
for audio_file in dataset_path.glob("*.wav"):
    audio, sr = librosa.load(audio_file, sr=16000)
    result = controller.process_audio(audio, use_llm_decision=True)
    print(f"{audio_file.name}: {result['strategy'].explanation}")
```

### Example 2: Process with different user profiles
```python
# Test with different hearing profiles
profiles = {
    "clarity": UserProfile(preference="clarity", hearing_loss_pattern="high_frequency"),
    "comfort": UserProfile(preference="comfort", hearing_loss_pattern="flat"),
    "balanced": UserProfile(preference="balanced", hearing_loss_pattern="low_frequency")
}

for profile_name, profile in profiles.items():
    controller = HearingAidController(model_name="gpt-4", user_profile=profile)
    result = controller.process_audio(audio, use_llm_decision=True)
    print(f"{profile_name}: {result['strategy'].explanation}")
```

### Example 3: Batch process with metrics
```python
import numpy as np
from tqdm import tqdm

results = []
for audio_file in tqdm(list(dataset_path.glob("*.wav"))):
    audio, sr = librosa.load(audio_file, sr=16000)
    result = controller.process_audio(audio, use_llm_decision=True)
    
    results.append({
        'file': audio_file.name,
        'noise_level': result['audio_features'].noise_level_db,
        'speech_prob': result['audio_features'].speech_probability,
        'strategy': result['strategy'].explanation
    })

# Analyze results
avg_noise = np.mean([r['noise_level'] for r in results])
avg_speech = np.mean([r['speech_prob'] for r in results])
print(f"Average Noise Level: {avg_noise:.1f} dB")
print(f"Average Speech Probability: {avg_speech*100:.1f}%")
```

---

## 📊 Creating Your Own Dataset

### Format Requirements:
- **Audio Format**: WAV, MP3, or FLAC
- **Sample Rate**: 16000 Hz (automatically resampled)
- **Channels**: Mono (stereo will be converted)
- **Duration**: Any (processed in chunks)

### Example Structure:
```
your_dataset/
├── clean_speech/
│   ├── sample1.wav
│   ├── sample2.wav
│   └── ...
├── noisy_speech/
│   ├── sample1.wav
│   ├── sample2.wav
│   └── ...
└── metadata.csv
```

---

## 🧪 Current Test Data

The system currently uses **synthetic audio** for testing:
- Generated sine waves at various frequencies
- White noise at different levels
- Silence (zeros)

See: [tests/test_audio.py](../tests/test_audio.py)

---

## 📈 Next Steps

1. **Download a dataset** from the options above
2. **Place audio files** in a folder
3. **Run the example**: `python examples/use_with_dataset.py`
4. **Customize** for your specific use case
