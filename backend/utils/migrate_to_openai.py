#!/usr/bin/env python3
"""
Migration utility to switch from SentenceTransformers to OpenAI embeddings.

This script helps users migrate their existing vector database from 
SentenceTransformers embeddings to OpenAI embeddings.

Since the embedding dimensions are different, the existing database 
needs to be cleared and rebuilt.
"""

import os
import shutil
import sys
import logging
from pathlib import Path

# Add parent directory to path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import get_system_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_chroma_db():
    """Clear the existing ChromaDB database"""
    config = get_system_config()
    chroma_path = Path(config.CHROMA_DB_PATH)
    
    if chroma_path.exists():
        logger.info(f"Clearing existing ChromaDB at: {chroma_path}")
        try:
            shutil.rmtree(chroma_path)
            logger.info("✅ Successfully cleared old ChromaDB database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear database: {e}")
            return False
    else:
        logger.info("ℹ️  No existing ChromaDB found - nothing to clear")
        return True

def verify_openai_key():
    """Verify that OpenAI API key is available"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY environment variable not found")
        logger.error("Please set your OpenAI API key in your .env file or environment variables")
        return False
    
    logger.info("✅ OpenAI API key found")
    return True

def test_openai_embeddings():
    """Test that OpenAI embeddings are working"""
    try:
        from embedding import EmbeddingService
        
        logger.info("Testing OpenAI embedding service...")
        service = EmbeddingService()
        
        # Test with a simple text
        test_text = "This is a test for OpenAI embeddings"
        embedding = service.get_embedding(test_text)
        
        logger.info(f"✅ OpenAI embeddings working! Dimension: {len(embedding)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to test OpenAI embeddings: {e}")
        return False

def main():
    """Main migration function"""
    print("🔄 Legal AI Migration: SentenceTransformers → OpenAI Embeddings")
    print("=" * 60)
    
    # Step 1: Verify OpenAI API key
    print("\n1. Checking OpenAI API key...")
    if not verify_openai_key():
        print("\n❌ Migration failed: OpenAI API key not available")
        sys.exit(1)
    
    # Step 2: Test OpenAI embeddings
    print("\n2. Testing OpenAI embedding service...")
    if not test_openai_embeddings():
        print("\n❌ Migration failed: OpenAI embeddings not working")
        sys.exit(1)
    
    # Step 3: Ask user confirmation
    print("\n3. Ready to clear old database...")
    print("⚠️  This will delete your existing vector database.")
    print("   You'll need to re-index your documents after migration.")
    
    confirm = input("\nProceed with clearing the database? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Migration cancelled by user")
        sys.exit(0)
    
    # Step 4: Clear database
    print("\n4. Clearing old ChromaDB database...")
    if not clear_chroma_db():
        print("\n❌ Migration failed: Could not clear database")
        sys.exit(1)
    
    print("\n✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Run your indexing process to rebuild the vector database")
    print("2. Your system will now use OpenAI embeddings")
    print("3. Enjoy the smaller Docker image size! 🐳")

if __name__ == "__main__":
    main()
