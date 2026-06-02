"""
Demo: Neural Noise Suppression for Hearing Aids
Shows how to use the neural denoiser component.
"""

import numpy as np
import logging
from pathlib import Path
import sys

# Add project root to path (parent of examples/)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.audio.neural_denoiser import NeuralDenoiser
from src.audio.denoising_integration import HybridDenoiser, DenoisingAwareFeatureExtractor
from src.audio.extractor import AudioFeatureExtractor
from src.hearing_aid.controller import HearingAidController
from src.hearing_aid.profiles import UserProfile

# Import generate_synthetic_dataset from sibling module
import importlib.util
_synthetic_demo_path = str(Path(__file__).resolve().parent / "synthetic_dataset_demo.py")
spec = importlib.util.spec_from_file_location("synthetic_demo", _synthetic_demo_path)
synthetic_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(synthetic_demo)
generate_synthetic_dataset = synthetic_demo.generate_synthetic_dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_basic_neural_denoising():
    """Demo 1: Basic neural noise suppression."""
    logger.info("="*80)
    logger.info("DEMO 1: BASIC NEURAL NOISE SUPPRESSION")
    logger.info("="*80)
    
    # Generate test audio
    dataset = generate_synthetic_dataset()
    noisy_audio = dataset['noisy_restaurant']
    
    logger.info(f"\nProcessing: Noisy Restaurant")
    logger.info(f"Audio shape: {noisy_audio.shape}")
    logger.info(f"Duration: {len(noisy_audio) / 16000:.2f} seconds")
    
    # Initialize denoiser (without pre-trained model)
    logger.info("\nInitializing neural denoiser...")
    denoiser = NeuralDenoiser(
        sample_rate=16000,
        device="cpu"  # Use CPU for compatibility
    )
    
    logger.info("Applying neural denoising...")
    
    # Apply different suppression strengths
    for strength in [0.5, 0.8, 1.0]:
        denoised = denoiser.denoise(noisy_audio, suppression_strength=strength)
        
        # Calculate statistics
        noise_level = np.sqrt(np.mean(noisy_audio ** 2))
        denoised_level = np.sqrt(np.mean(denoised ** 2))
        
        logger.info(f"  Suppression: {strength*100:.0f}% -> Output level: {denoised_level:.4f}")


def demo_hybrid_denoising():
    """Demo 2: Hybrid denoising with fallback."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 2: HYBRID DENOISING (Neural + Fallback)")
    logger.info("="*80)
    
    dataset = generate_synthetic_dataset()
    
    # Initialize hybrid denoiser with fallback
    logger.info("\nInitializing hybrid denoiser...")
    hybrid_denoiser = HybridDenoiser(
        neural_denoiser=NeuralDenoiser(sample_rate=16000, device="cpu"),
        use_neural=True,
        fallback_to_spectral=True
    )
    
    logger.info("Processing multiple scenarios:")
    logger.info(f"{'Scenario':<25} {'Input RMS':<15} {'Output RMS':<15} {'Reduction'}")
    logger.info("-"*70)
    
    for scenario_name, audio in dataset.items():
        if scenario_name in ['clean_speech', 'silence']:
            continue
        
        input_rms = np.sqrt(np.mean(audio ** 2))
        denoised = hybrid_denoiser.denoise(audio, suppression_strength=0.8)
        output_rms = np.sqrt(np.mean(denoised ** 2))
        reduction = (1 - output_rms / input_rms) * 100
        
        scenario_display = scenario_name.replace('_', ' ').title()[:24]
        logger.info(f"{scenario_display:<25} {input_rms:<15.4f} {output_rms:<15.4f} {reduction:>6.1f}%")


def demo_integration_with_controller():
    """Demo 3: Integration with existing hearing aid controller."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 3: INTEGRATION WITH HEARING AID CONTROLLER")
    logger.info("="*80)
    
    dataset = generate_synthetic_dataset()
    
    # Create controller with neural denoising
    profile = UserProfile(
        name="Neural Denoising User",
        preference="clarity",
        hearing_loss_pattern="high_frequency"
    )
    
    controller = HearingAidController(
        model_name="gpt-4",
        user_profile=profile
    )
    
    # Inject neural denoiser into processor
    denoiser = NeuralDenoiser(sample_rate=16000, device="cpu")
    
    # Process test scenario
    test_audio = dataset['noisy_restaurant']
    
    logger.info("\nProcessing with LLM-controlled audio enhancement:")
    result = controller.process_audio(test_audio, use_llm_decision=True)
    
    if result['status'] == 'success':
        logger.info(f"✓ Processing successful")
        logger.info(f"  Strategy: {result['strategy'].explanation}")
        logger.info(f"  Noise Level: {result['audio_features'].noise_level_db:.1f} dB")
        logger.info(f"  Speech Probability: {result['audio_features'].speech_probability*100:.1f}%")


def demo_feature_extraction_with_denoising():
    """Demo 4: Feature extraction with denoising context."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 4: DENOISING-AWARE FEATURE EXTRACTION")
    logger.info("="*80)
    
    dataset = generate_synthetic_dataset()
    
    # Create denoising-aware extractor
    base_extractor = AudioFeatureExtractor(sample_rate=16000)
    denoiser = NeuralDenoiser(sample_rate=16000, device="cpu")
    
    aware_extractor = DenoisingAwareFeatureExtractor(base_extractor, denoiser)
    
    # Extract features with denoising
    test_audio = dataset['noisy_restaurant']
    
    logger.info("\nExtracting features with denoising awareness:")
    results = aware_extractor.extract_with_denoising(
        test_audio,
        denoise=True,
        suppression_strength=0.8
    )
    
    base_feat = results['base_features']
    denoised_feat = results['denoised_features']
    
    logger.info(f"\nBefore denoising:")
    logger.info(f"  Noise Level: {base_feat.noise_level_db:.1f} dB")
    logger.info(f"  Speech Probability: {base_feat.speech_probability:.3f}")
    logger.info(f"  Spectral Centroid: {base_feat.spectral_centroid:.0f} Hz")
    
    logger.info(f"\nAfter denoising:")
    logger.info(f"  Noise Level: {denoised_feat.noise_level_db:.1f} dB")
    logger.info(f"  Speech Probability: {denoised_feat.speech_probability:.3f}")
    logger.info(f"  Spectral Centroid: {denoised_feat.spectral_centroid:.0f} Hz")
    
    logger.info(f"\nImprovement:")
    logger.info(f"  SNR Improvement: {results.get('snr_improvement', 'N/A'):.1f} dB")
    logger.info(f"  Speech Preservation: {results.get('speech_preservation', 'N/A'):.2f}x")


def demo_realtime_streaming():
    """Demo 5: Streaming/real-time processing simulation."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 5: REAL-TIME STREAMING SIMULATION")
    logger.info("="*80)
    
    dataset = generate_synthetic_dataset()
    audio = dataset['street_traffic']
    
    # Simulate streaming with chunk-based processing
    denoiser = NeuralDenoiser(sample_rate=16000, device="cpu")
    
    chunk_duration_ms = 100  # 100ms chunks
    chunk_samples = int(16000 * chunk_duration_ms / 1000)
    
    logger.info(f"\nProcessing {len(audio)/16000:.2f}s audio in {chunk_duration_ms}ms chunks")
    logger.info(f"Total chunks: {(len(audio) + chunk_samples - 1) // chunk_samples}")
    
    processed_chunks = []
    buffer = None
    
    for i in range(0, len(audio), chunk_samples):
        chunk = audio[i:i+chunk_samples]
        
        # Process chunk
        denoised_chunk, buffer = denoiser.denoise_streaming(
            chunk,
            buffer=buffer,
            suppression_strength=0.8
        )
        processed_chunks.append(denoised_chunk)
        
        if (i // chunk_samples + 1) % 10 == 0:
            chunk_num = i // chunk_samples + 1
            logger.info(f"  Processed chunk {chunk_num}/{(len(audio) + chunk_samples - 1) // chunk_samples}")
    
    # Reconstruct audio
    processed_audio = np.concatenate(processed_chunks)
    
    logger.info(f"\n✓ Streaming complete")
    logger.info(f"  Input shape: {audio.shape}")
    logger.info(f"  Output shape: {processed_audio.shape}")


if __name__ == "__main__":
    logger.info("\n")
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " "*78 + "║")
    logger.info("║" + "NEURAL NOISE SUPPRESSION FOR HEARING AIDS - DEMONSTRATION".center(78) + "║")
    logger.info("║" + " "*78 + "║")
    logger.info("╚" + "="*78 + "╝")
    
    # Run demos
    try:
        demo_basic_neural_denoising()
        demo_hybrid_denoising()
        demo_feature_extraction_with_denoising()
        demo_realtime_streaming()
        
        # Skip controller demo as it requires API key
        logger.info("\n" + "="*80)
        logger.info("NOTE: Controller integration demo requires OpenAI API key")
        logger.info("Set OPENAI_API_KEY environment variable to run that demo")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("\n✓ All demos completed!")
