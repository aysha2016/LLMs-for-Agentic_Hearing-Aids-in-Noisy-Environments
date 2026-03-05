#!/usr/bin/env python3
"""
Speech Separation Implementation Guide for Hearing Aid System

This guide walks through using the newly-implemented speaker separation feature
with the multi-speaker audio dataset. The feature supports user-preference-based
speaker selection from overlapping speech scenarios.

==============================================================================
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audio.speech_separation import separate_sources, select_preferred_source, separate_with_preference
from scipy.io import wavfile
import numpy as np


def example_1_load_multispeaker_audio():
    """Example 1: Load a multi-speaker audio file from the dataset."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Load Multi-Speaker Audio from Dataset")
    print("=" * 80)
    
    # Load office meeting with 4 speakers
    dataset_path = Path("datasets/multispeaker_audio/clean")
    audio_file = dataset_path / "office_4speaker.wav"
    
    if not audio_file.exists():
        print(f"Dataset file not found: {audio_file}")
        print("To generate the dataset, run: python create_multispeaker_dataset.py")
        return None
    
    sr, audio_int16 = wavfile.read(str(audio_file))
    audio_float = audio_int16.astype(np.float32) / 32767.0
    
    print(f"✓ Loaded: {audio_file.name}")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Duration: {len(audio_float) / sr:.2f} sec")
    print(f"  Shape: {audio_float.shape}")
    print(f"  RMS level: {np.sqrt(np.mean(audio_float**2)):.4f}")
    
    return sr, audio_float


def example_2_basic_separation(sr, audio):
    """Example 2: Perform basic speaker separation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Basic Speaker Separation")
    print("=" * 80)
    
    print("Separating audio into component sources...")
    sources = separate_sources(audio, sr, n_sources=2)
    
    print(f"✓ Separated into {len(sources)} components:")
    for idx, src in enumerate(sources, start=1):
        rms = np.sqrt(np.mean(src ** 2))
        peak = np.max(np.abs(src))
        print(f"  Component {idx}:")
        print(f"    Length: {len(src)} samples ({len(src)/sr:.2f} sec)")
        print(f"    RMS: {rms:.4f}")
        print(f"    Peak: {peak:.4f}")
    
    return sources


def example_3_user_preference_selection(sr, sources):
    """Example 3: Select speaker based on user preference."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: User Preference-Based Selection")
    print("=" * 80)
    
    preferences = ["loudest", "quietest", "highest_pitch", "lowest_pitch"]
    
    for pref in preferences:
        chosen = select_preferred_source(sources, sr, preference=pref)
        rms = np.sqrt(np.mean(chosen ** 2))
        print(f"✓ Preference '{pref}': selected stream with RMS={rms:.4f}")


def example_4_end_to_end_separation(sr, audio):
    """Example 4: End-to-end separation with preference selection."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: End-to-End Separation with Preference")
    print("=" * 80)
    
    preference = "loudest"
    print(f"Separating and selecting preference: {preference}")
    
    chosen, all_sources = separate_with_preference(
        audio, sr, preference=preference, n_sources=2
    )
    
    print(f"✓ Extracted {len(all_sources)} sources")
    print(f"  Selected stream RMS: {np.sqrt(np.mean(chosen**2)):.4f}")
    print(f"  Selected stream length: {len(chosen)} samples")
    
    return chosen, all_sources


def example_5_comparison_across_conditions(sr, scenario_name="office_2speaker.wav"):
    """Example 5: Separate same scenario across different noise conditions."""
    print("\n" + "=" * 80)
    print(f"EXAMPLE 5: Separation Across Noise Conditions")
    print(f"Scenario: {scenario_name}")
    print("=" * 80)
    
    conditions = [
        "clean",
        "office_noise_12db",
        "cafeteria_noise_10db",
        "traffic_noise_8db"
    ]
    
    for condition in conditions:
        audio_path = Path("datasets/multispeaker_audio") / condition / scenario_name
        
        if not audio_path.exists():
            print(f"  {condition:25s}: File not found")
            continue
        
        sr_loaded, audio = wavfile.read(str(audio_path))
        if sr_loaded != sr:
            sr = sr_loaded
        
        audio = audio.astype(np.float32) / 32767.0
        
        try:
            # Simple separation attempt
            sources = separate_sources(audio, sr, n_sources=2)
            chosen = select_preferred_source(sources, sr, preference="loudest")
            
            result_rms = np.sqrt(np.mean(chosen ** 2))
            print(f"  {condition:25s}: RMS={result_rms:.4f} (separation OK)")
        except Exception as e:
            print(f"  {condition:25s}: Separation failed - {e}")


def example_6_save_separated_streams(sr, sources, output_dir="separated_output"):
    """Example 6: Save separated speaker streams to disk."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Save Separated Streams")
    print("=" * 80)
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    for idx, src in enumerate(sources, start=1):
        # Normalize and convert to int16
        normalized = src / (np.max(np.abs(src)) + 1e-8)
        int16_data = np.int16(normalized * 32767)
        
        filename = os.path.join(output_dir, f"component_{idx}.wav")
        wavfile.write(filename, sr, int16_data)
        print(f"  Saved: {filename}")


def example_7_with_hearing_aid_system(sr, audio):
    """Example 7: Integrate separated audio with hearing aid system."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Integration with Hearing Aid System")
    print("=" * 80)
    
    try:
        from src.hearing_aid.controller import HearingAidController
        from src.hearing_aid.profiles import UserProfile
        
        # Separate the audio
        chosen, _ = separate_with_preference(
            audio, sr, preference="loudest", n_sources=2
        )
        
        # Process through hearing aid
        profile = UserProfile(preference="clarity")
        controller = HearingAidController(
            sample_rate=sr,
            user_profile=profile,
            enable_neural_denoising=False
        )
        
        result = controller.process_audio(chosen, use_llm_decision=False)
        processed = result["processed_audio"]
        
        print("  ✓ Executed separation + hearing aid processing pipeline")
        print(f"    Input RMS: {np.sqrt(np.mean(chosen**2)):.4f}")
        print(f"    Output RMS: {np.sqrt(np.mean(processed**2)):.4f}")
        
    except Exception as e:
        print(f"  Integration failed: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("SPEECH SEPARATION IMPLEMENTATION GUIDE")
    print("=" * 80)
    
    sr, audio = example_1_load_multispeaker_audio()
    if audio is None:
        return
    
    sources = example_2_basic_separation(sr, audio)
    example_3_user_preference_selection(sr, sources)
    chosen, all_sources = example_4_end_to_end_separation(sr, audio)
    example_5_comparison_across_conditions(sr)
    example_6_save_separated_streams(sr, all_sources)
    example_7_with_hearing_aid_system(sr, audio)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
The speech separation module provides:

1. separate_sources()
   - NMF-based speaker separation
   - Returns N estimated speaker streams
   - Works on raw audio waveforms

2. select_preferred_source()
   - Choose one stream by user preference
   - Supports: loudest, quietest, highest_pitch, lowest_pitch
   - Returns the selected audio stream

3. separate_with_preference()
   - Combines both functions for end-to-end workflow
   - Returns both chosen stream and all components
   - Convenient for quick integration

Key Use Cases:
- Multi-speaker meeting transcription
- Selective speaker focusing in hearing aids
- Speaker isolation for analysis
- Hearing aid personalization

API Reference:
  // Basic separation
  sources = separate_sources(audio, sr, n_sources=2)
  
  // Select by preference
  chosen = select_preferred_source(sources, sr, preference='loudest')
  
  // End-to-end pipeline
  chosen, all_sources = separate_with_preference(
      audio, sr, preference='loudest', n_sources=2
  )

See examples/speech_separation_demo.py for command-line usage.

### Integration with Hearing Aid Controller

The separation module can be invoked directly from the hearing aid
controller.  When ``use_speaker_separation`` is enabled the controller
runs the ORAL loop independently on each estimated source and returns
all processed streams along with the one matching the requested
preference:

```python
from src.hearing_aid.controller import HearingAidController

controller = HearingAidController(sample_rate=sr, user_profile=user_profile)
result = controller.process_audio(
    audio,
    use_llm_decision=True,
    use_speaker_separation=True,
    sep_n_sources=3,
    sep_preference="highest_pitch",
)

print(result.keys())
# => ['status', 'separated_streams', 'processed_streams',
#     'chosen_index', 'chosen_audio', 'processed_audio',
#     'strategies', 'audio_features', 'decision_made']

chosen = result['chosen_audio']
```""")


if __name__ == "__main__":
    main()
