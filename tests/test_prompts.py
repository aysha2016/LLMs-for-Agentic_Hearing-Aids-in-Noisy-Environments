"""Tests for src.llm.prompts module."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock
from src.llm.prompts import PromptBuilder
from src.audio.features import AudioFeatureSet


class TestPromptBuilder:
    """Tests for PromptBuilder."""

    @pytest.fixture
    def builder(self):
        return PromptBuilder()

    @pytest.fixture
    def builder_custom(self):
        return PromptBuilder(system_prompt="Custom system prompt")

    def test_default_system_prompt(self, builder):
        assert "expert audio processing" in builder.system_prompt
        assert "OBSERVE" in builder.system_prompt

    def test_custom_system_prompt(self, builder_custom):
        assert builder_custom.system_prompt == "Custom system prompt"

    # ---- _format_hearing_profile ----

    def test_format_hearing_profile_empty(self, builder):
        assert builder._format_hearing_profile({}) == "Normal hearing"

    def test_format_hearing_profile_none(self, builder):
        assert builder._format_hearing_profile(None) == "Normal hearing"

    def test_format_hearing_profile_with_losses(self, builder):
        profile = {"high": 15, "low": 0, "mid": 10}
        result = builder._format_hearing_profile(profile)
        assert "high: 15dB loss" in result
        assert "mid: 10dB loss" in result
        assert "low" not in result  # 0 dB loss should be excluded

    # ---- _format_recent_actions ----

    def test_format_recent_actions_empty(self, builder):
        assert builder._format_recent_actions([]) == "None"

    def test_format_recent_actions_with_dicts(self, builder):
        actions = [
            {"primary_action": {"strategy_name": "strategy_a"}},
            {"primary_action": {"strategy_name": "strategy_b"}},
        ]
        result = builder._format_recent_actions(actions)
        assert "strategy_a" in result
        assert "strategy_b" in result
        assert "→" in result

    def test_format_recent_actions_limits_to_3(self, builder):
        actions = [
            {"primary_action": {"strategy_name": f"s{i}"}} for i in range(10)
        ]
        result = builder._format_recent_actions(actions)
        # Should only include last 3
        assert "s7" in result
        assert "s8" in result
        assert "s9" in result

    def test_format_recent_actions_non_dict_items(self, builder):
        actions = ["not_a_dict", 42]
        result = builder._format_recent_actions(actions)
        assert result == "None"

    # ---- _format_feedback_summary ----

    def test_format_feedback_summary_empty(self, builder):
        assert builder._format_feedback_summary([]) == "No recent feedback"

    def test_format_feedback_summary_positive(self, builder):
        feedback = [
            {"satisfaction": 90},
            {"satisfaction": 80},
            {"satisfaction": 85},
        ]
        result = builder._format_feedback_summary(feedback)
        assert "positive" in result.lower()

    def test_format_feedback_summary_negative(self, builder):
        feedback = [
            {"satisfaction": 10},
            {"satisfaction": 20},
            {"satisfaction": 15},
        ]
        result = builder._format_feedback_summary(feedback)
        assert "negative" in result.lower()

    def test_format_feedback_summary_mixed(self, builder):
        feedback = [
            {"satisfaction": 50},
            {"satisfaction": 50},
        ]
        result = builder._format_feedback_summary(feedback)
        assert "mixed" in result.lower()

    # ---- _format_strategy ----

    def test_format_strategy(self, builder):
        strategy = {
            "noise_suppression_strength": 0.65,
            "speech_enhancement_strength": 0.4,
            "frequency_profile": "speech_optimized",
        }
        result = builder._format_strategy(strategy)
        assert "noise_suppression_strength: 0.65" in result
        assert "frequency_profile: speech_optimized" in result

    # ---- build_audio_context_prompt ----

    def test_build_audio_context_prompt_with_dict(self, builder):
        features = {
            "noise_level_db": 55.0,
            "speech_confidence": 0.75,
            "acoustic_scene": "restaurant",
            "sound_event_class": "speech",
            "is_silence": False,
        }
        user_profile = {
            "hearing_loss_profile": "Normal",
            "preference": "clarity",
            "power_mode": "normal",
            "noise_tolerance": "low",
        }
        prompt = builder.build_audio_context_prompt(features, user_profile)
        assert "55.0 dB" in prompt
        assert "75%" in prompt
        assert "restaurant" in prompt
        assert "clarity" in prompt

    def test_build_audio_context_prompt_with_feature_set(self, builder):
        feature_set = MagicMock()
        feature_set.to_dict.return_value = {
            "noise_level_db": 60.0,
            "speech_confidence": 0.5,
            "acoustic_scene": "office",
            "sound_event_class": "background_sound",
            "is_silence": False,
        }
        user_profile = {"preference": "balanced"}
        prompt = builder.build_audio_context_prompt(feature_set, user_profile)
        assert "60.0 dB" in prompt
        feature_set.to_dict.assert_called_once()

    def test_build_audio_context_prompt_nested_noise_level(self, builder):
        features = {
            "noise_level_db": {"value": 42.0},
            "speech_confidence": {"value": 0.9},
        }
        user_profile = {}
        prompt = builder.build_audio_context_prompt(features, user_profile)
        assert "42.0 dB" in prompt

    # ---- build_feedback_prompt ----

    def test_build_feedback_prompt(self, builder):
        features = MagicMock(spec=AudioFeatureSet)
        features.to_llm_context.return_value = "noise_level: 55 dB"
        user_profile = {
            "hearing_loss_pattern": "high_freq",
            "preference": "comfort",
        }
        feedback = "Too much noise suppression"
        prev_strategy = {
            "noise_suppression_strength": 0.8,
            "speech_enhancement_strength": 0.5,
        }
        prompt = builder.build_feedback_prompt(features, user_profile, feedback, prev_strategy)
        assert "Too much noise suppression" in prompt
        assert "noise_suppression_strength: 0.80" in prompt
        assert "high_freq" in prompt

    # ---- build_decision_prompt ----

    def test_build_decision_prompt(self, builder):
        observation = MagicMock()
        observation.acoustic_scene = "restaurant"
        observation.noise_level_db = 65.0
        observation.noise_type = "babble"
        observation.speech_presence = True
        observation.speech_confidence = 0.8
        observation.asr_transcript = "Hello there"
        observation.hearing_loss_profile = {"high": 10}
        observation.user_preference = "clarity"
        observation.listening_intent = "conversation"
        observation.device_state = {"battery_percent": 75}
        observation.recent_actions = []
        observation.feedback_history = []
        observation.temporal_context = {"time_of_day": "morning", "day_of_week": "Monday"}
        user_profile = {"preference": "clarity"}
        prompt = builder.build_decision_prompt(observation, user_profile)
        assert "restaurant" in prompt
        assert "65.0 dB" in prompt
        assert "Hello there" in prompt
        assert "strategy_name" in prompt
