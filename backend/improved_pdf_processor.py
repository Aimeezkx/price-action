"""
Improved PDF processing with better text extraction and chapter detection
"""

import fitz  # PyMuPDF
import os
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

class ImprovedPDFProcessor:
    """Improved PDF processing with better algorithms"""
    
    def __init__(self):
        self.max_file_size = 500 * 1024 * 1024  # 500MB limit
        self.min_chapter_length = 500  # Minimum characters for a chapter
        self.max_chapters = 50  # Maximum number of chapters to extract
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate PDF file"""
        file_size = os.path.getsize(file_path)
        
        if file_size > self.max_file_size:
            return {
                "valid": False,
                "error": f"File too large: {file_size / (1024*1024):.1f}MB (max: {self.max_file_size / (1024*1024):.1f}MB)"
            }
        
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            doc.close()
            
            return {
                "valid": True,
                "page_count": page_count,
                "file_size": file_size
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid PDF: {str(e)}"
            }
    
    def extract_text_improved(self, file_path: str) -> Dict[str, Any]:
        """Improved text extraction with better handling of different PDF types"""
        try:
            doc = fitz.open(file_path)
            pages = []
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Try multiple extraction methods
                text = ""
                
                # Method 1: Standard text extraction
                text = page.get_text()
                
                # Method 2: If text is sparse, try OCR-like extraction
                if len(text.strip()) < 50:  # Very little text found
                    try:
                        # Get text with layout preservation
                        text = page.get_text("dict")
                        text_content = []
                        if isinstance(text, dict) and "blocks" in text:
                            for block in text["blocks"]:
                                if "lines" in block:
                                    for line in block["lines"]:
                                        if "spans" in line:
                                            line_text = " ".join([span.get("text", "") for span in line["spans"]])
                                            if line_text.strip():
                                                text_content.append(line_text.strip())
                        text = "\n".join(text_content)
                    except:
                        # Fallback to basic extraction
                        text = page.get_text()
                
                # Clean up text
                text = self.clean_text(text)
                
                pages.append({
                    "page_number": page_num + 1,
                    "text": text,
                    "char_count": len(text)
                })
                full_text += text + "\n"
            
            doc.close()
            
            return {
                "success": True,
                "pages": pages,
                "full_text": full_text,
                "total_chars": len(full_text),
                "page_count": len(pages)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\-\'"]+', '', text)
        
        # Fix common OCR errors for Chinese text
        text = re.sub(r'([。！？])([a-zA-Z])', r'\1 \2', text)
        text = re.sub(r'([a-zA-Z])([。！？])', r'\1 \2', text)
        
        return text.strip()
    
    def extract_chapters_improved(self, text: str) -> List[Dict[str, Any]]:
        """Improved chapter extraction with better heuristics"""
        chapters = []
        
        # More sophisticated chapter patterns
        chapter_patterns = [
            # Chinese patterns
            r'^第[一二三四五六七八九十\d]+章[：:\s]*(.{1,100}?)(?:\n|$)',
            r'^第\d+章[：:\s]*(.{1,100}?)(?:\n|$)',
            r'^[一二三四五六七八九十]+[、．.][：:\s]*(.{1,100}?)(?:\n|$)',
            
            # English patterns
            r'^Chapter\s+\d+[：:\s]*(.{1,100}?)(?:\n|$)',
            r'^CHAPTER\s+\d+[：:\s]*(.{1,100}?)(?:\n|$)',
            
            # Numbered sections (more restrictive)
            r'^\d+\.\d*\s+(.{10,100}?)(?:\n|$)',
            r'^\d+[．.]\s+(.{10,100}?)(?:\n|$)',
        ]
        
        lines = text.split('\n')
        current_chapter = None
        current_content = []
        chapter_candidates = []
        
        # First pass: find potential chapter headings
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) < 5 or len(line) > 200:  # Skip very short or very long lines
                continue
                
            for pattern in chapter_patterns:
                match = re.match(pattern, line, re.MULTILINE | re.IGNORECASE)
                if match:
                    title = match.group(1).strip() if match.groups() else line.strip()
                    if len(title) > 3:  # Meaningful title
                        chapter_candidates.append({
                            'line_num': i,
                            'title': title,
                            'full_line': line
                        })
                    break
        
        # Filter candidates to avoid over-segmentation
        if len(chapter_candidates) > self.max_chapters:
            # Keep only the most promising candidates
            # Prefer longer titles and those with common chapter words
            chapter_words = ['chapter', '章', 'section', '节', 'part', '部分']
            
            scored_candidates = []
            for candidate in chapter_candidates:
                score = len(candidate['title'])  # Longer titles get higher scores
                for word in chapter_words:
                    if word in candidate['full_line'].lower():
                        score += 10
                scored_candidates.append((score, candidate))
            
            # Sort by score and take top candidates
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            chapter_candidates = [c[1] for c in scored_candidates[:self.max_chapters]]
            chapter_candidates.sort(key=lambda x: x['line_num'])  # Restore order
        
        # Second pass: extract content between chapters
        for i, candidate in enumerate(chapter_candidates):
            start_line = candidate['line_num']
            end_line = chapter_candidates[i + 1]['line_num'] if i + 1 < len(chapter_candidates) else len(lines)
            
            content_lines = lines[start_line + 1:end_line]
            content = '\n'.join(content_lines).strip()
            
            if len(content) >= self.min_chapter_length:  # Only include substantial chapters
                chapters.append({
                    "id": len(chapters) + 1,
                    "title": candidate['title'],
                    "content": content,
                    "word_count": len(content.split()),
                    "char_count": len(content)
                })
        
        # If no good chapters found, create sections based on content length
        if not chapters:
            words = text.split()
            if len(words) > 1000:  # Only split if substantial content
                chunk_size = max(500, len(words) // 10)  # Aim for ~10 sections
                for i in range(0, len(words), chunk_size):
                    chunk = ' '.join(words[i:i + chunk_size])
                    if len(chunk) >= self.min_chapter_length:
                        # Try to find a good title from the first sentence
                        sentences = chunk.split('.')[:3]
                        title = sentences[0][:50] + "..." if len(sentences[0]) > 50 else sentences[0]
                        
                        chapters.append({
                            "id": len(chapters) + 1,
                            "title": title or f"Section {len(chapters) + 1}",
                            "content": chunk,
                            "word_count": len(chunk.split()),
                            "char_count": len(chunk)
                        })
            else:
                # Single chapter for short documents
                chapters.append({
                    "id": 1,
                    "title": "Full Document",
                    "content": text,
                    "word_count": len(text.split()),
                    "char_count": len(text)
                })
        
        return chapters[:self.max_chapters]  # Ensure we don't exceed limit
    
    def extract_knowledge_points_improved(self, text: str) -> List[Dict[str, Any]]:
        """Improved knowledge point extraction"""
        knowledge_points = []
        
        # Enhanced keywords for different languages
        keywords = {
            'chinese': ['定义', '概念', '原理', '方法', '策略', '技巧', '要点', '关键', '重要', '注意', '特点', '优势', '缺点'],
            'english': ['definition', 'concept', 'principle', 'method', 'strategy', 'technique', 'important', 'key', 'note', 'crucial', 'advantage', 'disadvantage', 'feature']
        }
        
        # Split into sentences more carefully
        sentence_patterns = [
            r'[。！？.!?]+\s*',  # Chinese and English sentence endings
            r'\n\s*[•·▪▫]\s*',   # Bullet points
            r'\n\s*\d+[.)]\s*',  # Numbered lists
        ]
        
        sentences = []
        current_text = text
        for pattern in sentence_patterns:
            parts = re.split(pattern, current_text)
            sentences.extend([s.strip() for s in parts if s.strip()])
        
        # Score sentences based on keyword presence and other factors
        scored_sentences = []
        for sentence in sentences:
            if len(sentence) < 20 or len(sentence) > 500:  # Skip very short or very long
                continue
                
            score = 0
            sentence_lower = sentence.lower()
            
            # Check for keywords
            for lang, words in keywords.items():
                for word in words:
                    if word in sentence_lower:
                        score += 2
            
            # Bonus for sentences with numbers (often contain facts)
            if re.search(r'\d+', sentence):
                score += 1
            
            # Bonus for sentences with colons (often definitions)
            if ':' in sentence or '：' in sentence:
                score += 1
            
            # Penalty for very common words that indicate less important content
            common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            common_count = sum(1 for word in common_words if word in sentence_lower)
            if common_count > 5:
                score -= 1
            
            if score > 0:
                scored_sentences.append((score, sentence))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        for i, (score, sentence) in enumerate(scored_sentences[:20]):  # Top 20
            # Create a meaningful title
            title = sentence[:60] + "..." if len(sentence) > 60 else sentence
            title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', title).strip()
            
            knowledge_points.append({
                "id": i + 1,
                "title": title,
                "content": sentence,
                "score": score,
                "confidence": min(0.9, score / 5.0)  # Convert score to confidence
            })
        
        return knowledge_points
    
    def generate_flashcards_improved(self, chapters: List[Dict], knowledge_points: List[Dict]) -> Dict[str, Any]:
        """Generate improved flashcards"""
        cards = []
        
        # Generate cards from high-confidence knowledge points
        high_confidence_kp = [kp for kp in knowledge_points if kp.get('confidence', 0) > 0.6]
        for kp in high_confidence_kp[:15]:  # Limit to 15 best knowledge points
            cards.append({
                "id": len(cards) + 1,
                "question": f"What is the key concept: {kp['title']}?",
                "answer": kp['content'],
                "type": "concept",
                "difficulty": "medium",
                "confidence": kp.get('confidence', 0.5)
            })
        
        # Generate cards from substantial chapters
        substantial_chapters = [ch for ch in chapters if ch.get('word_count', 0) > 100]
        for chapter in substantial_chapters[:10]:  # Limit to 10 chapters
            # Create summary question
            cards.append({
                "id": len(cards) + 1,
                "question": f"Summarize the main points of: {chapter['title']}",
                "answer": chapter['content'][:300] + "..." if len(chapter['content']) > 300 else chapter['content'],
                "type": "summary",
                "difficulty": "hard",
                "confidence": 0.7
            })
        
        # Generate definition cards from content with colons
        colon_sentences = []
        for chapter in chapters:
            content = chapter.get('content', '')
            sentences = re.split(r'[。.!?]', content)
            for sentence in sentences:
                if ':' in sentence or '：' in sentence:
                    parts = re.split(r'[:：]', sentence, 1)
                    if len(parts) == 2 and len(parts[0].strip()) > 5 and len(parts[1].strip()) > 10:
                        colon_sentences.append((parts[0].strip(), parts[1].strip()))
        
        for term, definition in colon_sentences[:5]:  # Limit to 5 definition cards
            cards.append({
                "id": len(cards) + 1,
                "question": f"Define: {term}",
                "answer": definition,
                "type": "definition",
                "difficulty": "easy",
                "confidence": 0.8
            })
        
        return {
            "cards": cards,
            "count": len(cards),
            "types": {
                "concept": sum(1 for c in cards if c['type'] == 'concept'),
                "summary": sum(1 for c in cards if c['type'] == 'summary'),
                "definition": sum(1 for c in cards if c['type'] == 'definition')
            }
        }

# Test the improved processor
if __name__ == "__main__":
    processor = ImprovedPDFProcessor()
    
    # Test with different PDFs
    test_files = [
        "../resource/TPA-Trends.pdf"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n=== Testing with {os.path.basename(test_file)} ===")
            
            # Validate
            validation = processor.validate_file(test_file)
            print(f"Validation: {validation}")
            
            if validation['valid']:
                # Extract text
                text_result = processor.extract_text_improved(test_file)
                if text_result['success']:
                    print(f"Extracted {text_result['total_chars']} characters from {text_result['page_count']} pages")
                    
                    # Extract chapters
                    chapters = processor.extract_chapters_improved(text_result['full_text'])
                    print(f"Found {len(chapters)} chapters")
                    for i, ch in enumerate(chapters[:3]):
                        print(f"  Chapter {i+1}: {ch['title'][:50]}... ({ch['word_count']} words)")
                    
                    # Extract knowledge points
                    kp = processor.extract_knowledge_points_improved(text_result['full_text'])
                    print(f"Found {len(kp)} knowledge points")
                    for i, k in enumerate(kp[:3]):
                        print(f"  KP {i+1}: {k['title'][:50]}... (confidence: {k['confidence']:.2f})")
                    
                    # Generate cards
                    cards = processor.generate_flashcards_improved(chapters, kp)
                    print(f"Generated {cards['count']} flashcards: {cards['types']}")