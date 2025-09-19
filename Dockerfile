# Legal AI Full Stack Docker Image
# Use a base image that has both Python and Node.js
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ca-certificates \
    wget \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY app.py ./
COPY docker-entrypoint.py ./

# Create necessary directories
RUN mkdir -p backend/chroma_db
RUN mkdir -p backend/assets/decisions

# Copy legal documents if they exist
COPY backend/assets/ ./backend/assets/

# Install frontend dependencies
COPY frontend/package*.json ./frontend/
COPY frontend/postcss.config.mjs ./frontend/
COPY frontend/tailwind.config.ts ./frontend/
COPY frontend/next.config.mjs ./frontend/
COPY frontend/tsconfig.json ./frontend/

# Install npm dependencies for frontend (including dev dependencies for build)
RUN cd frontend && npm install

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose the ports (backend: 8000, frontend: 3000)
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Default command to run the complete application (Docker version)
CMD ["python", "docker-entrypoint.py"]
