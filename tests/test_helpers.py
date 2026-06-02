"""Tests for src.utils.helpers module."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from src.utils.helpers import normalize_audio, denormalize_audio, get_audio_statistics


class TestNormalizeAudio:
    """Tests for normalize_audio."""

    def test_basic_normalization(self):
        signal = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000)).astype(np.float32)
        result = normalize_audio(signal, target_db=-20.0)
        rms = np.sqrt(np.mean(result ** 2))
        rms_db = 20 * np.log10(rms)
        assert abs(rms_db - (-20.0)) < 0.5

    def test_target_db_respected(self):
        signal = np.random.randn(16000).astype(np.float32) * 0.5
        for target in [-10.0, -30.0, -40.0]:
            result = normalize_audio(signal, target_db=target)
            rms = np.sqrt(np.mean(result ** 2))
            rms_db = 20 * np.log10(rms)
            assert abs(rms_db - target) < 0.5

    def test_silent_signal_no_error(self):
        signal = np.zeros(16000, dtype=np.float32)
        result = normalize_audio(signal, target_db=-20.0)
        assert result.shape == signal.shape
        # silent input stays essentially silent (rms clipped at 1e-10)

    def test_preserves_shape(self):
        signal = np.random.randn(8000).astype(np.float32)
        result = normalize_audio(signal)
        assert result.shape == signal.shape


class TestDenormalizeAudio:
    """Tests for denormalize_audio."""

    def test_returns_copy(self):
        signal = np.array([1.0, 2.0, 3.0])
        result = denormalize_audio(signal)
        assert np.array_equal(result, signal)
        # must be a copy, not the same object
        result[0] = 999.0
        assert signal[0] != 999.0

    def test_shape_preserved(self):
        signal = np.random.randn(4000)
        result = denormalize_audio(signal, reference_db=-30.0)
        assert result.shape == signal.shape


class TestGetAudioStatistics:
    """Tests for get_audio_statistics."""

    def test_keys_present(self):
        signal = np.random.randn(16000).astype(np.float32)
        stats = get_audio_statistics(signal)
        for key in ['rms', 'rms_db', 'peak', 'peak_db', 'crest_factor', 'mean', 'std']:
            assert key in stats

    def test_values_are_floats(self):
        signal = np.random.randn(16000).astype(np.float32)
        stats = get_audio_statistics(signal)
        for key, val in stats.items():
            assert isinstance(val, float), f"{key} should be float, got {type(val)}"

    def test_sine_wave_peak(self):
        t = np.linspace(0, 1, 16000)
        signal = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        stats = get_audio_statistics(signal)
        assert abs(stats['peak'] - 1.0) < 0.01

    def test_rms_of_unit_sine(self):
        t = np.linspace(0, 1, 16000)
        signal = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        stats = get_audio_statistics(signal)
        expected_rms = 1.0 / np.sqrt(2)
        assert abs(stats['rms'] - expected_rms) < 0.02

    def test_silence_statistics(self):
        signal = np.zeros(16000, dtype=np.float32)
        stats = get_audio_statistics(signal)
        assert stats['rms'] == 0.0
        assert stats['peak'] == 0.0
        assert stats['mean'] == 0.0
        assert stats['std'] == 0.0
