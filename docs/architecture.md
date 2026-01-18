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
