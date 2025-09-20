import openai
import numpy as np
from typing import List, Union
import logging
import os
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        Initialize embedding service with OpenAI embeddings
        
        Args:
            model_name: Name of the OpenAI embedding model to use
                       - text-embedding-3-small: 1536 dimensions, cost-effective
                       - text-embedding-3-large: 3072 dimensions, higher performance
                       - text-embedding-ada-002: 1536 dimensions, previous generation
        """
        self.model_name = model_name
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Model specifications
        self.model_specs = {
            "text-embedding-3-small": {"dimensions": 1536, "max_tokens": 8191},
            "text-embedding-3-large": {"dimensions": 3072, "max_tokens": 8191},
            "text-embedding-ada-002": {"dimensions": 1536, "max_tokens": 8191}
        }
        
        if model_name not in self.model_specs:
            raise ValueError(f"Unsupported model: {model_name}")
            
        self.embedding_dimension = self.model_specs[model_name]["dimensions"]
        self.max_tokens = self.model_specs[model_name]["max_tokens"]
        
        logger.info(f"Initialized OpenAI embedding service with model: {model_name}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text using OpenAI API
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        try:
            # Truncate text if too long (rough estimation: 1 token ≈ 4 characters)
            if len(text) > self.max_tokens * 3:
                text = text[:self.max_tokens * 3]
                logger.warning(f"Text truncated to fit model limits for {self.model_name}")
            
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text,
                encoding_format="float"
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts efficiently using OpenAI API
        
        Args:
            texts: List of texts to embed (max 2048 texts per batch)
            
        Returns:
            List of embeddings
        """
        try:
            # OpenAI allows up to 2048 inputs per request
            batch_size = 2048
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Truncate texts if too long
                processed_texts = []
                for text in batch_texts:
                    if len(text) > self.max_tokens * 3:
                        text = text[:self.max_tokens * 3]
                        logger.warning(f"Text truncated to fit model limits for {self.model_name}")
                    processed_texts.append(text)
                
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=processed_texts,
                    encoding_format="float"
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error getting batch embeddings: {e}")
            raise
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts using OpenAI embeddings
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity score (0-1)
        """
        embeddings = self.get_embeddings_batch([text1, text2])
        
        # Calculate cosine similarity
        emb1 = np.array(embeddings[0])
        emb2 = np.array(embeddings[1])
        
        dot_product = np.dot(emb1, emb2)
        norm_a = np.linalg.norm(emb1)
        norm_b = np.linalg.norm(emb2)
        
        similarity = dot_product / (norm_a * norm_b)
        return float(similarity)
    
    def get_model_info(self) -> dict:
        """
        Get information about the embedding model
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dimension,
            'max_tokens': self.max_tokens,
            'provider': 'OpenAI'
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
    # Test the OpenAI embedding service
    import os
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable to test the embedding service")
        exit(1)
    
    service = EmbeddingService()
    
    text = "This is a legal case about contract disputes"
    embedding = service.get_embedding(text)
    
    print(f"Text: {text}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    
    # Test batch embeddings
    texts = [
        "Criminal law case involving theft",
        "Criminal proceedings about stolen property",
        "Civil contract dispute resolution"
    ]
    batch_embeddings = service.get_embeddings_batch(texts)
    print(f"\nBatch embeddings generated for {len(batch_embeddings)} texts")
    
    # Test similarity
    text1 = "Criminal law case involving theft"
    text2 = "Criminal proceedings about stolen property"
    similarity = service.calculate_similarity(text1, text2)
    print(f"\nSimilarity between:\n'{text1}'\nand\n'{text2}'\nScore: {similarity:.3f}")
    
    # Model info
    info = service.get_model_info()
    print(f"\nModel info: {info}")
    
    print(f"\nUsing OpenAI {info['model_name']} with {info['embedding_dimension']} dimensions")
