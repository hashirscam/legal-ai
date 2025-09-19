# Migration Guide: Switch to OpenAI Embeddings

This document explains the migration from Sentence Transformers to OpenAI embeddings to reduce Docker image size.

## What Changed

### Before (Sentence Transformers)
- **Model**: `all-MiniLM-L6-v2`
- **Embedding Dimension**: 384
- **Dependencies**: `sentence-transformers` (~2GB of additional dependencies)
- **Cost**: Free (local processing)

### After (OpenAI Embeddings)
- **Model**: `text-embedding-3-small`
- **Embedding Dimension**: 1536
- **Dependencies**: Only `openai` library (minimal size)
- **Cost**: Pay-per-use via OpenAI API

## Benefits

✅ **Significantly smaller Docker image** (reduces by ~2-3GB)  
✅ **Faster container startup** (no model download/loading)  
✅ **Better embedding quality** (OpenAI's latest models)  
✅ **No GPU requirements** (processed via API)  
✅ **Automatic updates** (latest model improvements)  

## Requirements

🔑 **OpenAI API Key** - You need a valid OpenAI API key with embedding access

## Migration Steps

### 1. Set Your OpenAI API Key

Add your OpenAI API key to your environment:

```bash
# In your .env file
OPENAI_API_KEY=your-actual-openai-api-key-here
```

Or set it in docker-compose.yml:
```yaml
environment:
  - OPENAI_API_KEY=your-actual-openai-api-key-here
```

### 2. Clean Up Existing Vector Database

⚠️ **Important**: Old embeddings are incompatible with new ones!

Run the cleanup script:
```bash
python cleanup_old_embeddings.py
```

This will remove your existing ChromaDB. You'll need to re-index your documents.

### 3. Test the New Implementation

Run the test script to verify everything works:
```bash
python test_openai_embeddings.py
```

### 4. Rebuild Your Docker Image

```bash
docker-compose build --no-cache
```

The new image will be much smaller!

### 5. Re-index Your Documents

Start your application and re-index your legal documents:
```bash
docker-compose up
```

The system will create a new vector database with OpenAI embeddings.

## Configuration Options

You can change the OpenAI embedding model in `backend/settings.py`:

```python
class VectorDBConfig:
    EMBEDDING_MODEL = "text-embedding-3-small"  # Options:
    # - "text-embedding-3-small" (1536 dims, cheaper)
    # - "text-embedding-3-large" (3072 dims, better quality)
    # - "text-embedding-ada-002" (1536 dims, legacy)
```

## Cost Estimation

OpenAI embedding costs (as of 2024):
- **text-embedding-3-small**: $0.00002 per 1K tokens
- **text-embedding-3-large**: $0.00013 per 1K tokens

Example: Indexing 1000 legal documents (~500K tokens total):
- Small model: ~$0.01
- Large model: ~$0.065

## Troubleshooting

### Error: "OPENAI_API_KEY not found"
Make sure you've set the environment variable correctly and restarted your containers.

### Error: "Invalid API key"
Verify your OpenAI API key is correct and has embedding access enabled.

### Error: "Rate limit exceeded"
The system includes automatic batching, but with large documents you might hit rate limits. The system will retry automatically.

### Different embedding dimensions
This is expected - OpenAI embeddings have different dimensions than Sentence Transformers. The cleanup script handles this transition.

## Rollback (if needed)

If you need to rollback to Sentence Transformers:

1. Add back to requirements.txt:
   ```
   sentence-transformers>=2.2.0
   ```

2. Update `backend/settings.py`:
   ```python
   EMBEDDING_MODEL = "all-MiniLM-L6-v2"
   ```

3. Revert `backend/utils/embedding.py` and `backend/utils/vector_db.py`

4. Rebuild Docker image and clean up database again

## Support

If you encounter issues during migration:
1. Check the test script output for specific errors
2. Verify your OpenAI API key is working
3. Ensure you've cleaned up the old database
4. Check Docker logs for detailed error messages

Happy migrating! 🚀
