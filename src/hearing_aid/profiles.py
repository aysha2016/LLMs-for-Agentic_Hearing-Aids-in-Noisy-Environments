"""User profile management."""

from dataclasses import dataclass, field
from typing import Dict, Optional, List


@dataclass
class UserProfile:
    """User hearing aid preferences and characteristics."""
    
    # Hearing characteristics
    hearing_loss_pattern: str = "flat"  # flat, high_frequency, low_frequency, sloping
    
    # Processing preferences
    preference: str = "balanced"  # clarity, comfort, balanced, natural
    power_mode: str = "normal"  # battery_saver, normal, performance
    background_noise_tolerance: str = "medium"  # low, medium, high
    
    # User settings
    user_id: Optional[str] = None
    name: Optional[str] = None
    
    # Adaptation settings
    learning_enabled: bool = True
    adaptation_speed: str = "medium"  # slow, medium, fast
    
    # Frequency preferences (dB adjustments)
    frequency_preferences: Dict[str, float] = field(default_factory=lambda: {
        "low": 0.0,
        "mid_low": 0.0,
        "mid_high": 0.0,
        "high": 0.0
    })
    
    # Usage patterns
    typical_environments: List[str] = field(default_factory=list)  # office, outdoor, home, etc.
    
    def to_dict(self) -> Dict:
        """Convert profile to dictionary."""
        return {
            "hearing_loss_pattern": self.hearing_loss_pattern,
            "preference": self.preference,
            "power_mode": self.power_mode,
            "background_noise_tolerance": self.background_noise_tolerance,
            "user_id": self.user_id,
            "name": self.name,
            "learning_enabled": self.learning_enabled,
            "adaptation_speed": self.adaptation_speed,
            "frequency_preferences": self.frequency_preferences,
            "typical_environments": self.typical_environments
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UserProfile":
        """Create profile from dictionary."""
        return cls(**data)


# Predefined profiles
PROFILE_CLARITY = UserProfile(
    hearing_loss_pattern="high_frequency",
    preference="clarity",
    background_noise_tolerance="low"
)

PROFILE_COMFORT = UserProfile(
    hearing_loss_pattern="flat",
    preference="comfort",
    background_noise_tolerance="high"
)

PROFILE_NATURAL = UserProfile(
    hearing_loss_pattern="flat",
    preference="natural",
    background_noise_tolerance="medium"
)

PROFILE_BATTERY_SAVER = UserProfile(
    hearing_loss_pattern="flat",
    preference="balanced",
    power_mode="battery_saver",
    adaptation_speed="slow"
)
