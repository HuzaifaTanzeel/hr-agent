"""
RAG Pipeline - Orchestrates document ingestion and storage
"""
import logging
from pathlib import Path
from typing import List, Optional
import chromadb
from chromadb.config import Settings

from app.rag.ingestion.document_loader import DocumentLoader
from app.rag.ingestion.chunking_service import ChunkingService, TextChunk
from app.rag.ingestion.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    RAG Pipeline for ingesting HR policy documents.
    
    Flow:
    1. Load documents
    2. Chunk documents
    3. Generate embeddings
    4. Store in vector database
    """
    
    def __init__(
        self,
        collection_name: str = "hr_policies",
        persist_directory: str = "./chroma_db",
        embedding_model: Optional[str] = None
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            collection_name: Name of the Chroma collection
            persist_directory: Directory to persist Chroma database
            embedding_model: Hugging Face model name for embeddings
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize services
        self.chunking_service = ChunkingService(
            chunk_size=500,
            chunk_overlap=100,
            min_chunk_size=100
        )
        self.embedding_service = EmbeddingService(model_name=embedding_model)
        
        # Initialize Chroma client
        self._init_chroma()
    
    def _init_chroma(self):
        """Initialize Chroma client and collection."""
        try:
            logger.info(f"🔄 Initializing Chroma database at {self.persist_directory}")
            
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            # Use the embedding function from our service
            embedding_dimension = self.embedding_service.get_embedding_dimension()
            
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"✅ Using existing collection: {self.collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "HR Policy Documents"}
                )
                logger.info(f"✅ Created new collection: {self.collection_name}")
            
            logger.info(f"   Collection size: {self.collection.count()} documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chroma: {str(e)}")
            raise
    
    def ingest_documents(self, document_paths: List[str]) -> int:
        """
        Ingest documents into the vector database.
        
        Args:
            document_paths: List of paths to documents to ingest
            
        Returns:
            Number of chunks ingested
        """
        logger.info("="*60)
        logger.info("🚀 Starting document ingestion")
        logger.info(f"   Documents to process: {len(document_paths)}")
        logger.info("="*60)
        
        all_chunks = []
        
        # Step 1: Load documents
        for doc_path in document_paths:
            try:
                logger.info(f"📄 Loading: {doc_path}")
                doc = DocumentLoader.load_markdown_file(doc_path)
                
                # Step 2: Chunk document
                chunks = self.chunking_service.chunk_markdown(
                    content=doc['content'],
                    metadata=doc['metadata']
                )
                
                all_chunks.extend(chunks)
                logger.info(f"   Created {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"❌ Failed to process {doc_path}: {str(e)}")
                continue
        
        if not all_chunks:
            logger.warning("⚠️  No chunks to ingest")
            return 0
        
        # Step 3: Generate embeddings
        texts = [chunk.text for chunk in all_chunks]
        logger.info(f"🔄 Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_service.embed_batch(texts)
        
        # Step 4: Prepare data for Chroma
        ids = [chunk.chunk_id for chunk in all_chunks]
        metadatas = [
            {
                **chunk.metadata,
                "chunk_id": chunk.chunk_id,
                "text_length": len(chunk.text)
            }
            for chunk in all_chunks
        ]
        
        # Step 5: Store in Chroma
        logger.info(f"💾 Storing {len(ids)} chunks in vector database...")
        
        # Delete existing documents if re-ingesting (optional - you might want to keep versioning)
        # self.collection.delete()  # Uncomment to reset collection
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        logger.info("="*60)
        logger.info(f"✅ Ingestion complete!")
        logger.info(f"   Total chunks ingested: {len(ids)}")
        logger.info(f"   Collection size: {self.collection.count()} documents")
        logger.info("="*60)
        
        return len(ids)
    
    def ingest_from_directory(self, directory_path: str, pattern: str = "*.md") -> int:
        """
        Ingest all documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            pattern: File pattern to match (default: "*.md")
            
        Returns:
            Number of chunks ingested
        """
        documents = DocumentLoader.load_from_directory(directory_path, pattern)
        document_paths = [doc['metadata']['source'] for doc in documents]
        
        if not document_paths:
            logger.warning(f"⚠️  No documents found in {directory_path}")
            return 0
        
        return self.ingest_documents(document_paths)
    
    def get_collection(self):
        """Get the Chroma collection for direct access."""
        return self.collection

