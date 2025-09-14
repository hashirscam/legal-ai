#!/usr/bin/env python3
"""
Simple test script to verify the legal AI system works correctly
"""

import asyncio
import logging
import os
from flow import create_offline_indexing_flow, create_online_research_flow
from utils.progress import get_progress_tracker

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_offline_indexing():
    """Test offline document processing and indexing"""
    print("🔄 Testing offline document indexing...")
    
    # Check if documents exist
    documents_dir = "assets/decisions"
    if not os.path.exists(documents_dir):
        print(f"❌ Documents directory not found: {documents_dir}")
        return False
    
    txt_files = [f for f in os.listdir(documents_dir) if f.endswith('.txt')]
    if not txt_files:
        print("❌ No .txt files found in documents directory")
        return False
    
    print(f"📁 Found {len(txt_files)} legal case files")
    
    # Create shared store
    shared = {
        "documents_directory": documents_dir,
        "processed_files": [],
        "total_files_processed": 0,
        "vector_db": None,
        "total_chunks_indexed": 0
    }
    
    try:
        # Run offline flow
        offline_flow = create_offline_indexing_flow()
        offline_flow.run(shared)
        
        # Check results
        files_processed = shared['total_files_processed']
        chunks_indexed = shared['total_chunks_indexed']
        vector_db = shared['vector_db']
        
        print(f"✅ Indexing completed!")
        print(f"   Files processed: {files_processed}")
        print(f"   Chunks indexed: {chunks_indexed}")
        print(f"   Vector DB created: {vector_db is not None}")
        
        return {
            'success': True,
            'vector_db': vector_db,
            'stats': {
                'files_processed': files_processed,
                'chunks_indexed': chunks_indexed
            }
        }
        
    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        logger.error(f"Indexing error: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}

async def test_online_research(vector_db, test_query):
    """Test online research process"""
    print(f"🔍 Testing online research with query: '{test_query}'")
    
    # Setup progress tracking
    def progress_callback(progress_data):
        stage = progress_data.get('stage', 'unknown')
        activity = progress_data.get('current_activity', '')
        print(f"   📋 {stage.upper()}: {activity}")
    
    # Register progress callback
    tracker = get_progress_tracker()
    tracker.register_callback(progress_callback)
    
    # Create shared store
    shared = {
        "user_query": test_query,
        "vector_db": vector_db,
        "retrieved_chunks": [],
        "retrieval_count": 0,
        "unique_documents": [],
        "unique_document_count": 0,
        "pruning_results": {},
        "relevant_documents": [],
        "document_summaries": {},
        "final_response": ""
    }
    
    try:
        # Run online flow
        online_flow = create_online_research_flow()
        await online_flow.run_async(shared)
        
        # Check results
        retrieval_count = shared['retrieval_count']
        unique_documents = shared['unique_document_count']
        relevant_documents = len(shared['relevant_documents'])
        final_response = shared['final_response']
        
        print(f"✅ Research completed!")
        print(f"   Documents found: {retrieval_count}")
        print(f"   Unique documents: {unique_documents}")
        print(f"   Relevant documents: {relevant_documents}")
        print(f"   Response length: {len(final_response)} characters")
        
        return {
            'success': True,
            'stats': {
                'retrieval_count': retrieval_count,
                'unique_documents': unique_documents,
                'relevant_documents': relevant_documents,
                'response_length': len(final_response)
            },
            'response': final_response
        }
        
    except Exception as e:
        print(f"❌ Research failed: {e}")
        logger.error(f"Research error: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}

async def run_full_system_test():
    """Run complete system test"""
    print("⚖️  Legal AI System - Full Test")
    print("=" * 50)
    
    # Check environment
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not set in environment")
        print("   Set your API key to test LLM functionality")
        print("   Example: export OPENAI_API_KEY='your-key-here'")
    
    # Test 1: Offline indexing
    print("\n🧪 Test 1: Offline Document Indexing")
    print("-" * 40)
    
    indexing_result = test_offline_indexing()
    if not indexing_result['success']:
        print("❌ System test failed at indexing stage")
        return False
    
    vector_db = indexing_result['vector_db']
    
    # Test 2: Online research
    print("\n🧪 Test 2: Online Legal Research")
    print("-" * 40)
    
    # Test with a simple query
    test_query = "criminal cases involving sexual offenses"
    research_result = await test_online_research(vector_db, test_query)
    
    if not research_result['success']:
        print("❌ System test failed at research stage")
        return False
    
    # Display final results
    print("\n" + "="*50)
    print("🎉 SYSTEM TEST RESULTS")
    print("="*50)
    
    print("📊 Indexing Statistics:")
    indexing_stats = indexing_result['stats']
    for key, value in indexing_stats.items():
        print(f"   {key}: {value}")
    
    print("\n📊 Research Statistics:")
    research_stats = research_result['stats']
    for key, value in research_stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n📋 Sample Response (first 300 chars):")
    print("-" * 40)
    response = research_result['response']
    print(f"{response[:300]}..." if len(response) > 300 else response)
    
    print("\n✅ All tests passed! System is ready for use.")
    return True

def main():
    """Main test function"""
    try:
        # Run the full system test
        success = asyncio.run(run_full_system_test())
        
        if success:
            print("\n🚀 Ready to use!")
            print("Run one of these commands to start:")
            print("   python main.py              # Command-line interface")
            print("   streamlit run streamlit_app.py  # Web interface")
        else:
            print("\n❌ System test failed. Check the errors above.")
            
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.error(f"Test error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
