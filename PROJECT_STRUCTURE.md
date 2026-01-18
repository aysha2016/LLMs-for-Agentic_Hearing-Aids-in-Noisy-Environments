# LLMs for Agentic Hearing Aids in Noisy Environments

A comprehensive project exploring how Large Language Models can serve as intelligent, safe decision layers for audio-only hearing aids.

## Project Structure

```
.
├── README.md                          # Main documentation
├── requirements.txt                   # Python dependencies
├── setup.py                           # Package setup
├── config/
│   ├── audio_config.yaml             # Audio processing configuration
│   └── model_config.yaml             # LLM model configuration
├── src/
│   ├── __init__.py
│   ├── audio/                        # Audio processing module
│   │   ├── __init__.py
│   │   ├── extractor.py             # Feature extraction
│   │   ├── processor.py             # Audio processing
│   │   └── features.py              # Feature data structures
│   ├── llm/                          # LLM decision layer
│   │   ├── __init__.py
│   │   ├── decision_engine.py       # Main decision engine
│   │   ├── prompts.py               # Prompt construction
│   │   └── safety.py                # Safety validation
│   ├── hearing_aid/                  # Hearing aid control
│   │   ├── __init__.py
│   │   ├── controller.py            # Main controller
│   │   ├── strategies.py            # Strategy library
│   │   └── profiles.py              # User profiles
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                # Logging setup
│       └── helpers.py               # Utility functions
├── tests/
│   ├── test_audio.py                # Audio module tests
│   ├── test_llm.py                  # LLM module tests
│   └── test_integration.py          # Integration tests
├── notebooks/
│   └── demo.py                       # Demo script
└── docs/
    ├── architecture.md              # System architecture
    ├── audio_features.md            # Feature documentation
    └── api_reference.md             # API reference
```

## Key Features

### Audio Analysis Without Raw Waveform Exposure
- Extract high-level features (spectral, temporal, semantic)
- Convert features to natural language for LLM understanding
- Maintain privacy by never exposing raw audio to LLM

### LLM-Based Decision Making
- Generate adaptive processing strategies using LLMs
- Contextually appropriate decisions based on environment
- User preference incorporation
- Feedback-based refinement

### Safe, Bounded Processing
- Comprehensive safety validation
- Configurable constraint enforcement
- Explainable decision rationale
- Parameter bounds enforcement

### Pre-built Strategy Library
- 8+ predefined strategies for common environments
- Manual preset selection
- Dynamic strategy generation
- User preference matching

## Quick Start

```python
import numpy as np
from src.hearing_aid.controller import HearingAidController
from src.hearing_aid.profiles import UserProfile

# Create user profile
profile = UserProfile(
    name="Alice",
    preference="clarity",
    hearing_loss_pattern="high_frequency"
)

# Initialize controller
controller = HearingAidController(user_profile=profile)

# Create or load audio
audio = np.random.randn(16000).astype(np.float32)

# Process with LLM decision
result = controller.process_audio(audio, use_llm_decision=True)
processed_audio = result['processed_audio']

# Or use preset
controller.select_strategy_preset("busy_office")
result = controller.process_audio(audio, use_llm_decision=False)
```

## Testing

```bash
pytest tests/ -v
```

## Architecture Highlights

1. **Audio Layer**: Feature extraction abstracts raw audio
2. **LLM Layer**: Decision making based on feature descriptions
3. **Processing Layer**: Strategy implementation without LLM access to waveforms

This design ensures safety, privacy, and interpretability while leveraging LLM capabilities.

## Documentation

- [Architecture](docs/architecture.md) - System design and data flow
- [Audio Features](docs/audio_features.md) - Feature extraction details
- [API Reference](docs/api_reference.md) - Complete API documentation

## Development

Install development dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

Run the demo:
```bash
python notebooks/demo.py
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

**Last Updated**: January 18, 2026
**Version**: 0.1.0
