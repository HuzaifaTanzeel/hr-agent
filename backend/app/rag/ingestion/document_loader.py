"""
Document Loader - Loads HR policy documents from various sources
"""
import logging
from pathlib import Path
from typing import List, Dict, Any
import markdown

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Loads and parses documents for ingestion"""
    
    @staticmethod
    def load_markdown_file(file_path: str) -> Dict[str, Any]:
        """
        Load a markdown file and return its content and metadata.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Dictionary with 'content' (text) and 'metadata' (file info)
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Document not found: {file_path}")
            
            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse markdown to extract text (remove markdown syntax)
            # For better chunking, we'll keep some structure but extract clean text
            html = markdown.markdown(content)
            
            # Extract metadata
            metadata = {
                "source": str(path),
                "filename": path.name,
                "file_type": "markdown",
                "file_size": path.stat().st_size
            }
            
            logger.info(f"📄 Loaded document: {path.name} ({metadata['file_size']} bytes)")
            
            return {
                "content": content,  # Keep markdown for better structure preservation
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Error loading document {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def load_from_directory(directory_path: str, pattern: str = "*.md") -> List[Dict[str, Any]]:
        """
        Load all documents matching a pattern from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            pattern: File pattern to match (default: "*.md")
            
        Returns:
            List of document dictionaries with 'content' and 'metadata'
        """
        documents = []
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.warning(f"⚠️  Directory not found: {directory_path}")
            return documents
        
        # Find all matching files
        files = list(directory.glob(pattern))
        logger.info(f"📁 Found {len(files)} document(s) in {directory_path}")
        
        for file_path in files:
            try:
                doc = DocumentLoader.load_markdown_file(str(file_path))
                documents.append(doc)
            except Exception as e:
                logger.error(f"❌ Failed to load {file_path}: {str(e)}")
                continue
        
        return documents

