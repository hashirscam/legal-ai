#!/usr/bin/env python3
"""
Legal AI System Docker Entry Point

This script starts both the FastAPI backend and Next.js frontend for Docker deployment.
Optimized for container environments.
"""

import subprocess
import os
import sys
import time
import signal
from pathlib import Path

FRONTEND_DIR = "frontend"

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import pocketflow
        import openai
        import chromadb
        print("✅ Python dependencies found")
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        return False
    
    # Check if Node.js and npm are available
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Node.js found: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
            
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ npm found: {result.stdout.strip()}")
        else:
            print("❌ npm not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Node.js/npm: {e}")
        return False
    
    return True

def check_env_vars():
    """Check if required environment variables are set"""
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key or openai_key == "your-openai-api-key-here":
        print("❌ OPENAI_API_KEY environment variable not set or invalid")
        print("Please set OPENAI_API_KEY in your docker-compose.yml or .env file")
        return False
    
    print("✅ Environment variables configured")
    return True

def create_backend_env():
    """Create backend environment file from environment variables"""
    backend_dir = Path("backend")
    backend_dir.mkdir(exist_ok=True)
    
    env_file = backend_dir / ".env"
    
    # Create .env file from environment variables
    with open(env_file, "w") as f:
        f.write("# Legal AI Research System Environment Variables (Docker)\n")
        f.write(f"OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY', '')}\n")
        f.write(f"DOCUMENTS_DIR={os.environ.get('DOCUMENTS_DIR', 'backend/assets/decisions')}\n")
        f.write(f"CHROMA_DB_PATH={os.environ.get('CHROMA_DB_PATH', 'backend/chroma_db')}\n")
        f.write(f"LOG_LEVEL={os.environ.get('LOG_LEVEL', 'INFO')}\n")
    
    print("✅ Backend environment file created")

def create_frontend_env():
    """Create frontend environment file"""
    frontend_dir = Path(FRONTEND_DIR)
    env_file = frontend_dir / ".env.local"
    
    with open(env_file, "w") as f:
        f.write("# Frontend environment variables (Docker)\n")
        f.write("NEXT_PUBLIC_API_URL=http://localhost:8000\n")
    
    print("✅ Frontend environment file created")

def install_frontend_deps():
    """Install frontend dependencies if needed"""
    frontend_dir = Path(FRONTEND_DIR)
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            print("✅ Frontend dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install frontend dependencies: {e}")
            return False
    else:
        print("✅ Frontend dependencies already installed")
    
    return True

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend on http://localhost:8000")
    
    env = os.environ.copy()
    env['PYTHONPATH'] = '/app'
    
    return subprocess.Popen([
        "python", "-m", "uvicorn", 
        "backend.api_server:app", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ], env=env)

def start_frontend():
    """Start the Next.js frontend"""
    print("🚀 Starting Next.js frontend on http://localhost:3000")
    frontend_dir = Path(FRONTEND_DIR)
    
    # Set environment for Next.js development
    env = os.environ.copy()
    env['NODE_ENV'] = 'development'  # Override the production setting for dev server
    
    return subprocess.Popen([
        "npm", "run", "dev", "--", "--hostname", "0.0.0.0"
    ], cwd=frontend_dir, env=env)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    """Main startup function"""
    print("⚖️  Legal AI Research System (Docker)")
    print("=" * 50)
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment variables
    if not check_env_vars():
        sys.exit(1)
    
    # Create environment files
    create_backend_env()
    create_frontend_env()
    
    # Install frontend dependencies if needed
    if not install_frontend_deps():
        sys.exit(1)
    
    # Start services
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend
        backend_process = start_backend()
        time.sleep(5)  # Give backend more time to start in Docker
        
        # Start frontend
        frontend_process = start_frontend()
        
        print("\n" + "=" * 50)
        print("🎉 Legal AI Research System is running!")
        print("📊 Backend API: http://localhost:8000")
        print("🌐 Frontend UI: http://localhost:3000")
        print("📖 API Docs: http://localhost:8000/docs")
        print("=" * 50)
        
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped")
                break
            
            if frontend_process and frontend_process.poll() is not None:
                print("❌ Frontend process stopped")
                break
    
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Shutting down services...")
    
    finally:
        # Cleanup processes
        if backend_process:
            print("Stopping backend...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        
        if frontend_process:
            print("Stopping frontend...")
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        
        print("👋 Services stopped. Goodbye!")

if __name__ == "__main__":
    main()
