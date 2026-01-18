"""Main hearing aid controller."""

import numpy as np
import time
from typing import Dict, Optional
import logging

from src.audio.extractor import AudioFeatureExtractor
from src.audio.processor import AudioProcessor, AudioProcessingStrategy
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
        llm_api_key: Optional[str] = None
    ):
        """
        Initialize hearing aid controller.
        
        Args:
            model_name: LLM model to use for decisions
            sample_rate: Audio sample rate in Hz
            user_profile: User profile (creates default if None)
            llm_api_key: API key for LLM service
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
        
        # State
        self.current_strategy: Optional[AudioProcessingStrategy] = None
        self.last_decision_time: Optional[float] = None
        self.decision_interval: float = 1.0  # Seconds between decisions
        self.processing_enabled = True
    
    def process_audio(
        self,
        audio_stream: np.ndarray,
        use_llm_decision: bool = True,
        force_decision: bool = False
    ) -> Dict:
        """
        Process audio stream through the hearing aid system.
        
        Args:
            audio_stream: Audio signal as numpy array
            use_llm_decision: Whether to use LLM for strategy selection
            force_decision: Force new decision even if within interval
        
        Returns:
            Dictionary with processing results
        """
        if not self.processing_enabled:
            return {
                "status": "disabled",
                "processed_audio": audio_stream,
                "strategy": None
            }
        
        # Extract features
        features = self.feature_extractor.extract_features(
            audio_stream,
            duration_ms=(len(audio_stream) / self.sample_rate) * 1000
        )
        features.timestamp = time.time()
        
        # Decide on strategy
        should_decide = force_decision or self._should_make_decision()
        
        if should_decide and use_llm_decision:
            strategy_dict = self.decision_engine.decide_strategy(
                features,
                self.user_profile.to_dict()
            )
            self.current_strategy = self._dict_to_strategy(strategy_dict)
            self.last_decision_time = time.time()
        elif not self.current_strategy:
            # Use default strategy if none selected yet
            self.current_strategy = self.strategy_library.get_strategy("quiet_office").strategy
        
        # Apply processing
        processed_audio = self.audio_processor.apply_strategy(
            audio_stream,
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
        # Extract features
        features = self.feature_extractor.extract_features(
            audio_stream,
            duration_ms=(len(audio_stream) / self.sample_rate) * 1000
        )
        features.timestamp = time.time()
        
        # Get current strategy as dict
        current_strategy_dict = self._strategy_to_dict(self.current_strategy)
        
        # Refine strategy based on feedback
        refined_strategy_dict = self.decision_engine.refine_strategy(
            features,
            self.user_profile.to_dict(),
            user_feedback,
            current_strategy_dict
        )
        
        self.current_strategy = self._dict_to_strategy(refined_strategy_dict)
        self.last_decision_time = time.time()
        
        # Apply refined processing
        processed_audio = self.audio_processor.apply_strategy(
            audio_stream,
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
