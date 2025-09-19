from openai import OpenAI
import numpy as np
from typing import List, Union
import logging
import os

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        Initialize embedding service with OpenAI embedding model
        
        Args:
            model_name: Name of the OpenAI embedding model to use
        """
        self.model_name = model_name
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
        
        self.client = OpenAI(api_key=api_key)
        # Set embedding dimensions based on model
        self.embedding_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        self.embedding_dimension = self.embedding_dimensions.get(model_name, 1536)
        logger.info(f"Initialized OpenAI embedding service with model: {model_name}")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text using OpenAI API
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding for text: {e}")
            raise
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts efficiently using OpenAI API
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        try:
            # OpenAI API can handle batches up to 2048 texts at once
            batch_size = min(2048, len(texts))
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch
                )
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
        except Exception as e:
            logger.error(f"Error getting batch embeddings: {e}")
            raise
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            embeddings = self.get_embeddings_batch([text1, text2])
            
            # Calculate cosine similarity
            embedding1 = np.array(embeddings[0])
            embedding2 = np.array(embeddings[1])
            
            dot_product = np.dot(embedding1, embedding2)
            norm_a = np.linalg.norm(embedding1)
            norm_b = np.linalg.norm(embedding2)
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            raise
    
    def get_model_info(self) -> dict:
        """
        Get information about the embedding model
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dimension,
            'max_sequence_length': 8192  # OpenAI models generally support up to 8192 tokens
        }

# Global embedding service instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """
    Get singleton instance of embedding service
    
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

def get_embedding(text: str) -> List[float]:
    """
    Utility function to get embedding for text
    
    Args:
        text: Input text
        
    Returns:
        Embedding vector
    """
    service = get_embedding_service()
    return service.get_embedding(text)

if __name__ == "__main__":
    # Test the embedding service
    service = EmbeddingService()
    
    text = "This is a legal case about contract disputes"
    embedding = service.get_embedding(text)
    
    print(f"Text: {text}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    
    # Test similarity
    text1 = "Criminal law case involving theft"
    text2 = "Criminal proceedings about stolen property"
    similarity = service.calculate_similarity(text1, text2)
    print(f"\nSimilarity between:\n'{text1}'\nand\n'{text2}'\nScore: {similarity:.3f}")
    
    # Model info
    info = service.get_model_info()
    print(f"\nModel info: {info}")
