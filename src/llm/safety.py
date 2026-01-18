"""Safety validation for LLM decisions - Strict compliance enforcement."""

from typing import Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SafetyCheck:
    """Result of safety validation."""
    
    is_safe: bool
    violations: list
    warnings: list
    message: str


class SafetyValidator:
    """
    Validates LLM decisions for hearing aid safety.
    
    Enforces strict compliance with:
    - Parameter bounds (no waveform data, no DSP coefficients)
    - Reversibility requirements
    - Stability constraints (no rapid oscillation)
    - Explicit rationale requirement
    """
    
    # STRICT Parameter Bounds
    MAX_NOISE_SUPPRESSION = 0.95
    MIN_NOISE_SUPPRESSION = 0.0
    
    MAX_SPEECH_ENHANCEMENT = 0.9
    MIN_SPEECH_ENHANCEMENT = 0.0
    
    MAX_COMPRESSION_RATIO = 8.0
    MIN_COMPRESSION_RATIO = 1.0
    
    MAX_HIGH_FREQ_BOOST = 10.0  # dB
    MIN_HIGH_FREQ_BOOST = -0.5  # dB
    
    MAX_LOW_FREQ_REDUCTION = 0.0  # dB
    MIN_LOW_FREQ_REDUCTION = -12.0  # dB
    
    MAX_ADAPTIVE_GAIN = 2.0
    MIN_ADAPTIVE_GAIN = 0.3
    
    MIN_NOISE_GATE_THRESHOLD = -60.0
    MAX_NOISE_GATE_THRESHOLD = -10.0
    
    MIN_DECISION_DURATION = 10  # seconds (prevent oscillation)
    MAX_DECISION_DURATION = 3600  # seconds (max 1 hour without review)
    
    ALLOWED_FREQUENCY_PROFILES = {'neutral', 'speech_optimized', 'clarity_boost', 'comfort_focus'}
    
    def validate_strategy(self, strategy: Dict) -> SafetyCheck:
        """
        Validate proposed processing strategy for strict safety compliance.
        
        Checks:
        1. No raw waveform requests
        2. No DSP coefficient outputs
        3. All parameters within bounds
        4. Rationale provided
        5. Reversibility assured
        6. Duration respects constraints
        
        Args:
            strategy: Processing strategy from LLM
        
        Returns:
            SafetyCheck with validation results
        """
        violations = []
        warnings = []
        
        # 1. Check for prohibited content (raw audio requests)
        strategy_str = str(strategy).lower()
        prohibited_terms = [
            'raw audio', 'waveform', 'sample rate', 'fft', 'coefficient',
            'impulse response', 'filter design', 'dsp', 'digital signal'
        ]
        for term in prohibited_terms:
            if term in strategy_str:
                violations.append(f"CRITICAL: Prohibited term detected: '{term}'. "
                                f"LLM must never request raw audio or DSP coefficients.")
        
        # 2. Validate required fields
        required_fields = [
            'strategy_name',
            'noise_suppression_strength',
            'speech_enhancement_strength',
            'compression_ratio',
            'high_freq_boost_db',
            'rationale',
            'confidence',
            'duration_seconds',
            'is_reversible'
        ]
        
        for field in required_fields:
            if field not in strategy:
                violations.append(f"Missing required field: {field}")
        
        # Skip parameter checks if required fields are missing
        if violations:
            message = f"Safety validation FAILED: {len(violations)} critical violation(s)"
            return SafetyCheck(
                is_safe=False,
                violations=violations,
                warnings=warnings,
                message=message
            )
        
        # 3. Validate noise suppression strength
        ns = float(strategy.get('noise_suppression_strength', 0.5))
        if ns < self.MIN_NOISE_SUPPRESSION or ns > self.MAX_NOISE_SUPPRESSION:
            violations.append(f"Noise suppression out of bounds: {ns:.2f} "
                            f"(valid: [{self.MIN_NOISE_SUPPRESSION}, {self.MAX_NOISE_SUPPRESSION}])")
        
        # 4. Validate speech enhancement strength
        se = float(strategy.get('speech_enhancement_strength', 0.0))
        if se < self.MIN_SPEECH_ENHANCEMENT or se > self.MAX_SPEECH_ENHANCEMENT:
            violations.append(f"Speech enhancement out of bounds: {se:.2f} "
                            f"(valid: [{self.MIN_SPEECH_ENHANCEMENT}, {self.MAX_SPEECH_ENHANCEMENT}])")
        
        # 5. Validate compression ratio
        cr = float(strategy.get('compression_ratio', 1.0))
        if cr < self.MIN_COMPRESSION_RATIO or cr > self.MAX_COMPRESSION_RATIO:
            violations.append(f"Compression ratio out of bounds: {cr:.2f} "
                            f"(valid: [{self.MIN_COMPRESSION_RATIO}, {self.MAX_COMPRESSION_RATIO}])")
        
        # 6. Validate high frequency boost
        hfb = float(strategy.get('high_freq_boost_db', 0.0))
        if hfb < self.MIN_HIGH_FREQ_BOOST or hfb > self.MAX_HIGH_FREQ_BOOST:
            violations.append(f"High freq boost out of bounds: {hfb:.1f}dB "
                            f"(valid: [{self.MIN_HIGH_FREQ_BOOST}, {self.MAX_HIGH_FREQ_BOOST}])")
        
        # 7. Validate low frequency reduction
        lfr = float(strategy.get('low_freq_reduction_db', 0.0))
        if lfr < self.MIN_LOW_FREQ_REDUCTION or lfr > self.MAX_LOW_FREQ_REDUCTION:
            violations.append(f"Low freq reduction out of bounds: {lfr:.1f}dB "
                            f"(valid: [{self.MIN_LOW_FREQ_REDUCTION}, {self.MAX_LOW_FREQ_REDUCTION}])")
        
        # 8. Validate frequency profile
        fp = strategy.get('frequency_profile', 'neutral')
        if fp not in self.ALLOWED_FREQUENCY_PROFILES:
            violations.append(f"Invalid frequency_profile: {fp} "
                            f"(valid: {self.ALLOWED_FREQUENCY_PROFILES})")
        
        # 9. Validate confidence
        conf = float(strategy.get('confidence', 0.5))
        if conf < 0.0 or conf > 1.0:
            violations.append(f"Confidence out of bounds: {conf:.2f} (valid: [0.0, 1.0])")
        
        # 10. Validate duration
        dur = int(strategy.get('duration_seconds', 30))
        if dur < self.MIN_DECISION_DURATION:
            violations.append(f"Duration too short: {dur}s (minimum: {self.MIN_DECISION_DURATION}s) "
                            f"- prevents rapid oscillation")
        if dur > self.MAX_DECISION_DURATION:
            violations.append(f"Duration too long: {dur}s (maximum: {self.MAX_DECISION_DURATION}s)")
        
        # 11. Validate reversibility
        if not strategy.get('is_reversible', False):
            violations.append("CRITICAL: Strategy must be reversible. "
                            "All decisions must include revert capability.")
        
        # 12. Validate rationale
        rationale = strategy.get('rationale', '')
        if not isinstance(rationale, str) or len(rationale) < 20:
            violations.append("Rationale must be a clear explanation (minimum 20 characters)")
        
        # 13. Low confidence warning
        if conf < 0.5:
            warnings.append(f"Low confidence decision ({conf:.0%}). "
                          f"Recommend minimal intervention strategy.")
        
        # 14. High aggressiveness warning
        total_aggressiveness = ns + se + (cr - 1.0) / 7.0 + hfb / 10.0
        if total_aggressiveness > 2.0:
            warnings.append(f"High aggressiveness score ({total_aggressiveness:.1f}). "
                          f"Recommend more conservative strategy.")
        
        # Generate comprehensive message
        if violations:
            message = f"❌ Safety FAILED: {len(violations)} violation(s)"
            if warnings:
                message += f" + {len(warnings)} warning(s)"
            is_safe = False
        elif warnings:
            message = f"⚠️ Safety PASSED with {len(warnings)} warning(s)"
            is_safe = True
        else:
            message = "✅ Safety validation PASSED - All constraints respected"
            is_safe = True
        
        logger.log(
            logging.ERROR if violations else logging.WARNING if warnings else logging.INFO,
            message
        )
        
        return SafetyCheck(
            is_safe=is_safe,
            violations=violations,
            warnings=warnings,
            message=message
        )
    
    def apply_safety_bounds(self, strategy: Dict) -> Dict:
        """
        Enforce safety bounds on strategy, clipping values if needed.
        
        Should only be used as fallback after validation fails.
        Logs all corrections for audit trail.
        
        Args:
            strategy: Processing strategy
        
        Returns:
            Strategy with safety bounds applied
        """
        safe_strategy = strategy.copy()
        corrections = []
        
        # Apply bounds with logging
        original_ns = safe_strategy.get('noise_suppression_strength', 0.5)
        safe_strategy['noise_suppression_strength'] = max(
            self.MIN_NOISE_SUPPRESSION,
            min(self.MAX_NOISE_SUPPRESSION, float(original_ns))
        )
        if safe_strategy['noise_suppression_strength'] != original_ns:
            corrections.append(f"noise_suppression: {original_ns:.2f} → {safe_strategy['noise_suppression_strength']:.2f}")
        
        original_se = safe_strategy.get('speech_enhancement_strength', 0.0)
        safe_strategy['speech_enhancement_strength'] = max(
            self.MIN_SPEECH_ENHANCEMENT,
            min(self.MAX_SPEECH_ENHANCEMENT, float(original_se))
        )
        if safe_strategy['speech_enhancement_strength'] != original_se:
            corrections.append(f"speech_enhancement: {original_se:.2f} → {safe_strategy['speech_enhancement_strength']:.2f}")
        
        original_cr = safe_strategy.get('compression_ratio', 1.0)
        safe_strategy['compression_ratio'] = max(
            self.MIN_COMPRESSION_RATIO,
            min(self.MAX_COMPRESSION_RATIO, float(original_cr))
        )
        if safe_strategy['compression_ratio'] != original_cr:
            corrections.append(f"compression_ratio: {original_cr:.2f} → {safe_strategy['compression_ratio']:.2f}")
        
        original_hfb = safe_strategy.get('high_freq_boost_db', 0.0)
        safe_strategy['high_freq_boost_db'] = max(
            self.MIN_HIGH_FREQ_BOOST,
            min(self.MAX_HIGH_FREQ_BOOST, float(original_hfb))
        )
        if safe_strategy['high_freq_boost_db'] != original_hfb:
            corrections.append(f"high_freq_boost: {original_hfb:.1f} → {safe_strategy['high_freq_boost_db']:.1f}")
        
        original_lfr = safe_strategy.get('low_freq_reduction_db', 0.0)
        safe_strategy['low_freq_reduction_db'] = max(
            self.MIN_LOW_FREQ_REDUCTION,
            min(self.MAX_LOW_FREQ_REDUCTION, float(original_lfr))
        )
        if safe_strategy['low_freq_reduction_db'] != original_lfr:
            corrections.append(f"low_freq_reduction: {original_lfr:.1f} → {safe_strategy['low_freq_reduction_db']:.1f}")
        
        if corrections:
            logger.warning(f"Safety bounds applied - Corrections: {'; '.join(corrections)}")
        
        return safe_strategy
