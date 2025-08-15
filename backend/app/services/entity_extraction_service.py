"""
NLP entity extraction pipeline for multilingual text processing.
"""

import re
import string
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Union
from collections import Counter, defaultdict
from enum import Enum

try:
    import spacy
    from spacy.lang.zh import Chinese
    from spacy.lang.en import English
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not available, using fallback entity extraction")

import jieba
import jieba.posseg as pseg


class Language(str, Enum):
    """Supported languages for entity extraction."""
    ENGLISH = "en"
    CHINESE = "zh"
    AUTO = "auto"


class EntityType(str, Enum):
    """Types of entities to extract."""
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    LOCATION = "LOC"
    CONCEPT = "CONCEPT"
    TERM = "TERM"
    NUMBER = "NUMBER"
    DATE = "DATE"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    TECHNICAL_TERM = "TECH"


@dataclass
class Entity:
    """Represents an extracted entity."""
    text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float
    frequency: int = 1
    context: str = ""
    
    def __hash__(self):
        return hash((self.text.lower(), self.entity_type))
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return (self.text.lower() == other.text.lower() and 
                self.entity_type == other.entity_type)


@dataclass
class EntityExtractionConfig:
    """Configuration for entity extraction."""
    
    # Language settings
    language: Language = Language.AUTO
    enable_chinese: bool = True
    enable_english: bool = True
    
    # Entity filtering
    min_entity_length: int = 2
    max_entity_length: int = 50
    min_frequency: int = 1
    min_confidence: float = 0.5
    
    # Stopwords and filtering
    use_stopwords: bool = True
    custom_stopwords: Set[str] = None
    filter_punctuation: bool = True
    filter_numbers_only: bool = True
    
    # Technical term detection
    detect_technical_terms: bool = True
    technical_patterns: List[str] = None
    
    # Deduplication
    enable_deduplication: bool = True
    similarity_threshold: float = 0.8


class EntityExtractionService:
    """Service for extracting and processing entities from text."""
    
    def __init__(self, config: Optional[EntityExtractionConfig] = None):
        """Initialize the entity extraction service."""
        self.config = config or EntityExtractionConfig()
        
        # Initialize NLP models
        self.en_nlp = None
        self.zh_nlp = None
        self._load_models()
        
        # Initialize stopwords
        self._load_stopwords()
        
        # Initialize technical term patterns
        self._load_technical_patterns()
    
    def _load_models(self):
        """Load spaCy models for different languages."""
        if SPACY_AVAILABLE:
            try:
                if self.config.enable_english:
                    # Try to load full English model, fallback to blank
                    try:
                        self.en_nlp = spacy.load("en_core_web_sm")
                    except OSError:
                        print("Warning: en_core_web_sm not found, using blank English model")
                        self.en_nlp = English()
                        # Add basic components
                        if "sentencizer" not in self.en_nlp.pipe_names:
                            self.en_nlp.add_pipe("sentencizer")
                
                if self.config.enable_chinese:
                    # Try to load Chinese model, fallback to blank
                    try:
                        self.zh_nlp = spacy.load("zh_core_web_sm")
                    except OSError:
                        print("Warning: zh_core_web_sm not found, using blank Chinese model")
                        self.zh_nlp = Chinese()
                        # Add basic components
                        if "sentencizer" not in self.zh_nlp.pipe_names:
                            self.zh_nlp.add_pipe("sentencizer")
                    
            except Exception as e:
                print(f"Error loading spaCy models: {e}")
                self.en_nlp = None
                self.zh_nlp = None
        else:
            print("spaCy not available, using fallback methods")
            self.en_nlp = None
            self.zh_nlp = None
        
        # Configure jieba for Chinese text processing
        try:
            jieba.initialize()
        except Exception as e:
            print(f"Error initializing jieba: {e}")
    
    def _load_stopwords(self):
        """Load stopwords for different languages."""
        self.stopwords = {
            Language.ENGLISH: set(),
            Language.CHINESE: set()
        }
        
        if self.config.use_stopwords:
            # English stopwords
            english_stopwords = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
                'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
                'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
            }
            self.stopwords[Language.ENGLISH] = english_stopwords
            
            # Chinese stopwords
            chinese_stopwords = {
                '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
                '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
                '看', '好', '自己', '这', '那', '里', '就是', '他', '时候', '可以', '下',
                '对', '生', '能', '而', '子', '那个', '你们', '所以', '把', '被', '还',
                '又', '让', '从', '给', '但', '什么', '些', '如果', '我们', '需要', '已经',
                '通过', '同时', '等', '由于', '因为', '所以', '但是', '然而', '虽然', '尽管'
            }
            self.stopwords[Language.CHINESE] = chinese_stopwords
        
        # Add custom stopwords if provided
        if self.config.custom_stopwords:
            for lang in self.stopwords:
                self.stopwords[lang].update(self.config.custom_stopwords)
    
    def _load_technical_patterns(self):
        """Load patterns for detecting technical terms."""
        default_patterns = [
            r'\b[A-Z]{2,}\b',  # Acronyms (e.g., API, HTTP, SQL)
            r'\b\w+(?:-\w+)+\b',  # Hyphenated terms (e.g., machine-learning)
            r'\b\w*[Tt]ech\w*\b',  # Technology-related terms
            r'\b\w*[Aa]lgorithm\w*\b',  # Algorithm-related terms
            r'\b\w*[Mm]odel\w*\b',  # Model-related terms
            r'\b\w*[Ss]ystem\w*\b',  # System-related terms
            r'\b\w*[Mm]ethod\w*\b',  # Method-related terms
            r'\b\w*[Pp]rocess\w*\b',  # Process-related terms
        ]
        
        self.technical_patterns = []
        patterns = self.config.technical_patterns or default_patterns
        
        for pattern in patterns:
            try:
                self.technical_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                print(f"Invalid regex pattern '{pattern}': {e}")
    
    def detect_language(self, text: str) -> Language:
        """Detect the primary language of the text."""
        if not text.strip():
            return Language.ENGLISH
        
        # Simple heuristic: count Chinese characters vs Latin characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = chinese_chars + latin_chars
        
        if total_chars == 0:
            return Language.ENGLISH
        
        chinese_ratio = chinese_chars / total_chars
        
        # If more than 30% Chinese characters, consider it Chinese
        if chinese_ratio > 0.3:
            return Language.CHINESE
        else:
            return Language.ENGLISH
    
    async def extract_entities(
        self, 
        text: str, 
        language: Optional[Language] = None
    ) -> List[Entity]:
        """
        Extract entities from text using appropriate NLP models.
        
        Args:
            text: Input text to process
            language: Language of the text (auto-detected if None)
            
        Returns:
            List of extracted entities
        """
        if not text.strip():
            return []
        
        # Detect language if not specified
        if language is None or language == Language.AUTO:
            language = self.detect_language(text)
        
        # Extract entities based on language
        entities = []
        
        if language == Language.ENGLISH:
            if self.en_nlp:
                entities.extend(await self._extract_english_entities(text))
            else:
                # Fallback to pattern-based extraction for English
                entities.extend(await self._extract_english_entities_fallback(text))
        elif language == Language.CHINESE:
            if self.zh_nlp:
                entities.extend(await self._extract_chinese_entities(text))
            else:
                # Use jieba-only extraction for Chinese
                entities.extend(await self._extract_chinese_entities_jieba_only(text))
        
        # Extract technical terms regardless of language
        if self.config.detect_technical_terms:
            entities.extend(await self._extract_technical_terms(text))
        
        # Filter and deduplicate entities
        entities = self._filter_entities(entities, language)
        
        if self.config.enable_deduplication:
            entities = self._deduplicate_entities(entities)
        
        # Calculate term frequencies
        entities = self._calculate_frequencies(entities, text)
        
        return entities
    
    async def _extract_english_entities(self, text: str) -> List[Entity]:
        """Extract entities from English text using spaCy."""
        entities = []
        
        try:
            doc = self.en_nlp(text)
            
            # Extract named entities
            for ent in doc.ents:
                entity_type = self._map_spacy_label_to_entity_type(ent.label_)
                if entity_type:
                    entities.append(Entity(
                        text=ent.text,
                        entity_type=entity_type,
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                        confidence=0.8,  # Default confidence for spaCy entities
                        context=self._extract_context(text, ent.start_char, ent.end_char)
                    ))
            
            # Extract noun phrases as potential concepts
            for chunk in doc.noun_chunks:
                # Skip single pronouns and very short chunks
                if len(chunk.text.split()) > 1 and chunk.root.pos_ != "PRON":
                    entities.append(Entity(
                        text=chunk.text,
                        entity_type=EntityType.CONCEPT,
                        start_pos=chunk.start_char,
                        end_pos=chunk.end_char,
                        confidence=0.6,
                        context=self._extract_context(text, chunk.start_char, chunk.end_char)
                    ))
            
        except Exception as e:
            print(f"Error in English entity extraction: {e}")
        
        return entities
    
    async def _extract_chinese_entities(self, text: str) -> List[Entity]:
        """Extract entities from Chinese text using spaCy and jieba."""
        entities = []
        
        try:
            # Use spaCy for named entity recognition if available
            if hasattr(self.zh_nlp, 'pipe_names') and 'ner' in self.zh_nlp.pipe_names:
                doc = self.zh_nlp(text)
                for ent in doc.ents:
                    entity_type = self._map_spacy_label_to_entity_type(ent.label_)
                    if entity_type:
                        entities.append(Entity(
                            text=ent.text,
                            entity_type=entity_type,
                            start_pos=ent.start_char,
                            end_pos=ent.end_char,
                            confidence=0.8,
                            context=self._extract_context(text, ent.start_char, ent.end_char)
                        ))
            
            # Use jieba for word segmentation and POS tagging
            words = pseg.cut(text)
            current_pos = 0
            
            for word, pos in words:
                word = word.strip()
                if not word:
                    current_pos += len(word)
                    continue
                
                start_pos = text.find(word, current_pos)
                if start_pos == -1:
                    current_pos += len(word)
                    continue
                
                end_pos = start_pos + len(word)
                
                # Map POS tags to entity types
                entity_type = self._map_jieba_pos_to_entity_type(pos)
                if entity_type and len(word) >= self.config.min_entity_length:
                    entities.append(Entity(
                        text=word,
                        entity_type=entity_type,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        confidence=0.7,
                        context=self._extract_context(text, start_pos, end_pos)
                    ))
                
                current_pos = end_pos
            
        except Exception as e:
            print(f"Error in Chinese entity extraction: {e}")
        
        return entities
    
    async def _extract_english_entities_fallback(self, text: str) -> List[Entity]:
        """Extract entities from English text using pattern matching fallback."""
        entities = []
        
        try:
            # Pattern-based entity extraction
            import nltk
            from nltk.tokenize import word_tokenize, sent_tokenize
            from nltk.tag import pos_tag
            
            # Ensure NLTK data is available
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            
            try:
                nltk.data.find('taggers/averaged_perceptron_tagger')
            except LookupError:
                nltk.download('averaged_perceptron_tagger', quiet=True)
            
            # Tokenize and tag
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            current_pos = 0
            for token, pos in pos_tags:
                start_pos = text.find(token, current_pos)
                if start_pos == -1:
                    current_pos += len(token)
                    continue
                
                end_pos = start_pos + len(token)
                
                # Map POS tags to entity types
                entity_type = self._map_nltk_pos_to_entity_type(pos)
                if entity_type and len(token) >= self.config.min_entity_length:
                    entities.append(Entity(
                        text=token,
                        entity_type=entity_type,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        confidence=0.6,  # Lower confidence for fallback method
                        context=self._extract_context(text, start_pos, end_pos)
                    ))
                
                current_pos = end_pos
            
            # Extract capitalized words as potential proper nouns
            capitalized_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
            for match in capitalized_pattern.finditer(text):
                term = match.group().strip()
                if len(term) >= self.config.min_entity_length:
                    entities.append(Entity(
                        text=term,
                        entity_type=EntityType.CONCEPT,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.5,
                        context=self._extract_context(text, match.start(), match.end())
                    ))
            
        except Exception as e:
            print(f"Error in English fallback entity extraction: {e}")
        
        return entities
    
    async def _extract_chinese_entities_jieba_only(self, text: str) -> List[Entity]:
        """Extract entities from Chinese text using jieba only."""
        entities = []
        
        try:
            # Use jieba for word segmentation and POS tagging
            words = pseg.cut(text)
            current_pos = 0
            
            for word, pos in words:
                word = word.strip()
                if not word:
                    current_pos += len(word)
                    continue
                
                start_pos = text.find(word, current_pos)
                if start_pos == -1:
                    current_pos += len(word)
                    continue
                
                end_pos = start_pos + len(word)
                
                # Map POS tags to entity types
                entity_type = self._map_jieba_pos_to_entity_type(pos)
                if entity_type and len(word) >= self.config.min_entity_length:
                    entities.append(Entity(
                        text=word,
                        entity_type=entity_type,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        confidence=0.7,
                        context=self._extract_context(text, start_pos, end_pos)
                    ))
                
                current_pos = end_pos
            
        except Exception as e:
            print(f"Error in Chinese jieba-only entity extraction: {e}")
        
        return entities
    
    def _map_nltk_pos_to_entity_type(self, pos: str) -> Optional[EntityType]:
        """Map NLTK POS tags to our entity types."""
        mapping = {
            'NNP': EntityType.PERSON,  # Proper noun, singular
            'NNPS': EntityType.PERSON,  # Proper noun, plural
            'NN': EntityType.TERM,  # Noun, singular
            'NNS': EntityType.TERM,  # Noun, plural
            'CD': EntityType.NUMBER,  # Cardinal number
            'JJ': EntityType.CONCEPT,  # Adjective
            'VBG': EntityType.CONCEPT,  # Verb, gerund/present participle
        }
        return mapping.get(pos)
    
    async def _extract_technical_terms(self, text: str) -> List[Entity]:
        """Extract technical terms using pattern matching."""
        entities = []
        
        for pattern in self.technical_patterns:
            for match in pattern.finditer(text):
                term = match.group().strip()
                if (len(term) >= self.config.min_entity_length and 
                    len(term) <= self.config.max_entity_length):
                    
                    entities.append(Entity(
                        text=term,
                        entity_type=EntityType.TECHNICAL_TERM,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.6,
                        context=self._extract_context(text, match.start(), match.end())
                    ))
        
        return entities
    
    def _map_spacy_label_to_entity_type(self, label: str) -> Optional[EntityType]:
        """Map spaCy entity labels to our entity types."""
        mapping = {
            'PERSON': EntityType.PERSON,
            'ORG': EntityType.ORGANIZATION,
            'GPE': EntityType.LOCATION,  # Geopolitical entity
            'LOC': EntityType.LOCATION,
            'MONEY': EntityType.MONEY,
            'PERCENT': EntityType.PERCENT,
            'DATE': EntityType.DATE,
            'TIME': EntityType.DATE,
            'CARDINAL': EntityType.NUMBER,
            'ORDINAL': EntityType.NUMBER,
            'QUANTITY': EntityType.NUMBER,
        }
        return mapping.get(label)
    
    def _map_jieba_pos_to_entity_type(self, pos: str) -> Optional[EntityType]:
        """Map jieba POS tags to our entity types."""
        mapping = {
            'nr': EntityType.PERSON,  # 人名
            'ns': EntityType.LOCATION,  # 地名
            'nt': EntityType.ORGANIZATION,  # 机构名
            'nz': EntityType.CONCEPT,  # 其他专名
            'n': EntityType.TERM,  # 名词
            'vn': EntityType.CONCEPT,  # 名动词
            'an': EntityType.CONCEPT,  # 名形词
        }
        return mapping.get(pos)
    
    def _extract_context(self, text: str, start_pos: int, end_pos: int, window: int = 50) -> str:
        """Extract context around an entity."""
        context_start = max(0, start_pos - window)
        context_end = min(len(text), end_pos + window)
        return text[context_start:context_end].strip()
    
    def _filter_entities(self, entities: List[Entity], language: Language) -> List[Entity]:
        """Filter entities based on configuration criteria."""
        filtered = []
        
        for entity in entities:
            # Length filter
            if (len(entity.text) < self.config.min_entity_length or 
                len(entity.text) > self.config.max_entity_length):
                continue
            
            # Confidence filter
            if entity.confidence < self.config.min_confidence:
                continue
            
            # Stopword filter
            if self.config.use_stopwords:
                if entity.text.lower() in self.stopwords.get(language, set()):
                    continue
            
            # Punctuation filter
            if self.config.filter_punctuation:
                if all(c in string.punctuation for c in entity.text):
                    continue
            
            # Numbers-only filter
            if self.config.filter_numbers_only:
                if entity.text.isdigit():
                    continue
            
            # Additional validation
            if self._is_valid_entity(entity):
                filtered.append(entity)
        
        return filtered
    
    def _is_valid_entity(self, entity: Entity) -> bool:
        """Additional validation for entities."""
        text = entity.text.strip()
        
        # Skip empty or whitespace-only entities
        if not text:
            return False
        
        # Skip entities that are just punctuation or symbols
        if all(not c.isalnum() for c in text):
            return False
        
        # Skip very common words that might be misclassified
        common_words = {'this', 'that', 'these', 'those', 'here', 'there', 'where', 'when'}
        if text.lower() in common_words:
            return False
        
        return True
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate and highly similar entities."""
        if not entities:
            return entities
        
        # Group entities by type
        entities_by_type = defaultdict(list)
        for entity in entities:
            entities_by_type[entity.entity_type].append(entity)
        
        deduplicated = []
        
        for entity_type, type_entities in entities_by_type.items():
            # Sort by confidence (highest first)
            type_entities.sort(key=lambda x: x.confidence, reverse=True)
            
            kept_entities = []
            
            for entity in type_entities:
                # Check if this entity is too similar to any kept entity
                is_duplicate = False
                
                for kept in kept_entities:
                    similarity = self._calculate_entity_similarity(entity, kept)
                    if similarity >= self.config.similarity_threshold:
                        # Merge with existing entity (keep the one with higher confidence)
                        if entity.confidence > kept.confidence:
                            kept_entities.remove(kept)
                            kept_entities.append(entity)
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    kept_entities.append(entity)
            
            deduplicated.extend(kept_entities)
        
        return deduplicated
    
    def _calculate_entity_similarity(self, entity1: Entity, entity2: Entity) -> float:
        """Calculate similarity between two entities."""
        text1 = entity1.text.lower().strip()
        text2 = entity2.text.lower().strip()
        
        # Exact match
        if text1 == text2:
            return 1.0
        
        # Check if one is contained in the other
        if text1 in text2 or text2 in text1:
            shorter = min(len(text1), len(text2))
            longer = max(len(text1), len(text2))
            return shorter / longer
        
        # Simple character-based similarity
        common_chars = set(text1) & set(text2)
        total_chars = set(text1) | set(text2)
        
        if not total_chars:
            return 0.0
        
        return len(common_chars) / len(total_chars)
    
    def _calculate_frequencies(self, entities: List[Entity], text: str) -> List[Entity]:
        """Calculate frequency of entities in the text."""
        text_lower = text.lower()
        
        for entity in entities:
            # Count occurrences of the entity text
            entity_text_lower = entity.text.lower()
            entity.frequency = text_lower.count(entity_text_lower)
        
        return entities
    
    def rank_entities_by_importance(
        self, 
        entities: List[Entity], 
        max_entities: Optional[int] = None
    ) -> List[Entity]:
        """
        Rank entities by importance based on frequency, confidence, and type.
        
        Args:
            entities: List of entities to rank
            max_entities: Maximum number of entities to return
            
        Returns:
            Ranked list of entities
        """
        if not entities:
            return entities
        
        # Define importance weights for different entity types
        type_weights = {
            EntityType.TECHNICAL_TERM: 1.0,
            EntityType.CONCEPT: 0.9,
            EntityType.TERM: 0.8,
            EntityType.PERSON: 0.7,
            EntityType.ORGANIZATION: 0.7,
            EntityType.LOCATION: 0.6,
            EntityType.NUMBER: 0.4,
            EntityType.DATE: 0.3,
            EntityType.MONEY: 0.3,
            EntityType.PERCENT: 0.3,
        }
        
        # Calculate importance score for each entity
        for entity in entities:
            type_weight = type_weights.get(entity.entity_type, 0.5)
            frequency_score = min(1.0, entity.frequency / 10.0)  # Normalize frequency
            length_score = min(1.0, len(entity.text) / 20.0)  # Longer terms might be more important
            
            entity.importance_score = (
                entity.confidence * 0.4 +
                frequency_score * 0.3 +
                type_weight * 0.2 +
                length_score * 0.1
            )
        
        # Sort by importance score (highest first)
        ranked_entities = sorted(entities, key=lambda x: x.importance_score, reverse=True)
        
        # Return top entities if max_entities is specified
        if max_entities:
            return ranked_entities[:max_entities]
        
        return ranked_entities
    
    def get_entity_statistics(self, entities: List[Entity]) -> Dict[str, any]:
        """Get statistics about extracted entities."""
        if not entities:
            return {
                'total_entities': 0,
                'unique_entities': 0,
                'entity_types': {},
                'avg_confidence': 0.0,
                'avg_frequency': 0.0
            }
        
        # Count entities by type
        type_counts = Counter(entity.entity_type for entity in entities)
        
        # Calculate averages
        avg_confidence = sum(entity.confidence for entity in entities) / len(entities)
        avg_frequency = sum(entity.frequency for entity in entities) / len(entities)
        
        # Count unique entities (by text)
        unique_texts = set(entity.text.lower() for entity in entities)
        
        return {
            'total_entities': len(entities),
            'unique_entities': len(unique_texts),
            'entity_types': dict(type_counts),
            'avg_confidence': round(avg_confidence, 3),
            'avg_frequency': round(avg_frequency, 2),
            'most_frequent': max(entities, key=lambda x: x.frequency).text if entities else None,
            'highest_confidence': max(entities, key=lambda x: x.confidence).text if entities else None
        }