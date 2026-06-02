"""Main hearing aid controller."""

import numpy as np
import time
from typing import Dict, Optional
import logging

from src.audio.extractor import AudioFeatureExtractor
from src.audio.processor import AudioProcessor, AudioProcessingStrategy
from src.audio.neural_denoiser import NeuralDenoiser
from src.audio.denoising_integration import HybridDenoiser
from src.llm.decision_engine import DecisionEngine
from src.hearing_aid.profiles import UserProfile
from src.hearing_aid.strategies import ProcessingStrategyLibrary


logger = logging.getLogger(__name__)


class HearingAidController:
    """
    Main controller for hearing aid system.
    
    Coordinates audio feature extraction, LLM decision making, and audio processing.
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4",
        sample_rate: int = 16000,
        user_profile: Optional[UserProfile] = None,
        llm_api_key: Optional[str] = None,
        denoiser_model_path: Optional[str] = "models/neural_denoiser.pt",
        denoiser_device: str = "cpu",
        enable_neural_denoising: bool = True
    ):
        """
        Initialize hearing aid controller.
        
        Args:
            model_name: LLM model to use for decisions
            sample_rate: Audio sample rate in Hz
            user_profile: User profile (creates default if None)
            llm_api_key: API key for LLM service
            denoiser_model_path: Path to neural denoiser weights (optional)
            denoiser_device: Device for denoiser inference
            enable_neural_denoising: Enable neural denoising pre-processing
        """
        self.sample_rate = sample_rate
        self.user_profile = user_profile or UserProfile()
        
        # Initialize components
        self.feature_extractor = AudioFeatureExtractor(sample_rate=sample_rate)
        self.audio_processor = AudioProcessor(sample_rate=sample_rate)
        self.decision_engine = DecisionEngine(
            model_name=model_name,
            api_key=llm_api_key,
            enable_safety=True
        )
        self.strategy_library = ProcessingStrategyLibrary()

        # Optional neural denoising pre-processing
        self.denoiser: Optional[HybridDenoiser] = None
        if enable_neural_denoising:
            try:
                neural = NeuralDenoiser(
                    sample_rate=sample_rate,
                    model_path=denoiser_model_path,
                    device=denoiser_device
                )
                self.denoiser = HybridDenoiser(
                    neural_denoiser=neural,
                    use_neural=True,
                    fallback_to_spectral=True
                )
            except Exception as exc:
                logger.warning(f"Neural denoiser init failed: {exc}. Using DSP-only processing.")
        
        # State
        self.current_strategy: Optional[AudioProcessingStrategy] = None
        self.last_decision_time: Optional[float] = None
        self.decision_interval: float = 1.0  # Seconds between decisions
        self.processing_enabled = True
    
    def process_audio(
        self,
        audio_stream: np.ndarray,
        use_llm_decision: bool = True,
        force_decision: bool = False,
        use_speaker_separation: bool = False,
        sep_n_sources: int = 2,
        sep_preference: str = "loudest",
    ) -> Dict:
        """
        Process audio stream through the hearing aid system.

        Supports optional speaker separation when multiple voices are present.

        Args:
            audio_stream: Audio signal as numpy array
            use_llm_decision: Whether to use LLM for strategy selection
            force_decision: Force new decision even if within interval
            use_speaker_separation: If True, separate input into multiple sources
            sep_n_sources: Number of sources to estimate during separation
            sep_preference: If separation is used, choose one stream according to
                this preference when returning a single output.

        Returns:
            Dictionary with processing results.  When separation is enabled the
            returned object includes additional keys:
                - "separated_streams": list of source audio arrays
                - "processed_streams": list of processed audio arrays
                - "chosen_index": index of stream matching ``sep_preference``
                - "chosen_audio": the chosen processed stream
        """
        if not self.processing_enabled:
            return {
                "status": "disabled",
                "processed_audio": audio_stream,
                "strategy": None
            }

        # optionally perform speaker separation first
        if use_speaker_separation:
            try:
                from src.audio.speech_separation import (
                    separate_sources, select_preferred_source
                )

                sources = separate_sources(
                    audio_stream,
                    self.sample_rate,
                    n_sources=sep_n_sources,
                )
            except Exception as exc:  # pragma: no cover - separation may fail
                logger.warning(f"Speaker separation failed: {exc}")
                use_speaker_separation = False
                sources = []

            if use_speaker_separation:
                processed_list = []
                strategy_list = []
                features_list = []

                # process each source independently through the regular pipeline
                for src in sources:
                    # feature extraction for this source
                    feats = self.feature_extractor.extract_features(
                        src,
                        duration_ms=(len(src) / self.sample_rate) * 1000
                    )
                    feats.timestamp = time.time()
                    features_list.append(feats)

                    # optional denoising on component
                    src_for_proc = src
                    if self.denoiser is not None:
                        try:
                            src_for_proc = self.denoiser.denoise(
                                src,
                                suppression_strength=0.9
                            )
                        except Exception as exc:  # pragma: no cover
                            logger.warning(f"Neural denoising failed on component: {exc}")
                            src_for_proc = src

                    # choose strategy for component
                    if (force_decision or self._should_make_decision()) and use_llm_decision:
                        strat_dict = self.decision_engine._decide_strategy_llm(
                            feats,
                            self.user_profile.to_dict()
                        )
                        strat_dict = self._clamp_strategy_dict(strat_dict)
                        strat = self._dict_to_strategy(strat_dict)
                        # store strat when first component decided
                        if not self.current_strategy:
                            self.current_strategy = strat
                        self.last_decision_time = time.time()
                    else:
                        strat = self.current_strategy or self.strategy_library.get_strategy("quiet_office").strategy

                    strategy_list.append(strat)

                    processed_comp = self.audio_processor.apply_strategy(
                        src_for_proc,
                        strat
                    )
                    processed_list.append(processed_comp)

                # determine chosen stream by preference
                try:
                    chosen_audio = select_preferred_source(
                        processed_list,
                        self.sample_rate,
                        preference=sep_preference,
                    )
                    chosen_index = next(
                        i for i, s in enumerate(processed_list) if np.allclose(s, chosen_audio, atol=1e-6)
                    )
                except Exception as exc:
                    logger.warning(f"Preferred source selection failed: {exc}. Falling back to first stream.")
                    chosen_index = 0
                    chosen_audio = processed_list[0] if processed_list else np.array([])

                return {
                    "status": "success",
                    "separated_streams": sources,
                    "processed_streams": processed_list,
                    "chosen_index": chosen_index,
                    "chosen_audio": chosen_audio,
                    "processed_audio": processed_list if processed_list else audio_stream,
                    "strategies": strategy_list,
                    "audio_features": features_list,
                    "decision_made": True,
                }

        # --- regular processing when separation not used ---
        # Extract features from original audio for decision-making
        features = self.feature_extractor.extract_features(
            audio_stream,
            duration_ms=(len(audio_stream) / self.sample_rate) * 1000
        )
        features.timestamp = time.time()

        # Optional denoising before DSP processing
        audio_for_processing = audio_stream
        if self.denoiser is not None:
            try:
                audio_for_processing = self.denoiser.denoise(
                    audio_stream,
                    suppression_strength=0.9
                )
            except Exception as exc:
                logger.warning(f"Neural denoising failed: {exc}. Using raw audio.")

        # Decide on strategy
        should_decide = force_decision or self._should_make_decision()

        if should_decide and use_llm_decision:
            strategy_dict = self.decision_engine._decide_strategy_llm(
                features,
                self.user_profile.to_dict()
            )
            strategy_dict = self._clamp_strategy_dict(strategy_dict)
            self.current_strategy = self._dict_to_strategy(strategy_dict)
            self.last_decision_time = time.time()
        elif not self.current_strategy:
            # Use default strategy if none selected yet
            self.current_strategy = self.strategy_library.get_strategy("quiet_office").strategy

        # Apply processing
        processed_audio = self.audio_processor.apply_strategy(
            audio_for_processing,
            self.current_strategy
        )

        # Return results
        return {
            "status": "success",
            "processed_audio": processed_audio,
            "strategy": self.current_strategy,
            "audio_features": features,
            "decision_made": should_decide
        }
    
    def process_audio_with_feedback(
        self,
        audio_stream: np.ndarray,
        user_feedback: str
    ) -> Dict:
        """
        Process audio and refine strategy based on user feedback.
        
        Args:
            audio_stream: Audio signal
            user_feedback: User's feedback on processing
        
        Returns:
            Dictionary with processing results
        """
        # Extract features from original audio for decision-making
        features = self.feature_extractor.extract_features(
            audio_stream,
            duration_ms=(len(audio_stream) / self.sample_rate) * 1000
        )
        features.timestamp = time.time()

        # Optional denoising before DSP processing
        audio_for_processing = audio_stream
        if self.denoiser is not None:
            try:
                audio_for_processing = self.denoiser.denoise(
                    audio_stream,
                    suppression_strength=0.9
                )
            except Exception as exc:
                logger.warning(f"Neural denoising failed: {exc}. Using raw audio.")
        
        # Get current strategy as dict
        current_strategy_dict = self._strategy_to_dict(self.current_strategy)
        
        # Refine strategy based on feedback
        refined_strategy_dict = self.decision_engine.refine_strategy(
            features,
            self.user_profile.to_dict(),
            user_feedback,
            current_strategy_dict
        )

        refined_strategy_dict = self._clamp_strategy_dict(refined_strategy_dict)
        self.current_strategy = self._dict_to_strategy(refined_strategy_dict)
        self.last_decision_time = time.time()
        
        # Apply refined processing
        processed_audio = self.audio_processor.apply_strategy(
            audio_for_processing,
            self.current_strategy
        )
        
        return {
            "status": "success",
            "processed_audio": processed_audio,
            "strategy": self.current_strategy,
            "audio_features": features,
            "feedback_applied": True
        }
    
    def set_user_profile(self, profile: UserProfile):
        """Update user profile."""
        self.user_profile = profile
        logger.info(f"User profile updated: {profile.name or 'Unknown'}")
    
    def select_strategy_preset(self, preset_name: str) -> bool:
        """
        Manually select a strategy preset.
        
        Args:
            preset_name: Name of strategy preset
        
        Returns:
            True if successful, False otherwise
        """
        preset = self.strategy_library.get_strategy(preset_name)
        if preset:
            self.current_strategy = preset.strategy
            logger.info(f"Strategy preset selected: {preset_name}")
            return True
        else:
            logger.warning(f"Strategy preset not found: {preset_name}")
            return False
    
    def enable_processing(self):
        """Enable audio processing."""
        self.processing_enabled = True
        logger.info("Audio processing enabled")
    
    def disable_processing(self):
        """Disable audio processing (passthrough mode)."""
        self.processing_enabled = False
        logger.info("Audio processing disabled")
    
    def get_system_status(self) -> Dict:
        """Get current system status."""
        return {
            "processing_enabled": self.processing_enabled,
            "current_strategy": self.current_strategy.explanation if self.current_strategy else None,
            "user_profile": self.user_profile.name or "Default",
            "decision_engine_summary": self.decision_engine.get_decision_summary(),
            "available_presets": self.strategy_library.list_strategies()
        }
    
    def _should_make_decision(self) -> bool:
        """Check if enough time has passed to make new decision."""
        if self.last_decision_time is None:
            return True
        
        elapsed = time.time() - self.last_decision_time
        return elapsed >= self.decision_interval
    
    def _dict_to_strategy(self, strategy_dict: Dict) -> AudioProcessingStrategy:
        """Convert dictionary to AudioProcessingStrategy."""
        return AudioProcessingStrategy(
            noise_suppression_strength=strategy_dict.get('noise_suppression_strength', 0.5),
            speech_enhancement_level=strategy_dict.get('speech_enhancement_level', 0.5),
            dynamic_range_compression_ratio=strategy_dict.get('dynamic_range_compression_ratio', 1.0),
            frequency_emphasis=strategy_dict.get('frequency_emphasis'),
            high_frequency_boost=strategy_dict.get('high_frequency_boost', 0.0),
            low_frequency_reduction=strategy_dict.get('low_frequency_reduction', 0.0),
            adaptive_gain=strategy_dict.get('adaptive_gain', 1.0),
            noise_gate_threshold=strategy_dict.get('noise_gate_threshold', -40.0),
            explanation=strategy_dict.get('rationale', '')
        )

    def _clamp_strategy_dict(self, strategy_dict: Dict) -> Dict:
        """Clamp LLM strategy values to conservative bounds for natural speech."""
        clamped = dict(strategy_dict)

        def clamp(value: float, low: float, high: float) -> float:
            return max(low, min(high, value))

        clamped['noise_suppression_strength'] = clamp(
            float(clamped.get('noise_suppression_strength', 0.5)), 0.0, 0.65
        )
        clamped['speech_enhancement_level'] = clamp(
            float(clamped.get('speech_enhancement_level', 0.3)), 0.0, 0.5
        )
        clamped['dynamic_range_compression_ratio'] = clamp(
            float(clamped.get('dynamic_range_compression_ratio', 1.0)), 1.0, 3.0
        )
        clamped['high_frequency_boost'] = clamp(
            float(clamped.get('high_frequency_boost', 0.0)), -0.5, 2.0
        )
        clamped['low_frequency_reduction'] = clamp(
            float(clamped.get('low_frequency_reduction', 0.0)), -4.0, 0.0
        )
        clamped['adaptive_gain'] = clamp(
            float(clamped.get('adaptive_gain', 1.0)), 0.8, 1.2
        )
        clamped['noise_gate_threshold'] = clamp(
            float(clamped.get('noise_gate_threshold', -45.0)), -55.0, -25.0
        )

        return clamped
    
    def _strategy_to_dict(self, strategy: Optional[AudioProcessingStrategy]) -> Dict:
        """Convert AudioProcessingStrategy to dictionary."""
        if strategy is None:
            return {}
        
        return {
            'noise_suppression_strength': strategy.noise_suppression_strength,
            'speech_enhancement_level': strategy.speech_enhancement_level,
            'dynamic_range_compression_ratio': strategy.dynamic_range_compression_ratio,
            'frequency_emphasis': strategy.frequency_emphasis,
            'high_frequency_boost': strategy.high_frequency_boost,
            'low_frequency_reduction': strategy.low_frequency_reduction,
            'adaptive_gain': strategy.adaptive_gain,
            'noise_gate_threshold': strategy.noise_gate_threshold,
            'rationale': strategy.explanation
        }
