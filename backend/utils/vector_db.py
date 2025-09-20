import chromadb
from chromadb.utils import embedding_functions
import os
from typing import List, Dict, Any, Tuple
import logging
import sys
import openai
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import get_system_config, get_vector_db_config

logger = logging.getLogger(__name__)

class OpenAIEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Custom OpenAI embedding function for ChromaDB"""
    
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name = model_name
        
    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        """Generate embeddings for input documents"""
        try:
            # Handle both single string and list of strings
            if isinstance(input, str):
                input = [input]
            
            # Process in batches to avoid API limits
            batch_size = 2048
            all_embeddings = []
            
            for i in range(0, len(input), batch_size):
                batch = input[i:i + batch_size]
                
                # Truncate texts that are too long (rough estimation: 1 token ≈ 4 characters)
                # Use a conservative limit of 30,000 characters (≈ 7,500 tokens) to stay well under 8,192
                processed_batch = []
                for text in batch:
                    if len(text) > 30000:
                        text = text[:30000]
                        logger.warning(f"Text truncated to fit OpenAI model limits (was {len(text)} chars)")
                    processed_batch.append(text)
                
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=processed_batch,
                    encoding_format="float"
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

class VectorDatabase:
    def __init__(self, persist_directory: str = None):
        """
        Initialize ChromaDB vector database with OpenAI embeddings
        
        Args:
            persist_directory: Directory to persist the database (uses config if None)
        """
        config = get_system_config()
        vdb_config = get_vector_db_config()
        
        persist_dir = persist_directory or config.CHROMA_DB_PATH
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Use OpenAI embeddings instead of SentenceTransformers
        self.embedding_function = OpenAIEmbeddingFunction(
            model_name=vdb_config.EMBEDDING_MODEL
        )
        self.collection = None
        logger.info(f"Initialized vector database with OpenAI embeddings at {persist_dir}")
    
    def create_or_get_collection(self, collection_name: str = "legal_cases"):
        """
        Create or get existing collection
        
        Args:
            collection_name: Name of the collection
        """
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Retrieved existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Created new collection: {collection_name}")
        
        return self.collection
    
    def add_documents(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """
        Add documents to the vector database
        
        Args:
            texts: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of unique document IDs
        """
        if not self.collection:
            self.create_or_get_collection()
        
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(texts)} documents to collection")
    
    def search(self, query: str, n_results: int = 10, similarity_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            n_results: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of search results with documents, metadata, and scores
        """
        if not self.collection:
            self.create_or_get_collection()
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Filter results by similarity threshold
        # Note: ChromaDB returns distances, we convert to similarity scores
        filtered_results = []
        
        for i, distance in enumerate(results['distances'][0]):
            # Convert distance to similarity score (assuming cosine distance)
            similarity_score = 1.0 - distance
            
            if similarity_score >= similarity_threshold:
                filtered_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': similarity_score,
                    'id': results['ids'][0][i]
                })
        
        logger.info(f"Found {len(filtered_results)} documents above similarity threshold {similarity_threshold}")
        return filtered_results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection
        
        Returns:
            Dictionary with collection statistics
        """
        if not self.collection:
            self.create_or_get_collection()
        
        count = self.collection.count()
        return {
            'total_documents': count,
            'collection_name': self.collection.name
        }

def create_vector_db() -> VectorDatabase:
    """
    Factory function to create vector database instance
    """
    return VectorDatabase()

if __name__ == "__main__":
    # Test the vector database
    db = create_vector_db()
    db.create_or_get_collection("test_collection")
    
    # Test data
    texts = ["This is a test document", "This is another test document"]
    metadatas = [{"source": "test1"}, {"source": "test2"}]
    ids = ["doc1", "doc2"]
    
    db.add_documents(texts, metadatas, ids)
    
    # Search test
    results = db.search("test document", n_results=5, similarity_threshold=0.5)
    print(f"Found {len(results)} results")
    for result in results:
        print(f"Score: {result['score']:.3f}, Text: {result['text'][:50]}...")
