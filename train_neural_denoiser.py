"""
Training script for neural denoiser using synthetic audio dataset.
"""

import numpy as np
import argparse
import logging
from pathlib import Path

from src.audio.neural_denoiser import NeuralDenoiser, DenoisingTrainer
from examples.synthetic_dataset_demo import generate_synthetic_dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_training_pairs(sample_rate: int = 16000):
    """
    Create training pairs (noisy, clean) from synthetic dataset.
    
    Returns:
        Dictionary mapping scenario to (noisy_audio, clean_audio) pairs
    """
    logger.info("Generating synthetic dataset for training...")
    
    dataset = generate_synthetic_dataset(sample_rate=sample_rate)
    
    # Create training pairs
    # The base speech is clean, and each scenario is "noisy"
    training_pairs = {}
    
    speech = dataset['clean_speech']
    
    for scenario_name, noisy_audio in dataset.items():
        if scenario_name != 'clean_speech' and scenario_name != 'silence':
            # Use clean speech as reference
            training_pairs[scenario_name] = (noisy_audio, speech)
    
    logger.info(f"Created {len(training_pairs)} training pairs")
    return training_pairs


def train_denoiser(
    model_output_path: str = "models/neural_denoiser.pt",
    epochs: int = 50,
    learning_rate: float = 1e-3,
    device: str = "cpu"
):
    """
    Train neural denoiser on synthetic dataset.
    
    Args:
        model_output_path: Path to save trained model
        epochs: Number of training epochs
        learning_rate: Learning rate for optimizer
        device: Device to train on ('cpu' or 'cuda')
    """
    logger.info("="*80)
    logger.info("NEURAL DENOISER TRAINING")
    logger.info("="*80)
    
    # Create output directory
    Path(model_output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize denoiser
    logger.info("Initializing neural denoiser...")
    denoiser = NeuralDenoiser(
        sample_rate=16000,
        n_fft=512,
        hop_length=160,
        model_path=None,  # Start with random initialization
        device=device
    )
    
    # Initialize trainer
    trainer = DenoisingTrainer(
        denoiser,
        learning_rate=learning_rate,
        device=device
    )
    
    # Generate training data
    training_pairs = create_training_pairs()
    
    # Train
    logger.info(f"Starting training for {epochs} epochs on {len(training_pairs)} scenarios...")
    history = trainer.train(
        training_pairs,
        epochs=epochs,
        save_path=model_output_path
    )
    
    # Print summary
    logger.info("="*80)
    logger.info("TRAINING SUMMARY")
    logger.info("="*80)
    logger.info(f"Final Loss: {history['loss'][-1]:.6f}")
    logger.info(f"Best Loss: {min(history['loss']):.6f}")
    logger.info(f"Model saved to: {model_output_path}")
    logger.info("="*80)
    
    return denoiser, history


def evaluate_denoiser(
    model_path: str = "models/neural_denoiser.pt",
    device: str = "cpu"
):
    """
    Evaluate trained denoiser on test scenarios.
    
    Args:
        model_path: Path to trained model
        device: Device to run on
    """
    logger.info("="*80)
    logger.info("NEURAL DENOISER EVALUATION")
    logger.info("="*80)
    
    # Load model
    denoiser = NeuralDenoiser(
        sample_rate=16000,
        model_path=model_path,
        device=device
    )
    
    # Generate test data
    dataset = generate_synthetic_dataset()
    speech = dataset['clean_speech']
    
    # Evaluate on each scenario
    logger.info("\nEvaluation Results:")
    logger.info(f"{'Scenario':<25} {'Input SNR':<15} {'Output SNR':<15}")
    logger.info("-"*55)
    
    for scenario_name, noisy_audio in dataset.items():
        if scenario_name in ['clean_speech', 'silence']:
            continue
        
        # Compute input SNR
        noise = noisy_audio - speech * 0.5  # Rough noise estimate
        signal_power = np.mean(speech ** 2)
        noise_power = np.mean(noise ** 2)
        input_snr = 10 * np.log10(signal_power / (noise_power + 1e-8))
        
        # Apply denoising
        denoised = denoiser.denoise(noisy_audio, suppression_strength=0.8)
        
        # Compute output SNR
        noise_out = denoised - speech * 0.5
        noise_power_out = np.mean(noise_out ** 2)
        output_snr = 10 * np.log10(signal_power / (noise_power_out + 1e-8))
        
        snr_improvement = output_snr - input_snr
        
        scenario_display = scenario_name.replace('_', ' ').title()[:24]
        logger.info(f"{scenario_display:<25} {input_snr:<15.2f} {output_snr:<15.2f}")
    
    logger.info("="*80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train neural denoiser for hearing aid")
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-3,
        help="Learning rate for training"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="models/neural_denoiser.pt",
        help="Path to save trained model"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to train on"
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate pre-trained model instead of training"
    )
    
    args = parser.parse_args()
    
    if args.evaluate:
        evaluate_denoiser(args.model_path, args.device)
    else:
        train_denoiser(
            model_output_path=args.model_path,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            device=args.device
        )
