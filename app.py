#!/usr/bin/env python3
"""
Legal AI System Startup Script

This script starts both the FastAPI backend and Next.js frontend for the Legal AI Research System.
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
        print("Please run: pip install -r requirements.txt")
        return False
    
    # Check if Node.js and npm are available
    try:
        # Check Node.js
        node_found = False
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                node_found = True
                print(f"✅ Node.js found: {result.stdout.strip()}")
            else:
                print("❌ Node.js not found")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("❌ Node.js not found")
        
        # Check npm
        npm_found = False
        try:
            # On Windows, try different ways to call npm
            npm_commands = [
                ["npm", "--version"],
                ["npm.cmd", "--version"],
                ["npm.ps1", "--version"]
            ]
            
            for cmd in npm_commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, shell=True)
                    if result.returncode == 0:
                        npm_found = True
                        print(f"✅ npm found: {result.stdout.strip()}")
                        break
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            if not npm_found:
                print("❌ npm not found")
        except Exception as e:
            print(f"❌ Error checking npm: {e}")
        
        if not node_found or not npm_found:
            print("❌ Node.js or npm not found. Please install Node.js")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Node.js/npm: {e}")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists with required variables"""
    env_file = Path("backend/.env")
    if not env_file.exists():
        print("❌ .env file not found in backend directory")
        print("Creating backend/.env file with default settings...")
        
        # Create backend directory if it doesn't exist
        backend_dir = Path("backend")
        backend_dir.mkdir(exist_ok=True)
        
        with open(env_file, "w") as f:
            f.write("# Legal AI Research System Environment Variables\n")
            f.write("OPENAI_API_KEY=your-openai-api-key-here\n")
            f.write("\n")
            f.write("# Optional: Customize these if needed\n")
            f.write("# DOCUMENTS_DIR=assets/decisions\n")
            f.write("# CHROMA_DB_PATH=./chroma_db\n")
        
        print("📝 Created backend/.env file. Please add your OpenAI API key to the backend/.env file")
        return False
    
    # Check if OpenAI API key is set
    with open(env_file, "r") as f:
        content = f.read()
        if "your-openai-api-key-here" in content or "OPENAI_API_KEY=" not in content:
            print("❌ Please set your OPENAI_API_KEY in the backend/.env file")
            return False
    
    print("✅ Environment file configured")
    return True

def install_frontend_deps():
    """Install frontend dependencies"""
    frontend_dir = Path(FRONTEND_DIR)
    if not frontend_dir.exists():
        print("❌ Frontend directory 'legal-ai' not found")
        return False
    
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json not found in frontend directory")
        return False
    
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        try:
            # Try different npm commands for Windows compatibility
            npm_commands = [
                ["npm", "install"],
                ["npm.cmd", "install"],
                ["npm.ps1", "install"]
            ]
            
            success = False
            for cmd in npm_commands:
                try:
                    subprocess.run(cmd, cwd=frontend_dir, check=True, shell=True)
                    success = True
                    break
                except subprocess.CalledProcessError:
                    continue
            
            if success:
                print("✅ Frontend dependencies installed")
            else:
                print("❌ Failed to install frontend dependencies")
                return False
        except Exception as e:
            print(f"❌ Failed to install frontend dependencies: {e}")
            return False
    else:
        print("✅ Frontend dependencies already installed")
    
    return True

def create_frontend_env():
    """Create frontend environment file"""
    frontend_dir = Path(FRONTEND_DIR)
    env_file = frontend_dir / ".env.local"
    
    if not env_file.exists():
        print("📝 Creating frontend environment file...")
        with open(env_file, "w") as f:
            f.write("# Frontend environment variables\n")
            f.write("NEXT_PUBLIC_API_URL=http://localhost:8000\n")
        print("✅ Frontend environment file created")

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend on http://localhost:8000")
    # Set PYTHONPATH to include current directory so backend module can be imported
    env = os.environ.copy()
    env['PYTHONPATH'] = os.getcwd()
    
    # Use the virtual environment's Python interpreter
    venv_python = os.path.join(os.getcwd(), "legenv", "bin", "python")
    if not os.path.exists(venv_python):
        # Fallback to system Python if venv not found
        venv_python = sys.executable
    
    return subprocess.Popen([
        venv_python, "-m", "uvicorn", 
        "backend.api_server:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ], env=env)

def start_frontend():
    """Start the Next.js frontend"""
    print("🚀 Starting Next.js frontend on http://localhost:3000")
    frontend_dir = Path(FRONTEND_DIR)
    
    # Try different npm commands for Windows compatibility
    npm_commands = [
        ["npm", "run", "dev"],
        ["npm.cmd", "run", "dev"],
        ["npm.ps1", "run", "dev"]
    ]
    
    for cmd in npm_commands:
        try:
            return subprocess.Popen(cmd, cwd=frontend_dir, shell=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    # If all fail, raise an error
    raise RuntimeError("Could not start frontend - npm not found")

def main():
    """Main startup function"""
    print("⚖️  Legal AI Research System Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_env_file():
        sys.exit(1)
    
    # Install frontend dependencies
    if not install_frontend_deps():
        sys.exit(1)
    
    # Create frontend environment
    create_frontend_env()
    
    # Start services
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend
        backend_process = start_backend()
        time.sleep(3)  # Give backend time to start
        
        # Start frontend
        frontend_process = start_frontend()
        
        print("\n" + "=" * 50)
        print("🎉 Legal AI Research System is starting!")
        print("📊 Backend API: http://localhost:8000")
        print("🌐 Frontend UI: http://localhost:3000")
        print("📖 API Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop both services")
        print("=" * 50)
        
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped")
                break
            
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped")
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
    
    finally:
        # Cleanup processes
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        
        print("👋 Services stopped. Goodbye!")

if __name__ == "__main__":
    main()