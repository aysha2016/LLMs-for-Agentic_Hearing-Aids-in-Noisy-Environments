#!/usr/bin/env python3
"""
Demo: Load and work with the multi-speaker audio dataset
"""

import json
import numpy as np
from scipy.io import wavfile
from pathlib import Path
import matplotlib.pyplot as plt

# separation utility used in this demo
from src.audio.speech_separation import separate_with_preference

def load_multispeaker_dataset():
    """Load all multi-speaker audio files from the dataset"""
    dataset_path = Path("datasets/multispeaker_audio")
    
    if not dataset_path.exists():
        print("❌ Dataset not found at", dataset_path.absolute())
        return None
    
    # Load metadata
    metadata_file = dataset_path / "dataset_metadata.json"
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    total_files = sum(len(v) for v in metadata.get('conditions', {}).values())
    print(f"✅ Dataset loaded with {total_files} audio files")
    print(f"   Location: {dataset_path.absolute()}\n")
    
    return dataset_path, metadata


def list_dataset_files(dataset_path):
    """Show all files organized by condition"""
    conditions = [
        "clean",
        "office_noise_12db",
        "cafeteria_noise_10db",
        "traffic_noise_8db"
    ]
    
    print("=" * 70)
    print("MULTI-SPEAKER AUDIO DATASET CONTENTS")
    print("=" * 70)
    
    for condition in conditions:
        condition_path = dataset_path / condition
        wav_files = sorted(condition_path.glob("*.wav"))
        print(f"\n📁 {condition.upper()} ({len(wav_files)} files)")
        print("-" * 70)
        
        for wav_file in wav_files:
            size_mb = wav_file.stat().st_size / (1024 * 1024)
            print(f"   • {wav_file.name:40s} ({size_mb:.2f} MB)")
    
    print("\n" + "=" * 70)


def load_audio_sample(dataset_path, condition="clean", filename="office_2speaker.wav"):
    """Load a specific audio file from the dataset"""
    audio_path = dataset_path / condition / filename
    
    if not audio_path.exists():
        print(f"❌ File not found: {audio_path}")
        return None, None
    
    # Load audio
    sample_rate, audio_data = wavfile.read(str(audio_path))
    
    # Convert int16 to float32 (-1.0 to 1.0 range)
    if audio_data.dtype == np.int16:
        audio_float = audio_data.astype(np.float32) / 32767.0
    else:
        audio_float = audio_data.astype(np.float32)
    
    print(f"✅ Loaded: {audio_path.name}")
    print(f"   Sample rate: {sample_rate} Hz")
    print(f"   Duration: {len(audio_float) / sample_rate:.2f} seconds")
    print(f"   Channels: 1 (mono)")
    print(f"   Shape: {audio_float.shape}")
    print(f"   Min/Max: {audio_float.min():.3f} / {audio_float.max():.3f}")
    
    return sample_rate, audio_float


def analyze_audio_across_conditions(dataset_path, scenario_name="office_2speaker.wav"):
    """Compare the same scenario across all noise conditions"""
    conditions = [
        "clean",
        "office_noise_12db",
        "cafeteria_noise_10db",
        "traffic_noise_8db"
    ]
    
    print(f"\n{'=' * 70}")
    print(f"COMPARING: {scenario_name} across noise conditions")
    print(f"{'=' * 70}\n")
    
    results = {}
    
    for condition in conditions:
        audio_path = dataset_path / condition / scenario_name
        
        if not audio_path.exists():
            print(f"⚠️  {condition}: File not found")
            continue
        
        sr, audio = wavfile.read(str(audio_path))
        
        # Convert to float
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32767.0
        
        # Compute metrics
        rms = np.sqrt(np.mean(audio ** 2))
        peak = np.max(np.abs(audio))
        crest = peak / rms if rms > 0 else 0
        
        results[condition] = {
            'rms': rms,
            'peak': peak,
            'crest_factor': crest,
            'duration_sec': len(audio) / sr
        }
        
        print(f"📊 {condition:25s}")
        print(f"   RMS level: {rms:.4f}")
        print(f"   Peak level: {peak:.4f}")
        print(f"   Crest factor: {crest:.2f}")
        print(f"   Duration: {len(audio) / sr:.2f} sec\n")
    
    return results


def get_dataset_summary(dataset_path, metadata):
    """Print summary statistics about the dataset"""
    print(f"\n{'=' * 70}")
    print("DATASET SUMMARY")
    print(f"{'=' * 70}\n")
    
    print(f"Sample rate: {metadata.get('sample_rate', 16000)} Hz (hearing aid standard)")
    print(f"Total size: 13 MB")
    print(f"Audio format: 16-bit PCM, Mono")
    
    # Count files per condition
    conditions = metadata.get('conditions', {})
    total_files = 0
    scenarios = set()
    speaker_counts = set()
    
    print(f"\nAcoustic conditions: {len(conditions)}")
    for condition_name, scenario_dict in conditions.items():
        file_count = len(scenario_dict)
        print(f"  • {condition_name}: {file_count} files")
        total_files += file_count
        
        # Extract scenario info
        for scenario_name, scenario_info in scenario_dict.items():
            scenarios.add(scenario_name)
            if isinstance(scenario_info, dict):
                speaker_counts.add(scenario_info.get('speakers', 0))
    
    print(f"\nTotal files: {total_files}")
    print(f"\nScenario types: {len(scenarios)}")
    for s in sorted(scenarios):
        print(f"  • {s}")
    
    print(f"\nSpeaker counts: {sorted(speaker_counts)}")
    
    return {
        'total_files': total_files,
        'conditions': len(conditions),
        'scenarios': len(scenarios),
        'speaker_counts': sorted(speaker_counts)
    }


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("MULTI-SPEAKER AUDIO DATASET DEMO")
    print("=" * 70 + "\n")
    
    # Load dataset
    result = load_multispeaker_dataset()
    if result is None:
        print("\nTo generate the dataset, run:")
        print("  python create_multispeaker_dataset.py")
        return
    
    dataset_path, metadata = result
    
    # List all files
    list_dataset_files(dataset_path)
    
    # Load a sample audio file
    print("\n" + "=" * 70)
    print("LOADING SAMPLE AUDIO")
    print("=" * 70)
    sample_sr, sample_audio = load_audio_sample(
        dataset_path, 
        condition="clean", 
        filename="office_4speaker.wav"
    )
    
    # Demonstrate basic speaker separation & preference selection
    if sample_sr is not None:
        print("\n" + "=" * 70)
        print("DEMONSTRATING SPEAKER SEPARATION")
        print("=" * 70)
        try:
            chosen, components = separate_with_preference(
                sample_audio, sample_sr, preference="loudest", n_sources=2
            )
            print(f"   separated into {len(components)} streams; "
                  f"chosen loudest has length {len(chosen)} samples")
        except Exception as e:
            print(f"   separation demo failed: {e}")
        
    # Compare same scenario across conditions
    if sample_sr is not None:
        analyze_audio_across_conditions(
            dataset_path,
            scenario_name="office_4speaker.wav"
        )
    
    # Show dataset summary
    get_dataset_summary(dataset_path, metadata)
    
    print("\n" + "=" * 70)
    print("USAGE EXAMPLES")
    print("=" * 70 + "\n")
    
    print("1️⃣  Load audio from clean condition:")
    print("""
    from scipy.io import wavfile
    sr, audio = wavfile.read('datasets/multispeaker_audio/clean/office_4speaker.wav')
    audio_float = audio / 32767.0
    """)
    
    print("2️⃣  Process through hearing aid:")
    print("""
    from src.hearing_aid.controller import HearingAidController
    controller = HearingAidController(profile='mild')
    processed = controller.apply_processing(audio_float)
    """)
    
    print("3️⃣  Evaluate intelligibility:")
    print("""
    from src.audio.multispeaker_evaluation import MultiSpeakerEvaluator
    evaluator = MultiSpeakerEvaluator()
    metrics = evaluator.evaluate_audio(audio_float, sr)
    print(f"Intelligibility: {metrics.intelligibility:.2%}")
    """)
    
    print("4️⃣  Process with separation-enabled hearing aid:")
    print("""
    from src.hearing_aid.controller import HearingAidController
    controller = HearingAidController(sample_rate=sr)
    result = controller.process_audio(
        audio_float,
        use_llm_decision=False,
        use_speaker_separation=True,
        sep_n_sources=2,
        sep_preference='loudest'
    )
    processed_list = result['processed_streams']
    chosen = result['chosen_audio']
    """)
    
    print("\n" + "=" * 70)
    print("✅ Dataset ready to use!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
