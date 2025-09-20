#!/usr/bin/env python3
"""
Quick script to index all legal documents into the vector database
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append('.')

def main():
    print("🔄 Starting document indexing...")
    print("This will process all legal documents and create embeddings using OpenAI")
    print("=" * 60)
    
    try:
        from backend.main import run_offline_indexing
        result = run_offline_indexing()
        
        print("\n✅ Indexing completed successfully!")
        print(f"📁 Files processed: {result.get('total_files_processed', 0)}")
        print(f"📊 Chunks indexed: {result.get('total_chunks_indexed', 0)}")
        print("\n🎉 Your legal AI system is now ready to use!")
        
    except Exception as e:
        print(f"\n❌ Error during indexing: {e}")
        print("Please check your OpenAI API key and try again.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())


