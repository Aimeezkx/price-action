"""Privacy service for data protection and sanitization."""

import re
from typing import Dict, List, Optional, Any, Pattern
from dataclasses import dataclass
from enum import Enum

try:
    from app.core.config import settings
except ImportError:
    # Fallback for testing
    class MockSettings:
        privacy_mode = False
    settings = MockSettings()


class PrivacyLevel(Enum):
    """Privacy protection levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class SanitizationRule:
    """Rule for data sanitization."""
    pattern: Pattern[str]
    replacement: str
    description: str
    privacy_level: PrivacyLevel


class PrivacyService:
    """Service for privacy protection and data sanitization."""
    
    def __init__(self):
        self.sanitization_rules = self._initialize_default_rules()
        self.custom_rules = {}
    
    def _initialize_default_rules(self) -> List[SanitizationRule]:
        """Initialize default sanitization rules."""
        return [
            # Email addresses
            SanitizationRule(
                pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                replacement='***@***.***',
                description='Email address',
                privacy_level=PrivacyLevel.LOW
            ),
            
            # Phone numbers (various formats)
            SanitizationRule(
                pattern=re.compile(r'\b\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
                replacement='***-***-****',
                description='Phone number',
                privacy_level=PrivacyLevel.LOW
            ),
            
            # Social Security Numbers
            SanitizationRule(
                pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                replacement='***-**-****',
                description='Social Security Number',
                privacy_level=PrivacyLevel.HIGH
            ),
            
            # Credit card numbers
            SanitizationRule(
                pattern=re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
                replacement='****-****-****-****',
                description='Credit card number',
                privacy_level=PrivacyLevel.HIGH
            ),
            
            # IP addresses
            SanitizationRule(
                pattern=re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
                replacement='***.***.***.***',
                description='IP address',
                privacy_level=PrivacyLevel.MEDIUM
            ),
            
            # Names (basic pattern - two capitalized words)
            SanitizationRule(
                pattern=re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'),
                replacement='*** ***',
                description='Person name',
                privacy_level=PrivacyLevel.MEDIUM
            ),
            
            # Dates (YYYY-MM-DD format)
            SanitizationRule(
                pattern=re.compile(r'\b\d{4}-\d{2}-\d{2}\b'),
                replacement='****-**-**',
                description='Date',
                privacy_level=PrivacyLevel.LOW
            ),
            
            # Medical record numbers
            SanitizationRule(
                pattern=re.compile(r'\b(?:MRN|MR|Medical Record)[\s#:]*\d+\b', re.IGNORECASE),
                replacement='MRN: [REDACTED]',
                description='Medical record number',
                privacy_level=PrivacyLevel.HIGH
            ),
            
            # Account numbers
            SanitizationRule(
                pattern=re.compile(r'\b(?:Account|Acct)[\s#:]*\d{6,}\b', re.IGNORECASE),
                replacement='Account: [REDACTED]',
                description='Account number',
                privacy_level=PrivacyLevel.MEDIUM
            ),
            
            # Driver's license numbers
            SanitizationRule(
                pattern=re.compile(r'\b(?:DL|License)[\s#:]*[A-Z0-9]{6,}\b', re.IGNORECASE),
                replacement='License: [REDACTED]',
                description='Driver license number',
                privacy_level=PrivacyLevel.HIGH
            ),
            
            # Addresses (basic pattern)
            SanitizationRule(
                pattern=re.compile(r'\b\d+\s+[A-Z][a-z]+\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court)\b', re.IGNORECASE),
                replacement='[ADDRESS REDACTED]',
                description='Street address',
                privacy_level=PrivacyLevel.MEDIUM
            ),
        ]
    
    def configure_sanitization_patterns(self, custom_patterns: Dict[str, str]):
        """Configure custom sanitization patterns."""
        self.custom_rules = {}
        for pattern_str, replacement in custom_patterns.items():
            try:
                pattern = re.compile(pattern_str)
                self.custom_rules[pattern_str] = SanitizationRule(
                    pattern=pattern,
                    replacement=replacement,
                    description=f'Custom pattern: {pattern_str}',
                    privacy_level=PrivacyLevel.MEDIUM
                )
            except re.error as e:
                # Log invalid pattern but don't fail
                print(f"Invalid regex pattern '{pattern_str}': {e}")
    
    def sanitize_content(self, content: str, privacy_level: PrivacyLevel = PrivacyLevel.MEDIUM) -> str:
        """Sanitize content based on privacy level."""
        if not content:
            return content
        
        sanitized = content
        
        # Apply default rules
        for rule in self.sanitization_rules:
            if rule.privacy_level.value <= privacy_level.value or privacy_level == PrivacyLevel.MAXIMUM:
                sanitized = rule.pattern.sub(rule.replacement, sanitized)
        
        # Apply custom rules
        for rule in self.custom_rules.values():
            if rule.privacy_level.value <= privacy_level.value or privacy_level == PrivacyLevel.MAXIMUM:
                sanitized = rule.pattern.sub(rule.replacement, sanitized)
        
        return sanitized
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove sensitive information."""
        if not filename:
            return filename
        
        # Apply sanitization rules to filename
        sanitized = self.sanitize_content(filename, PrivacyLevel.HIGH)
        
        # Additional filename-specific sanitization
        sensitive_keywords = [
            'medical', 'patient', 'confidential', 'private', 'personal',
            'ssn', 'social', 'security', 'tax', 'financial', 'bank',
            'credit', 'card', 'password', 'secret', 'classified'
        ]
        
        for keyword in sensitive_keywords:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            sanitized = pattern.sub('[REDACTED]', sanitized)
        
        return sanitized
    
    def sanitize_sql_query(self, query: str) -> str:
        """Sanitize SQL query for logging."""
        if not query:
            return query
        
        # Remove potential sensitive data from SQL queries
        sanitized = self.sanitize_content(query, PrivacyLevel.HIGH)
        
        # Replace string literals that might contain sensitive data
        sanitized = re.sub(r"'[^']*'", "'[REDACTED]'", sanitized)
        sanitized = re.sub(r'"[^"]*"', '"[REDACTED]"', sanitized)
        
        return sanitized
    
    def sanitize_api_response(self, response_data: Any) -> Any:
        """Sanitize API response data."""
        if isinstance(response_data, str):
            return self.sanitize_content(response_data)
        elif isinstance(response_data, dict):
            return {key: self.sanitize_api_response(value) for key, value in response_data.items()}
        elif isinstance(response_data, list):
            return [self.sanitize_api_response(item) for item in response_data]
        else:
            return response_data
    
    def detect_sensitive_data(self, content: str) -> List[Dict[str, Any]]:
        """Detect sensitive data in content."""
        detections = []
        
        for rule in self.sanitization_rules:
            matches = rule.pattern.finditer(content)
            for match in matches:
                detections.append({
                    'type': rule.description,
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'privacy_level': rule.privacy_level.value
                })
        
        return detections
    
    def is_privacy_mode_enabled(self) -> bool:
        """Check if privacy mode is enabled."""
        return getattr(settings, 'privacy_mode', False)
    
    def get_privacy_level(self) -> PrivacyLevel:
        """Get current privacy level."""
        if self.is_privacy_mode_enabled():
            return PrivacyLevel.MAXIMUM
        else:
            return PrivacyLevel.MEDIUM
    
    def sanitize_for_logging(self, data: Any, context: str = None) -> Any:
        """Sanitize data specifically for logging."""
        privacy_level = PrivacyLevel.HIGH if self.is_privacy_mode_enabled() else PrivacyLevel.MEDIUM
        
        if isinstance(data, str):
            sanitized = self.sanitize_content(data, privacy_level)
            
            # Additional context-specific sanitization
            if context == 'filename':
                sanitized = self.sanitize_filename(sanitized)
            elif context == 'sql':
                sanitized = self.sanitize_sql_query(sanitized)
            
            return sanitized
        elif isinstance(data, dict):
            return {key: self.sanitize_for_logging(value, context) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_for_logging(item, context) for item in data]
        else:
            return data
    
    def create_privacy_report(self, content: str) -> Dict[str, Any]:
        """Create privacy analysis report for content."""
        detections = self.detect_sensitive_data(content)
        
        # Group by type
        by_type = {}
        for detection in detections:
            type_name = detection['type']
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(detection)
        
        # Calculate risk score
        risk_score = 0
        for detection in detections:
            if detection['privacy_level'] == PrivacyLevel.HIGH.value:
                risk_score += 3
            elif detection['privacy_level'] == PrivacyLevel.MEDIUM.value:
                risk_score += 2
            else:
                risk_score += 1
        
        return {
            'total_detections': len(detections),
            'by_type': by_type,
            'risk_score': risk_score,
            'risk_level': self._calculate_risk_level(risk_score),
            'recommendations': self._get_privacy_recommendations(by_type)
        }
    
    def _calculate_risk_level(self, risk_score: int) -> str:
        """Calculate risk level based on score."""
        if risk_score >= 10:
            return 'HIGH'
        elif risk_score >= 5:
            return 'MEDIUM'
        elif risk_score > 0:
            return 'LOW'
        else:
            return 'NONE'
    
    def _get_privacy_recommendations(self, detections_by_type: Dict[str, List]) -> List[str]:
        """Get privacy recommendations based on detections."""
        recommendations = []
        
        if 'Social Security Number' in detections_by_type:
            recommendations.append('Consider enabling maximum privacy mode for documents containing SSNs')
        
        if 'Credit card number' in detections_by_type:
            recommendations.append('Financial information detected - ensure secure storage and transmission')
        
        if 'Medical record number' in detections_by_type:
            recommendations.append('Medical information detected - verify HIPAA compliance requirements')
        
        if 'Email address' in detections_by_type:
            recommendations.append('Email addresses detected - consider data retention policies')
        
        if len(detections_by_type) > 3:
            recommendations.append('Multiple types of sensitive data detected - consider comprehensive privacy review')
        
        return recommendations


# Global privacy service instance
privacy_service = PrivacyService()

# Alias for backward compatibility
privacy_manager = privacy_service