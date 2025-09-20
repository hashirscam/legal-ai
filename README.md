# Legal AI Research System

A comprehensive legal case law retrieval system that uses RAG (Retrieval-Augmented Generation) with parallel processing to provide thorough legal research while minimizing hallucinations.

## Features

- **High Recall Vector Search**: Retrieves 30+ document chunks with 50%+ similarity to avoid missing important precedents
- **Intelligent Document Pruning**: Parallel agents analyze full documents for relevance before processing
- **Comprehensive Information Extraction**: Parallel reading agents extract detailed information from relevant cases
- **Real-time Progress Tracking**: Live updates showing document retrieval, pruning, and reading progress
- **Grounded Responses**: All answers are based solely on retrieved case law to prevent hallucinations
- **User-Friendly Interface**: Both command-line and Streamlit web interfaces
- **Docker Optimized**: Lightweight deployment using OpenAI embeddings instead of local models for minimal image size

## Architecture

The system follows a multi-stage pipeline:

1. **Offline Indexing**: Process legal documents and create vector database
2. **Initial Retrieval**: High-recall vector search (similarity > 50%)
3. **Document Extraction**: Identify unique documents from retrieved chunks
4. **Parallel Pruning**: Multiple agents filter relevant documents
5. **Parallel Reading**: Extract information from filtered documents
6. **Final Aggregation**: Synthesize findings into comprehensive response

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file with your API keys:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Alternative models
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# Optional: Database path
CHROMA_DB_PATH=./chroma_db
```

> **Note**: If you previously used the system with SentenceTransformers, you'll need to clear your ChromaDB database (`backend/chroma_db/`) to rebuild it with OpenAI embeddings, as the embedding dimensions are different.

### 3. Legal Documents

Place your legal case files (.txt format) in the `assets/decisions/` directory. The system expects files with metadata at the beginning in this format:

```
Link: <https://canlii.ca/t/xxxxx>
Date: 2025 01 15
File number: 22-12345
Citation: R. v. Smith, 2025 ONCJ 123
Court: Ontario Court Of Justice
Region: Toronto
Client: John Smith
Judge: Justice A. B. Johnson

[Document content follows...]
```

## Usage

### CLI

Run using:
```
python3 start_legal_ai.py
```

You may find some frontend errors. If so, change the react version in frontend/package.json to:

Change 1 ->

```
    "@types/react": "18.2.0",
    "@types/react-dom": "18.2.0",
```

Change 2 ->

```
    "react": "18.2.0",
    "react-dom": "18.2.0",
```


Secondly, if you face tailwind error, install the following NPM package:

```
npm install tailwindcss @tailwindcss/postcss postcss
```


Features:
- Interactive web interface
- Real-time progress visualization
- Research history tracking
- Example queries
- System status monitoring

## System Design

### Core Components

- **Vector Database**: ChromaDB for efficient similarity search
- **Embedding Model**: OpenAI `text-embedding-3-small`
- **LLM Integration**: OpenAI GPT-4o (configurable)
- **Parallel Processing**: Async processing for pruning and reading agents
- **Progress Tracking**: Real-time UI updates throughout the pipeline

### Design Patterns

- **RAG Pattern**: Retrieval-augmented generation with legal case law
- **Agent Pattern**: Intelligent pruning and reading agents
- **Workflow Pattern**: Multi-stage processing pipeline
- **Parallel Processing**: Concurrent document analysis

## Key Files

```
legal-ai/
├── main.py                 # Command-line interface
├── streamlit_app.py        # Web interface
├── flow.py                 # Workflow definitions
├── nodes.py               # Core processing nodes
├── nodes_agents.py        # Agent nodes (pruning, reading, aggregation)
├── utils/
│   ├── vector_db.py       # ChromaDB integration
│   ├── embedding.py       # Embedding service
│   ├── file_processor.py  # Legal document processing
│   ├── chunking.py        # Text chunking for legal documents
│   ├── progress.py        # Progress tracking
│   └── call_llm.py        # LLM wrapper
├── assets/decisions/      # Legal case files
└── docs/design.md         # Detailed system design
```

## Example Queries

- "Criminal cases involving pedophiles in Ontario 2025"
- "Sexual assault cases with publication bans"
- "Recent decisions on child pornography charges"
- "Cases involving breach of trust by public officials"
- "Sentencing guidelines for internet-based sexual offences"

## Performance Characteristics

- **Recall-Optimized**: Prioritizes completeness over speed to avoid missing critical cases
- **Parallel Processing**: Multiple agents work simultaneously for efficiency
- **Intelligent Filtering**: Two-stage filtering (vector similarity + LLM pruning) ensures relevance
- **Progress Transparency**: Real-time updates keep users informed during processing

## System Requirements

- Python 3.8+
- OpenAI API access
- 4GB+ RAM (for vector database and embeddings)
- Storage space for document index (varies by document collection size)

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure `OPENAI_API_KEY` is set in `.env` file
2. **No Documents Found**: Check that `.txt` files exist in `assets/decisions/`
3. **Memory Issues**: Reduce chunk size in `utils/chunking.py` if processing large documents
4. **Slow Processing**: Consider reducing the number of initial retrievals in `nodes.py`

### Logging

The system provides detailed logging. To increase verbosity:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Follow the agentic coding principles outlined in `docs/design.md`
2. Test both offline indexing and online research workflows
3. Ensure progress tracking works correctly
4. Maintain the separation between data processing and LLM calls

## License

This system is designed for legal research and educational purposes. Ensure compliance with applicable legal and ethical guidelines when processing legal documents.
