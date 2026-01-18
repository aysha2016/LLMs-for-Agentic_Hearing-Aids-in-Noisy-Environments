"""
LLM Hearing Aid System - Demo

This notebook demonstrates the key features of the LLM-based hearing aid system.
"""

import numpy as np
import matplotlib.pyplot as plt
from src.hearing_aid.controller import HearingAidController
from src.hearing_aid.profiles import UserProfile, PROFILE_CLARITY, PROFILE_COMFORT
from src.audio.features import AudioFeatureSet


def create_test_audio(duration_sec=1, noise_level=0.1, frequency=1000):
    """Create synthetic test audio."""
    sample_rate = 16000
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec))
    
    # Speech-like signal
    signal = np.sin(2 * np.pi * frequency * t) * 0.3
    signal += 0.05 * np.sin(2 * np.pi * frequency * 2 * t)
    signal += 0.03 * np.sin(2 * np.pi * frequency * 0.5 * t)
    
    # Add noise
    signal += noise_level * np.random.randn(len(signal))
    
    return signal.astype(np.float32)


# Create controller
print("=" * 60)
print("LLM Hearing Aid System Demo")
print("=" * 60)

# Initialize with clarity profile
profile = UserProfile(
    name="Demo User",
    preference="clarity",
    hearing_loss_pattern="high_frequency"
)

controller = HearingAidController(
    model_name="gpt-4",
    user_profile=profile
)

print(f"\n✓ System initialized for user: {profile.name}")
print(f"✓ Processing preference: {profile.preference}")

# Create test audio with noise
print("\n" + "=" * 60)
print("Creating test audio...")
print("=" * 60)

audio_quiet = create_test_audio(duration_sec=1, noise_level=0.05, frequency=1000)
audio_noisy = create_test_audio(duration_sec=1, noise_level=0.3, frequency=1000)

print(f"✓ Quiet audio created: {len(audio_quiet)} samples")
print(f"✓ Noisy audio created: {len(audio_noisy)} samples")

# Process quiet audio
print("\n" + "=" * 60)
print("Processing quiet environment...")
print("=" * 60)

result_quiet = controller.process_audio(audio_quiet, use_llm_decision=True)

if result_quiet['status'] == 'success':
    print(f"✓ Audio processed successfully")
    print(f"✓ Strategy: {result_quiet['strategy'].explanation}")
    
    features = result_quiet['audio_features']
    print(f"\nAudio Analysis:")
    print(f"  - Noise Level: {features.noise_level_db:.1f} dB")
    print(f"  - Speech Probability: {features.speech_probability*100:.1f}%")
    print(f"  - Spectral Centroid: {features.spectral_centroid:.0f} Hz")
    print(f"  - Sound Event: {features.sound_event_class}")

# Process noisy audio
print("\n" + "=" * 60)
print("Processing noisy environment...")
print("=" * 60)

result_noisy = controller.process_audio(audio_noisy, use_llm_decision=True)

if result_noisy['status'] == 'success':
    print(f"✓ Audio processed successfully")
    print(f"✓ Strategy: {result_noisy['strategy'].explanation}")
    
    features = result_noisy['audio_features']
    print(f"\nAudio Analysis:")
    print(f"  - Noise Level: {features.noise_level_db:.1f} dB")
    print(f"  - Speech Probability: {features.speech_probability*100:.1f}%")
    print(f"  - Spectral Centroid: {features.spectral_centroid:.0f} Hz")
    print(f"  - Sound Event: {features.sound_event_class}")

# Demonstrate preset strategies
print("\n" + "=" * 60)
print("Available Processing Strategies")
print("=" * 60)

strategies = controller.strategy_library.list_strategies()
for strategy_name in strategies:
    desc = controller.strategy_library.get_preset_description(strategy_name)
    print(f"  • {strategy_name}: {desc}")

# Demonstrate user feedback refinement
print("\n" + "=" * 60)
print("User Feedback Refinement")
print("=" * 60)

print("User feedback: 'Too much high-frequency boost, needs more bass'")
result_refined = controller.process_audio_with_feedback(
    audio_noisy,
    "Too much high-frequency boost, needs more bass"
)

if result_refined['status'] == 'success':
    print(f"✓ Strategy refined")
    print(f"✓ New strategy: {result_refined['strategy'].explanation}")

# System status
print("\n" + "=" * 60)
print("System Status")
print("=" * 60)

status = controller.get_system_status()
print(f"✓ Processing enabled: {status['processing_enabled']}")
print(f"✓ Current user: {status['user_profile']}")
print(f"✓ Available presets: {len(status['available_presets'])}")
print(f"✓ Decisions recorded: {status['decision_engine_summary'].get('decisions_recorded', 0)}")

print("\n" + "=" * 60)
print("Demo complete!")
print("=" * 60)
