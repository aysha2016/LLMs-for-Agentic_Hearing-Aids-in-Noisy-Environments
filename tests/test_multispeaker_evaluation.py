"""Tests for src.audio.multispeaker_evaluation module."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
import tempfile
import pytest
import numpy as np
from dataclasses import asdict

from src.audio.multispeaker_evaluation import (
    EvaluationMetrics,
    MultiSpeakerEvaluator,
    export_metrics_to_csv,
    export_metrics_to_json,
)


# ---- EvaluationMetrics dataclass ----

class TestEvaluationMetrics:

    def _make_metrics(self, **overrides):
        defaults = dict(
            scenario_name="office_meeting",
            condition="clean",
            duration_sec=10.0,
            snr_db=None,
            signal_power=0.01,
            noise_power=None,
            noise_level_db=-40.0,
            zero_crossing_rate=0.15,
            spectral_centroid_hz=2000.0,
            spectral_spread_hz=500.0,
            rms_level_db=-20.0,
            peak_level_db=-6.0,
            dynamic_range_db=14.0,
            crest_factor=4.0,
            spectral_complexity=3.0,
            temporal_complexity=0.5,
            speech_probability=0.7,
            num_speakers_estimated=2,
            intelligibility_estimate=0.75,
        )
        defaults.update(overrides)
        return EvaluationMetrics(**defaults)

    def test_creation(self):
        m = self._make_metrics()
        assert m.scenario_name == "office_meeting"
        assert m.condition == "clean"

    def test_asdict(self):
        m = self._make_metrics()
        d = asdict(m)
        assert isinstance(d, dict)
        assert d["scenario_name"] == "office_meeting"
        assert d["intelligibility_estimate"] == 0.75


# ---- MultiSpeakerEvaluator ----

class TestMultiSpeakerEvaluator:

    @pytest.fixture
    def evaluator(self):
        return MultiSpeakerEvaluator(sample_rate=16000)

    @pytest.fixture
    def speech_like_signal(self):
        """Generate speech-like signal with formant frequencies."""
        sr = 16000
        t = np.linspace(0, 1, sr, dtype=np.float32)
        signal = (
            0.3 * np.sin(2 * np.pi * 200 * t)
            + 0.2 * np.sin(2 * np.pi * 800 * t)
            + 0.1 * np.sin(2 * np.pi * 2000 * t)
        )
        return signal.astype(np.float32)

    def test_evaluate_audio_returns_metrics(self, evaluator, speech_like_signal):
        metrics = evaluator.evaluate_audio(speech_like_signal, "test_scenario", "clean")
        assert isinstance(metrics, EvaluationMetrics)
        assert metrics.scenario_name == "test_scenario"
        assert metrics.condition == "clean"

    def test_evaluate_audio_duration(self, evaluator, speech_like_signal):
        metrics = evaluator.evaluate_audio(speech_like_signal, "test", "clean")
        assert abs(metrics.duration_sec - 1.0) < 0.01

    def test_evaluate_audio_rms_reasonable(self, evaluator, speech_like_signal):
        metrics = evaluator.evaluate_audio(speech_like_signal, "test", "clean")
        assert metrics.rms_level_db < 0
        assert metrics.rms_level_db > -100

    def test_evaluate_audio_noisy_has_snr(self, evaluator, speech_like_signal):
        metrics = evaluator.evaluate_audio(speech_like_signal, "test", "noisy_office")
        assert metrics.snr_db is not None

    def test_evaluate_audio_clean_no_snr(self, evaluator, speech_like_signal):
        metrics = evaluator.evaluate_audio(speech_like_signal, "test", "clean")
        assert metrics.snr_db is None

    def test_spectral_centroid_positive(self, evaluator, speech_like_signal):
        metrics = evaluator.evaluate_audio(speech_like_signal, "test", "clean")
        assert metrics.spectral_centroid_hz > 0

    def test_zero_crossing_rate_bounded(self, evaluator, speech_like_signal):
        metrics = evaluator.evaluate_audio(speech_like_signal, "test", "clean")
        assert 0 <= metrics.zero_crossing_rate <= 1.0

    def test_intelligibility_bounded(self, evaluator, speech_like_signal):
        metrics = evaluator.evaluate_audio(speech_like_signal, "test", "clean")
        assert 0 <= metrics.intelligibility_estimate <= 1.0

    def test_num_speakers_positive(self, evaluator, speech_like_signal):
        metrics = evaluator.evaluate_audio(speech_like_signal, "test", "clean")
        assert metrics.num_speakers_estimated >= 1

    # ---- Private helper methods ----

    def test_estimate_noise_level(self, evaluator, speech_like_signal):
        noise_level = evaluator._estimate_noise_level(speech_like_signal)
        assert isinstance(noise_level, (float, np.floating))
        assert noise_level < 10  # should be a reasonable dB value

    def test_estimate_noise_level_short_signal(self, evaluator):
        # Very short signal (< 1 frame)
        signal = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        noise_level = evaluator._estimate_noise_level(signal)
        assert noise_level == -80.0

    def test_estimate_speech_probability(self, evaluator, speech_like_signal):
        prob = evaluator._estimate_speech_probability(speech_like_signal)
        assert 0 <= prob <= 1.0

    def test_estimate_speech_probability_empty(self, evaluator):
        signal = np.array([], dtype=np.float32)
        prob = evaluator._estimate_speech_probability(signal)
        assert prob == 0.0

    def test_estimate_num_speakers(self, evaluator, speech_like_signal):
        n = evaluator._estimate_num_speakers(speech_like_signal, spectral_complexity=2.0)
        assert n >= 1

    def test_estimate_num_speakers_high_complexity(self, evaluator, speech_like_signal):
        n = evaluator._estimate_num_speakers(speech_like_signal, spectral_complexity=4.0)
        assert n >= 1

    def test_estimate_intelligibility(self, evaluator, speech_like_signal):
        score = evaluator._estimate_intelligibility(
            speech_like_signal, speech_probability=0.8, spectral_centroid=2000.0
        )
        assert 0 <= score <= 1.0

    # ---- compare_conditions ----

    def test_compare_conditions(self, evaluator, speech_like_signal):
        clean = evaluator.evaluate_audio(speech_like_signal, "scenario", "clean")
        noisy_signal = speech_like_signal + np.random.randn(len(speech_like_signal)).astype(np.float32) * 0.3
        noisy = evaluator.evaluate_audio(noisy_signal, "scenario", "noisy")
        comparison = evaluator.compare_conditions([clean], [noisy])
        assert "clean" in comparison
        assert "noisy" in comparison
        assert "degradation" in comparison

    # ---- generate_summary ----

    def test_generate_summary(self, evaluator, speech_like_signal):
        metrics1 = evaluator.evaluate_audio(speech_like_signal, "s1", "clean")
        metrics2 = evaluator.evaluate_audio(speech_like_signal, "s2", "noisy")
        summary = evaluator.generate_summary([metrics1, metrics2])
        assert summary["total_scenarios"] == 2
        assert "avg_intelligibility" in summary
        assert "conditions" in summary


# ---- Export functions ----

class TestExportFunctions:

    def _make_metrics(self):
        return EvaluationMetrics(
            scenario_name="test",
            condition="clean",
            duration_sec=1.0,
            snr_db=None,
            signal_power=0.01,
            noise_power=None,
            noise_level_db=-40.0,
            zero_crossing_rate=0.15,
            spectral_centroid_hz=2000.0,
            spectral_spread_hz=500.0,
            rms_level_db=-20.0,
            peak_level_db=-6.0,
            dynamic_range_db=14.0,
            crest_factor=4.0,
            spectral_complexity=3.0,
            temporal_complexity=0.5,
            speech_probability=0.7,
            num_speakers_estimated=2,
            intelligibility_estimate=0.75,
        )

    def test_export_to_csv(self):
        metrics = [self._make_metrics()]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            filepath = f.name
        try:
            export_metrics_to_csv(metrics, filepath)
            assert os.path.exists(filepath)
            with open(filepath) as f:
                content = f.read()
            assert "scenario_name" in content
            assert "test" in content
        finally:
            os.unlink(filepath)

    def test_export_to_csv_empty(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            filepath = f.name
        try:
            export_metrics_to_csv([], filepath)
            # Should not create the file content (just returns)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_export_to_json(self):
        metrics = [self._make_metrics()]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name
        try:
            export_metrics_to_json(metrics, filepath)
            assert os.path.exists(filepath)
            with open(filepath) as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["scenario_name"] == "test"
        finally:
            os.unlink(filepath)
