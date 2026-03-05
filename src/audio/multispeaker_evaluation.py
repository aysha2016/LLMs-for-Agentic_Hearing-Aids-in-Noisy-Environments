"""Evaluation metrics and analysis for multi-speaker hearing aid scenarios."""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json
import csv

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Container for audio evaluation metrics."""
    scenario_name: str
    condition: str
    duration_sec: float
    snr_db: Optional[float]
    
    # Audio quality metrics
    signal_power: float
    noise_power: Optional[float]
    noise_level_db: float
    
    # Speech intelligibility
    zero_crossing_rate: float
    spectral_centroid_hz: float
    spectral_spread_hz: float
    
    # Multi-speaker indicators
    rms_level_db: float
    peak_level_db: float
    dynamic_range_db: float
    crest_factor: float
    
    # Complexity metrics
    spectral_complexity: float
    temporal_complexity: float
    speech_probability: float
    
    # Specific to multi-speaker
    num_speakers_estimated: int
    intelligibility_estimate: float


class MultiSpeakerEvaluator:
    """Evaluate audio quality and intelligibility for multi-speaker scenarios."""
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize evaluator.
        
        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
        logger.info(f"Initialized MultiSpeakerEvaluator at {sample_rate}Hz")
    
    def evaluate_audio(self, audio: np.ndarray, scenario_name: str, 
                      condition: str, noise_type: Optional[str] = None) -> EvaluationMetrics:
        """
        Comprehensive audio evaluation.
        
        Args:
            audio: Audio array
            scenario_name: Name of scenario
            condition: "clean" or noise condition
            noise_type: Type of noise if applicable
        
        Returns:
            EvaluationMetrics object
        """
        logger.info(f"Evaluating: {scenario_name} ({condition})")
        
        duration = len(audio) / self.sample_rate
        
        # Level measurements
        rms_level = np.sqrt(np.mean(audio ** 2))
        rms_db = 20 * np.log10(rms_level + 1e-8)
        peak_level = np.max(np.abs(audio))
        peak_db = 20 * np.log10(peak_level + 1e-8)
        dynamic_range = peak_db - rms_db
        crest_factor = peak_level / (rms_level + 1e-8)
        
        # Spectral analysis
        fft = np.fft.rfft(audio)
        magnitude = np.abs(fft)
        freqs = np.fft.rfftfreq(len(audio), 1/self.sample_rate)
        
        # Spectral centroid
        spectral_centroid = np.sum(freqs * magnitude) / (np.sum(magnitude) + 1e-8)
        
        # Spectral spread (bandwidth)
        spectral_spread = np.sqrt(
            np.sum(magnitude * (freqs - spectral_centroid) ** 2) / (np.sum(magnitude) + 1e-8)
        )
        
        # Spectral complexity (entropy)
        power_spectrum = magnitude ** 2 / (np.sum(magnitude ** 2) + 1e-8)
        spectral_complexity = -np.sum(power_spectrum * np.log(power_spectrum + 1e-8))
        
        # Temporal features
        zero_crossing_rate = np.mean(np.abs(np.diff(np.sign(audio)))) / 2
        
        # Temporal complexity (variation in energy)
        frame_length = self.sample_rate // 100  # 10ms frames
        frames = []
        for i in range(0, len(audio) - frame_length, frame_length):
            frames.append(np.sqrt(np.mean(audio[i:i+frame_length] ** 2)))
        temporal_complexity = np.std(frames) if frames else 0
        
        # Noise level estimation
        noise_level_db = self._estimate_noise_level(audio)
        
        # Speech probability
        speech_probability = self._estimate_speech_probability(audio)
        
        # Multi-speaker estimation
        num_speakers = self._estimate_num_speakers(audio, spectral_complexity)
        
        # Intelligibility estimate
        intelligibility = self._estimate_intelligibility(audio, speech_probability, spectral_centroid)
        
        # SNR calculation
        snr_db = None
        if condition != "clean":
            signal_power = np.mean(audio ** 2)
            snr_db = 10 * np.log10(signal_power / (10 ** (noise_level_db / 10)) + 1e-8)
        
        metrics = EvaluationMetrics(
            scenario_name=scenario_name,
            condition=condition,
            duration_sec=duration,
            snr_db=snr_db,
            signal_power=float(np.mean(audio ** 2)),
            noise_power=None,
            noise_level_db=float(noise_level_db),
            zero_crossing_rate=float(zero_crossing_rate),
            spectral_centroid_hz=float(spectral_centroid),
            spectral_spread_hz=float(spectral_spread),
            rms_level_db=float(rms_db),
            peak_level_db=float(peak_db),
            dynamic_range_db=float(dynamic_range),
            crest_factor=float(crest_factor),
            spectral_complexity=float(spectral_complexity),
            temporal_complexity=float(temporal_complexity),
            speech_probability=float(speech_probability),
            num_speakers_estimated=int(num_speakers),
            intelligibility_estimate=float(intelligibility)
        )
        
        return metrics
    
    def _estimate_noise_level(self, audio: np.ndarray, percentile: float = 10.0) -> float:
        """
        Estimate noise level using power spectrum percentile.
        
        Args:
            audio: Audio array
            percentile: Percentile for noise floor
        
        Returns:
            Noise level in dB
        """
        # Compute power spectrum in frames
        frame_length = self.sample_rate // 100  # 10ms frames
        powers = []
        
        for i in range(0, len(audio) - frame_length, frame_length):
            frame = audio[i:i+frame_length]
            power = np.mean(frame ** 2)
            powers.append(power)
        
        if not powers:
            return -80.0
        
        noise_power = np.percentile(powers, percentile)
        return 10 * np.log10(noise_power + 1e-8)
    
    def _estimate_speech_probability(self, audio: np.ndarray) -> float:
        """
        Estimate probability that audio contains speech.
        
        Args:
            audio: Audio array
        
        Returns:
            Probability between 0 and 1
        """
        frame_length = self.sample_rate // 100  # 10ms frames
        speech_frames = 0
        total_frames = 0
        
        for i in range(0, len(audio) - frame_length, frame_length):
            frame = audio[i:i+frame_length]
            total_frames += 1
            
            # Speech typically has moderate ZCR and good energy
            zcr = np.mean(np.abs(np.diff(np.sign(frame)))) / 2
            energy = np.mean(frame ** 2)
            
            # Simple heuristic for speech detection
            if 0.01 < zcr < 0.4 and energy > 1e-6:
                speech_frames += 1
        
        if total_frames == 0:
            return 0.0
        
        return speech_frames / total_frames
    
    def _estimate_num_speakers(self, audio: np.ndarray, spectral_complexity: float) -> int:
        """
        Estimate number of speakers by analyzing spectral and temporal complexity.
        
        Args:
            audio: Audio array
            spectral_complexity: Spectral entropy
        
        Returns:
            Estimated number of speakers
        """
        # Analyze variance in different frequency bands
        fft = np.fft.rfft(audio)
        magnitude = np.abs(fft)
        freqs = np.fft.rfftfreq(len(audio), 1/self.sample_rate)
        
        # Divide into frequency bands (typical speech formants)
        bands = {
            "low": (50, 500),
            "mid": (500, 2500),
            "high": (2500, 8000)
        }
        
        band_energy = {}
        for band_name, (low, high) in bands.items():
            mask = (freqs >= low) & (freqs <= high)
            band_energy[band_name] = np.sum(magnitude[mask] ** 2)
        
        # Multi-speaker typically shows more balanced energy across bands
        energies = np.array(list(band_energy.values()))
        energy_ratio = np.std(energies) / (np.mean(energies) + 1e-8)
        
        # Estimate based on spectral complexity and energy distribution
        if spectral_complexity > 3.5 and energy_ratio < 0.5:
            return 4  # High complexity, balanced bands -> many speakers
        elif spectral_complexity > 3.0 and energy_ratio < 1.0:
            return 3
        elif spectral_complexity > 2.5:
            return 2
        else:
            return 1
    
    def _estimate_intelligibility(self, audio: np.ndarray, speech_probability: float, 
                                 spectral_centroid: float) -> float:
        """
        Estimate speech intelligibility.
        
        Args:
            audio: Audio array
            speech_probability: Probability of speech presence
            spectral_centroid: Centroid frequency in Hz
        
        Returns:
            Intelligibility score 0-1
        """
        # Intelligibility factors:
        # 1. Speech presence (higher is better)
        # 2. Spectral centroid in human speech range (800-2500Hz is good)
        # 3. Dynamic range (too flat is bad)
        
        score = 0.0
        
        # Speech presence component
        score += speech_probability * 0.5
        
        # Spectral centroid component
        if 1000 < spectral_centroid < 3500:
            centroid_score = 1.0 - abs(spectral_centroid - 2000) / 1500
        else:
            centroid_score = 0.3
        score += centroid_score * 0.3
        
        # Dynamic range component
        frame_length = self.sample_rate // 100
        if len(audio) > frame_length:
            frame_powers = [np.mean(audio[i:i+frame_length] ** 2) 
                          for i in range(0, len(audio) - frame_length, frame_length)]
            if len(frame_powers) > 1:
                dynamic = (np.max(frame_powers) - np.min(frame_powers)) / (np.mean(frame_powers) + 1e-8)
                dynamic_score = min(dynamic / 100, 1.0)
            else:
                dynamic_score = 0.5
        else:
            dynamic_score = 0.5
        
        score += dynamic_score * 0.2
        
        return min(max(score, 0.0), 1.0)
    
    def compare_conditions(self, clean_metrics: List[EvaluationMetrics], 
                          noisy_metrics: List[EvaluationMetrics]) -> Dict:
        """
        Compare clean vs noisy conditions.
        
        Args:
            clean_metrics: Metrics for clean audio
            noisy_metrics: Metrics for noisy audio
        
        Returns:
            Comparison results
        """
        logger.info("Comparing clean vs noisy conditions")
        
        clean_avg = {
            "intelligibility": np.mean([m.intelligibility_estimate for m in clean_metrics]),
            "snr": np.nanmean([m.snr_db for m in clean_metrics if m.snr_db]),
            "speech_prob": np.mean([m.speech_probability for m in clean_metrics]),
        }
        
        noisy_avg = {
            "intelligibility": np.mean([m.intelligibility_estimate for m in noisy_metrics]),
            "snr": np.nanmean([m.snr_db for m in noisy_metrics if m.snr_db]),
            "speech_prob": np.mean([m.speech_probability for m in noisy_metrics]),
        }
        
        comparison = {
            "clean": clean_avg,
            "noisy": noisy_avg,
            "degradation": {
                "intelligibility_db": 20 * np.log10((1 - noisy_avg["intelligibility"]) / (1 - clean_avg["intelligibility"] + 1e-8) + 1e-8),
                "speech_prob_loss": (clean_avg["speech_prob"] - noisy_avg["speech_prob"]) * 100,
            }
        }
        
        return comparison
    
    def generate_summary(self, all_metrics: List[EvaluationMetrics]) -> Dict:
        """
        Generate summary statistics over all evaluations.
        
        Args:
            all_metrics: List of all evaluation metrics
        
        Returns:
            Summary dictionary
        """
        logger.info(f"Generating summary for {len(all_metrics)} evaluations")
        
        return {
            "total_scenarios": len(all_metrics),
            "avg_duration_sec": np.mean([m.duration_sec for m in all_metrics]),
            "avg_intelligibility": np.mean([m.intelligibility_estimate for m in all_metrics]),
            "avg_num_speakers": np.mean([m.num_speakers_estimated for m in all_metrics]),
            "avg_spectral_centroid": np.mean([m.spectral_centroid_hz for m in all_metrics]),
            "avg_noise_level": np.mean([m.noise_level_db for m in all_metrics]),
            "conditions": list(set([m.condition for m in all_metrics])),
            "min_intelligibility": min([m.intelligibility_estimate for m in all_metrics]),
            "max_intelligibility": max([m.intelligibility_estimate for m in all_metrics]),
        }


def export_metrics_to_csv(metrics_list: List[EvaluationMetrics], filepath: str) -> None:
    """
    Export metrics to CSV file.
    
    Args:
        metrics_list: List of evaluation metrics
        filepath: Output CSV file path
    """
    logger.info(f"Exporting {len(metrics_list)} metrics to {filepath}")
    
    if not metrics_list:
        logger.warning("No metrics to export")
        return
    
    keys = list(asdict(metrics_list[0]).keys())
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        
        for metric in metrics_list:
            writer.writerow(asdict(metric))
    
    logger.info(f"Exported metrics to {filepath}")


def export_metrics_to_json(metrics_list: List[EvaluationMetrics], filepath: str) -> None:
    """
    Export metrics to JSON file.
    
    Args:
        metrics_list: List of evaluation metrics
        filepath: Output JSON file path
    """
    logger.info(f"Exporting {len(metrics_list)} metrics to {filepath}")
    
    data = [asdict(m) for m in metrics_list]
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Exported metrics to {filepath}")
