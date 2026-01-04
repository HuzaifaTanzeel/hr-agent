"""
Retrieval Service - Retrieves relevant policy chunks for RAG
"""
import logging
from typing import List, Dict, Any, Optional
import chromadb

from app.rag.ingestion.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service for retrieving relevant policy chunks using semantic search.
    """
    
    def __init__(
        self,
        collection: chromadb.Collection,
        embedding_service: EmbeddingService,
        top_k: int = 3
    ):
        """
        Initialize retrieval service.
        
        Args:
            collection: Chroma collection containing policy chunks
            embedding_service: Service for generating query embeddings
            top_k: Number of top results to retrieve
        """
        self.collection = collection
        self.embedding_service = embedding_service
        self.top_k = top_k
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant policy chunks for a query.
        
        Args:
            query: User's question/query
            top_k: Number of results to return (overrides default)
            filter_metadata: Optional metadata filters for filtering results
            
        Returns:
            List of relevant chunks with text, metadata, and similarity scores
        """
        try:
            k = top_k or self.top_k
            
            logger.info(f"🔍 Retrieving top {k} chunks for query: {query[:100]}...")
            
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)
            
            # Search in Chroma
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter_metadata,  # Optional metadata filtering
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            retrieved_chunks = []
            
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    chunk = {
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i],
                        "similarity": 1 - results['distances'][0][i]  # Convert distance to similarity
                    }
                    retrieved_chunks.append(chunk)
                
                logger.info(f"✅ Retrieved {len(retrieved_chunks)} chunks")
                similarity_scores = [f'{c["similarity"]:.3f}' for c in retrieved_chunks]
                logger.info(f"   Similarity scores: {similarity_scores}")
            else:
                logger.warning("⚠️  No results found for query")
            
            return retrieved_chunks
            
        except Exception as e:
            logger.error(f"❌ Error retrieving chunks: {str(e)}")
            return []
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context for LLM.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant policy information found."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            section_header = chunk['metadata'].get('section_header', '')
            source = chunk['metadata'].get('filename', 'Policy Document')
            
            context_part = f"[Policy Reference {i}]"
            if section_header:
                context_part += f"\nSection: {section_header}"
            context_part += f"\nSource: {source}"
            context_part += f"\nContent:\n{chunk['text']}\n"
            
            context_parts.append(context_part)
        
        return "\n---\n".join(context_parts)

