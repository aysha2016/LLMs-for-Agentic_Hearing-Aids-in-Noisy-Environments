# LLMs for Agentic Hearing Aids in Noisy Environments

## Overview

This repository explores how Large Language Models can be used as safe, agentic decision layers for audio-only hearing aids, enabling:

- **Adaptive Noise Handling**: Dynamic noise suppression strategies based on environmental context
- **Semantic Speech Recovery**: Intelligent speech enhancement and reconstruction using language understanding
- **Personalized Listening Strategies**: User preference-based audio processing and adaptation
- **Waveform-Free Processing**: Audio analysis and decision-making without direct waveform manipulation

## Core Architecture: Observe-Reason-Act-Learn (ORAL) Loop

The system implements a continuous decision loop that ensures safe, explainable, and adaptive hearing aid control:

### 1. **OBSERVE**
- Gather acoustic scene context (noise level, speech presence, ASR confidence)
- Collect user context (hearing profile, preferences, intent)
- Review historical effectiveness and feedback
- **Critical**: Never access raw audio waveforms - only high-level descriptors

### 2. **REASON**
- Infer listening intent (conversation, environmental awareness, speaker focus)
- Assess current speech intelligibility
- Compare with similar past situations
- Evaluate trade-offs: clarity vs. comfort vs. stability vs. power efficiency
- When uncertain, prefer minimal intervention

### 3. **ACT**
- Generate one primary action with bounded, reversible parameters
- Noise suppression: [0.0-0.95], Speech enhancement: [0.0-0.9]
- Compression ratio: [1.0-8.0], Frequency adjustments: [-12 to +10] dB
- Provide explicit rationale, confidence level, and duration (minimum 10 seconds)
- Include secondary conditional adjustments
- **Never output waveforms, DSP coefficients, or out-of-bounds parameters**

### 4. **LEARN**
- Collect objective feedback (ASR confidence change, user overrides)
- Collect subjective feedback (satisfaction ratings)
- Incrementally update strategy rankings for similar future contexts
- Keep all updates reversible and explainable

**[→ Full Details: See `docs/decision_loop.md` and `docs/core_requirements.md`]**

## Key Concepts

### Architecture
The system operates as a multi-layer decision framework:
1. **Audio Input Layer**: Receives audio streams and extracts high-level features (spectral, temporal, semantic)
2. **LLM Decision Layer**: Processes audio context and user profile to generate adaptive processing strategies
3. **Audio Processing Layer**: Implements decisions via signal processing without exposing raw waveforms to the LLM
4. **User Feedback Loop**: Continuously refines strategies based on user satisfaction

### Safety Considerations
- **LLMs operate on audio descriptors, not raw waveforms**: Maintains privacy and reduces attack surface
- **Decisions are verified and bounded by safety constraints**: All parameters checked before execution
- **Transparent decision logging for explainability**: Users can understand why actions were taken
- **User privacy maintained through local processing**: Audio never leaves the device
- **Strict prohibitions**: No raw audio requests, no DSP coefficient outputs, no out-of-bounds parameters, no irreversible changes

## Repository Structure

```
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   ├── model_config.yaml
│   └── audio_config.yaml
├── src/
│   ├── __init__.py
│   ├── audio/
│   │   ├── extractor.py
│   │   ├── processor.py
│   │   └── features.py
│   ├── llm/
│   │   ├── decision_engine.py
│   │   ├── prompts.py
│   │   └── safety.py
│   ├── hearing_aid/
│   │   ├── controller.py
│   │   ├── strategies.py
│   │   └── profiles.py
│   └── utils/
│       ├── logger.py
│       └── helpers.py
├── tests/
│   ├── test_audio.py
│   ├── test_llm.py
│   └── test_integration.py
├── notebooks/
│   └── demo.ipynb
└── docs/
    ├── architecture.md
    ├── decision_loop.md
    ├── core_requirements.md
    ├── audio_features.md
    └── api_reference.md
```

## Getting Started

### Installation

```bash
git clone https://github.com/yourusername/LLMs-for-Agentic_Hearing-Aids-in-Noisy-Environments.git
cd LLMs-for-Agentic_Hearing-Aids-in-Noisy-Environments
pip install -r requirements.txt
```

### Quick Start

```python
from src.hearing_aid.controller import HearingAidController

# Initialize the system
controller = HearingAidController(
    model_name="gpt-4",
    audio_config_path="config/audio_config.yaml"
)

# Process audio stream with ORAL loop
result = controller.process_audio(
    audio_context=audio_features,  # High-level descriptors, never raw audio
    user_preferences=user_profile
)

print(result.strategy_name)
print(result.noise_suppression_strength)
print(result.rationale)
print(result.confidence)
```

## Features

### Audio Feature Extraction
- Spectral analysis (MFCC, mel-spectrogram) - descriptors only
- Temporal characteristics (onset detection, pitch estimation)
- Semantic descriptors (speech/noise classification, scene labels)
- Environmental context detection
- **Privacy-first**: No raw waveforms exposed

### LLM Decision Making (ORAL Loop)
- **Observe**: Context-aware situation assessment
- **Reason**: Multi-objective trade-off analysis with uncertainty handling
- **Act**: Bounded, reversible, explainable recommendations
- **Learn**: Incremental strategy ranking updates
- Adaptive learning from feedback
- Explainable decision rationales
- Conservative defaults when uncertain

### Hearing Aid Strategies
- Noise suppression profiles (light, moderate, aggressive)
- Speech enhancement modes (off, subtle, moderate, strong)
- Dynamic range compression (1.0x to 8.0x)
- Personalized frequency shaping (neutral, speech-optimized, clarity-boost, comfort-focus)
- Automatic strategy selection based on context and user preferences

## Safety & Compliance

### Strict Rules (Non-Negotiable)

| Rule | Rationale |
|------|-----------|
| ❌ No raw audio requests | Privacy protection, security |
| ❌ No DSP coefficients | Prevents system-level manipulation |
| ❌ No out-of-bounds parameters | Prevents hearing damage |
| ❌ No irreversible changes | User control and safety |
| ❌ No rapid oscillation (< 10s) | User experience, stability |
| ✅ Always provide rationale | Explainability and trust |
| ✅ Always include revert capability | User control |
| ✅ Always respect hearing profile | Medical safety |

### Parameter Constraints

| Parameter | Min | Max | Purpose |
|-----------|-----|-----|---------|
| Noise Suppression | 0.0 | 0.95 | Prevent over-suppression artifacts |
| Speech Enhancement | 0.0 | 0.9 | Prevent harshness |
| Compression Ratio | 1.0 | 8.0 | Dynamic range control |
| High Freq Boost | -0.5 | +10 dB | Treble management |
| Low Freq Reduction | -12 | 0 dB | Bass management |
| Decision Duration | 10 | 3600 | Stability window (seconds) |

### Validation Pipeline

```
LLM Decision → Validate Safety → Check Bounds → Respect Hearing Profile
    ↓              ↓                ↓                    ↓
   ✓✓✓         All OK?          All OK?            All OK?
    │            │ ✗                │ ✗                 │ ✗
    │            └→ Violations      └→ Log & Clip       └→ Log & Block
    │                reported            return          fallback
    ↓
Execute with audit trail
```

## Configuration

Edit `config/audio_config.yaml` and `config/model_config.yaml` to customize:
- Audio feature extraction parameters
- LLM model selection and temperature
- Processing strategies and safety constraints
- User preference profiles
- Learning update rates and bounds

## Testing

```bash
pytest tests/ -v
```

Test coverage includes:
- Audio feature extraction correctness
- LLM decision validation and bounds checking
- Safety constraint enforcement
- ORAL loop integration
- Feedback learning mechanisms

## Performance Considerations

- **Latency**: Optimized for real-time inference (target < 200ms)
- **Power Consumption**: Efficient feature extraction for battery operation
- **Accuracy**: Validated on diverse acoustic environments
- **Safety**: 100% compliance with all constraints before execution

## Documentation

- **[Decision Loop Architecture](docs/decision_loop.md)**: Detailed ORAL loop explanation with examples
- **[Core Requirements](docs/core_requirements.md)**: Strict safety rules and responsibilities
- **[Audio Features](docs/audio_features.md)**: Feature extraction and descriptors
- **[API Reference](docs/api_reference.md)**: Complete system API documentation

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. **Ensure all changes respect ORAL loop constraints and safety rules**
4. Add tests for new functionality
5. Verify safety validation passes all checks
6. Submit a pull request with detailed description

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this repository in your research, please cite:

```bibtex
@software{llm_hearing_aids_2026,
  title={LLMs for Agentic Hearing Aids in Noisy Environments: Safe, Explainable Decision Making},
  author={Aysha},
  year={2026},
  url={https://github.com/yourusername/LLMs-for-Agentic_Hearing-Aids-in-Noisy-Environments}
}
```

## Contact

For questions, issues, or feedback:
- Open a GitHub issue
- Review the documentation in `docs/`
- Check the core requirements in `docs/core_requirements.md` for safety guidelines

---

**Last Updated**: January 18, 2026

**Status**: Active Development - ORAL Loop Implementation Complete ✅


---

**Last Updated**: January 18, 2026