"""
Chunking Service - Splits documents into optimal chunks for embedding
Uses semantic chunking with overlap for better retrieval
"""
import logging
import re
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    text: str
    chunk_id: str
    metadata: Dict[str, Any]
    start_index: int
    end_index: int


class ChunkingService:
    """
    Chunking service with best practices:
    - Semantic chunking (splits on natural boundaries)
    - Overlap between chunks for context preservation
    - Metadata preservation
    - Configurable chunk size
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        min_chunk_size: int = 100
    ):
        """
        Initialize chunking service.
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum size of a chunk (smaller chunks are merged)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_markdown(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[TextChunk]:
        """
        Chunk markdown content using semantic boundaries.
        
        Strategy:
        1. Split on headers (##, ###) to preserve semantic structure
        2. Split long sections on paragraphs
        3. Add overlap between chunks
        4. Preserve metadata
        
        Args:
            content: Markdown content to chunk
            metadata: Document metadata
            
        Returns:
            List of TextChunk objects
        """
        chunks = []
        
        # First, split by major sections (headers)
        sections = self._split_by_headers(content)
        
        chunk_index = 0
        for section in sections:
            section_text = section['text']
            section_metadata = {**metadata, **section.get('metadata', {})}
            
            # If section is small enough, use it as-is
            if len(section_text) <= self.chunk_size:
                chunk = TextChunk(
                    text=section_text.strip(),
                    chunk_id=f"{metadata.get('filename', 'doc')}_chunk_{chunk_index}",
                    metadata=section_metadata,
                    start_index=section.get('start_index', 0),
                    end_index=section.get('end_index', len(section_text))
                )
                chunks.append(chunk)
                chunk_index += 1
            else:
                # Split large sections into smaller chunks with overlap
                section_chunks = self._split_with_overlap(
                    section_text,
                    section_metadata,
                    chunk_index,
                    section.get('start_index', 0)
                )
                chunks.extend(section_chunks)
                chunk_index += len(section_chunks)
        
        # Merge very small chunks with previous ones
        chunks = self._merge_small_chunks(chunks)
        
        logger.info(f"📦 Created {len(chunks)} chunks from document")
        return chunks
    
    def _split_by_headers(self, content: str) -> List[Dict[str, Any]]:
        """
        Split markdown content by headers to preserve semantic structure.
        
        Returns:
            List of sections with text and metadata
        """
        sections = []
        
        # Pattern to match markdown headers (## Header or ### Header)
        header_pattern = r'^(#{2,3})\s+(.+)$'
        
        lines = content.split('\n')
        current_section = []
        current_header = None
        current_start = 0
        
        for i, line in enumerate(lines):
            match = re.match(header_pattern, line)
            
            if match:
                # Save previous section if it exists
                if current_section:
                    section_text = '\n'.join(current_section).strip()
                    if section_text:
                        sections.append({
                            'text': section_text,
                            'metadata': {'section_header': current_header} if current_header else {},
                            'start_index': current_start,
                            'end_index': current_start + len(section_text)
                        })
                
                # Start new section
                current_header = match.group(2).strip()
                current_section = [line]  # Include header in section
                current_start = sum(len(l) + 1 for l in lines[:i])  # +1 for newline
            else:
                current_section.append(line)
        
        # Add final section
        if current_section:
            section_text = '\n'.join(current_section).strip()
            if section_text:
                sections.append({
                    'text': section_text,
                    'metadata': {'section_header': current_header} if current_header else {},
                    'start_index': current_start,
                    'end_index': current_start + len(section_text)
                })
        
        # If no headers found, treat entire content as one section
        if not sections:
            sections.append({
                'text': content,
                'metadata': {},
                'start_index': 0,
                'end_index': len(content)
            })
        
        return sections
    
    def _split_with_overlap(
        self,
        text: str,
        metadata: Dict[str, Any],
        start_chunk_index: int,
        start_char_index: int
    ) -> List[TextChunk]:
        """
        Split text into chunks with overlap.
        
        Uses paragraph boundaries when possible for better semantic coherence.
        """
        chunks = []
        
        # First, try to split by paragraphs
        paragraphs = text.split('\n\n')
        
        current_chunk = []
        current_length = 0
        chunk_index = start_chunk_index
        char_index = start_char_index
        
        for para in paragraphs:
            para_length = len(para) + 2  # +2 for \n\n
            
            # If adding this paragraph would exceed chunk size
            if current_length + para_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk).strip()
                if chunk_text:
                    chunks.append(TextChunk(
                        text=chunk_text,
                        chunk_id=f"{metadata.get('filename', 'doc')}_chunk_{chunk_index}",
                        metadata=metadata.copy(),
                        start_index=char_index - len(chunk_text),
                        end_index=char_index
                    ))
                    chunk_index += 1
                
                # Start new chunk with overlap
                # Take last part of previous chunk for overlap
                if self.chunk_overlap > 0 and chunk_text:
                    overlap_text = chunk_text[-self.chunk_overlap:]
                    current_chunk = [overlap_text, para]
                    current_length = len(overlap_text) + para_length
                else:
                    current_chunk = [para]
                    current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length
            
            char_index += para_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append(TextChunk(
                    text=chunk_text,
                    chunk_id=f"{metadata.get('filename', 'doc')}_chunk_{chunk_index}",
                    metadata=metadata.copy(),
                    start_index=char_index - len(chunk_text),
                    end_index=char_index
                ))
        
        return chunks
    
    def _merge_small_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """
        Merge chunks that are too small with previous chunks.
        """
        if not chunks:
            return chunks
        
        merged = []
        i = 0
        
        while i < len(chunks):
            current = chunks[i]
            
            # If chunk is too small and not the last one
            if len(current.text) < self.min_chunk_size and i < len(chunks) - 1:
                # Try to merge with next chunk
                next_chunk = chunks[i + 1]
                merged_text = current.text + "\n\n" + next_chunk.text
                
                merged.append(TextChunk(
                    text=merged_text,
                    chunk_id=current.chunk_id,
                    metadata=current.metadata,
                    start_index=current.start_index,
                    end_index=next_chunk.end_index
                ))
                i += 2  # Skip next chunk as it's merged
            else:
                merged.append(current)
                i += 1
        
        return merged

