"""
Privacy-compliant external service integration
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from app.core.config import settings
from app.utils.logging import SecurityLogger

security_logger = SecurityLogger(__name__)


class PrivacyCompliantService:
    """Base class for privacy-compliant external service integration"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{__name__}.{service_name}")
    
    def is_privacy_mode_enabled(self) -> bool:
        """Check if privacy mode is enabled"""
        return settings.privacy_mode
    
    async def call_external_service(self, data: Any, endpoint: str) -> Optional[Any]:
        """Call external service with privacy checks"""
        if self.is_privacy_mode_enabled():
            self.logger.info(f"Privacy mode enabled - skipping external service call to {endpoint}")
            return None
        
        # Log the external service call
        security_logger.log_security_event(
            "external_service_call",
            {
                "service": self.service_name,
                "endpoint": endpoint,
                "data_type": type(data).__name__
            },
            "INFO"
        )
        
        # In a real implementation, this would make the actual API call
        # For now, return None to indicate no external processing
        return None


class LLMService(PrivacyCompliantService):
    """Privacy-compliant LLM service integration"""
    
    def __init__(self):
        super().__init__("llm_service")
    
    async def extract_knowledge(self, text: str, document_id: UUID) -> Optional[List[Dict[str, Any]]]:
        """Extract knowledge using LLM with privacy compliance"""
        if self.is_privacy_mode_enabled():
            self.logger.info("Privacy mode enabled - using local knowledge extraction")
            return await self._local_knowledge_extraction(text)
        
        # In non-privacy mode, would call external LLM API
        self.logger.info("Privacy mode disabled - would call external LLM API")
        return await self._local_knowledge_extraction(text)  # Fallback for now
    
    async def _local_knowledge_extraction(self, text: str) -> List[Dict[str, Any]]:
        """Local knowledge extraction as fallback"""
        # Simple rule-based extraction for privacy mode
        knowledge_points = []
        
        # Look for definition patterns
        import re
        
        # Pattern: "X is Y" or "X means Y"
        definition_patterns = [
            r'([A-Z][a-zA-Z\s]+)\s+is\s+([^.]+\.)',
            r'([A-Z][a-zA-Z\s]+)\s+means\s+([^.]+\.)',
            r'([A-Z][a-zA-Z\s]+):\s+([^.]+\.)'
        ]
        
        for pattern in definition_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                if len(term) > 2 and len(definition) > 10:
                    knowledge_points.append({
                        "kind": "definition",
                        "text": f"{term}: {definition}",
                        "entities": [term],
                        "confidence": 0.7
                    })
        
        return knowledge_points


class OCRService(PrivacyCompliantService):
    """Privacy-compliant OCR service integration"""
    
    def __init__(self):
        super().__init__("ocr_service")
    
    async def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """Extract text from image with privacy compliance"""
        if self.is_privacy_mode_enabled():
            self.logger.info("Privacy mode enabled - skipping OCR processing")
            return None
        
        # In non-privacy mode, would call external OCR API
        self.logger.info("Privacy mode disabled - would call external OCR API")
        return None  # No OCR processing for now


class EmbeddingService(PrivacyCompliantService):
    """Privacy-compliant embedding service"""
    
    def __init__(self):
        super().__init__("embedding_service")
        self._local_model = None
    
    async def generate_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings with privacy compliance"""
        if self.is_privacy_mode_enabled():
            return await self._local_embeddings(texts)
        
        # In non-privacy mode, could use external embedding API
        return await self._local_embeddings(texts)  # Use local for now
    
    async def _local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model"""
        try:
            # Import here to avoid loading if not needed
            from sentence_transformers import SentenceTransformer
            
            if self._local_model is None:
                self.logger.info("Loading local embedding model")
                self._local_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            # Generate embeddings
            embeddings = self._local_model.encode(texts)
            return embeddings.tolist()
            
        except ImportError:
            self.logger.error("sentence-transformers not available for local embeddings")
            return [[0.0] * 384 for _ in texts]  # Return zero vectors as fallback
        except Exception as e:
            self.logger.error(f"Error generating local embeddings: {e}")
            return [[0.0] * 384 for _ in texts]


class PrivacyManager:
    """Central privacy management"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.ocr_service = OCRService()
        self.embedding_service = EmbeddingService()
    
    def get_privacy_status(self) -> Dict[str, Any]:
        """Get current privacy configuration status"""
        return {
            "privacy_mode": settings.privacy_mode,
            "anonymize_logs": settings.anonymize_logs,
            "use_llm": settings.use_llm,
            "enable_file_scanning": settings.enable_file_scanning,
            "external_services": {
                "llm": not settings.privacy_mode and settings.use_llm,
                "ocr": not settings.privacy_mode,
                "embeddings": "local_only"
            }
        }
    
    async def process_with_privacy_compliance(self, operation: str, data: Any, **kwargs) -> Any:
        """Process data with privacy compliance"""
        if settings.privacy_mode:
            security_logger.log_security_event(
                "privacy_mode_processing",
                {
                    "operation": operation,
                    "data_type": type(data).__name__
                },
                "INFO"
            )
        
        # Route to appropriate service based on operation
        if operation == "extract_knowledge":
            return await self.llm_service.extract_knowledge(data, kwargs.get('document_id'))
        elif operation == "ocr_image":
            return await self.ocr_service.extract_text_from_image(data)
        elif operation == "generate_embeddings":
            return await self.embedding_service.generate_embeddings(data)
        else:
            self.logger.warning(f"Unknown operation: {operation}")
            return None
    
    def validate_privacy_settings(self) -> List[str]:
        """Validate privacy settings and return any warnings"""
        warnings = []
        
        if not settings.privacy_mode and settings.use_llm:
            warnings.append("Privacy mode disabled with LLM enabled - data may be sent to external services")
        
        if not settings.anonymize_logs:
            warnings.append("Log anonymization disabled - sensitive data may appear in logs")
        
        if not settings.enable_file_scanning:
            warnings.append("File scanning disabled - malicious files may not be detected")
        
        return warnings


# Global privacy manager instance
privacy_manager = PrivacyManager()