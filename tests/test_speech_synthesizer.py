"""Tests for src.audio.speech_synthesizer module."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.audio.speech_synthesizer import (
    SpeechSynthesizer,
    SpeechScenarioGenerator,
    create_noisy_speech,
)


# ---- SpeechSynthesizer ----

class TestSpeechSynthesizer:

    def test_init_default(self):
        synth = SpeechSynthesizer()
        assert synth.sample_rate == 16000
        assert synth.voice_profile == "neutral"

    def test_init_custom(self):
        synth = SpeechSynthesizer(sample_rate=22050, voice_profile="male")
        assert synth.sample_rate == 22050
        assert synth.voice_profile == "male"

    def test_voice_config_lookup(self):
        for voice in ["male", "female", "neutral", "child"]:
            synth = SpeechSynthesizer(voice_profile=voice)
            assert synth.voice_config["lang"] == "en"

    def test_unknown_voice_falls_back_to_neutral(self):
        synth = SpeechSynthesizer(voice_profile="robot")
        assert synth.voice_config == SpeechSynthesizer.VOICE_CONFIGS["neutral"]

    # ---- _apply_emotion_to_text ----

    def test_apply_emotion_neutral(self):
        synth = SpeechSynthesizer()
        assert synth._apply_emotion_to_text("Hello.", "neutral") == "Hello."

    def test_apply_emotion_excited(self):
        synth = SpeechSynthesizer()
        result = synth._apply_emotion_to_text("Hello.", "excited")
        assert result.endswith("!")

    def test_apply_emotion_happy_replaces_period(self):
        synth = SpeechSynthesizer()
        result = synth._apply_emotion_to_text("Hello.", "happy")
        assert result == "Hello!"

    def test_apply_emotion_happy_no_period(self):
        synth = SpeechSynthesizer()
        result = synth._apply_emotion_to_text("Hello", "happy")
        assert result == "Hello"

    def test_apply_emotion_sad_unchanged(self):
        synth = SpeechSynthesizer()
        result = synth._apply_emotion_to_text("Hello.", "sad")
        assert result == "Hello."

    # ---- _pitch_shift ----

    def test_pitch_shift_identity(self):
        synth = SpeechSynthesizer()
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000)).astype(np.float32)
        result = synth._pitch_shift(audio, factor=1.0)
        assert len(result) == len(audio)

    def test_pitch_shift_higher(self):
        synth = SpeechSynthesizer()
        audio = np.random.randn(16000).astype(np.float32)
        result = synth._pitch_shift(audio, factor=0.8)
        # factor < 1 → higher pitch → longer output
        assert len(result) > len(audio)

    def test_pitch_shift_lower(self):
        synth = SpeechSynthesizer()
        audio = np.random.randn(16000).astype(np.float32)
        result = synth._pitch_shift(audio, factor=1.2)
        # factor > 1 → lower pitch → shorter output
        assert len(result) < len(audio)

    def test_pitch_shift_dtype(self):
        synth = SpeechSynthesizer()
        audio = np.random.randn(16000).astype(np.float32)
        result = synth._pitch_shift(audio, factor=0.9)
        assert result.dtype == np.float32

    # ---- _resample ----

    def test_resample_same_rate(self):
        synth = SpeechSynthesizer()
        audio = np.random.randn(16000).astype(np.float32)
        result = synth._resample(audio, 16000, 16000)
        assert np.array_equal(result, audio)

    def test_resample_downsample(self):
        synth = SpeechSynthesizer()
        audio = np.random.randn(16000).astype(np.float32)
        result = synth._resample(audio, 16000, 8000)
        assert len(result) == 8000

    def test_resample_upsample(self):
        synth = SpeechSynthesizer()
        audio = np.random.randn(8000).astype(np.float32)
        result = synth._resample(audio, 8000, 16000)
        assert len(result) == 16000

    def test_resample_dtype(self):
        synth = SpeechSynthesizer()
        audio = np.random.randn(16000).astype(np.float32)
        result = synth._resample(audio, 16000, 22050)
        assert result.dtype == np.float32

    # ---- _apply_emotion ----

    def test_apply_emotion_audio_neutral(self):
        synth = SpeechSynthesizer()
        audio = np.random.randn(16000).astype(np.float32)
        result = synth._apply_emotion(audio, "neutral")
        assert np.array_equal(result, audio)

    def test_apply_emotion_audio_happy(self):
        synth = SpeechSynthesizer()
        audio = np.random.randn(16000).astype(np.float32) * 0.5
        result = synth._apply_emotion(audio, "happy")
        # happy → amplitude 1.1, so output should be louder
        assert not np.array_equal(result, audio)

    def test_apply_emotion_audio_clips(self):
        synth = SpeechSynthesizer()
        audio = np.ones(1000, dtype=np.float32) * 0.95
        result = synth._apply_emotion(audio, "excited")
        assert np.all(result <= 1.0)
        assert np.all(result >= -1.0)

    def test_apply_emotion_unknown_uses_neutral(self):
        synth = SpeechSynthesizer()
        audio = np.random.randn(1000).astype(np.float32) * 0.5
        result = synth._apply_emotion(audio, "unknown_emotion")
        # unknown → neutral params → no pitch shift, amplitude=1.0
        assert np.allclose(np.clip(audio, -1.0, 1.0), result, atol=1e-6)


# ---- SpeechScenarioGenerator ----

class TestSpeechScenarioGenerator:

    def test_init(self):
        gen = SpeechScenarioGenerator(sample_rate=16000)
        assert gen.sample_rate == 16000
        assert gen.use_gpu is False


# ---- create_noisy_speech ----

class TestCreateNoisySpeech:

    @pytest.fixture
    def speech(self):
        t = np.linspace(0, 1, 16000, dtype=np.float32)
        return np.sin(2 * np.pi * 440 * t)

    def test_gaussian_noise(self, speech):
        noisy = create_noisy_speech(speech, noise_type="gaussian", snr_db=10.0)
        assert noisy.shape == speech.shape
        assert noisy.dtype == np.float32
        assert not np.array_equal(noisy, speech)

    def test_pink_noise(self, speech):
        noisy = create_noisy_speech(speech, noise_type="pink", snr_db=10.0)
        assert noisy.shape == speech.shape
        assert noisy.dtype == np.float32

    def test_office_noise(self, speech):
        noisy = create_noisy_speech(speech, noise_type="office", snr_db=10.0)
        assert noisy.shape == speech.shape
        assert noisy.dtype == np.float32

    def test_unknown_noise_type(self, speech):
        noisy = create_noisy_speech(speech, noise_type="whatever", snr_db=10.0)
        assert noisy.shape == speech.shape

    def test_output_clipped(self, speech):
        noisy = create_noisy_speech(speech, noise_type="gaussian", snr_db=-10.0)
        assert np.all(noisy >= -1.0)
        assert np.all(noisy <= 1.0)

    def test_high_snr_similar_to_original(self, speech):
        noisy = create_noisy_speech(speech, noise_type="gaussian", snr_db=100.0)
        # At very high SNR, noisy should be close to original
        correlation = np.corrcoef(speech, noisy)[0, 1]
        assert correlation > 0.99
