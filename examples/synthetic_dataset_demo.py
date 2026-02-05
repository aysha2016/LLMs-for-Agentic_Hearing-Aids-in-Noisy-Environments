"""
Synthetic Audio Dataset Demo
Creates and processes various synthetic audio scenarios through the hearing aid system.
"""

import numpy as np
from src.hearing_aid.controller import HearingAidController
from src.hearing_aid.profiles import UserProfile
from src.audio.features import AudioFeatureSet


def generate_synthetic_dataset(sample_rate=16000):
    """Generate synthetic audio samples representing different scenarios."""
    
    duration = 2  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    dataset = {}
    
    # 1. Clean Speech Simulation (mixed frequencies)
    print("Generating: Clean speech...")
    speech = (
        0.3 * np.sin(2 * np.pi * 200 * t) +  # Fundamental frequency
        0.2 * np.sin(2 * np.pi * 400 * t) +  # First harmonic
        0.15 * np.sin(2 * np.pi * 800 * t) + # Second harmonic
        0.1 * np.sin(2 * np.pi * 1600 * t)   # Third harmonic
    )
    dataset['clean_speech'] = speech.astype(np.float32)
    
    # 2. Quiet Office (speech + low background noise)
    print("Generating: Quiet office...")
    office_noise = np.random.randn(len(t)) * 0.05
    dataset['quiet_office'] = (speech * 0.7 + office_noise).astype(np.float32)
    
    # 3. Noisy Restaurant (speech + high background noise)
    print("Generating: Noisy restaurant...")
    restaurant_noise = (
        np.random.randn(len(t)) * 0.2 +
        0.1 * np.sin(2 * np.pi * 60 * t)  # HVAC hum
    )
    dataset['noisy_restaurant'] = (speech * 0.5 + restaurant_noise).astype(np.float32)
    
    # 4. Street Traffic (low frequency noise)
    print("Generating: Street traffic...")
    traffic_noise = (
        0.3 * np.sin(2 * np.pi * 80 * t) +
        0.2 * np.sin(2 * np.pi * 120 * t) +
        np.random.randn(len(t)) * 0.15
    )
    dataset['street_traffic'] = (speech * 0.4 + traffic_noise).astype(np.float32)
    
    # 5. Silence
    print("Generating: Silence...")
    dataset['silence'] = np.zeros(len(t), dtype=np.float32)
    
    # 6. Music (complex harmonic structure)
    print("Generating: Music...")
    music = (
        0.3 * np.sin(2 * np.pi * 440 * t) +  # A4
        0.2 * np.sin(2 * np.pi * 554.37 * t) +  # C#5
        0.15 * np.sin(2 * np.pi * 659.25 * t)   # E5
    )
    dataset['music'] = music.astype(np.float32)
    
    # 7. High Frequency Noise (hearing aid challenge)
    print("Generating: High frequency noise...")
    high_freq_noise = (
        speech * 0.6 +
        0.2 * np.sin(2 * np.pi * 4000 * t) +
        0.15 * np.sin(2 * np.pi * 6000 * t)
    )
    dataset['high_frequency_noise'] = high_freq_noise.astype(np.float32)
    
    # 8. Sudden Loud Noise
    print("Generating: Sudden loud noise...")
    sudden_noise = speech.copy()
    midpoint = len(t) // 2
    sudden_noise[midpoint:midpoint+int(0.2*sample_rate)] += 0.8 * np.random.randn(int(0.2*sample_rate))
    dataset['sudden_loud_noise'] = sudden_noise.astype(np.float32)
    
    return dataset


def process_synthetic_dataset():
    """Process synthetic dataset through the hearing aid system."""
    
    print("="*80)
    print("SYNTHETIC AUDIO DATASET PROCESSING DEMO")
    print("="*80)
    print()
    
    # Generate dataset
    print("📊 GENERATING SYNTHETIC AUDIO DATASET")
    print("-"*80)
    dataset = generate_synthetic_dataset()
    print(f"✓ Generated {len(dataset)} audio scenarios\n")
    
    # Create user profiles to test
    profiles = {
        "Clarity": UserProfile(
            name="Clarity User",
            preference="clarity",
            hearing_loss_pattern="high_frequency"
        ),
        "Comfort": UserProfile(
            name="Comfort User",
            preference="comfort",
            hearing_loss_pattern="flat"
        ),
        "Balanced": UserProfile(
            name="Balanced User",
            preference="balanced",
            hearing_loss_pattern="low_frequency"
        )
    }
    
    # Process each scenario with each profile
    results_summary = []
    
    for profile_name, profile in profiles.items():
        print("="*80)
        print(f"TESTING PROFILE: {profile_name}")
        print("="*80)
        print()
        
        controller = HearingAidController(
            model_name="gpt-4",
            user_profile=profile
        )
        
        for scenario_name, audio in dataset.items():
            print(f"🎧 Processing: {scenario_name.replace('_', ' ').title()}")
            print("-"*80)
            
            # Process audio
            result = controller.process_audio(audio, use_llm_decision=True)
            
            if result['status'] == 'success':
                features = result['audio_features']
                strategy = result['strategy']
                
                # Display results
                print(f"  Status: ✅ SUCCESS")
                print(f"  Strategy: {strategy.explanation}")
                print(f"  \n  Audio Analysis:")
                print(f"    • Noise Level: {features.noise_level_db:.1f} dB")
                print(f"    • Speech Probability: {features.speech_probability*100:.1f}%")
                print(f"    • Spectral Centroid: {features.spectral_centroid:.0f} Hz")
                print(f"    • Zero Crossing Rate: {features.zero_crossing_rate:.3f}")
                print(f"    • Sound Event: {features.sound_event_class}")
                print(f"    • Noise Type: {features.noise_type}")
                print(f"    • Is Silence: {features.is_silence}")
                print(f"    • Is Speech Present: {features.is_speech_present}")
                
                # Store results
                results_summary.append({
                    'profile': profile_name,
                    'scenario': scenario_name,
                    'noise_level': features.noise_level_db,
                    'speech_prob': features.speech_probability,
                    'strategy': strategy.explanation,
                    'noise_suppression': getattr(strategy, 'noise_suppression_strength', 'N/A'),
                    'speech_enhancement': getattr(strategy, 'speech_enhancement_level', 'N/A')
                })
            else:
                print(f"  Status: ❌ FAILED")
                print(f"  Error: {result.get('error', 'Unknown error')}")
            
            print()
    
    # Summary Statistics
    print("="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print()
    
    # Group by scenario
    scenarios = list(dataset.keys())
    print(f"{'Scenario':<25} {'Avg Noise (dB)':<15} {'Avg Speech %':<15} {'Samples'}")
    print("-"*80)
    
    for scenario in scenarios:
        scenario_results = [r for r in results_summary if r['scenario'] == scenario]
        if scenario_results:
            avg_noise = np.mean([r['noise_level'] for r in scenario_results])
            avg_speech = np.mean([r['speech_prob'] for r in scenario_results]) * 100
            count = len(scenario_results)
            
            scenario_display = scenario.replace('_', ' ').title()[:24]
            print(f"{scenario_display:<25} {avg_noise:<15.1f} {avg_speech:<15.1f} {count}")
    
    print()
    print("="*80)
    print(f"✓ PROCESSED {len(results_summary)} TOTAL SAMPLES")
    print(f"✓ {len(dataset)} SCENARIOS × {len(profiles)} PROFILES")
    print("="*80)
    
    return results_summary, dataset


if __name__ == "__main__":
    results, dataset = process_synthetic_dataset()
    
    print("\n🎉 Dataset processing complete!")
    print(f"   Generated {len(dataset)} synthetic audio scenarios")
    print(f"   Processed {len(results)} total audio samples")
    print("\n💾 Dataset samples stored in memory (shape: 2 seconds @ 16kHz)")
