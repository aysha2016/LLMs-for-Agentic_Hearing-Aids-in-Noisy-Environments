"""Processing strategy library and presets."""

from typing import Dict, Optional
from dataclasses import dataclass
from src.audio.processor import AudioProcessingStrategy


@dataclass
class StrategyPreset:
    """Predefined processing strategy."""
    
    name: str
    description: str
    strategy: AudioProcessingStrategy


class ProcessingStrategyLibrary:
    """Library of predefined processing strategies."""
    
    def __init__(self):
        """Initialize strategy library."""
        self.presets = self._create_presets()
    
    def _create_presets(self) -> Dict[str, StrategyPreset]:
        """Create library of standard strategies."""
        return {
            "silence": StrategyPreset(
                name="Silence",
                description="Minimal processing for quiet environments",
                strategy=AudioProcessingStrategy(
                    noise_suppression_strength=0.1,
                    speech_enhancement_level=0.0,
                    dynamic_range_compression_ratio=1.0,
                    high_frequency_boost=0.0,
                    low_frequency_reduction=0.0,
                    adaptive_gain=1.0,
                    noise_gate_threshold=-60.0,
                    explanation="Minimal processing - environment is quiet"
                )
            ),
            "quiet_office": StrategyPreset(
                name="Quiet Office",
                description="Light processing for quiet office environments",
                strategy=AudioProcessingStrategy(
                    noise_suppression_strength=0.3,
                    speech_enhancement_level=0.3,
                    dynamic_range_compression_ratio=2.0,
                    high_frequency_boost=1.0,
                    low_frequency_reduction=-2.0,
                    adaptive_gain=1.0,
                    noise_gate_threshold=-45.0,
                    explanation="Light noise suppression with speech enhancement"
                )
            ),
            "busy_office": StrategyPreset(
                name="Busy Office",
                description="Moderate processing for busy office with background noise",
                strategy=AudioProcessingStrategy(
                    noise_suppression_strength=0.6,
                    speech_enhancement_level=0.5,
                    dynamic_range_compression_ratio=3.0,
                    high_frequency_boost=2.0,
                    low_frequency_reduction=-3.0,
                    adaptive_gain=1.1,
                    noise_gate_threshold=-40.0,
                    explanation="Moderate noise suppression for office chatter"
                )
            ),
            "crowded_restaurant": StrategyPreset(
                name="Crowded Restaurant",
                description="Strong processing for high-noise environments",
                strategy=AudioProcessingStrategy(
                    noise_suppression_strength=0.8,
                    speech_enhancement_level=0.7,
                    dynamic_range_compression_ratio=4.5,
                    high_frequency_boost=3.0,
                    low_frequency_reduction=-4.0,
                    adaptive_gain=1.2,
                    noise_gate_threshold=-35.0,
                    explanation="Strong speech extraction in very noisy environment"
                )
            ),
            "outdoor": StrategyPreset(
                name="Outdoor",
                description="Moderate processing for outdoor environments",
                strategy=AudioProcessingStrategy(
                    noise_suppression_strength=0.5,
                    speech_enhancement_level=0.4,
                    dynamic_range_compression_ratio=2.5,
                    high_frequency_boost=1.5,
                    low_frequency_reduction=-2.5,
                    adaptive_gain=1.0,
                    noise_gate_threshold=-42.0,
                    explanation="Balanced approach for outdoor noise"
                )
            ),
            "music": StrategyPreset(
                name="Music",
                description="Minimal processing to preserve music quality",
                strategy=AudioProcessingStrategy(
                    noise_suppression_strength=0.2,
                    speech_enhancement_level=0.1,
                    dynamic_range_compression_ratio=1.5,
                    high_frequency_boost=0.5,
                    low_frequency_reduction=-1.0,
                    adaptive_gain=1.0,
                    noise_gate_threshold=-50.0,
                    explanation="Preserve dynamic range for music listening"
                )
            ),
            "phone_call": StrategyPreset(
                name="Phone Call",
                description="Optimize for phone call clarity",
                strategy=AudioProcessingStrategy(
                    noise_suppression_strength=0.7,
                    speech_enhancement_level=0.8,
                    dynamic_range_compression_ratio=5.0,
                    high_frequency_boost=4.0,
                    low_frequency_reduction=-5.0,
                    adaptive_gain=1.3,
                    noise_gate_threshold=-38.0,
                    explanation="Optimize for telephone speech clarity"
                )
            ),
            "comfort_mode": StrategyPreset(
                name="Comfort Mode",
                description="Gentle processing prioritizing comfort over clarity",
                strategy=AudioProcessingStrategy(
                    noise_suppression_strength=0.4,
                    speech_enhancement_level=0.2,
                    dynamic_range_compression_ratio=2.0,
                    high_frequency_boost=0.5,
                    low_frequency_reduction=-1.0,
                    adaptive_gain=0.9,
                    noise_gate_threshold=-50.0,
                    explanation="Gentle processing for comfortable listening"
                )
            ),
        }
    
    def get_strategy(self, name: str) -> Optional[StrategyPreset]:
        """
        Get strategy by name.
        
        Args:
            name: Strategy name
        
        Returns:
            StrategyPreset or None if not found
        """
        return self.presets.get(name)
    
    def list_strategies(self) -> list:
        """Get list of all available strategy names."""
        return list(self.presets.keys())
    
    def get_preset_description(self, name: str) -> Optional[str]:
        """Get description of a preset."""
        preset = self.presets.get(name)
        return preset.description if preset else None
