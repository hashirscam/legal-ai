import streamlit as st
import asyncio
import logging
import os
import time
from datetime import datetime
from flow import create_offline_indexing_flow, create_online_research_flow
from utils.progress import get_progress_tracker
import threading

# Page configuration
st.set_page_config(
    page_title="Legal AI Research System",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
    }
    .progress-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-box {
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
    }
    .status-idle { background-color: #e8e8e8; }
    .status-active { background-color: #d4edda; }
    .status-error { background-color: #f8d7da; }
    .reading-item {
        padding: 0.25rem 0.5rem;
        margin: 0.1rem 0;
        background-color: white;
        border-left: 3px solid #007bff;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'indexing_completed' not in st.session_state:
    st.session_state.indexing_completed = False
if 'vector_db' not in st.session_state:
    st.session_state.vector_db = None
if 'research_history' not in st.session_state:
    st.session_state.research_history = []
if 'current_progress' not in st.session_state:
    st.session_state.current_progress = {}

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def run_offline_indexing():
    """Run offline indexing process"""
    
    # Create shared store
    shared = {
        "documents_directory": "assets/decisions",
        "processed_files": [],
        "total_files_processed": 0,
        "vector_db": None,
        "total_chunks_indexed": 0
    }
    
    try:
        # Create and run offline flow
        offline_flow = create_offline_indexing_flow()
        offline_flow.run(shared)
        
        # Store results
        st.session_state.vector_db = shared.get("vector_db")
        st.session_state.indexing_completed = True
        
        return {
            'success': True,
            'files_processed': shared['total_files_processed'],
            'chunks_indexed': shared['total_chunks_indexed']
        }
        
    except Exception as e:
        logging.error(f"Indexing error: {e}")
        return {
            'success': False,
            'error': str(e)
        }

async def run_online_research(user_query):
    """Run online research process"""
    
    # Progress tracking setup
    progress_container = st.empty()
    
    def update_ui_progress(progress_data):
        """Update UI with progress information"""
        st.session_state.current_progress = progress_data
        
        with progress_container.container():
            display_progress(progress_data)
    
    # Register progress callback
    tracker = get_progress_tracker()
    tracker.register_callback(update_ui_progress)
    
    # Create shared store
    shared = {
        "user_query": user_query,
        "vector_db": st.session_state.vector_db,
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
        # Create and run online flow
        online_flow = create_online_research_flow()
        await online_flow.run_async(shared)
        
        # Store result
        result = {
            'success': True,
            'query': user_query,
            'timestamp': datetime.now(),
            'documents_found': shared['retrieval_count'],
            'unique_documents': shared['unique_document_count'],
            'relevant_documents': len(shared['relevant_documents']),
            'response': shared['final_response']
        }
        
        st.session_state.research_history.append(result)
        return result
        
    except Exception as e:
        logging.error(f"Research error: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def display_progress(progress_data):
    """Display real-time progress information"""
    if not progress_data:
        return
    
    stage = progress_data.get('stage', 'idle')
    status = progress_data.get('status', 'No status')
    activity = progress_data.get('current_activity', '')
    
    # Progress header
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown(f"**Stage:** {stage.title()}")
    
    with col2:
        st.markdown(f"**Status:** {status}")
    
    with col3:
        elapsed = progress_data.get('elapsed_time', 0)
        st.markdown(f"**Time:** {elapsed:.1f}s")
    
    # Progress details
    if activity:
        st.info(f"🔄 {activity}")
    
    # Stage-specific progress
    if stage == 'retrieval':
        docs_found = progress_data.get('documents_found', 0)
        if docs_found > 0:
            st.success(f"📄 Found {docs_found} relevant document chunks")
    
    elif stage == 'pruning':
        completed = progress_data.get('pruning_completed', 0)
        total = progress_data.get('total_pruning', 0)
        if total > 0:
            progress_bar = st.progress(completed / total)
            st.write(f"🔍 Analyzing documents: {completed}/{total}")
    
    elif stage == 'reading':
        documents_being_read = progress_data.get('documents_being_read', [])
        document_statuses = progress_data.get('document_statuses', {})
        completed_readings = progress_data.get('completed_readings', 0)
        total_readings = progress_data.get('total_readings', 0)
        
        if documents_being_read:
            st.write("📖 **Reading Documents (All in Parallel):**")
            
            # Create columns for better visual layout
            for doc in documents_being_read:
                status = document_statuses.get(doc, 'pending')
                
                col1, col2 = st.columns([1, 10])
                
                with col1:
                    if status == 'completed':
                        st.markdown("✅")
                    elif status == 'reading':
                        st.markdown("🔄")
                    elif status == 'error':
                        st.markdown("❌")
                    else:  # pending
                        st.markdown("⏳")
                
                with col2:
                    if status == 'reading':
                        st.markdown(f"**{doc}** - *Reading...*")
                    elif status == 'completed':
                        st.markdown(f"**{doc}** - *Completed*")
                    elif status == 'error':
                        st.markdown(f"**{doc}** - *Error*")
                    else:
                        st.markdown(f"**{doc}** - *Waiting*")
        
        if total_readings > 0:
            progress_bar = st.progress(completed_readings / total_readings)
            st.write(f"Progress: {completed_readings}/{total_readings} documents completed")
    
    elif stage == 'aggregation':
        st.info("🧠 Synthesizing findings into comprehensive response...")
    
    elif stage == 'completed':
        st.success("✅ Research completed successfully!")

def main():
    """Main Streamlit application"""
    setup_logging()
    
    # Main header
    st.markdown('<h1 class="main-header">⚖️ Legal AI Research System</h1>', unsafe_allow_html=True)
    
    # Sidebar for system status and controls
    with st.sidebar:
        st.header("📊 System Status")
        
        # Document indexing section
        st.subheader("Document Index")
        
        documents_dir = "assets/decisions"
        if os.path.exists(documents_dir):
            txt_files = [f for f in os.listdir(documents_dir) if f.endswith('.txt')]
            st.write(f"📁 {len(txt_files)} legal case files found")
            
            if not st.session_state.indexing_completed:
                if st.button("🔄 Create Vector Index", type="primary"):
                    with st.spinner("Creating vector database index..."):
                        result = run_offline_indexing()
                        
                        if result['success']:
                            st.success("✅ Indexing completed!")
                            st.write(f"Files processed: {result['files_processed']}")
                            st.write(f"Chunks indexed: {result['chunks_indexed']}")
                            st.rerun()
                        else:
                            st.error(f"❌ Indexing failed: {result['error']}")
            else:
                st.success("✅ Vector index ready")
                if st.button("🔄 Rebuild Index"):
                    st.session_state.indexing_completed = False
                    st.session_state.vector_db = None
                    st.rerun()
        else:
            st.error(f"❌ Documents directory not found: {documents_dir}")
        
        # Research history
        st.subheader("📚 Research History")
        if st.session_state.research_history:
            for i, research in enumerate(reversed(st.session_state.research_history[-5:])):
                with st.expander(f"Query {len(st.session_state.research_history)-i}: {research['query'][:30]}..."):
                    st.write(f"**Time:** {research['timestamp'].strftime('%H:%M:%S')}")
                    st.write(f"**Documents:** {research['documents_found']}")
                    st.write(f"**Relevant:** {research['relevant_documents']}")
        else:
            st.write("No research conducted yet")
    
    # Main content area
    if not st.session_state.indexing_completed:
        st.warning("⚠️ Please create the vector index first using the sidebar button.")
        st.info("""
        **Getting Started:**
        1. Click 'Create Vector Index' in the sidebar to process legal documents
        2. Once indexing is complete, you can start researching legal queries
        3. The system will show real-time progress as it processes your queries
        """)
        
    else:
        # Query input section
        st.header("🔍 Legal Research Query")
        
        # Example queries
        with st.expander("💡 Example Queries"):
            example_queries = [
                "Criminal cases involving pedophiles in Ontario 2025",
                "Sexual assault cases with publication bans",
                "Recent decisions on child pornography charges",
                "Cases involving breach of trust by public officials",
                "Sentencing guidelines for internet-based sexual offences"
            ]
            
            for query in example_queries:
                if st.button(query, key=f"example_{query[:20]}"):
                    st.session_state.current_query = query
        
        # Query input
        query_input = st.text_area(
            "Enter your legal research question:",
            value=st.session_state.get('current_query', ''),
            height=100,
            placeholder="e.g., What are the recent Ontario cases involving pedophilia charges?"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            search_button = st.button("🔍 Research", type="primary", disabled=not query_input.strip())
        with col2:
            if st.button("🗑️ Clear"):
                st.session_state.current_query = ""
                st.rerun()
        
        # Research execution
        if search_button and query_input.strip():
            st.header("📋 Research Progress")
            
            # Create placeholder for progress
            progress_placeholder = st.empty()
            result_placeholder = st.empty()
            
            # Run research
            with st.spinner("Initializing research..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(run_online_research(query_input.strip()))
                loop.close()
            
            # Display results
            with result_placeholder.container():
                if result['success']:
                    st.success("✅ Research completed!")
                    
                    # Results summary
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Documents Found", result['documents_found'])
                    with col2:
                        st.metric("Unique Documents", result['unique_documents'])
                    with col3:
                        st.metric("Relevant Documents", result['relevant_documents'])
                    with col4:
                        st.metric("Research Time", f"{st.session_state.current_progress.get('elapsed_time', 0):.1f}s")
                    
                    # Final response
                    st.header("📋 Research Results")
                    st.markdown("---")
                    st.markdown(result['response'])
                    
                else:
                    st.error(f"❌ Research failed: {result.get('error', 'Unknown error')}")
        
        # Show current progress if available
        if st.session_state.current_progress:
            st.header("⚡ Current Progress")
            display_progress(st.session_state.current_progress)

if __name__ == "__main__":
    main()
