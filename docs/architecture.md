# Architecture

## System Design

The LLM-based hearing aid system is composed of three main layers:

### 1. Audio Abstraction Layer
- **Purpose**: Extract meaningful features from audio without exposing raw waveforms
- **Components**:
  - `AudioFeatureExtractor`: Extracts spectral, temporal, and semantic features
  - `AudioFeatureSet`: Data structure for features
  - Features include: MFCC, spectral centroid, speech probability, noise classification

### 2. LLM Decision Layer
- **Purpose**: Make intelligent decisions about audio processing strategies
- **Components**:
  - `DecisionEngine`: Orchestrates LLM calls and decision making
  - `PromptBuilder`: Constructs prompts with audio context
  - `SafetyValidator`: Ensures decisions meet safety constraints
  - Works only with feature descriptions, not raw audio

### 3. Audio Processing Layer
- **Purpose**: Implement LLM-determined strategies
- **Components**:
  - `AudioProcessor`: Applies processing strategies
  - `AudioProcessingStrategy`: Specifies processing parameters
  - `ProcessingStrategyLibrary`: Predefined strategies

## Data Flow

```
Raw Audio
    ↓
[Audio Feature Extraction]
    ↓
Audio Features (High-level descriptors)
    ↓
[LLM Decision Engine]
    ├─ Context: Features + User Profile
    ├─ Decision: Processing Strategy
    └─ Validation: Safety Checks
    ↓
Processing Strategy (Parameters)
    ↓
[Audio Processing]
    ├─ Apply Noise Suppression
    ├─ Apply Speech Enhancement
    ├─ Apply Compression
    └─ Apply EQ/Gains
    ↓
Processed Audio
```

## Safety Architecture

1. **Constraint Layer**: SafetyValidator enforces bounds on all parameters
2. **Validation Layer**: Checks LLM output before applying to audio
3. **Bounds Enforcement**: Clips values to safe ranges
4. **Transparency**: All decisions logged and explainable

## Hearing Aid Components

### User Profile
- Hearing loss pattern
- Preference mode (clarity/comfort/natural)
- Power mode (battery_saver/normal/performance)
- Personal frequency adjustments

### Strategy Library
- Predefined strategies for common environments
- Manual preset selection option
- Dynamic generation via LLM

### Controller
- Coordinates all components
- Manages state and decision timing
- Supports feedback refinement

## Complete System Architecture

This section expands the architecture to show the full pipeline, major modules, and the data flow between them.

### End-to-End Pipeline

1. **Input Capture**
   - Audio streams enter the system at the device boundary (microphone or file input).
   - The controller keeps input as waveform data locally and only exposes high-level descriptors to the LLM layer.

2. **Feature Extraction (Observe)**
   - `AudioFeatureExtractor` computes spectral, temporal, and semantic descriptors.
   - Features include speech probability, noise level, spectral centroid, and scene classification.
   - These descriptors are the only inputs to the decision layer.

3. **Decision Layer (Reason)**
   - `DecisionEngine` assembles prompts and decides a processing strategy.
   - `SafetyValidator` checks for bounds, reversibility, and rationale requirements.
   - The decision is converted into an `AudioProcessingStrategy` and clamped to safe ranges.

4. **Neural Denoising Pre-Process (Act - Optional)**
   - If enabled, a `HybridDenoiser` applies neural denoising first.
   - Falls back to spectral subtraction if neural inference fails.
   - This stage aims to reduce residual noise before DSP processing.

5. **DSP Processing (Act)**
   - `AudioProcessor` applies the strategy:
   - Noise suppression
   - Noise gate
   - Speech enhancement
   - Dynamic range compression
   - Frequency shaping / EQ
   - Output is clipped to safe audio bounds.

6. **Feedback and Learning (Learn)**
   - User feedback and objective metrics can refine future decisions.
   - Strategy summaries are logged for explainability.

### Data Flow (Detailed)

```
Audio Input (waveform)
  ↓
AudioFeatureExtractor
  ↓
Audio Features (descriptors only)
  ↓
DecisionEngine
  ├─ PromptBuilder
  ├─ SafetyValidator
  └─ Strategy clamp
  ↓
AudioProcessingStrategy
  ↓
HybridDenoiser (optional)
  ├─ NeuralDenoiser
  └─ Spectral fallback
  ↓
AudioProcessor (DSP)
  ├─ Noise suppression
  ├─ Noise gate
  ├─ Speech enhancement
  ├─ Compression
  └─ Frequency shaping
  ↓
Processed Audio Output
  ↓
Feedback Loop (optional)
```

### Component Responsibilities

- **Controller**: Orchestrates the entire pipeline, enforces decision timing, and selects strategies.
- **Feature Extraction**: Converts waveforms into safe, privacy-preserving descriptors.
- **LLM Decision**: Generates bounded, reversible strategies with explicit rationale.
- **Safety Validation**: Rejects unsafe outputs and clips parameters to allowed ranges.
- **Neural Denoiser**: Reduces residual noise before DSP when enabled.
- **DSP Processor**: Applies the final, safe transformations to the waveform.
- **Feedback Loop**: Captures user feedback and improves future decisions.

### Configuration Surface

- **Audio feature parameters**: Sample rate, FFT, hop length, thresholds.
- **Model parameters**: LLM model selection and safety enforcement.
- **Strategy bounds**: Noise suppression and enhancement limits.
- **Denoiser enablement**: Optional neural denoising with fallback.

### Reliability and Safety Principles

- Raw waveforms are never sent to the LLM layer.
- Decisions are bounded, reversible, and logged.
- Conservative defaults are used under uncertainty.
- Fallbacks ensure audio passes through even when the neural path fails.
