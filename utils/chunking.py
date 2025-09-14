import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LegalTextChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize the legal text chunker
        
        Args:
            chunk_size: Target size for each chunk in characters
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        logger.info(f"Initialized chunker with chunk_size={chunk_size}, overlap={overlap}")
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using legal-aware patterns
        
        Args:
            text: Input text to split
            
        Returns:
            List of sentences
        """
        # Legal-aware sentence splitting patterns
        # Handle common legal abbreviations that shouldn't end sentences
        abbreviations = ['v\.', 'vs\.', 'c\.', 'para\.', 'paras\.', 's\.', 'ss\.', 
                        'R\.S\.C\.', 'S\.C\.', 'O\.Reg\.', 'Reg\.', 'J\.', 'C\.J\.']
        
        # Temporarily replace abbreviations to avoid false splits
        protected_text = text
        replacements = {}
        for i, abbrev in enumerate(abbreviations):
            placeholder = f"__ABBREV_{i}__"
            protected_text = re.sub(abbrev, placeholder, protected_text, flags=re.IGNORECASE)
            replacements[placeholder] = abbrev.replace('\\.', '.')
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', protected_text)
        
        # Restore abbreviations
        for i, sentence in enumerate(sentences):
            for placeholder, original in replacements.items():
                sentences[i] = sentence.replace(placeholder, original)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs
        
        Args:
            text: Input text to split
            
        Returns:
            List of paragraphs
        """
        # Split on double newlines or numbered paragraphs
        paragraphs = re.split(r'\n\s*\n|\n\s*\[\d+\]|\n\s*\(\d+\)', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_by_legal_sections(self, text: str) -> List[str]:
        """
        Split text by legal sections (e.g., numbered sections, subsections)
        
        Args:
            text: Input text to split
            
        Returns:
            List of sections
        """
        # Patterns for legal section markers
        section_patterns = [
            r'\n\s*\[\d+\]',  # [1], [2], etc.
            r'\n\s*\(\d+\)',  # (1), (2), etc.
            r'\n\s*\d+\.',    # 1., 2., etc.
            r'\n\s*[A-Z]\.',  # A., B., etc.
            r'\n\s*\([a-z]\)', # (a), (b), etc.
        ]
        
        # Try each pattern and use the one that gives the most reasonable splits
        best_splits = [text]
        
        for pattern in section_patterns:
            splits = re.split(pattern, text)
            if len(splits) > 1 and len(splits) < 50:  # Reasonable number of sections
                # Check if splits are reasonable length
                avg_length = sum(len(s) for s in splits) / len(splits)
                if 100 < avg_length < 2000:  # Reasonable section length
                    best_splits = splits
                    break
        
        return [s.strip() for s in best_splits if s.strip()]
    
    def create_chunks(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Create chunks from legal text using multiple strategies
        
        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries
        """
        if not text or len(text.strip()) == 0:
            return []
        
        chunks = []
        
        # Try different splitting strategies in order of preference
        strategies = [
            ("legal_sections", self._split_by_legal_sections),
            ("paragraphs", self._split_by_paragraphs),
            ("sentences", self._split_by_sentences)
        ]
        
        best_chunks = None
        strategy_used = "character"
        
        for strategy_name, split_func in strategies:
            sections = split_func(text)
            
            # Check if this strategy produces reasonable chunks
            if len(sections) > 1:
                temp_chunks = []
                
                for i, section in enumerate(sections):
                    if len(section) <= self.chunk_size:
                        # Section fits in one chunk
                        temp_chunks.append(section)
                    else:
                        # Section too large, need to split further
                        temp_chunks.extend(self._split_large_section(section))
                
                # Merge small adjacent chunks
                temp_chunks = self._merge_small_chunks(temp_chunks)
                
                if temp_chunks:
                    best_chunks = temp_chunks
                    strategy_used = strategy_name
                    break
        
        # Fallback to character-based chunking if no strategy worked
        if best_chunks is None:
            best_chunks = self._character_based_chunking(text)
            strategy_used = "character"
        
        # Convert to chunk dictionaries with metadata
        for i, chunk_text in enumerate(best_chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                'chunk_index': i,
                'chunk_count': len(best_chunks),
                'chunk_strategy': strategy_used,
                'chunk_size': len(chunk_text),
                'chunk_start': text.find(chunk_text) if chunk_text in text else -1
            })
            
            chunks.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })
        
        logger.info(f"Created {len(chunks)} chunks using {strategy_used} strategy")
        return chunks
    
    def _split_large_section(self, section: str) -> List[str]:
        """
        Split a large section into smaller chunks
        
        Args:
            section: Large section text
            
        Returns:
            List of smaller chunks
        """
        if len(section) <= self.chunk_size:
            return [section]
        
        # Try sentence-based splitting first
        sentences = self._split_by_sentences(section)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += (" " if current_chunk else "") + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """
        Merge chunks that are too small
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of merged chunks
        """
        if not chunks:
            return chunks
        
        merged = []
        current = chunks[0]
        
        for i in range(1, len(chunks)):
            next_chunk = chunks[i]
            
            # If current chunk is too small and merging won't exceed limit
            if (len(current) < self.chunk_size // 2 and 
                len(current) + len(next_chunk) <= self.chunk_size):
                current += "\n\n" + next_chunk
            else:
                merged.append(current)
                current = next_chunk
        
        merged.append(current)
        return merged
    
    def _character_based_chunking(self, text: str) -> List[str]:
        """
        Fallback character-based chunking with overlap
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break
            
            # Try to end at a word boundary
            chunk_end = end
            for i in range(end, max(start + self.chunk_size // 2, end - 100), -1):
                if text[i].isspace():
                    chunk_end = i
                    break
            
            chunks.append(text[start:chunk_end])
            start = chunk_end - self.overlap
        
        return chunks

def create_chunker(chunk_size: int = 1000, overlap: int = 200) -> LegalTextChunker:
    """
    Factory function to create a text chunker
    
    Args:
        chunk_size: Target size for each chunk
        overlap: Overlap between chunks
        
    Returns:
        LegalTextChunker instance
    """
    return LegalTextChunker(chunk_size, overlap)

if __name__ == "__main__":
    # Test the chunker
    chunker = LegalTextChunker(chunk_size=500, overlap=100)
    
    # Sample legal text
    sample_text = """
    ONTARIO COURT OF JUSTICE
    
    [1] This is the first paragraph of the legal decision.
    
    [2] This is the second paragraph discussing the facts of the case.
    The defendant was charged under section 123 of the Criminal Code.
    
    [3] The court must consider the following factors:
    (a) The nature of the offense
    (b) The circumstances of the defendant
    (c) The public interest
    
    [4] In conclusion, the court finds that the evidence supports the conviction.
    """
    
    chunks = chunker.create_chunks(sample_text, {'case_name': 'Test Case', 'year': '2024'})
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i + 1}:")
        print(f"Strategy: {chunk['metadata']['chunk_strategy']}")
        print(f"Size: {chunk['metadata']['chunk_size']}")
        print(f"Text: {chunk['text'][:100]}...")
