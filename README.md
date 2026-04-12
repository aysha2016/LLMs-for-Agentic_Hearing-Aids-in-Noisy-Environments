# LLMs for Agentic Hearing Aids in Noisy Environments

## Overview

This repository explores how Large Language Models can be used as safe, agentic decision layers for audio-only hearing aids, enabling:

- **Adaptive Noise Handling**: Dynamic noise suppression strategies based on environmental context
- **Semantic Speech Recovery**: Intelligent speech enhancement and reconstruction using language understanding
- **Personalized Listening Strategies**: User preference-based audio processing and adaptation
- **Waveform-Free Processing**: Audio analysis and decision-making without direct waveform manipulation

## Selected Research Contributions

### 1. Real-Time Audio-Visual Active Speaker Detection System
- Built a multimodal, real-time active speaker detector combining lip-motion analysis and audio cues.
- Integrated Conformer-style blocks (multi-head self-attention, convolution, feed-forward) into U-Net-like architectures.
- Implemented synchronized audio–video feature extraction and multi-face tracking with per-speaker temporal alignment.
- Achieved robust active-speaker performance in noisy, overlapping-speech environments.

### 2. Deep Complex U-Net (DCUC-Net) with Multimodal Fusion
- Extended Deep Complex U-Net to fuse visual features and attention pathways for audio-visual speech enhancement.
- Developed complex-valued neural networks that model both real and imaginary spectral components.
- Designed cross-modal fusion strategies for injecting visual embeddings into the spectral domain.
- Used Conformer layers to capture both global and local audio-visual dependencies.

### 3. AI-Driven Audio-Visual Avatar Dataset (8K+ Avatars)
- Created a large-scale dataset of over 8,400 synthetic avatars from CHAMELEON-style videos.
- Built data generation pipelines with noise injection and domain randomization.
- Designed benchmarking protocols to compare real versus avatar latency and perceived quality.
- Enabled scalable, controlled experiments for real-time audio-visual system development.

### 4. Agentic LLM-Based Audio-Only “Hearing Aid” System
- Developed an agentic hearing system that dynamically adapts responses based on audio context.
- Designed a decision-making architecture with reasoning and adaptive feedback loops.
- Implemented context-aware audio understanding while meeting real-time processing constraints.
- Shifted the hearing aid approach from passive enhancement toward interactive intelligence.

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
git clone https://github.com/aysha16/LLMs-for-Agentic_Hearing-Aids-in-Noisy-Environments.git
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

### Speaker Separation & Multi-Speaker Enhancement (Experimental)
- A lightweight NMF-based source separation utility has been added
  (`src/audio/speech_separation.py`).  It splits a mixed multi-speaker
  signal into multiple streams and can choose one according to user
  preference (loudest, quietest, highest/lowest pitch).
- The main hearing aid controller now supports optional separation with
  the `use_speaker_separation` flag.  When enabled, each estimated source
  is processed through the ORAL decision pipeline independently, and the
  preferred stream is returned.

  ```python
  controller = HearingAidController(sample_rate=sr, user_profile=user_profile)
  result = controller.process_audio(
      audio,
      use_llm_decision=True,
      use_speaker_separation=True,
      sep_n_sources=2,
      sep_preference="loudest",
  )
  processed_list = result["processed_streams"]            # list of streams
  chosen = result["chosen_audio"]                         # preferred one
  ```

- CLI utility examples:
  ```bash
  python examples/speech_separation_demo.py \
      --condition clean --scenario office_4speaker.wav \
      --preference loudest
  ```
  and the multi-speaker dataset demo now illustrates separation and
  controller processing together.

  ```bash
  python examples/intent_adaptive_simulation.py \
      --output-dir output_intent_simulation \
      --scenario office_meeting \
      --noise-type office \
      --snr-db 12
  ```

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
- **Memory Usage**: Monitored and measured for streaming efficiency
- **Benchmarking**: Compare proposed system vs DSP baselines with `tools/benchmark_pipeline.py`
- **Evaluation Framework**: Run multi-talker metrics collection with `tools/evaluation_harness.py`
- **Accuracy**: Validated on diverse acoustic environments
- **Safety**: 100% compliance with all constraints before execution

## Documentation

- **[Decision Loop Architecture](docs/decision_loop.md)**: Detailed ORAL loop explanation with examples
- **[Core Requirements](docs/core_requirements.md)**: Strict safety rules and responsibilities
- **[Audio Features](docs/audio_features.md)**: Feature extraction and descriptors
- **[API Reference](docs/api_reference.md)**: Complete system API documentation
- **[Benchmarking Results](BENCHMARK_RESULTS.md)**: Latency, memory, and energy metrics
- **[Benchmarking Guide](docs/benchmarking.md)**: How to run and interpret benchmarks

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
