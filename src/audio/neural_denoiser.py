"""Neural noise suppression component for hearing aid system."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SpectralMaskingNet(nn.Module):
    """
    Lightweight U-Net architecture for spectral masking.
    
    Predicts ideal ratio mask (IRM) for noise suppression.
    Efficient for real-time inference on hearing aid devices.
    """
    
    def __init__(self, n_freq_bins: int = 257, n_channels: int = 32):
        """
        Initialize spectral masking network.
        
        Args:
            n_freq_bins: Number of frequency bins in spectrogram
            n_channels: Base number of channels for convolutions
        """
        super().__init__()
        self.n_freq_bins = n_freq_bins
        self.n_channels = n_channels
        
        # Encoder (downsampling)
        self.encoder1 = self._conv_block(1, n_channels)
        self.encoder2 = self._conv_block(n_channels, n_channels * 2)
        self.encoder3 = self._conv_block(n_channels * 2, n_channels * 4)
        
        # Bottleneck
        self.bottleneck = self._conv_block(n_channels * 4, n_channels * 8)
        
        # Decoder (upsampling)
        self.decoder3 = self._conv_block(n_channels * 8 + n_channels * 4, n_channels * 4)
        self.decoder2 = self._conv_block(n_channels * 4 + n_channels * 2, n_channels * 2)
        self.decoder1 = self._conv_block(n_channels * 2 + n_channels, n_channels)
        
        # Output layer
        self.output = nn.Conv2d(n_channels, 1, kernel_size=3, padding=1)
        self.sigmoid = nn.Sigmoid()
        
        # Pooling for downsampling
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
    
    def _conv_block(self, in_channels: int, out_channels: int) -> nn.Sequential:
        """Create a convolution block with batch norm and ReLU."""
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through network.
        
        Args:
            x: Input spectrogram [batch_size, 1, freq_bins, time_frames]
        
        Returns:
            Spectral mask [batch_size, 1, freq_bins, time_frames]
        """
        # Encoder
        e1 = self.encoder1(x)
        e1_pool = self.pool(e1)
        
        e2 = self.encoder2(e1_pool)
        e2_pool = self.pool(e2)
        
        e3 = self.encoder3(e2_pool)
        e3_pool = self.pool(e3)
        
        # Bottleneck
        b = self.bottleneck(e3_pool)
        
        # Decoder with skip connections
        d3 = F.interpolate(b, size=e3.shape[2:], mode='bilinear', align_corners=False)
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.decoder3(d3)
        
        d2 = F.interpolate(d3, size=e2.shape[2:], mode='bilinear', align_corners=False)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.decoder2(d2)
        
        d1 = F.interpolate(d2, size=e1.shape[2:], mode='bilinear', align_corners=False)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.decoder1(d1)
        
        # Output
        out = self.output(d1)
        mask = self.sigmoid(out)
        
        return mask


class NeuralDenoiser:
    """
    Neural noise suppression for hearing aid system.
    
    Uses spectral masking with a learned neural network.
    Supports both pre-trained models and training from data.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        n_fft: int = 512,
        hop_length: int = 160,
        model_path: Optional[str] = None,
        device: str = "cpu"
    ):
        """
        Initialize neural denoiser.
        
        Args:
            sample_rate: Audio sample rate in Hz
            n_fft: FFT size for spectrogram
            hop_length: Number of samples between frames
            model_path: Path to pre-trained model weights
            device: Device to run model on ('cpu' or 'cuda')
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.device = device
        
        # Calculate frequency bins
        self.n_freq_bins = n_fft // 2 + 1
        
        # Initialize network
        self.model = SpectralMaskingNet(n_freq_bins=self.n_freq_bins)
        self.model.to(device)
        self.model.eval()  # Set to evaluation mode by default
        
        # Load pre-trained weights if provided
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
            logger.info(f"Loaded pre-trained model from {model_path}")
        else:
            logger.warning("No pre-trained model loaded. Using random initialization.")
    
    def load_model(self, model_path: str) -> None:
        """Load pre-trained model weights."""
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint)
        logger.info(f"Model loaded from {model_path}")
    
    def save_model(self, model_path: str, metadata: Optional[Dict] = None) -> None:
        """Save model weights and metadata."""
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'sample_rate': self.sample_rate,
            'n_fft': self.n_fft,
            'hop_length': self.hop_length,
        }
        if metadata:
            checkpoint.update(metadata)
        
        torch.save(checkpoint, model_path)
        logger.info(f"Model saved to {model_path}")
    
    def denoise(
        self,
        audio: np.ndarray,
        suppression_strength: float = 1.0
    ) -> np.ndarray:
        """
        Denoise audio using neural network.
        
        Args:
            audio: Input audio signal (numpy array, float32)
            suppression_strength: Mask aggressiveness (0-1)
        
        Returns:
            Denoised audio (numpy array, same shape as input)
        """
        # Convert to tensor
        audio_tensor = torch.from_numpy(audio).float().to(self.device)
        
        # Compute STFT
        spec = torch.stft(
            audio_tensor,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            window=torch.hann_window(self.n_fft, device=self.device),
            return_complex=True
        )
        
        # Magnitude spectrogram
        mag = torch.abs(spec)
        phase = torch.angle(spec)
        
        # Normalize for network input
        mag_norm = (mag - mag.mean()) / (mag.std() + 1e-8)
        
        # Prepare input [batch, channels, freq, time]
        x = mag_norm.unsqueeze(0).unsqueeze(0)
        
        # Get spectral mask
        with torch.no_grad():
            mask = self.model(x)
        
        # Apply suppression strength adjustment
        mask = 1 - (1 - mask) * suppression_strength
        mask = mask.squeeze()
        
        # Apply mask to magnitude
        mag_masked = mag * mask
        
        # Reconstruct complex spectrogram
        spec_masked = mag_masked * torch.exp(1j * phase)
        
        # Inverse STFT
        audio_denoised = torch.istft(
            spec_masked,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            window=torch.hann_window(self.n_fft, device=self.device)
        )
        
        return audio_denoised.cpu().numpy().astype(np.float32)
    
    def denoise_streaming(
        self,
        audio_chunk: np.ndarray,
        buffer: Optional[np.ndarray] = None,
        suppression_strength: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Process audio chunk for streaming/real-time application.
        
        Args:
            audio_chunk: Current audio chunk
            buffer: Previous overlap buffer
            suppression_strength: Mask aggressiveness
        
        Returns:
            Tuple of (processed_audio, new_buffer)
        """
        # For streaming, we would handle overlapping windows
        # For now, simple version without sophisticated overlap-add
        return self.denoise(audio_chunk, suppression_strength), None


class DenoisingTrainer:
    """
    Trainer for neural denoiser using synthetic audio data.
    """
    
    def __init__(
        self,
        model: NeuralDenoiser,
        learning_rate: float = 1e-3,
        device: str = "cpu"
    ):
        """
        Initialize trainer.
        
        Args:
            model: NeuralDenoiser instance
            learning_rate: Training learning rate
            device: Device to train on
        """
        self.model = model
        self.device = device
        self.optimizer = torch.optim.Adam(model.model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
    
    def prepare_training_data(
        self,
        noisy_audio: np.ndarray,
        clean_audio: np.ndarray
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Prepare training data (spectrograms).
        
        Args:
            noisy_audio: Noisy audio signal
            clean_audio: Clean reference audio signal
        
        Returns:
            Tuple of (noisy_spec, clean_spec) as tensors
        """
        def get_spectrogram(audio):
            tensor = torch.from_numpy(audio).float().to(self.device)
            spec = torch.stft(
                tensor,
                n_fft=self.model.n_fft,
                hop_length=self.model.hop_length,
                window=torch.hann_window(self.model.n_fft, device=self.device),
                return_complex=True
            )
            mag = torch.abs(spec)
            mag_norm = (mag - mag.mean()) / (mag.std() + 1e-8)
            return mag_norm
        
        noisy_spec = get_spectrogram(noisy_audio)
        clean_spec = get_spectrogram(clean_audio)
        
        return noisy_spec, clean_spec
    
    def train_step(
        self,
        noisy_spec: torch.Tensor,
        clean_spec: torch.Tensor
    ) -> float:
        """
        Single training step.
        
        Args:
            noisy_spec: Noisy spectrogram
            clean_spec: Clean spectrogram
        
        Returns:
            Loss value
        """
        self.model.model.train()
        
        # Prepare batch
        x = noisy_spec.unsqueeze(0).unsqueeze(0)  # [1, 1, freq, time]
        
        # Compute ideal ratio mask
        clean_spec_exp = clean_spec.unsqueeze(0).unsqueeze(0)
        noisy_spec_exp = noisy_spec.unsqueeze(0).unsqueeze(0)
        irm = clean_spec_exp / (noisy_spec_exp + 1e-8)
        irm = torch.clamp(irm, 0, 1)
        
        # Forward pass
        pred_mask = self.model.model(x)
        
        # Calculate loss
        loss = self.criterion(pred_mask, irm)
        
        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        self.model.model.eval()
        return loss.item()
    
    def train(
        self,
        dataset: Dict[str, Tuple[np.ndarray, np.ndarray]],
        epochs: int = 10,
        save_path: Optional[str] = None
    ) -> Dict[str, list]:
        """
        Train denoiser on dataset.
        
        Args:
            dataset: Dictionary of {scenario: (noisy_audio, clean_audio)}
            epochs: Number of training epochs
            save_path: Path to save best model
        
        Returns:
            Training history
        """
        history = {'loss': []}
        best_loss = float('inf')
        
        logger.info(f"Training for {epochs} epochs on {len(dataset)} scenarios")
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            
            for scenario_name, (noisy_audio, clean_audio) in dataset.items():
                noisy_spec, clean_spec = self.prepare_training_data(noisy_audio, clean_audio)
                loss = self.train_step(noisy_spec, clean_spec)
                epoch_loss += loss
            
            epoch_loss /= len(dataset)
            history['loss'].append(epoch_loss)
            
            if epoch_loss < best_loss:
                best_loss = epoch_loss
                if save_path:
                    self.model.save_model(save_path, {'epoch': epoch, 'loss': epoch_loss})
            
            if (epoch + 1) % max(1, epochs // 5) == 0:
                logger.info(f"Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f}")
        
        logger.info(f"Training complete. Best loss: {best_loss:.4f}")
        return history
