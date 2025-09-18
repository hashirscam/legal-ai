# Legal AI Research System - Full Stack Integration

This document describes the complete integration between the beautiful Next.js frontend and the powerful Python backend for the Legal AI Research System.

## 🎯 Overview

The system now consists of:

1. **Backend**: FastAPI server (`api_server.py`) that bridges your existing PocketFlow-based legal AI system
2. **Frontend**: Beautiful Next.js application with modern UI components
3. **Real-time Communication**: WebSocket connections for live progress updates
4. **API Integration**: RESTful APIs connecting frontend to backend seamlessly

## 🏗️ Architecture

```
┌─────────────────────┐    HTTP/WebSocket    ┌──────────────────────┐
│   Next.js Frontend  │ ◄─────────────────► │   FastAPI Backend   │
│   (Port 3000)       │                      │   (Port 8000)        │
└─────────────────────┘                      └──────────────────────┘
                                                        │
                                                        ▼
                                             ┌──────────────────────┐
                                             │  PocketFlow System   │
                                             │  • Document Indexing │
                                             │  • Vector Search     │
                                             │  • AI Agents         │
                                             │  • Progress Tracking │
                                             └──────────────────────┘
```

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)

```bash
# Run the startup script
python start_legal_ai.py
```

This script will:
- Check all dependencies
- Install frontend packages
- Set up environment files
- Start both backend and frontend
- Open the system at http://localhost:3000

### Option 2: Manual Startup

1. **Start the Backend**:
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start FastAPI server
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

2. **Start the Frontend**:
```bash
# Navigate to frontend directory
cd legal-ai

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start Next.js development server
npm run dev
```

3. **Access the System**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
legal-ai-system/
├── api_server.py              # FastAPI backend server
├── start_legal_ai.py         # Startup script
├── requirements.txt          # Python dependencies
├── .env                      # Backend environment variables
├── main.py                   # Original CLI interface
├── streamlit_app.py          # Original Streamlit interface
├── flow.py                   # PocketFlow workflow definitions
├── nodes.py                  # Document processing nodes
├── nodes_agents.py           # AI agent nodes
├── settings.py               # Configuration settings
├── utils/                    # Utility functions
│   ├── call_llm.py          # LLM integration
│   ├── vector_db.py         # ChromaDB interface
│   ├── progress.py          # Progress tracking
│   └── ...
├── assets/
│   └── decisions/           # Legal case documents (.txt files)
├── chroma_db/              # Vector database storage
└── frontend/               # Next.js frontend
    ├── app/
    │   ├── page.tsx        # Main application page
    │   └── layout.tsx      # App layout
    ├── components/         # React components
    │   ├── document-indexing-dashboard.tsx
    │   ├── research-query-interface.tsx
    │   ├── research-results-display.tsx
    │   └── real-time-progress-tracker.tsx
    ├── lib/
    │   ├── api.ts          # API client and hooks
    │   └── utils.ts        # Utility functions
    ├── package.json        # Frontend dependencies
    └── .env.local         # Frontend environment variables
```

## 🔌 API Endpoints

The FastAPI backend provides these endpoints:

### System Management
- `GET /api/status` - Get system indexing status and statistics
- `GET /api/documents` - List all documents in the system
- `POST /api/indexing/start` - Start document indexing process

### Research Operations
- `POST /api/research/query` - Start a research query
- `GET /api/research/progress/{session_id}` - Get research progress
- `GET /api/research/results/{session_id}` - Get research results

### Real-time Updates
- `WebSocket /ws/progress/{session_id}` - Real-time progress updates

## 🎨 Frontend Features

### Document Indexing Dashboard
- Real-time indexing status and statistics
- Document library with file details
- Index rebuilding capabilities
- Visual progress tracking

### Research Query Interface
- Natural language query input
- Advanced filtering options
- Example queries for different legal areas
- Saved query management

### Real-time Progress Tracker
- Live updates during research process
- Stage-by-stage progress visualization
- Document reading status
- Performance metrics

### Research Results Display
- Comprehensive tabbed results view
- Executive summary and key findings
- Full legal analysis with markdown support
- Cited documents with relevance scores
- Legal principles and recommendations
- Export capabilities

## 🔧 Configuration

### Backend Configuration (`settings.py`)

Key settings you can customize:

```python
class SystemConfig:
    DOCUMENTS_DIR = "assets/decisions"  # Legal case files location
    CHROMA_DB_PATH = "./chroma_db"     # Vector database path
    LOG_LEVEL = "INFO"                  # Logging level

class LLMConfig:
    MODEL = "gpt-4o"                   # OpenAI model
    MAX_RETRIES = 3                    # LLM call retries
    MAX_PARALLEL_READING = 10          # Concurrent document reading

class VectorDBConfig:
    SIMILARITY_THRESHOLD = 0.5         # Search similarity threshold
    MAX_RESULTS = 30                   # Maximum search results
```

### Environment Variables

**Backend (`.env`)**:
```
OPENAI_API_KEY=your-openai-api-key-here
DOCUMENTS_DIR=assets/decisions
CHROMA_DB_PATH=./chroma_db
```

**Frontend (`.env.local`)**:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🔄 Data Flow

### Document Indexing Flow
1. Frontend triggers indexing via API call
2. Backend runs PocketFlow offline indexing
3. Documents are processed and chunked
4. Vector embeddings are created and stored in ChromaDB
5. Progress updates sent via WebSocket
6. Frontend displays real-time indexing status

### Research Query Flow
1. User enters query in frontend interface
2. Frontend sends query to backend API
3. Backend creates research session and starts PocketFlow online flow
4. Progress updates streamed via WebSocket:
   - **Retrieval**: Vector search for relevant chunks
   - **Pruning**: AI agents filter relevant documents
   - **Reading**: Parallel AI agents extract information
   - **Aggregation**: Final synthesis and response generation
5. Results returned and displayed in frontend

## 🐛 Troubleshooting

### Common Issues

**Backend won't start**:
- Check that all Python dependencies are installed: `pip install -r requirements.txt`
- Ensure OpenAI API key is set in `.env` file
- Verify documents exist in `assets/decisions/` directory

**Frontend won't connect to backend**:
- Check that backend is running on port 8000
- Verify `NEXT_PUBLIC_API_URL` in `.env.local` is correct
- Check browser console for CORS errors

**WebSocket connection fails**:
- Ensure backend supports WebSocket (uvicorn with `--ws` flag)
- Frontend will fallback to polling if WebSocket fails
- Check browser developer tools for connection errors

**Indexing fails**:
- Ensure document files are in correct format (.txt files)
- Check available disk space for ChromaDB
- Verify OpenAI API key has sufficient credits

**Research queries fail**:
- Ensure documents are indexed first
- Check OpenAI API rate limits
- Verify query is not empty or too long

### Logs and Debugging

**Backend logs**: Check console output from FastAPI server
**Frontend logs**: Check browser developer tools console
**API logs**: Visit http://localhost:8000/docs for interactive API testing

## 🔒 Security Considerations

- **API Keys**: Never commit API keys to version control
- **CORS**: Currently configured for development (localhost only)
- **Rate Limiting**: Consider implementing rate limiting for production
- **Input Validation**: API includes basic input validation
- **File Access**: Backend only accesses configured document directories

## 🚀 Production Deployment

For production deployment:

1. **Backend**:
   - Use production WSGI server (gunicorn + uvicorn)
   - Configure proper CORS origins
   - Set up SSL/HTTPS
   - Use environment-based configuration
   - Implement proper logging and monitoring

2. **Frontend**:
   - Build optimized production bundle: `npm run build`
   - Deploy to static hosting (Vercel, Netlify) or container
   - Update API URL to production backend
   - Configure proper CSP headers

3. **Database**:
   - Use persistent storage for ChromaDB
   - Consider backups for vector database
   - Monitor disk usage and performance

## 📈 Performance Optimization

- **Backend**: Uses async processing and parallel AI agents
- **Frontend**: Implements real-time updates with WebSocket fallback
- **Database**: ChromaDB optimized for similarity search
- **Caching**: Consider implementing Redis for session caching in production

## 🤝 Contributing

The integration is designed to be modular and extensible:

- **Add new API endpoints** in `api_server.py`
- **Extend frontend components** in `legal-ai/components/`
- **Modify AI workflows** in `flow.py` and `nodes_agents.py`
- **Update configuration** in `settings.py`

## 📝 License

This integration maintains the same license as your original Legal AI system.

---

**🎉 Congratulations! Your Legal AI Research System now has a beautiful, modern frontend that seamlessly integrates with your powerful backend!**

Visit http://localhost:3000 to experience the full system in action.
