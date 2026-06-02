"""Tests for src.audio.multispeaker_dataset module."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import tempfile
import pytest
import numpy as np

from src.audio.multispeaker_dataset import MultiSpeakerScenarioGenerator


class TestMultiSpeakerScenarioGenerator:

    @pytest.fixture
    def gen(self):
        return MultiSpeakerScenarioGenerator(sample_rate=16000)

    # ---- _fallback_speech_signal ----

    def test_fallback_speech_signal_length(self, gen):
        signal = gen._fallback_speech_signal(8000)
        assert len(signal) == 8000

    def test_fallback_speech_signal_dtype(self, gen):
        signal = gen._fallback_speech_signal(4000)
        assert signal.dtype == np.float32

    def test_fallback_speech_signal_not_silent(self, gen):
        signal = gen._fallback_speech_signal(8000)
        assert np.max(np.abs(signal)) > 0

    # ---- create_office_meeting ----

    def test_create_office_meeting_shape(self, gen):
        audio = gen.create_office_meeting(num_speakers=3, duration_sec=5.0)
        expected_samples = int(5.0 * 16000)
        assert len(audio) == expected_samples

    def test_create_office_meeting_dtype(self, gen):
        audio = gen.create_office_meeting(num_speakers=2, duration_sec=3.0)
        assert audio.dtype == np.float32

    def test_create_office_meeting_not_silent(self, gen):
        audio = gen.create_office_meeting(num_speakers=2, duration_sec=3.0)
        assert np.max(np.abs(audio)) > 0

    def test_create_office_meeting_bounded(self, gen):
        audio = gen.create_office_meeting(num_speakers=4, duration_sec=5.0)
        assert np.max(np.abs(audio)) <= 1.0

    # ---- create_crowded_cafeteria ----

    def test_create_crowded_cafeteria_shape(self, gen):
        audio = gen.create_crowded_cafeteria(num_speakers=4, duration_sec=5.0)
        assert len(audio) == int(5.0 * 16000)

    def test_create_crowded_cafeteria_bounded(self, gen):
        audio = gen.create_crowded_cafeteria(num_speakers=4, duration_sec=5.0)
        assert np.max(np.abs(audio)) <= 1.0

    # ---- create_lecture_hall ----

    def test_create_lecture_hall_shape(self, gen):
        audio = gen.create_lecture_hall(num_speakers=2, duration_sec=10.0)
        assert len(audio) == int(10.0 * 16000)

    def test_create_lecture_hall_not_silent(self, gen):
        audio = gen.create_lecture_hall(num_speakers=2, duration_sec=10.0)
        assert np.max(np.abs(audio)) > 0

    # ---- create_phone_conference ----

    def test_create_phone_conference_shape(self, gen):
        audio = gen.create_phone_conference(num_speakers=3, duration_sec=8.0)
        assert len(audio) == int(8.0 * 16000)

    def test_create_phone_conference_bounded(self, gen):
        audio = gen.create_phone_conference(num_speakers=3, duration_sec=8.0)
        assert np.max(np.abs(audio)) <= 1.0

    # ---- add_background_noise ----

    def test_add_noise_white(self, gen):
        audio = np.random.randn(16000).astype(np.float32) * 0.5
        noisy = gen.add_background_noise(audio, noise_type="white", snr_db=10.0)
        assert noisy.shape == audio.shape
        assert not np.array_equal(noisy, audio)

    def test_add_noise_pink(self, gen):
        audio = np.random.randn(16000).astype(np.float32) * 0.5
        noisy = gen.add_background_noise(audio, noise_type="pink", snr_db=10.0)
        assert noisy.shape == audio.shape

    def test_add_noise_office(self, gen):
        audio = np.random.randn(16000).astype(np.float32) * 0.5
        noisy = gen.add_background_noise(audio, noise_type="office", snr_db=15.0)
        assert noisy.shape == audio.shape

    def test_add_noise_traffic(self, gen):
        audio = np.random.randn(16000).astype(np.float32) * 0.5
        noisy = gen.add_background_noise(audio, noise_type="traffic", snr_db=8.0)
        assert noisy.shape == audio.shape

    def test_add_noise_restaurant(self, gen):
        audio = np.random.randn(16000).astype(np.float32) * 0.5
        noisy = gen.add_background_noise(audio, noise_type="restaurant", snr_db=12.0)
        assert noisy.shape == audio.shape

    def test_add_noise_unknown_type(self, gen):
        audio = np.random.randn(16000).astype(np.float32) * 0.5
        noisy = gen.add_background_noise(audio, noise_type="unknown_type", snr_db=10.0)
        assert noisy.shape == audio.shape

    def test_add_noise_clipping_prevention(self, gen):
        audio = np.ones(16000, dtype=np.float32) * 0.9
        noisy = gen.add_background_noise(audio, noise_type="white", snr_db=0.0)
        assert np.max(np.abs(noisy)) <= 1.0

    # ---- save_dataset ----

    def test_save_dataset(self, gen):
        scenarios = {
            "test_scenario": np.random.randn(16000).astype(np.float32) * 0.5,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            gen.save_dataset(scenarios, output_dir=tmpdir)
            expected_file = os.path.join(tmpdir, "test_scenario.wav")
            assert os.path.exists(expected_file)
            assert os.path.getsize(expected_file) > 0

    # ---- create_diversity_dataset ----

    def test_create_diversity_dataset_returns_dict(self, gen):
        dataset = gen.create_diversity_dataset(num_scenarios=10)
        assert isinstance(dataset, dict)
        assert len(dataset) > 0

    def test_create_diversity_dataset_values_are_arrays(self, gen):
        dataset = gen.create_diversity_dataset(num_scenarios=10)
        for name, audio in dataset.items():
            assert isinstance(audio, np.ndarray), f"{name} should be ndarray"
            assert len(audio) > 0
