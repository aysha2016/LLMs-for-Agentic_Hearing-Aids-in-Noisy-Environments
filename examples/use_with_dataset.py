"""
Example: Using the Hearing Aid System with Real Audio Datasets

This script shows how to:
1. Load audio from files or datasets
2. Process with the hearing aid system
3. Evaluate results
"""

import numpy as np
import librosa
from pathlib import Path
from src.hearing_aid.controller import HearingAidController
from src.hearing_aid.profiles import UserProfile


# ============================================================================
# METHOD 1: Process a single audio file
# ============================================================================

def process_audio_file(audio_path, user_profile=None):
    """Process a real audio file through the hearing aid system."""
    
    # Load audio file
    audio, sr = librosa.load(audio_path, sr=16000)
    print(f"✓ Loaded audio: {audio_path}")
    print(f"  - Sample rate: {sr} Hz")
    print(f"  - Duration: {len(audio)/sr:.2f} seconds")
    print(f"  - Shape: {audio.shape}")
    
    # Create controller
    if user_profile is None:
        user_profile = UserProfile(
            name="Dataset User",
            preference="clarity",
            hearing_loss_pattern="high_frequency"
        )
    
    controller = HearingAidController(
        model_name="gpt-4",
        user_profile=user_profile
    )
    
    # Process audio
    result = controller.process_audio(audio, use_llm_decision=True)
    
    if result['status'] == 'success':
        print(f"\n✓ Processing successful!")
        print(f"  - Strategy: {result['strategy'].explanation}")
        print(f"  - Noise Level: {result['audio_features'].noise_level_db:.1f} dB")
        print(f"  - Speech Prob: {result['audio_features'].speech_probability*100:.1f}%")
        
        # Get processed audio
        processed_audio = result['processed_audio']
        return processed_audio, result
    else:
        print(f"✗ Processing failed: {result.get('error', 'Unknown error')}")
        return None, None


# ============================================================================
# METHOD 2: Process multiple files from a dataset
# ============================================================================

def process_audio_dataset(dataset_path, output_path=None):
    """Process multiple audio files from a dataset directory."""
    
    dataset_path = Path(dataset_path)
    audio_files = list(dataset_path.glob("*.wav")) + list(dataset_path.glob("*.mp3"))
    
    print(f"\n📂 Found {len(audio_files)} audio files in dataset")
    
    # Create controller
    controller = HearingAidController(
        model_name="gpt-4",
        user_profile=UserProfile(preference="clarity")
    )
    
    results = []
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] Processing: {audio_file.name}")
        
        # Load and process
        audio, sr = librosa.load(audio_file, sr=16000)
        result = controller.process_audio(audio, use_llm_decision=True)
        
        if result['status'] == 'success':
            results.append({
                'filename': audio_file.name,
                'noise_level': result['audio_features'].noise_level_db,
                'speech_prob': result['audio_features'].speech_probability,
                'strategy': result['strategy'].explanation
            })
            
            # Optionally save processed audio
            if output_path:
                output_file = Path(output_path) / f"processed_{audio_file.name}"
                # librosa.output.write_wav(output_file, result['processed_audio'], sr)
                print(f"  ✓ Saved to: {output_file}")
        
        print(f"  ✓ Noise: {result['audio_features'].noise_level_db:.1f} dB")
        print(f"  ✓ Speech: {result['audio_features'].speech_probability*100:.1f}%")
    
    return results


# ============================================================================
# METHOD 3: Use with numpy array datasets (e.g., from .npy files)
# ============================================================================

def process_numpy_dataset(npy_file_path):
    """Process audio data from numpy array files."""
    
    # Load numpy array
    audio_data = np.load(npy_file_path, allow_pickle=False)
    print(f"✓ Loaded numpy dataset: {npy_file_path}")
    print(f"  - Shape: {audio_data.shape}")
    
    # If multiple samples in dataset
    if len(audio_data.shape) == 2:
        num_samples = audio_data.shape[0]
        print(f"  - Number of samples: {num_samples}")
        
        controller = HearingAidController(
            model_name="gpt-4",
            user_profile=UserProfile(preference="clarity")
        )
        
        results = []
        for i, audio in enumerate(audio_data):
            print(f"\n[{i+1}/{num_samples}] Processing sample {i}")
            result = controller.process_audio(audio, use_llm_decision=True)
            results.append(result)
        
        return results
    else:
        # Single audio signal
        controller = HearingAidController(
            model_name="gpt-4",
            user_profile=UserProfile(preference="clarity")
        )
        return controller.process_audio(audio_data, use_llm_decision=True)


# ============================================================================
# METHOD 4: Use with common audio datasets (LibriSpeech, DNS, etc.)
# ============================================================================

def process_librispeech_dataset(librispeech_path):
    """
    Process LibriSpeech dataset.
    
    Download from: http://www.openslr.org/12
    """
    import os
    
    librispeech_path = Path(librispeech_path)
    
    # LibriSpeech structure: speaker_id/chapter_id/*.flac
    audio_files = list(librispeech_path.rglob("*.flac"))
    
    print(f"📂 Found {len(audio_files)} audio files in LibriSpeech dataset")
    
    controller = HearingAidController(
        model_name="gpt-4",
        user_profile=UserProfile(preference="clarity")
    )
    
    results = []
    
    for audio_file in audio_files[:10]:  # Process first 10 for demo
        audio, sr = librosa.load(audio_file, sr=16000)
        result = controller.process_audio(audio, use_llm_decision=True)
        
        results.append({
            'file': audio_file.name,
            'noise_level': result['audio_features'].noise_level_db,
            'speech_prob': result['audio_features'].speech_probability
        })
    
    return results


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LLM Hearing Aid System - Dataset Processing Examples")
    print("=" * 70)
    
    # Example 1: Process single file (if it exists)
    # processed, result = process_audio_file("path/to/your/audio.wav")
    
    # Example 2: Process directory of files
    # results = process_audio_dataset("path/to/dataset/", "path/to/output/")
    
    # Example 3: Process numpy array
    # results = process_numpy_dataset("path/to/audio_data.npy")
    
    # Example 4: Create synthetic test data and process
    print("\n📊 Demo: Processing synthetic audio samples")
    print("-" * 70)
    
    # Create synthetic noisy audio
    sample_rate = 16000
    duration = 2  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Simulate speech with noise
    speech_signal = np.sin(2 * np.pi * 300 * t) * 0.3  # Low freq
    speech_signal += np.sin(2 * np.pi * 800 * t) * 0.2  # Speech range
    noise = np.random.randn(len(t)) * 0.1
    audio = (speech_signal + noise).astype(np.float32)
    
    # Process with hearing aid system
    controller = HearingAidController(
        model_name="gpt-4",
        user_profile=UserProfile(preference="clarity")
    )
    
    result = controller.process_audio(audio, use_llm_decision=True)
    
    if result['status'] == 'success':
        print(f"\n✓ Processing Complete!")
        print(f"  - Strategy: {result['strategy'].explanation}")
        print(f"  - Noise Level: {result['audio_features'].noise_level_db:.1f} dB")
        print(f"  - Speech Probability: {result['audio_features'].speech_probability*100:.1f}%")
        print(f"  - Sound Event: {result['audio_features'].sound_event_class}")
    
    print("\n" + "=" * 70)
    print("✓ Demo complete!")
    print("=" * 70)
