"""Multi-speaker dataset generation and evaluation for hearing aid systems."""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from scipy.io import wavfile
import os
from src.utils.audio_ops import (
    normalize_signal,
    normalize_peak,
    mix_audio_at_offset,
    add_noise_at_snr,
)

logger = logging.getLogger(__name__)


class MultiSpeakerScenarioGenerator:
    """Generate realistic multi-speaker scenarios with overlapping speech."""
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize multi-speaker scenario generator.
        
        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
        logger.info(f"Initialized MultiSpeakerScenarioGenerator at {sample_rate}Hz")
    
    def create_office_meeting(self, num_speakers: int = 4, duration_sec: float = 10.0) -> np.ndarray:
        """
        Create overlapping office meeting scenario.
        
        Args:
            num_speakers: Number of concurrent speakers
            duration_sec: Duration of meeting
        
        Returns:
            Mixed audio array with multiple speakers
        """
        logger.info(f"Generating office meeting: {num_speakers} speakers, {duration_sec}s")
        
        # Dialogue samples for different speakers
        speaker_texts = [
            "I think we should focus on the Q3 metrics and adjust our strategy accordingly.",
            "The customer feedback shows strong interest in the new features.",
            "We need to allocate more resources to the development team.",
            "Let's schedule a follow-up meeting next week to review progress.",
            "The timeline looks feasible if we start immediately."
        ]
        
        mixed_audio = np.zeros(int(duration_sec * self.sample_rate), dtype=np.float32)
        
        # Simulate speakers with staggered starts
        for i in range(min(num_speakers, len(speaker_texts))):
            start_time = i * (duration_sec / num_speakers)
            speaker_audio = self._generate_synthetic_speech(speaker_texts[i])
            
            if len(speaker_audio) > 0:
                speaker_audio = normalize_signal(speaker_audio) * (0.8 / num_speakers)
                start_sample = int(start_time * self.sample_rate)
                mix_audio_at_offset(mixed_audio, speaker_audio, start_sample)

        return normalize_peak(mixed_audio)
    
    def create_crowded_cafeteria(self, num_speakers: int = 6, duration_sec: float = 15.0) -> np.ndarray:
        """
        Create crowded cafeteria with simultaneous overlapping conversations.
        
        Args:
            num_speakers: Number of concurrent speakers
            duration_sec: Duration of scenario
        
        Returns:
            Mixed audio array
        """
        logger.info(f"Generating crowded cafeteria: {num_speakers} speakers, {duration_sec}s")
        
        speaker_texts = [
            "Have you tried the new sandwich? It's really good.",
            "That sounds like a plan. Let's meet up later.",
            "I can't believe how busy it is today.",
            "Did you finish that project we talked about?",
            "Yeah, I'll send you the files tomorrow morning.",
            "This coffee is amazing, much better than usual.",
        ]
        
        mixed_audio = np.zeros(int(duration_sec * self.sample_rate), dtype=np.float32)
        
        # Create more chaotic overlapping
        for i in range(min(num_speakers, len(speaker_texts))):
            start_time = np.random.uniform(0, duration_sec * 0.7)
            duration = np.random.uniform(2, 5)

            speaker_audio = self._generate_synthetic_speech(speaker_texts[i])

            if len(speaker_audio) > 0:
                speaker_audio = normalize_signal(speaker_audio) * (0.7 / num_speakers)
                start_sample = int(start_time * self.sample_rate)
                mix_audio_at_offset(mixed_audio, speaker_audio, start_sample)

        return normalize_peak(mixed_audio)
    
    def create_lecture_hall(self, num_speakers: int = 3, duration_sec: float = 20.0) -> np.ndarray:
        """
        Create lecture scenario with main speaker and audience questions.
        
        Args:
            num_speakers: Additional speakers (questioners) plus 1 lecturer
            duration_sec: Duration of lecture
        
        Returns:
            Mixed audio array
        """
        logger.info(f"Generating lecture scenario: 1 lecturer + {num_speakers} audience, {duration_sec}s")
        
        lecturer_text = "The next topic covers signal processing fundamentals. Pay particular attention to the Fourier transform and its applications in audio."
        
        audience_questions = [
            "Could you clarify the relationship between time and frequency domains?",
            "How does this apply to real-time audio processing?",
            "What are the computational requirements for these algorithms?",
        ]
        
        mixed_audio = np.zeros(int(duration_sec * self.sample_rate), dtype=np.float32)
        
        # Lecturer (dominant)
        lecturer_audio = self._generate_synthetic_speech(lecturer_text)
        if len(lecturer_audio) > 0:
            lecturer_audio = normalize_signal(lecturer_audio) * 0.8
            duration_samples = min(len(lecturer_audio), int(duration_sec * self.sample_rate))
            mixed_audio[:duration_samples] += lecturer_audio[:duration_samples]
        
        # Audience questions
        for i in range(min(num_speakers, len(audience_questions))):
            start_time = 5 + i * 4  # Questions start at 5s, 4s apart
            question_audio = self._generate_synthetic_speech(audience_questions[i])
            
            if len(question_audio) > 0:
                question_audio = normalize_signal(question_audio) * 0.4
                start_sample = int(start_time * self.sample_rate)
                mix_audio_at_offset(mixed_audio, question_audio, start_sample)

        return normalize_peak(mixed_audio)
    
    def create_phone_conference(self, num_speakers: int = 4, duration_sec: float = 12.0) -> np.ndarray:
        """
        Create phone conference call scenario.
        
        Args:
            num_speakers: Number of participants
            duration_sec: Duration of call
        
        Returns:
            Mixed audio array
        """
        logger.info(f"Generating phone conference: {num_speakers} speakers, {duration_sec}s")
        
        texts = [
            "Thank you for joining the call. Let's start with updates from each team.",
            "Our team completed the first phase on schedule.",
            "We encountered some challenges but found solutions.",
            "Next week we'll have the product review meeting.",
        ]
        
        mixed_audio = np.zeros(int(duration_sec * self.sample_rate), dtype=np.float32)
        
        # More structured, less overlapping than cafeteria
        for i in range(min(num_speakers, len(texts))):
            start_time = i * (duration_sec / num_speakers)
            speaker_audio = self._generate_synthetic_speech(texts[i])
            
            if len(speaker_audio) > 0:
                speaker_audio = normalize_signal(speaker_audio) * 0.75
                start_sample = int(start_time * self.sample_rate)
                mix_audio_at_offset(mixed_audio, speaker_audio, start_sample)

        return normalize_peak(mixed_audio)
    
    def add_background_noise(self, audio: np.ndarray, noise_type: str = "office", snr_db: float = 15.0) -> np.ndarray:
        """
        Add background noise to audio.
        
        Args:
            audio: Input audio array
            noise_type: "office", "traffic", "restaurant", "white", "pink"
            snr_db: Signal-to-noise ratio in dB
        
        Returns:
            Audio with added noise
        """
        logger.info(f"Adding {noise_type} noise at {snr_db:.1f} dB SNR")
        
        # Generate synthetic noise
        if noise_type == "white":
            noise = np.random.randn(len(audio))
        elif noise_type == "pink":
            # Simple pink noise approximation
            noise = np.random.randn(len(audio))
            b, a = [1.0], [1.0, -0.8]
            from scipy.signal import lfilter
            noise = lfilter(b, a, noise)
        elif noise_type == "office":
            # Mix of white noise and lower frequency components
            noise = np.random.randn(len(audio))
            office_tone = np.sin(2 * np.pi * 60 * np.arange(len(audio)) / self.sample_rate)
            noise = noise * 0.7 + office_tone * 0.3
        elif noise_type == "traffic":
            # Lower frequency noise
            noise = np.random.randn(len(audio))
            from scipy.signal import butter, filtfilt
            b, a = butter(4, [100, 2000], btype='band', fs=self.sample_rate)
            noise = filtfilt(b, a, noise)
        elif noise_type == "restaurant":
            # Mixture of speech-like and ambient noise
            noise = np.random.randn(len(audio)) * 0.6
            ambient = np.sin(2 * np.pi * np.arange(len(audio)) / (self.sample_rate / 200))
            noise = noise + ambient * 0.4
        else:
            noise = np.random.randn(len(audio))
        
        noise = normalize_signal(noise)
        noisy_audio = add_noise_at_snr(audio, noise, snr_db)

        max_val = np.max(np.abs(noisy_audio))
        if max_val > 1.0:
            noisy_audio = normalize_peak(noisy_audio)

        return noisy_audio
    
    def _generate_synthetic_speech(self, text: str) -> np.ndarray:
        """
        Generate synthetic speech for a text sample.
        
        Args:
            text: Text to synthesize
        
        Returns:
            Audio array
        """
        try:
            from src.audio.speech_synthesizer import SpeechSynthesizer
            
            # Randomly select voice for variety
            voices = ["male", "female", "neutral"]
            voice = np.random.choice(voices)
            
            synthesizer = SpeechSynthesizer(sample_rate=self.sample_rate, voice_profile=voice)
            audio = synthesizer.synthesize_text(text, emotion="neutral")
            return audio
        except Exception as e:
            logger.warning(f"Failed to synthesize speech: {e}. Using fallback.")
            return self._fallback_speech_signal(len(text) * 100)
    
    def _fallback_speech_signal(self, length: int) -> np.ndarray:
        """
        Generate fallback speech-like signal.
        
        Args:
            length: Length of signal in samples
        
        Returns:
            Synthetic speech-like audio
        """
        t = np.arange(length) / self.sample_rate
        
        # Mix of frequencies to simulate speech
        signal = np.zeros(length)
        signal += 0.3 * np.sin(2 * np.pi * 200 * t)  # Base frequency
        signal += 0.2 * np.sin(2 * np.pi * 400 * t)  # Formant
        signal += 0.15 * np.sin(2 * np.pi * 800 * t)  # Formant
        
        # Apply envelope for naturalism
        envelope = np.sin(np.pi * np.arange(length) / length) ** 2
        signal = signal * envelope
        
        return signal.astype(np.float32)
    
    def create_diversity_dataset(self, num_scenarios: int = 10) -> Dict[str, np.ndarray]:
        """
        Create diverse multi-speaker dataset.
        
        Args:
            num_scenarios: Number of scenarios to generate
        
        Returns:
            Dictionary of scenario names to audio arrays
        """
        logger.info(f"Generating diversity dataset with {num_scenarios} scenarios")
        
        scenarios = {}
        
        # Office meetings (3 scenarios, varying complexity)
        for i in range(2):
            num_speakers = 3 + i
            name = f"office_meeting_{num_speakers}speaker"
            scenarios[name] = self.create_office_meeting(num_speakers=num_speakers)
        
        # Crowded environments (2 scenarios)
        scenarios["cafeteria_quiet"] = self.create_crowded_cafeteria(num_speakers=3, duration_sec=10)
        scenarios["cafeteria_crowded"] = self.create_crowded_cafeteria(num_speakers=6, duration_sec=15)
        
        # Lecture scenarios (2 scenarios)
        scenarios["lecture_small"] = self.create_lecture_hall(num_speakers=2, duration_sec=15)
        scenarios["lecture_large"] = self.create_lecture_hall(num_speakers=4, duration_sec=20)
        
        # Phone conferences (2 scenarios)
        scenarios["phone_small"] = self.create_phone_conference(num_speakers=3, duration_sec=10)
        scenarios["phone_large"] = self.create_phone_conference(num_speakers=5, duration_sec=15)
        
        # Add edge cases (1 scenario)
        scenarios["high_overlap"] = self.create_crowded_cafeteria(num_speakers=8, duration_sec=12)
        
        return scenarios
    
    def save_dataset(self, scenarios: Dict[str, np.ndarray], output_dir: str = "datasets/multispeaker") -> None:
        """
        Save multi-speaker dataset to disk.
        
        Args:
            scenarios: Dictionary of scenario names to audio arrays
            output_dir: Output directory
        """
        os.makedirs(output_dir, exist_ok=True)
        
        for name, audio in scenarios.items():
            filename = os.path.join(output_dir, f"{name}.wav")
            
            # Convert to int16
            audio_int16 = np.int16(audio / np.max(np.abs(audio) + 1e-8) * 32767)
            
            wavfile.write(filename, self.sample_rate, audio_int16)
            logger.info(f"Saved: {filename} ({len(audio)/self.sample_rate:.1f}s)")


def create_evaluation_dataset(output_dir: str = "datasets/multispeaker") -> Dict[str, Dict[str, np.ndarray]]:
    """
    Create comprehensive multi-speaker evaluation dataset with clean and noisy versions.
    
    Args:
        output_dir: Directory to save dataset
    
    Returns:
        Dictionary with clean and noisy scenarios
    """
    logger.info("Creating comprehensive multi-speaker evaluation dataset")
    
    os.makedirs(output_dir, exist_ok=True)
    
    generator = MultiSpeakerScenarioGenerator(sample_rate=16000)
    
    # Generate base scenarios
    base_scenarios = generator.create_diversity_dataset(num_scenarios=10)
    
    dataset = {
        "clean": base_scenarios,
        "noisy_office": {},
        "noisy_cafeteria": {},
        "noisy_traffic": {},
        "noisy_restaurant": {},
    }
    
    # Add noisy versions
    for scenario_name, audio in base_scenarios.items():
        # Office noise scenarios
        dataset["noisy_office"][scenario_name] = generator.add_background_noise(audio, noise_type="office", snr_db=12)
        
        # Cafeteria noise
        dataset["noisy_cafeteria"][scenario_name] = generator.add_background_noise(audio, noise_type="restaurant", snr_db=10)
        
        # Traffic noise
        dataset["noisy_traffic"][scenario_name] = generator.add_background_noise(audio, noise_type="traffic", snr_db=8)
        
        # Restaurant/crowded noise
        dataset["noisy_restaurant"][scenario_name] = generator.add_background_noise(audio, noise_type="restaurant", snr_db=10)
    
    # Save all scenarios
    for condition_name, scenarios in dataset.items():
        condition_dir = os.path.join(output_dir, condition_name)
        generator.save_dataset(scenarios, condition_dir)
    
    logger.info(f"Saved {len(dataset)} conditions with {len(base_scenarios)} scenarios each")
    
    return dataset
