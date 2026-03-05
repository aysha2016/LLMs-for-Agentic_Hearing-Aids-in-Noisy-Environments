#!/usr/bin/env python3
"""
Process multi-speaker audio through the hearing aid system
"""

import json
import numpy as np
from scipy.io import wavfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hearing_aid.controller import HearingAidController
from src.hearing_aid.profiles import UserProfile
from src.audio.multispeaker_evaluation import MultiSpeakerEvaluator


def load_audio_from_dataset(condition="clean", scenario="office_4speaker.wav"):
    """Load audio from the multi-speaker dataset"""
    dataset_path = Path("datasets/multispeaker_audio")
    audio_path = dataset_path / condition / scenario
    
    if not audio_path.exists():
        print(f"❌ Audio file not found: {audio_path}")
        return None, None
    
    sr, audio_int16 = wavfile.read(str(audio_path))
    audio_float = audio_int16.astype(np.float32) / 32767.0
    
    return sr, audio_float


def process_audio_with_hearing_aid(audio, sr, profile_settings=None, use_separation=False, sep_n_sources=2, sep_preference='loudest'):
    """Process audio through the hearing aid system.

    Args:
        audio: waveform array
        sr: sample rate
        profile_settings: dict for user profile
        use_separation: if True, run speaker separation first
        sep_n_sources: number of sources for separation
        sep_preference: preference when choosing from separated results
    """
    print(f"\n{'=' * 70}")
    print(f"HEARING AID PROCESSING")
    print(f"{'=' * 70}\n")
    
    # Create user profile
    if profile_settings is None:
        profile_settings = {}
    
    user_profile = UserProfile(**profile_settings)
    
    # Initialize controller
    controller = HearingAidController(
        sample_rate=sr,
        user_profile=user_profile,
        enable_neural_denoising=False  # Disable neural denoising for speed
    )
    
    # Apply processing
    print("⏳ Processing audio through hearing aid...")
    result = controller.process_audio(
        audio,
        use_llm_decision=False,
        use_speaker_separation=use_separation,
        sep_n_sources=sep_n_sources,
        sep_preference=sep_preference,
    )
    
    processed = result.get("processed_audio")
    
    # If separation produced multiple streams show summary
    if use_separation and isinstance(processed, list):
        print(f"   Produced {len(processed)} processed streams")
        idx = result.get('chosen_index', 0)
        print(f"   Chosen index: {idx}")
        processed_main = result.get('chosen_audio')
    else:
        processed_main = processed
    
    print(f"✅ Processing complete")
    print(f"   Input shape: {audio.shape}")
    if isinstance(processed_main, np.ndarray):
        print(f"   Output shape: {processed_main.shape}")
        print(f"   Input range: [{audio.min():.4f}, {audio.max():.4f}]")
        print(f"   Output range: [{processed_main.min():.4f}, {processed_main.max():.4f}]")
    
    return processed, controller


def analyze_processing_effect(audio_original, audio_processed, sr):
    """Analyze how processing affected the audio"""
    print(f"\n{'=' * 70}")
    print("PROCESSING ANALYSIS")
    print(f"{'=' * 70}\n")
    
    # Compute RMS levels
    rms_original = np.sqrt(np.mean(audio_original ** 2))
    rms_processed = np.sqrt(np.mean(audio_processed ** 2))
    
    print(f"RMS Level:")
    print(f"  Original: {rms_original:.6f}")
    print(f"  Processed: {rms_processed:.6f}")
    print(f"  Change: {(rms_processed/rms_original - 1) * 100:+.1f}%")
    
    # Compute peak levels
    peak_original = np.max(np.abs(audio_original))
    peak_processed = np.max(np.abs(audio_processed))
    
    print(f"\nPeak Level:")
    print(f"  Original: {peak_original:.6f}")
    print(f"  Processed: {peak_processed:.6f}")
    print(f"  Change: {(peak_processed/peak_original - 1) * 100:+.1f}%")
    
    # Compute spectral properties
    from scipy.fftpack import fft
    
    fft_original = np.abs(fft(audio_original))
    fft_processed = np.abs(fft(audio_processed))
    
    freq_bins = np.fft.fftfreq(len(audio_original), 1/sr)
    
    # Find spectral centroid
    def compute_centroid(spectrum, freqs):
        pos_freqs = freqs[:len(spectrum)//2]
        pos_spectrum = spectrum[:len(spectrum)//2]
        return np.sum(pos_freqs * pos_spectrum) / np.sum(pos_spectrum)
    
    centroid_original = compute_centroid(fft_original, freq_bins)
    centroid_processed = compute_centroid(fft_processed, freq_bins)
    
    print(f"\nSpectral Centroid:")
    print(f"  Original: {centroid_original:.1f} Hz")
    print(f"  Processed: {centroid_processed:.1f} Hz")
    print(f"  Change: {(centroid_processed - centroid_original):+.1f} Hz")
    
    # Signal-to-noise change
    noise_floor_original = np.percentile(np.abs(audio_original), 33)
    noise_floor_processed = np.percentile(np.abs(audio_processed), 33)
    
    snr_original = peak_original / (noise_floor_original + 1e-6)
    snr_processed = peak_processed / (noise_floor_processed + 1e-6)
    
    print(f"\nEstimated SNR:")
    print(f"  Original: {snr_original:.2f} dB")
    print(f"  Processed: {snr_processed:.2f} dB")
    print(f"  Change: {10 * np.log10(snr_processed / snr_original):+.2f} dB")


def evaluate_intelligibility(audio, sr, scenario_name="test", condition="clean"):
    """Evaluate intelligibility of audio"""
    print(f"\n{'=' * 70}")
    print("AUDIO QUALITY METRICS")
    print(f"{'=' * 70}\n")
    
    # Initialize evaluator
    evaluator = MultiSpeakerEvaluator()
    
    # Evaluate
    print("⏳ Computing audio metrics...")
    metrics = evaluator.evaluate_audio(audio, scenario_name, condition)
    
    print(f"✅ Evaluation complete\n")
    print(f"Speech Probability: {metrics.speech_probability:.2%}")
    print(f"Estimated Intelligibility: {metrics.intelligibility_estimate:.2%}")
    print(f"Estimated Speaker Count: {metrics.num_speakers_estimated}")
    print(f"\nSpectral Properties:")
    print(f"  Centroid: {metrics.spectral_centroid_hz:.1f} Hz")
    print(f"  Spread: {metrics.spectral_spread_hz:.1f} Hz")
    print(f"  Complexity: {metrics.spectral_complexity:.3f}")
    print(f"\nDynamic Range:")
    print(f"  RMS Level: {metrics.rms_level_db:.2f} dB")
    print(f"  Peak Level: {metrics.peak_level_db:.2f} dB")
    print(f"  Crest Factor: {metrics.crest_factor:.2f}")
    
    return metrics


def compare_profiles_on_scenario(condition="clean", scenario="office_4speaker.wav"):
    """Compare different hearing aid profiles on same audio"""
    print(f"\n{'=' * 70}")
    print(f"PROFILE COMPARISON")
    print(f"Condition: {condition} | Scenario: {scenario}")
    print(f"{'=' * 70}\n")
    
    # Load audio
    sr, audio = load_audio_from_dataset(condition, scenario)
    if audio is None:
        return
    
    # Different profile settings
    profile_settings_list = [
        {"preference": "clarity", "background_noise_tolerance": "low"},
        {"preference": "balanced", "background_noise_tolerance": "medium"},
        {"preference": "natural", "background_noise_tolerance": "high"},
    ]
    
    profile_names = ["clarity", "balanced", "natural"]
    evaluator = MultiSpeakerEvaluator()
    
    results = {}
    
    for name, settings in zip(profile_names, profile_settings_list):
        print(f"Processing with profile: {name}...")
        
        # Process
        user_profile = UserProfile(**settings)
        controller = HearingAidController(
            sample_rate=sr,
            user_profile=user_profile,
            enable_neural_denoising=False
        )
        result = controller.process_audio(audio, use_llm_decision=False)
        processed = result["processed_audio"]
        
        # Evaluate
        metrics = evaluator.evaluate_audio(processed, scenario, condition, noise_type=name)
        
        results[name] = {
            'intelligibility': metrics.intelligibility_estimate,
            'speech_probability': metrics.speech_probability,
            'rms': metrics.rms_level_db,
            'peak': metrics.peak_level_db,
            'spectral_centroid': metrics.spectral_centroid_hz,
            'speaker_count': metrics.num_speakers_estimated,
        }
    
    print(f"\n{'=' * 70}")
    print("COMPARISON RESULTS")
    print(f"{'=' * 70}\n")
    
    print(f"Profile          | Intelligibility | Speech Prob | RMS Level | Speakers")
    print("-" * 78)
    for name in profile_names:
        r = results[name]
        print(f"{name:15s} | {r['intelligibility']:15.2%} | {r['speech_probability']:10.2%} | {r['rms']:9.4f} | {r['speaker_count']:8.1f}")
    
    return results


def batch_process_dataset(condition="clean", num_files=3):
    """Process multiple files from the dataset"""
    print(f"\n{'=' * 70}")
    print(f"BATCH PROCESSING: {condition}")
    print(f"{'=' * 70}\n")
    
    dataset_path = Path("datasets/multispeaker_audio") / condition
    wav_files = sorted(list(dataset_path.glob("*.wav")))[:num_files]
    
    if not wav_files:
        print(f"❌ No audio files found in {dataset_path}")
        return
    
    user_profile = UserProfile()
    controller = HearingAidController(
        sample_rate=16000,
        user_profile=user_profile,
        enable_neural_denoising=False
    )
    evaluator = MultiSpeakerEvaluator()
    
    results = {}
    
    for audio_file in wav_files:
        print(f"\n📄 Processing: {audio_file.name}")
        print("-" * 70)
        
        sr, audio = wavfile.read(str(audio_file))
        audio_float = audio.astype(np.float32) / 32767.0
        
        # Process
        result = controller.process_audio(audio_float, use_llm_decision=False)
        processed = result["processed_audio"]
        
        # Evaluate both
        metrics_orig = evaluator.evaluate_audio(audio_float, audio_file.stem, condition)
        metrics_proc = evaluator.evaluate_audio(processed, audio_file.stem, condition + "_processed")
        
        # Store results
        results[audio_file.name] = {
            'original': {
                'intelligibility': metrics_orig.intelligibility_estimate,
                'speech_probability': metrics_orig.speech_probability,
                'rms': metrics_orig.rms_level_db,
            },
            'processed': {
                'intelligibility': metrics_proc.intelligibility_estimate,
                'speech_probability': metrics_proc.speech_probability,
                'rms': metrics_proc.rms_level_db,
            }
        }
        
        orig = results[audio_file.name]['original']
        proc = results[audio_file.name]['processed']
        
        print(f"  Original  → Intelligibility: {orig['intelligibility']:.2%}, Speech: {orig['speech_probability']:.2%}")
        print(f"  Processed → Intelligibility: {proc['intelligibility']:.2%}, Speech: {proc['speech_probability']:.2%}")
        print(f"  Improvement: {(proc['intelligibility'] - orig['intelligibility'])*100:+.1f}%")
    
    return results


def main():
    """Main processing pipeline"""
    print("\n" + "=" * 70)
    print("MULTI-SPEAKER HEARING AID PROCESSOR")
    print("=" * 70)
    
    # Select scenario
    condition = "clean"
    scenario = "office_4speaker.wav"
    
    print(f"\nSelected: {condition}/{scenario}")
    
    # 1. Load audio
    print(f"\n{'=' * 70}")
    print("STEP 1: LOAD AUDIO")
    print(f"{'=' * 70}\n")
    
    sr, audio = load_audio_from_dataset(condition, scenario)
    if audio is None:
        print("❌ Failed to load audio. Exiting.")
        return
    
    print(f"✅ Loaded audio")
    print(f"   Duration: {len(audio) / sr:.2f} seconds")
    print(f"   Sample rate: {sr} Hz")
    print(f"   Channels: mono")
    
    # 2. Process with hearing aid
    print(f"\n{'=' * 70}")
    print("STEP 2: PROCESS WITH HEARING AID")
    print(f"{'=' * 70}")
    
    processed, controller = process_audio_with_hearing_aid(audio, sr, profile_settings={"preference": "clarity"})
    
    # 3. Analyze processing effect
    analyze_processing_effect(audio, processed, sr)
    
    # 4. Evaluate intelligibility
    print(f"\n{'=' * 70}")
    print("STEP 3: EVALUATE ORIGINAL AUDIO")
    print(f"{'=' * 70}")
    metrics_original = evaluate_intelligibility(audio, sr, "office_4speaker", "clean")
    
    print(f"\n{'=' * 70}")
    print("STEP 4: EVALUATE PROCESSED AUDIO")
    print(f"{'=' * 70}")
    metrics_processed = evaluate_intelligibility(processed, sr, "office_4speaker", "clean_processed")
    
    # 5. Summary
    print(f"\n{'=' * 70}")
    print("PROCESSING SUMMARY")
    print(f"{'=' * 70}\n")
    
    intel_change = metrics_processed.intelligibility_estimate - metrics_original.intelligibility_estimate
    speech_change = metrics_processed.speech_probability - metrics_original.speech_probability
    
    print(f"Intelligibility: {metrics_original.intelligibility_estimate:.2%} → {metrics_processed.intelligibility_estimate:.2%} ({intel_change:+.2%})")
    print(f"Speech Probability: {metrics_original.speech_probability:.2%} → {metrics_processed.speech_probability:.2%} ({speech_change:+.2%})")
    print(f"Estimated Speakers: {metrics_original.num_speakers_estimated} → {metrics_processed.num_speakers_estimated}")
    
    # 6. Compare profiles
    print("\n" + "=" * 70)
    print("STEP 5: COMPARE HEARING AID PROFILES")
    print("=" * 70)
    compare_profiles_on_scenario(condition, scenario)
    
    # 7. Batch process
    print("\n" + "=" * 70)
    print("STEP 6: BATCH PROCESS MULTIPLE SCENARIOS")
    print("=" * 70)
    batch_process_dataset(condition, num_files=3)
    
    print("\n" + "=" * 70)
    print("✅ PROCESSING COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
