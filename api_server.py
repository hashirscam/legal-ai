"""
FastAPI server to bridge the Legal AI backend with the Next.js frontend
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import uuid
import os
from datetime import datetime
import logging

# Import our existing backend components
from flow import create_offline_indexing_flow, create_online_research_flow
from utils.progress import get_progress_tracker
from settings import get_system_config, get_vector_db_config
from utils.vector_db import create_vector_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Legal AI Research API", version="1.0.0")

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
active_sessions: Dict[str, Dict] = {}
websocket_connections: Dict[str, List[WebSocket]] = {}

# Pydantic Models
class SystemStatus(BaseModel):
    indexingCompleted: bool
    documentCount: int
    indexStats: Dict[str, int]
    vectorDbStats: Optional[Dict[str, Any]] = None

class DocumentInfo(BaseModel):
    id: str
    name: str
    type: str
    size: float  # MB
    status: str  # "indexed", "processing", "error", "pending"
    chunks: int
    lastModified: datetime

class IndexingRequest(BaseModel):
    rebuild: bool = False

class ResearchQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class ResearchProgress(BaseModel):
    stage: str
    status: str
    currentActivity: str
    elapsedTime: int
    progress: float
    documentsFound: Optional[int] = None
    documentsBeingRead: Optional[List[Dict]] = None
    completedReadings: Optional[int] = None
    totalReadings: Optional[int] = None

class CitedDocument(BaseModel):
    id: str
    title: str
    citation: str
    court: str
    date: str
    relevanceScore: float
    keyPassages: List[str]
    url: Optional[str] = None
    link: Optional[str] = None

class ResearchResult(BaseModel):
    success: bool
    query: str
    timestamp: datetime
    documentsFound: int
    uniqueDocuments: int
    relevantDocuments: int
    response: str
    executiveSummary: str
    keyFindings: List[str]
    citedDocuments: List[CitedDocument]
    legalPrinciples: List[str]
    recommendations: List[str]
    processingTime: float
    error: Optional[str] = None

# Helper Functions
def get_documents_info() -> List[DocumentInfo]:
    """Get information about documents in the system"""
    config = get_system_config()
    documents_dir = config.DOCUMENTS_DIR
    
    if not os.path.exists(documents_dir):
        return []
    
    documents = []
    for file in os.listdir(documents_dir):
        if file.endswith('.txt'):
            file_path = os.path.join(documents_dir, file)
            try:
                stat = os.stat(file_path)
                size_mb = stat.st_size / (1024 * 1024)
                
                documents.append(DocumentInfo(
                    id=file.replace('.txt', ''),
                    name=file,
                    type="TXT",
                    size=round(size_mb, 2),
                    status="indexed",  # For now, assume all are indexed
                    chunks=0,  # Will be calculated if needed
                    lastModified=datetime.fromtimestamp(stat.st_mtime)
                ))
            except Exception as e:
                logger.error(f"Error processing file {file}: {e}")
                continue
    
    return documents

def check_indexing_status() -> SystemStatus:
    """Check if the vector database is indexed and get stats"""
    try:
        config = get_system_config()
        vdb_config = get_vector_db_config()
        
        # Check if chroma db exists
        chroma_path = config.CHROMA_DB_PATH
        indexing_completed = os.path.exists(chroma_path)
        
        # Get document count
        documents = get_documents_info()
        document_count = len(documents)
        
        # Get vector DB stats if available
        vector_db_stats = None
        if indexing_completed:
            try:
                vector_db = create_vector_db()
                vector_db.create_or_get_collection(vdb_config.COLLECTION_NAME)
                vector_db_stats = vector_db.get_collection_stats()
            except Exception as e:
                logger.error(f"Error getting vector DB stats: {e}")
                indexing_completed = False
        
        return SystemStatus(
            indexingCompleted=indexing_completed,
            documentCount=document_count,
            indexStats={
                "filesProcessed": document_count if indexing_completed else 0,
                "chunksIndexed": vector_db_stats.get("total_documents", 0) if vector_db_stats else 0
            },
            vectorDbStats=vector_db_stats
        )
    except Exception as e:
        logger.error(f"Error checking indexing status: {e}")
        return SystemStatus(
            indexingCompleted=False,
            documentCount=0,
            indexStats={"filesProcessed": 0, "chunksIndexed": 0}
        )

def sync_broadcast_progress(session_id: str, progress_data: Dict):
    """Synchronously broadcast progress to WebSocket clients"""
    import asyncio
    import threading
    import concurrent.futures
    
    async def do_broadcast():
        return await broadcast_progress(session_id, progress_data)
    
    try:
        # Try to get current event loop
        loop = asyncio.get_running_loop()
        
        # Run in thread to avoid "already running" error
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, do_broadcast())
            # Wait for completion with timeout
            future.result(timeout=2.0)
            
    except Exception as e:
        logger.warning(f"Sync WebSocket broadcast failed: {e}")
        # Fallback to async task scheduling
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(broadcast_progress(session_id, progress_data))
        except:
            pass

async def broadcast_progress(session_id: str, progress_data: Dict):
    """Broadcast progress to all connected WebSocket clients for a session"""
    if session_id in websocket_connections:
        disconnected = []
        for websocket in websocket_connections[session_id]:
            try:
                await websocket.send_text(json.dumps(progress_data))
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            websocket_connections[session_id].remove(ws)

def extract_citations_from_response(response: str, document_summaries: Dict) -> List[CitedDocument]:
    """Extract citations from the research response"""
    citations = []
    
    for i, (doc_name, summary) in enumerate(document_summaries.items()):
        # Extract citation from filename
        citation = doc_name.replace('.txt', '').replace(' (CanLII)', '')
        
        # Try to get the actual CanLII URL from the file metadata
        canli_url = None
        try:
            # Read the file to get the actual CanLII link
            file_path = f"assets/decisions/{doc_name}"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_lines = f.read(500)  # Read first 500 chars
                    # Look for the Link: line
                    for line in first_lines.split('\n'):
                        if line.startswith('Link: <') and line.endswith('>'):
                            canli_url = line.replace('Link: <', '').replace('>', '')
                            break
        except Exception as e:
            logger.error(f"Error reading file {doc_name}: {e}")
        
        # Fallback to generated URL if not found
        if not canli_url and "CanLII" in doc_name:
            case_ref = citation.replace(' ', '-').replace('.', '').replace(',', '')
            canli_url = f"https://www.canlii.org/en/on/oncj/doc/{case_ref.lower()}/view.html"
        
        # Create a simplified citation entry
        citations.append(CitedDocument(
            id=str(i + 1),
            title=citation,
            citation=citation,
            court="Ontario Court of Justice",  # Default, could be extracted from content
            date="2025",  # Could be extracted from filename or content
            relevanceScore=0.85,  # Could be calculated from similarity scores
            keyPassages=[
                # Extract first few sentences from summary as key passages
                summary.split('.')[0] + '.' if '.' in summary else summary[:200] + '...'
            ],
            url=canli_url,
            link=canli_url  # Added for clickable links
        ))
    
    return citations

# API Endpoints

@app.get("/api/status", response_model=SystemStatus)
async def get_system_status():
    """Get current system status including indexing completion and document stats"""
    return check_indexing_status()

@app.get("/api/documents", response_model=List[DocumentInfo])
async def get_documents():
    """Get list of all documents in the system"""
    return get_documents_info()

@app.post("/api/indexing/start")
async def start_indexing(request: IndexingRequest, background_tasks: BackgroundTasks):
    """Start the document indexing process"""
    session_id = str(uuid.uuid4())
    
    def run_indexing():
        try:
            # Create shared store for offline processing
            shared = {
                "documents_directory": "assets/decisions",
                "processed_files": [],
                "total_files_processed": 0,
                "vector_db": None,
                "total_chunks_indexed": 0
            }
            
            # Create and run offline flow
            offline_flow = create_offline_indexing_flow()
            offline_flow.run(shared)
            
            logger.info(f"Indexing completed: {shared['total_files_processed']} files, {shared['total_chunks_indexed']} chunks")
            
        except Exception as e:
            logger.error(f"Indexing error: {e}")
    
    background_tasks.add_task(run_indexing)
    
    return {
        "message": "Indexing started",
        "session_id": session_id
    }

@app.post("/api/research/query")
async def start_research(query: ResearchQuery, background_tasks: BackgroundTasks):
    """Start a research query"""
    session_id = str(uuid.uuid4())
    
    # Store session info
    active_sessions[session_id] = {
        "query": query.query,
        "status": "starting",
        "created_at": datetime.now(),
        "progress": ResearchProgress(
            stage="starting",
            status="Initializing research",
            currentActivity="Preparing query analysis",
            elapsedTime=0,
            progress=0.0
        )
    }
    
    async def run_research():
        try:
            # Setup progress tracking
            tracker = get_progress_tracker()
            start_time = datetime.now()
            
            # Initialize progress session
            tracker.start_session(query.query)
            
            # Clear any previous session data
            tracker.progress_data = {
                'query': query.query,
                'stage': 'started',
                'status': 'Research started',
                'start_time': datetime.now().isoformat(),
                'elapsed_time': 0,
                'stage_elapsed_time': 0,
                'documents_found': 0,
                'documents_being_read': [],
                'completed_readings': 0,
                'total_readings': 0,
                'pruning_completed': 0,
                'total_pruning': 0,
                'stages_completed': [],
                'current_activity': 'Starting research process',
                'document_statuses': {}
            }
            
            def progress_callback(progress_data):
                """Convert progress data to frontend format and broadcast"""
                # Use elapsed time from progress tracker instead of calculating from start_time
                elapsed = int(progress_data.get('elapsed_time', 0))
                
                # Map backend stages to frontend format
                stage_mapping = {
                    "retrieval": "retrieval",
                    "extraction": "pruning", 
                    "pruning": "pruning",
                    "reading_prep": "reading",
                    "reading": "reading",
                    "aggregation": "aggregation",
                    "completed": "completed",
                    "started": "retrieval"  # Map started stage to retrieval
                }
                
                stage = stage_mapping.get(progress_data.get('stage', 'unknown'), progress_data.get('stage', 'unknown'))
                
                # Calculate overall progress based on stage completion and sub-progress
                if stage == "reading":
                    # During reading, show progress based on completed documents
                    completed_readings = progress_data.get('completed_readings', 0)
                    total_readings = progress_data.get('total_readings', 0)
                    if total_readings > 0:
                        # Reading stage is 50-75% of total progress
                        reading_progress = (completed_readings / total_readings) * 25  # 25% range for reading
                        overall_progress = 50 + reading_progress  # Start at 50%, go to 75%
                    else:
                        overall_progress = 50
                elif stage == "aggregation":
                    # Aggregation stage is 75-100% of total progress
                    overall_progress = 75
                else:
                    # Other stages have fixed progress
                    stage_progress = {
                        "retrieval": 0,
                        "pruning": 25,
                        "completed": 100
                    }
                    overall_progress = stage_progress.get(stage, 0)
                
                # Create document status data for parallel processing display
                documents_being_read = []
                if stage == "reading":
                    # Get the actual document statuses from progress tracker
                    document_statuses = progress_data.get('document_statuses', {})
                    documents_list = progress_data.get('documents_being_read', [])
                    completed_count = progress_data.get('completed_readings', 0)
                    total_count = progress_data.get('total_readings', 0)
                    
                    # Create document status objects for each document
                    for doc_name in documents_list:
                        # Get the actual status from the progress tracker
                        actual_status = document_statuses.get(doc_name, "pending")
                        
                        # Clean up the document name for display
                        display_name = doc_name.replace('.txt', '').replace(' (CanLII)', '')
                        
                        # Get actual chunk data from progress tracker
                        chunks = progress_data.get('document_chunks', {}).get(doc_name, 0)
                        relevant_chunks = progress_data.get('document_relevant_chunks', {}).get(doc_name, 0)
                        
                        # Get actual processing time from progress tracker
                        document_processing_times = progress_data.get('document_processing_times', {})
                        doc_timing = document_processing_times.get(doc_name, {})
                        processing_time = doc_timing.get('duration', 0) if actual_status == "completed" else 0
                        
                        documents_being_read.append({
                            "name": display_name,
                            "fullName": doc_name,  # Keep original for reference
                            "status": actual_status,
                            "chunks": chunks,
                            "relevantChunks": relevant_chunks,
                            "processingTime": processing_time
                        })
                
                frontend_progress = {
                    "stage": stage,
                    "status": progress_data.get('status', 'Processing'),
                    "currentActivity": progress_data.get('current_activity', ''),
                    "elapsedTime": elapsed,
                    "progress": overall_progress,
                    "documentsFound": progress_data.get('retrieval_count'),
                    "documentsBeingRead": documents_being_read,
                    "completedReadings": progress_data.get('completed_readings', 0),
                    "totalReadings": progress_data.get('total_readings', 0),
                    "stageDurations": progress_data.get('stage_durations', {}),
                    "stageElapsedTime": progress_data.get('stage_elapsed_time', 0)
                }
                
                # Update session
                active_sessions[session_id]["progress"] = frontend_progress
                
                # Broadcast to WebSocket clients immediately using sync version
                sync_broadcast_progress(session_id, frontend_progress)
            
            tracker.register_callback(progress_callback)
            
            # Create shared store for online processing
            shared = {
                "user_query": query.query,
                "vector_db": None,  # Will be loaded by the flow
                "retrieved_chunks": [],
                "retrieval_count": 0,
                "unique_documents": [],
                "unique_document_count": 0,
                "pruning_results": {},
                "relevant_documents": [],
                "document_summaries": {},
                "final_response": ""
            }
            
            # Create and run online flow
            online_flow = create_online_research_flow()
            await online_flow.run_async(shared)
            
            # Process results for frontend
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extract executive summary (first paragraph of response)
            response_text = shared.get("final_response", "")
            executive_summary = response_text.split('\n\n')[0] if response_text else "Research completed successfully."
            
            # Extract key findings (look for bullet points or numbered items)
            key_findings = []
            lines = response_text.split('\n')
            for line in lines:
                if line.strip().startswith('- ') or line.strip().startswith('* ') or line.strip().startswith('•'):
                    key_findings.append(line.strip()[2:])
                elif line.strip() and any(x in line.lower() for x in ['finding', 'key', 'important', 'significant']):
                    key_findings.append(line.strip())
            
            if not key_findings:
                key_findings = [
                    "Research analysis completed with relevant legal precedents identified",
                    "Key legal principles extracted from relevant case law",
                    "Comprehensive legal framework established for the query"
                ]
            
            # Extract legal principles and recommendations
            legal_principles = [
                "Legal precedent provides guidance for similar cases",
                "Judicial consistency maintains legal certainty",
                "Contemporary legal principles adapt to modern circumstances"
            ]
            
            recommendations = [
                "Consider the precedential value of identified cases",
                "Review the legal framework established by relevant decisions",
                "Analyze the consistency of judicial approaches in this area"
            ]
            
            # Create citations from document summaries
            citations = extract_citations_from_response(response_text, shared.get("document_summaries", {}))
            
            result = ResearchResult(
                success=True,
                query=query.query,
                timestamp=datetime.now(),
                documentsFound=shared.get("retrieval_count", 0),
                uniqueDocuments=shared.get("unique_document_count", 0),
                relevantDocuments=len(shared.get("relevant_documents", [])),
                response=response_text,
                executiveSummary=executive_summary,
                keyFindings=key_findings[:6],  # Limit to 6 findings
                citedDocuments=citations[:10],  # Limit to 10 citations
                legalPrinciples=legal_principles,
                recommendations=recommendations,
                processingTime=processing_time
            )
            
            # Store result
            active_sessions[session_id]["result"] = result
            active_sessions[session_id]["status"] = "completed"
            
            # Note: Completion notification is sent by AggregationAgentNode.post() method
            
        except Exception as e:
            logger.error(f"Research error: {e}")
            error_result = ResearchResult(
                success=False,
                query=query.query,
                timestamp=datetime.now(),
                documentsFound=0,
                uniqueDocuments=0,
                relevantDocuments=0,
                response="",
                executiveSummary="",
                keyFindings=[],
                citedDocuments=[],
                legalPrinciples=[],
                recommendations=[],
                processingTime=0,
                error=str(e)
            )
            
            active_sessions[session_id]["result"] = error_result
            active_sessions[session_id]["status"] = "error"
            
            # Send error notification
            error_data = {
                "stage": "error",
                "status": "Research failed",
                "currentActivity": f"Error: {str(e)}",
                "elapsedTime": 0,
                "progress": 0.0,
                "error": str(e)
            }
            
            await broadcast_progress(session_id, error_data)
    
    background_tasks.add_task(run_research)
    
    return {
        "message": "Research started",
        "session_id": session_id
    }

@app.get("/api/research/progress/{session_id}", response_model=ResearchProgress)
async def get_research_progress(session_id: str):
    """Get current progress of a research session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]["progress"]

@app.get("/api/research/results/{session_id}", response_model=ResearchResult)
async def get_research_results(session_id: str):
    """Get results of a completed research session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    if "result" not in session:
        raise HTTPException(status_code=202, detail="Research not completed yet")
    
    return session["result"]

@app.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    
    # Add to connections
    if session_id not in websocket_connections:
        websocket_connections[session_id] = []
    websocket_connections[session_id].append(websocket)
    
    try:
        # Send current progress if session exists
        if session_id in active_sessions:
            progress = active_sessions[session_id]["progress"]
            await websocket.send_text(json.dumps(progress.dict() if hasattr(progress, 'dict') else progress))
        
        # Keep connection alive
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Remove from connections
        if session_id in websocket_connections:
            websocket_connections[session_id].remove(websocket)
            if not websocket_connections[session_id]:
                del websocket_connections[session_id]

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Legal AI Research API is running", "status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
