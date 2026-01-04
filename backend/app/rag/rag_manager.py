"""
RAG Manager - Singleton for managing RAG pipeline and retrieval
"""
import logging
from pathlib import Path
from typing import Optional

from app.rag.rag_pipeline import RAGPipeline
from app.rag.retrieval_service import RetrievalService
from app.rag.ingestion.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGManager:
    """
    Singleton manager for RAG operations.
    Initializes pipeline and provides retrieval service.
    """
    _instance: Optional['RAGManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.pipeline: Optional[RAGPipeline] = None
            self.retrieval_service: Optional[RetrievalService] = None
            self.embedding_service: Optional[EmbeddingService] = None
            self._initialized = True
    
    def initialize(
        self,
        collection_name: str = "hr_policies",
        persist_directory: str = "./chroma_db",
        embedding_model: Optional[str] = None
    ):
        """
        Initialize RAG pipeline and retrieval service.
        
        Args:
            collection_name: Name of Chroma collection
            persist_directory: Directory for Chroma persistence
            embedding_model: Hugging Face model name
        """
        if self.pipeline is not None:
            logger.info("🔄 RAG Manager already initialized")
            return
        
        try:
            logger.info("🚀 Initializing RAG Manager...")
            
            # Initialize pipeline
            self.pipeline = RAGPipeline(
                collection_name=collection_name,
                persist_directory=persist_directory,
                embedding_model=embedding_model
            )
            
            # Initialize embedding service (shared with pipeline)
            self.embedding_service = self.pipeline.embedding_service
            
            # Initialize retrieval service
            self.retrieval_service = RetrievalService(
                collection=self.pipeline.get_collection(),
                embedding_service=self.embedding_service,
                top_k=3
            )
            
            logger.info("✅ RAG Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Manager: {str(e)}")
            raise
    
    def ensure_ingested(self, policy_directory: str = "./docs/policies"):
        """
        Ensure policy documents are ingested.
        If collection is empty, ingest documents from directory.
        
        Args:
            policy_directory: Directory containing policy documents
        """
        if self.pipeline is None:
            raise RuntimeError("RAG Manager not initialized")
        
        collection = self.pipeline.get_collection()
        count = collection.count()
        
        if count == 0:
            logger.info("📚 No documents in collection, starting ingestion...")
            policy_path = Path(policy_directory)
            
            if not policy_path.exists():
                logger.warning(f"⚠️  Policy directory not found: {policy_directory}")
                logger.info("   Creating sample policy document...")
                # Create directory if it doesn't exist
                policy_path.mkdir(parents=True, exist_ok=True)
            
            # Ingest documents
            chunks_ingested = self.pipeline.ingest_from_directory(
                directory_path=str(policy_path),
                pattern="*.md"
            )
            
            if chunks_ingested == 0:
                logger.warning("⚠️  No documents were ingested. Please add policy documents.")
        else:
            logger.info(f"✅ Collection already has {count} documents")
    
    def get_retrieval_service(self) -> RetrievalService:
        """Get the retrieval service."""
        if self.retrieval_service is None:
            raise RuntimeError("RAG Manager not initialized")
        return self.retrieval_service


# Global singleton instance
rag_manager = RAGManager()

