# API Reference

## Core Classes

### HearingAidController
Main controller for the hearing aid system.

```python
from src.hearing_aid.controller import HearingAidController

controller = HearingAidController(
    model_name="gpt-4",
    user_profile=my_profile
)
```

#### Methods

- `process_audio(audio_stream, use_llm_decision=True)`: Process audio through the system
- `process_audio_with_feedback(audio_stream, user_feedback)`: Process and refine based on feedback
- `set_user_profile(profile)`: Update user preferences
- `select_strategy_preset(preset_name)`: Manually select a strategy
- `enable_processing()`: Enable audio processing
- `disable_processing()`: Disable processing (passthrough)
- `get_system_status()`: Get current system state

### UserProfile
Represents user preferences and hearing characteristics.

```python
from src.hearing_aid.profiles import UserProfile

profile = UserProfile(
    hearing_loss_pattern="high_frequency",
    preference="clarity",
    power_mode="normal"
)
```

#### Attributes

- `hearing_loss_pattern`: Type of hearing loss
- `preference`: Processing preference (clarity/comfort/natural/balanced)
- `power_mode`: Energy consumption mode
- `background_noise_tolerance`: Noise handling preference
- `frequency_preferences`: Band-specific adjustments (dB)
- `typical_environments`: Common usage environments

### AudioFeatureExtractor
Extracts high-level audio features.

```python
from src.audio.extractor import AudioFeatureExtractor

extractor = AudioFeatureExtractor(sample_rate=16000)
features = extractor.extract_features(audio_signal)
```

#### Methods

- `extract_features(audio_signal, duration_ms)`: Extract features from audio

#### Returns

`AudioFeatureSet` containing:
- Spectral features (MFCC, centroid, rolloff)
- Temporal features (ZCR, onset, tempo)
- Semantic descriptors (speech probability, noise type)
- Environmental context

### AudioProcessor
Applies audio processing strategies.

```python
from src.audio.processor import AudioProcessor, AudioProcessingStrategy

processor = AudioProcessor(sample_rate=16000)
strategy = AudioProcessingStrategy(
    noise_suppression_strength=0.6,
    speech_enhancement_level=0.5,
    ...
)
processed = processor.apply_strategy(audio, strategy)
```

### DecisionEngine
LLM-based decision making.

```python
from src.llm.decision_engine import DecisionEngine

engine = DecisionEngine(model_name="gpt-4", enable_safety=True)
decision = engine.decide_strategy(features, user_profile)
```

#### Methods

- `decide_strategy(features, user_profile)`: Generate processing strategy
- `refine_strategy(features, user_profile, feedback, previous)`: Refine based on feedback

### SafetyValidator
Validates decisions for safety.

```python
from src.llm.safety import SafetyValidator

validator = SafetyValidator()
check = validator.validate_strategy(strategy)
safe_strategy = validator.apply_safety_bounds(strategy)
```

## Processing Strategies

### Built-in Presets

- `silence`: Minimal processing
- `quiet_office`: Light enhancement
- `busy_office`: Moderate noise suppression
- `crowded_restaurant`: Strong speech extraction
- `outdoor`: Balanced outdoor processing
- `music`: Preserve audio quality
- `phone_call`: Optimize for telephony
- `comfort_mode`: Gentle processing

### Strategy Parameters

- `noise_suppression_strength`: 0-1 (higher = more suppression)
- `speech_enhancement_level`: 0-1 (higher = more enhancement)
- `dynamic_range_compression_ratio`: 1-10 (higher = more compression)
- `high_frequency_boost`: -12 to +12 dB
- `low_frequency_reduction`: -12 to 0 dB
- `adaptive_gain`: 0.3-2.0 (linear multiplier)
- `noise_gate_threshold`: -60 to -10 dB

## Example Usage

```python
import numpy as np
from src.hearing_aid.controller import HearingAidController
from src.hearing_aid.profiles import UserProfile

# Setup
profile = UserProfile(name="Alice", preference="clarity")
controller = HearingAidController(user_profile=profile)

# Create test audio (1 second)
audio = np.random.randn(16000).astype(np.float32)

# Process with LLM decision
result = controller.process_audio(audio, use_llm_decision=True)
processed_audio = result['processed_audio']
strategy = result['strategy']

# Apply user feedback
result = controller.process_audio_with_feedback(
    audio,
    "Too much bass reduction, too little speech"
)

# Or use preset
controller.select_strategy_preset("busy_office")
result = controller.process_audio(audio, use_llm_decision=False)

# Check status
status = controller.get_system_status()
print(status)
```
