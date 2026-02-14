"""Neural Text-to-Speech synthesis using Google Text-to-Speech for realistic speech generation."""

import numpy as np
from scipy.io import wavfile
import logging
from typing import List, Dict, Tuple, Optional
import os
import tempfile

logger = logging.getLogger(__name__)

try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("gTTS not installed. Install with: pip install gtts")


class SpeechSynthesizer:
    """Synthesize realistic, natural-sounding speech using Google Text-to-Speech."""
    
    # Language codes for different voices
    VOICE_CONFIGS = {
        "male": {"lang": "en", "tld": "com"},
        "female": {"lang": "en", "tld": "com"},
        "neutral": {"lang": "en", "tld": "com"},
        "child": {"lang": "en", "tld": "com"},
    }
    
    def __init__(self, sample_rate: int = 16000, voice_profile: str = "neutral", use_gpu: bool = False):
        """
        Initialize Google TTS speech synthesizer for natural-sounding speech.
        
        Args:
            sample_rate: Audio sample rate in Hz (typically 16000)
            voice_profile: Voice type - "male", "female", "child", or "neutral"
            use_gpu: Ignored (Google TTS is cloud-based)
        """
        if not TTS_AVAILABLE:
            raise ImportError("gTTS not installed. Install with: pip install gtts")
        
        self.sample_rate = sample_rate
        self.voice_profile = voice_profile
        self.use_gpu = use_gpu
        
        # Store voice config
        self.voice_config = self.VOICE_CONFIGS.get(voice_profile, self.VOICE_CONFIGS["neutral"])
        
        logger.info(f"Speech synthesizer initialized with {voice_profile} voice at {sample_rate}Hz (using Google TTS)")

    
    def synthesize_text(self, text: str, emotion: str = "neutral", output_file: Optional[str] = None) -> np.ndarray:
        """
        Synthesize text to realistic speech audio using Google TTS.
        
        Args:
            text: Text to synthesize
            emotion: Emotion type - "neutral", "happy", "sad", "excited"
                    (applied through speech rate modulation)
            output_file: Optional file path to save the audio
        
        Returns:
            Audio array (numpy ndarray, float32)
        """
        try:
            logger.info(f"Synthesizing: '{text[:50]}...' ({emotion} emotion)")
            
            # Create temporary file for TTS output
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                # Modify text based on emotion
                emotion_text = self._apply_emotion_to_text(text, emotion)
                
                # Generate speech using Google TTS
                tts = gTTS(text=emotion_text, lang=self.voice_config["lang"], 
                          tld=self.voice_config["tld"], slow=False)
                tts.save(tmp_path)
                
                # Convert MP3 to WAV using scipy/librosa
                audio_float = self._convert_mp3_to_wav(tmp_path)
                
                # Resample if necessary
                if audio_float.shape[0] > 0 and self.sample_rate != 22050:
                    audio_float = self._resample(audio_float, 22050, self.sample_rate)
                
                # Apply additional emotion modulation
                if emotion != "neutral":
                    audio_float = self._apply_emotion(audio_float, emotion)
                
                # Save if requested
                if output_file:
                    audio_int16 = np.int16(audio_float / np.max(np.abs(audio_float) + 1e-5) * 32767)
                    wavfile.write(output_file, self.sample_rate, audio_int16)
                    logger.info(f"Saved synthesized speech to: {output_file}")
                
                return audio_float
            
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            raise
    
    def _apply_emotion_to_text(self, text: str, emotion: str) -> str:
        """
        Modify text based on emotion for more natural prosody.
        
        Args:
            text: Original text
            emotion: Emotion type
        
        Returns:
            Modified text
        """
        if emotion == "excited":
            # Add exclamation marks for excitement
            return text.rstrip('.!?') + '!'
        elif emotion == "sad":
            # Keep text as is but will be processed differently
            return text
        elif emotion == "happy":
            # Add friendly punctuation
            if text.endswith('.'):
                return text[:-1] + '!'
            return text
        return text
    
    def _convert_mp3_to_wav(self, mp3_path: str) -> np.ndarray:
        """
        Convert MP3 file to PCM audio array.
        
        Args:
            mp3_path: Path to MP3 file
        
        Returns:
            Audio array
        """
        try:
            # Try using scipy/librosa
            import librosa
            y, sr = librosa.load(mp3_path, sr=None)
            return y.astype(np.float32)
        except:
            try:
                # Fallback: use pydub if available
                from pydub import AudioSegment
                sound = AudioSegment.from_mp3(mp3_path)
                samples = np.array(sound.get_array_of_samples(), dtype=np.float32)
                if sound.channels == 2:
                    samples = samples.reshape((-1, 2)).mean(axis=1)
                samples = samples / (2 ** 15)  # Normalize
                return samples
            except:
                logger.error("Could not convert MP3. Please install librosa or pydub.")
                return np.array([], dtype=np.float32)
    
    def _apply_emotion(self, audio: np.ndarray, emotion: str) -> np.ndarray:
        """
        Apply emotional characteristics through pitch and amplitude modulation.
        
        Args:
            audio: Input audio array
            emotion: Emotion type
        
        Returns:
            Modified audio array
        """
        if emotion == "neutral":
            return audio
        
        emotion_params = {
            "neutral": {
                "pitch_shift": 1.0,
                "speed_factor": 1.0,
                "amplitude": 1.0,
            },
            "happy": {
                "pitch_shift": 0.8,      # Higher pitch
                "speed_factor": 1.1,    # Slightly faster
                "amplitude": 1.1,       # Slightly louder
            },
            "sad": {
                "pitch_shift": 1.2,     # Lower pitch
                "speed_factor": 0.95,   # Slightly slower
                "amplitude": 0.85,      # Quieter
            },
            "excited": {
                "pitch_shift": 0.7,     # Much higher pitch
                "speed_factor": 1.15,   # Much faster
                "amplitude": 1.2,       # Louder
            },
        }
        
        params = emotion_params.get(emotion, emotion_params["neutral"])
        
        # Apply pitch shift via simple resampling (pitch_shift > 1 = lower pitch)
        if params["pitch_shift"] != 1.0:
            audio = self._pitch_shift(audio, params["pitch_shift"])
        
        # Apply amplitude modulation
        audio = audio * params["amplitude"]
        
        # Clip to avoid distortion
        audio = np.clip(audio, -1.0, 1.0)
        
        return audio
    
    def _pitch_shift(self, audio: np.ndarray, factor: float) -> np.ndarray:
        """
        Simple pitch shift via resampling.
        
        Args:
            audio: Input audio
            factor: Pitch shift factor (>1 = lower pitch, <1 = higher pitch)
        
        Returns:
            Pitch-shifted audio
        """
        # Resample to change pitch
        new_length = int(len(audio) / factor)
        indices = np.linspace(0, len(audio) - 1, new_length)
        resampled = np.interp(indices, np.arange(len(audio)), audio)
        
        return resampled.astype(np.float32)
    
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Resample audio to target sample rate.
        
        Args:
            audio: Input audio
            orig_sr: Original sample rate
            target_sr: Target sample rate
        
        Returns:
            Resampled audio
        """
        if orig_sr == target_sr:
            return audio
        
        ratio = target_sr / orig_sr
        new_length = int(len(audio) * ratio)
        
        # Linear interpolation resampling
        indices = np.linspace(0, len(audio) - 1, new_length)
        resampled = np.interp(indices, np.arange(len(audio)), audio)
        
        return resampled.astype(np.float32)
    
    def synthesize_dialogue(self, dialogue: List[Tuple[str, str]]) -> Dict[str, np.ndarray]:
        """
        Synthesize multi-speaker dialogue.
        
        Args:
            dialogue: List of (speaker_name, text) tuples
        
        Returns:
            Dictionary mapping speaker names to audio arrays
        """
        results = {}
        voice_types = ["female", "male", "neutral", "child"]
        
        for i, (speaker, text) in enumerate(dialogue):
            voice_type = voice_types[i % len(voice_types)]
            try:
                synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type, use_gpu=self.use_gpu)
                audio = synthesizer.synthesize_text(text)
                results[speaker] = audio
                logger.info(f"Synthesized speech for {speaker} ({voice_type}): {len(text)} characters")
            except Exception as e:
                logger.error(f"Error synthesizing dialogue for {speaker}: {e}")
                results[speaker] = np.array([])
        
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
        logger.info(f"Synthesizing with context: {context}")
        return self.synthesize_text(text)


class SpeechScenarioGenerator:
    """Generate various speech scenarios with realistic neural TTS."""
    
    def __init__(self, sample_rate: int = 16000, use_gpu: bool = False):
        """
        Initialize scenario generator.
        
        Args:
            sample_rate: Audio sample rate
            use_gpu: Whether to use GPU
        """
        self.sample_rate = sample_rate
        self.use_gpu = use_gpu
        logger.info("Scenario generator initialized with Coqui TTS")
    
    def generate_conference_call(self) -> Dict[str, np.ndarray]:
        """Generate simulated conference call with different speakers."""
        dialogue = [
            ("Alice", "Thanks everyone for joining the call. Let's discuss the quarterly results.", "female"),
            ("Bob", "Sure, I've prepared some analysis on our market performance.", "male"),
            ("Carol", "And I have updates on the customer feedback and satisfaction metrics.", "female"),
        ]
        
        logger.info("Generating conference call scenario...")
        results = {}
        
        for speaker, text, voice_type in dialogue:
            try:
                synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type, use_gpu=self.use_gpu)
                audio = synthesizer.synthesize_text(text)
                results[speaker] = audio
                logger.info(f"  ✓ {speaker} ({voice_type}): {len(audio)/self.sample_rate:.1f}s")
            except Exception as e:
                logger.error(f"Error generating speech for {speaker}: {e}")
                results[speaker] = np.array([])
        
        return results
    
    def generate_casual_conversation(self) -> Dict[str, np.ndarray]:
        """Generate casual conversation with different voices."""
        dialogue = [
            ("Alice", "Hey, how was your weekend?", "female"),
            ("Bob", "It was great! I went hiking and visited a new coffee shop.", "male"),
            ("Alice", "That sounds fun. Did you take any photos?", "female"),
        ]
        
        logger.info("Generating casual conversation...")
        results = {}
        
        for speaker, text, voice_type in dialogue:
            try:
                synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type, use_gpu=self.use_gpu)
                audio = synthesizer.synthesize_text(text)
                results[speaker] = audio
                logger.info(f"  ✓ {speaker} ({voice_type}): {len(audio)/self.sample_rate:.1f}s")
            except Exception as e:
                logger.error(f"Error generating speech for {speaker}: {e}")
                results[speaker] = np.array([])
        
        return results
    
    def generate_presentation(self) -> Dict[str, np.ndarray]:
        """Generate formal presentation with professional voice."""
        text = (
            "Good morning everyone. Today I'm going to discuss the latest advancements in hearing aid technology. "
            "Modern hearing aids are becoming increasingly sophisticated with AI-powered features. "
            "They can now adapt to different acoustic environments in real time. "
            "This presentation will cover three main topics: signal processing, machine learning integration, and user experience."
        )
        
        logger.info("Generating formal presentation...")
        try:
            synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile="male", use_gpu=self.use_gpu)
            audio = synthesizer.synthesize_text(text)
            logger.info(f"  ✓ Generated {len(audio)/self.sample_rate:.1f}s of presentation")
            return {"presenter": audio}
        except Exception as e:
            logger.error(f"Error generating presentation: {e}")
            return {"presenter": np.array([])}
    
    def generate_phone_call(self) -> Dict[str, np.ndarray]:
        """Generate simulated phone call with different voices."""
        dialogue = [
            ("Caller", "Hi, I'm calling to confirm our meeting tomorrow at two PM.", "male"),
            ("Receiver", "Yes, that works for me. Should I bring the presentation files?", "female"),
            ("Caller", "That would be helpful. See you then.", "male"),
        ]
        
        logger.info("Generating phone call...")
        results = {}
        
        for speaker, text, voice_type in dialogue:
            try:
                synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type, use_gpu=self.use_gpu)
                audio = synthesizer.synthesize_text(text)
                results[speaker] = audio
                logger.info(f"  ✓ {speaker} ({voice_type}): {len(audio)/self.sample_rate:.1f}s")
            except Exception as e:
                logger.error(f"Error generating speech for {speaker}: {e}")
                results[speaker] = np.array([])
        
        return results
    
    def generate_reading(self) -> Dict[str, np.ndarray]:
        """Generate voice reading of text."""
        text = (
            "Hearing loss is one of the most common sensory disorders affecting millions of people worldwide. "
            "It can impact communication, social interaction, and overall quality of life. "
            "However, modern hearing aids with advanced signal processing can significantly improve hearing ability. "
            "The integration of artificial intelligence allows these devices to adapt intelligently to user preferences and environmental conditions."
        )
        
        logger.info("Generating reading...")
        try:
            synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile="female", use_gpu=self.use_gpu)
            audio = synthesizer.synthesize_text(text)
            logger.info(f"  ✓ Generated {len(audio)/self.sample_rate:.1f}s of reading")
            return {"narrator": audio}
        except Exception as e:
            logger.error(f"Error generating reading: {e}")
            return {"narrator": np.array([])}
    
    def generate_custom(self, text: str, scenario_name: str = "custom", 
                       voice_type: str = "neutral", emotion: str = "neutral") -> np.ndarray:
        """
        Generate custom speech scenario.
        
        Args:
            text: Text to synthesize
            scenario_name: Name of the scenario
            voice_type: "male", "female", "child", or "neutral"
            emotion: "neutral", "happy", "sad", or "excited"
        
        Returns:
            Audio array
        """
        logger.info(f"Generating custom scenario: {scenario_name}")
        try:
            synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type, use_gpu=self.use_gpu)
            audio = synthesizer.synthesize_text(text, emotion=emotion)
            logger.info(f"  ✓ Generated {len(audio)/self.sample_rate:.1f}s ({voice_type}, {emotion})")
            return audio
        except Exception as e:
            logger.error(f"Error generating custom scenario: {e}")
            return np.array([])
    
    def generate_emotional_variations(self, text: str) -> Dict[str, np.ndarray]:
        """Generate same text with different emotions."""
        emotions = ["neutral", "happy", "sad", "excited"]
        results = {}
        
        logger.info("Generating emotional variations...")
        try:
            synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile="female", use_gpu=self.use_gpu)
            for emotion in emotions:
                audio = synthesizer.synthesize_text(text, emotion=emotion)
                results[emotion] = audio
                logger.info(f"  ✓ {emotion}: {len(audio)/self.sample_rate:.1f}s")
        except Exception as e:
            logger.error(f"Error generating emotional variations: {e}")
            for emotion in emotions:
                results[emotion] = np.array([])
        
        return results
    
    def generate_voice_variations(self, text: str) -> Dict[str, np.ndarray]:
        """Generate same text in different voice types."""
        voices = ["male", "female", "child", "neutral"]
        results = {}
        
        logger.info("Generating voice variations...")
        for voice_type in voices:
            try:
                synthesizer = SpeechSynthesizer(self.sample_rate, voice_profile=voice_type, use_gpu=self.use_gpu)
                audio = synthesizer.synthesize_text(text)
                results[voice_type] = audio
                logger.info(f"  ✓ {voice_type}: {len(audio)/self.sample_rate:.1f}s")
            except Exception as e:
                logger.error(f"Error generating speech for {voice_type}: {e}")
                results[voice_type] = np.array([])
        
        return results


def create_noisy_speech(speech: np.ndarray, noise_type: str = "gaussian", snr_db: float = 10.0) -> np.ndarray:
    """
    Add noise to speech audio to simulate real-world conditions.
    
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
        # Pink noise approximation
        white = np.random.randn(len(speech))
        noise = np.cumsum(white) / len(speech) * 0.05
    
    elif noise_type == "office":
        # Simulate office background noise (HVAC, people, etc.)
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
