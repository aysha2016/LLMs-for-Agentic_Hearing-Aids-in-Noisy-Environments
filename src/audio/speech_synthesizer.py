"""Synthetic speech synthesis module for hearing aid testing."""

import numpy as np
from scipy.io import wavfile
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class SpeechSynthesizer:
    """Synthesize realistic speech-like audio with multiple voice profiles."""
    
    def __init__(self, sample_rate: int = 16000, voice_profile: str = "neutral"):
        """
        Initialize speech synthesizer.
        
        Args:
            sample_rate: Audio sample rate in Hz
            voice_profile: Voice type - "male", "female", "child", or "neutral"
        """
        self.sample_rate = sample_rate
        self.voice_profile = voice_profile
        self._set_voice_parameters(voice_profile)
        logger.info(f"Speech synthesizer initialized at {sample_rate}Hz with {voice_profile} voice")
    
    def _set_voice_parameters(self, voice_profile: str):
        """Set voice characteristics based on profile."""
        profiles = {
            "male": {
                "f0_base": 100,      # Fundamental frequency base (Hz)
                "f0_range": 40,      # Variation range
                "f1_base": 700,      # First formant
                "f2_base": 1220,     # Second formant
                "f3_base": 2600,     # Third formant
            },
            "female": {
                "f0_base": 200,      # Higher pitch for female
                "f0_range": 60,
                "f1_base": 650,
                "f2_base": 1400,
                "f3_base": 2800,
            },
            "child": {
                "f0_base": 250,      # Even higher for child
                "f0_range": 80,
                "f1_base": 600,
                "f2_base": 1500,
                "f3_base": 3000,
            },
            "neutral": {
                "f0_base": 150,
                "f0_range": 50,
                "f1_base": 700,
                "f2_base": 1300,
                "f3_base": 2700,
            }
        }
        self.voice_params = profiles.get(voice_profile, profiles["neutral"])
    
    def synthesize_text(self, text: str, emotion: str = "neutral", output_file: str = None) -> np.ndarray:
        """
        Synthesize text to speech-like audio with emotion variation.
        
        Args:
            text: Text to synthesize (length determines duration)
            emotion: Emotion type - "neutral", "happy", "sad", "excited"
            output_file: Optional file to save audio
        
        Returns:
            Audio array (numpy ndarray)
        """
        try:
            # Duration based on character count
            duration = max(len(text) / 10, 0.5)
            num_samples = int(duration * self.sample_rate)
            t = np.linspace(0, duration, num_samples)
            
            # Generate speech-like audio with emotion
            audio = self._formant_synthesis(t, emotion)
            
            # Normalize
            audio_float = audio.astype(np.float32)
            
            # Save if requested
            if output_file:
                audio_int16 = np.int16(audio_float / np.max(np.abs(audio_float)) * 32767)
                wavfile.write(output_file, self.sample_rate, audio_int16)
                logger.info(f"Saved {emotion} synthesized speech to: {output_file}")
            
            return audio_float
        
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            raise
    
    def _formant_synthesis(self, t: np.ndarray, emotion: str = "neutral") -> np.ndarray:
        """
        Generate speech-like audio using formant synthesis with emotion.
        
        Args:
            t: Time array
            emotion: Emotion type affecting pitch contour and intensity
        
        Returns:
            Synthesized audio
        """
        # Get voice parameters
        f0_base = self.voice_params["f0_base"]
        f0_range = self.voice_params["f0_range"]
        
        # Emotion-based pitch modulation
        emotion_params = {
            "neutral": {"pitch_var": 0.3, "intensity": 0.8, "vibrato": 0.02},
            "happy": {"pitch_var": 0.6, "intensity": 0.9, "vibrato": 0.03},
            "sad": {"pitch_var": 0.1, "intensity": 0.6, "vibrato": 0.01},
            "excited": {"pitch_var": 0.8, "intensity": 1.0, "vibrato": 0.04},
        }
        emotion_cfg = emotion_params.get(emotion, emotion_params["neutral"])
        
        # Fundamental frequency with emotion-based variation
        f0_var = emotion_cfg["pitch_var"]
        f0 = f0_base + f0_range * (
            f0_var * np.sin(2 * np.pi * 0.5 * t) +  # Slow variation
            f0_var * 0.3 * np.sin(2 * np.pi * 1.5 * t)  # Faster variation
        )
        
        # Formant frequencies with variation
        f1 = self.voice_params["f1_base"] + 150 * np.sin(2 * np.pi * 0.3 * t)
        f2 = self.voice_params["f2_base"] + 200 * np.cos(2 * np.pi * 0.4 * t)
        f3 = self.voice_params["f3_base"] + 300 * np.sin(2 * np.pi * 0.2 * t)
        
        # Generate fundamental frequency component
        phase0 = 2 * np.pi * np.cumsum(f0) / self.sample_rate
        voiced = np.sin(phase0)
        
        # Add vibrato (natural pitch wobble)
        vibrato_depth = emotion_cfg["vibrato"]
        vibrato = vibrato_depth * np.sin(2 * np.pi * 5 * t)  # 5 Hz vibrato
        voiced *= (1 + vibrato)
        
        # Generate formant components
        phase1 = 2 * np.pi * np.cumsum(f1) / self.sample_rate
        phase2 = 2 * np.pi * np.cumsum(f2) / self.sample_rate
        phase3 = 2 * np.pi * np.cumsum(f3) / self.sample_rate
        
        formant1 = 0.3 * np.sin(phase1)
        formant2 = 0.2 * np.sin(phase2)
        formant3 = 0.1 * np.sin(phase3)
        
        # Combine components
        audio = voiced * (formant1 + formant2 + formant3)
        
        # Add consonant-like characteristics (noise bursts)
        noise = np.random.randn(len(t)) * 0.02
        audio += noise
        
        # Amplitude envelope with emotion
        envelope = np.ones_like(t)
        attack_time = int(0.05 * self.sample_rate)
        release_time = int(0.05 * self.sample_rate)
        
        # Attack phase
        envelope[:attack_time] = np.linspace(0, 1, attack_time)
        # Release phase
        envelope[-release_time:] = np.linspace(1, 0, release_time)
        
        # Mid-section dynamics based on emotion
        mid_start = attack_time
        mid_end = len(t) - release_time
        mid_length = mid_end - mid_start
        
        if emotion == "happy":
            # Increasing intensity for happy
            envelope[mid_start:mid_end] *= np.linspace(0.8, 1.0, mid_length)
        elif emotion == "sad":
            # Decreasing intensity for sad
            envelope[mid_start:mid_end] *= np.linspace(1.0, 0.7, mid_length)
        elif emotion == "excited":
            # Pulsing intensity for excited
            envelope[mid_start:mid_end] *= (0.8 + 0.2 * np.sin(2 * np.pi * 2 * t[mid_start:mid_end]))
        
        audio *= envelope
        
        # Apply intensity based on emotion
        audio *= emotion_cfg["intensity"]
        
        # Normalize to [-1, 1] range
        return audio / np.max(np.abs(audio)) * 0.8
    
    def synthesize_dialogue(self, dialogue: List[Tuple[str, str]]) -> Dict[str, np.ndarray]:
        """
        Synthesize multi-speaker dialogue.
        
        Args:
            dialogue: List of (speaker_name, text) tuples
        
        Returns:
            Dictionary mapping speaker names to audio arrays
        """
        results = {}
        for speaker, text in dialogue:
            audio = self.synthesize_text(text)
            results[speaker] = audio
            logger.info(f"Synthesized speech for {speaker}: {len(text)} characters")
        
        return results
    
    def synthesize_with_context(self, text: str, context: str) -> np.ndarray:
        """
        Synthesize text with context information.
        
        Args:
            text: Main text to synthesize
            context: Context description (e.g., "office meeting", "outdoor conversation")
        
        Returns:
            Audio array
        """
        logger.info(f"Context: {context}")
        return self.synthesize_text(text)
    
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        if orig_sr == target_sr:
            return audio
        
        ratio = target_sr / orig_sr
        new_length = int(len(audio) * ratio)
        
        # Simple linear interpolation resampling
        indices = np.linspace(0, len(audio) - 1, new_length)
        resampled = np.interp(indices, np.arange(len(audio)), audio)
        
        return resampled.astype(np.int16)


class SpeechScenarioGenerator:
    """Generate various speech scenarios with realistic voice variation."""
    
    def __init__(self, sample_rate: int = 16000):
        """Initialize scenario generator."""
        self.sample_rate = sample_rate
        logger.info("Scenario generator initialized with multiple voice profiles")
    
    def generate_conference_call(self) -> Dict[str, np.ndarray]:
        """Generate simulated conference call with different speakers."""
        dialogue = [
            ("Alice", "Thanks everyone for joining the call. Let's discuss the quarterly results.", "female", "neutral"),
            ("Bob", "Sure, I've prepared some analysis on our market performance.", "male", "neutral"),
            ("Carol", "And I have updates on the customer feedback and satisfaction metrics.", "female", "happy"),
        ]
        
        logger.info("Generating conference call scenario with multiple speakers...")
        results = {}
        for speaker, text, voice_type, emotion in dialogue:
            synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type)
            audio = synthesizer.synthesize_text(text, emotion=emotion)
            results[speaker] = audio
            logger.info(f"  • {speaker} ({voice_type}, {emotion}): Generated {len(audio)/self.sample_rate:.1f}s")
        
        return results
    
    def generate_casual_conversation(self) -> Dict[str, np.ndarray]:
        """Generate casual conversation with different voices."""
        dialogue = [
            ("Alice", "Hey, how was your weekend?", "female", "happy"),
            ("Bob", "It was great! I went hiking and visited a new coffee shop.", "male", "excited"),
            ("Alice", "That sounds fun. Did you take any photos?", "female", "neutral"),
        ]
        
        logger.info("Generating casual conversation with varied voices...")
        results = {}
        for speaker, text, voice_type, emotion in dialogue:
            synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type)
            audio = synthesizer.synthesize_text(text, emotion=emotion)
            results[speaker] = audio
            logger.info(f"  • {speaker} ({voice_type}, {emotion}): Generated {len(audio)/self.sample_rate:.1f}s")
        
        return results
    
    def generate_presentation(self) -> Dict[str, np.ndarray]:
        """Generate formal presentation with professional male voice."""
        text = (
            "Good morning everyone. Today I'm going to discuss the latest advancements in hearing aid technology. "
            "Modern hearing aids are becoming increasingly sophisticated with AI-powered features. "
            "They can now adapt to different acoustic environments in real time. "
            "This presentation will cover three main topics: signal processing, machine learning integration, and user experience."
        )
        
        logger.info("Generating formal presentation (male, neutral)...")
        synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile="male")
        audio = synthesizer.synthesize_text(text, emotion="neutral")
        logger.info(f"  Generated {len(audio)/self.sample_rate:.1f}s of presentation")
        
        return {"presenter": audio}
    
    def generate_phone_call(self) -> Dict[str, np.ndarray]:
        """Generate simulated phone call with different voices."""
        dialogue = [
            ("Caller", "Hi, I'm calling to confirm our meeting tomorrow at two PM.", "male", "neutral"),
            ("Receiver", "Yes, that works for me. Should I bring the presentation files?", "female", "neutral"),
            ("Caller", "That would be helpful. See you then.", "male", "neutral"),
        ]
        
        logger.info("Generating phone call with different speakers...")
        results = {}
        for speaker, text, voice_type, emotion in dialogue:
            synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type)
            audio = synthesizer.synthesize_text(text, emotion=emotion)
            results[speaker] = audio
            logger.info(f"  • {speaker} ({voice_type}): Generated {len(audio)/self.sample_rate:.1f}s")
        
        return results
    
    def generate_reading(self) -> Dict[str, np.ndarray]:
        """Generate voice reading of text in female voice."""
        text = (
            "Hearing loss is one of the most common sensory disorders affecting millions of people worldwide. "
            "It can impact communication, social interaction, and overall quality of life. "
            "However, modern hearing aids with advanced signal processing can significantly improve hearing ability. "
            "The integration of artificial intelligence allows these devices to adapt intelligently to user preferences and environmental conditions."
        )
        
        logger.info("Generating reading (female, neutral)...")
        synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile="female")
        audio = synthesizer.synthesize_text(text, emotion="neutral")
        logger.info(f"  Generated {len(audio)/self.sample_rate:.1f}s of reading")
        
        return {"narrator": audio}
    
    def generate_custom(self, text: str, scenario_name: str = "custom", 
                       voice_type: str = "neutral", emotion: str = "neutral") -> np.ndarray:
        """
        Generate custom speech scenario with voice and emotion control.
        
        Args:
            text: Text to synthesize
            scenario_name: Name of the scenario
            voice_type: "male", "female", "child", or "neutral"
            emotion: "neutral", "happy", "sad", or "excited"
        
        Returns:
            Audio array
        """
        logger.info(f"Generating custom scenario: {scenario_name} ({voice_type}, {emotion})")
        synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type)
        audio = synthesizer.synthesize_text(text, emotion=emotion)
        logger.info(f"  Generated {len(audio)/self.sample_rate:.1f}s")
        
        return audio
    
    def generate_emotional_variations(self, text: str) -> Dict[str, np.ndarray]:
        """Generate same text with different emotions."""
        emotions = ["neutral", "happy", "sad", "excited"]
        synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile="female")
        
        results = {}
        logger.info(f"Generating emotional variations of text...")
        for emotion in emotions:
            audio = synthesizer.synthesize_text(text, emotion=emotion)
            results[emotion] = audio
            logger.info(f"  • {emotion}: Generated {len(audio)/self.sample_rate:.1f}s")
        
        return results
    
    def generate_voice_variations(self, text: str) -> Dict[str, np.ndarray]:
        """Generate same text in different voice types."""
        voices = ["male", "female", "child", "neutral"]
        
        results = {}
        logger.info(f"Generating voice variations of text...")
        for voice_type in voices:
            synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type)
            audio = synthesizer.synthesize_text(text, emotion="neutral")
            results[voice_type] = audio
            logger.info(f"  • {voice_type}: Generated {len(audio)/self.sample_rate:.1f}s")
        
        return results


def create_noisy_speech(speech: np.ndarray, noise_type: str = "gaussian", snr_db: float = 10.0) -> np.ndarray:
    """
    Add noise to speech audio.
    
    Args:
        speech: Speech audio array
        noise_type: Type of noise ("gaussian", "pink", "office")
        snr_db: Signal-to-noise ratio in dB
    
    Returns:
        Noisy speech audio
    """
    if noise_type == "gaussian":
        noise = np.random.randn(len(speech)) * 0.1
    
    elif noise_type == "pink":
        # Simple pink noise approximation
        white = np.random.randn(len(speech))
        noise = np.cumsum(white) / len(speech) * 0.05
    
    elif noise_type == "office":
        # Simulate office background noise
        t = np.linspace(0, len(speech) / 16000, len(speech))
        noise = (
            0.05 * np.sin(2 * np.pi * 60 * t) +  # HVAC hum
            0.03 * np.sin(2 * np.pi * 120 * t) +  # AC ripple
            np.random.randn(len(speech)) * 0.02  # Random noise
        )
    else:
        noise = np.random.randn(len(speech)) * 0.05
    
    # Normalize noise to achieve desired SNR
    signal_power = np.mean(speech ** 2)
    noise_power = np.mean(noise ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_scaling = np.sqrt(signal_power / (snr_linear * noise_power))
    
    noisy_speech = speech + noise * noise_scaling
    
    return np.clip(noisy_speech, -1.0, 1.0).astype(np.float32)
