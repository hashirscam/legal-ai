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
        # Try different ways to find node and npm on Windows
        node_commands = ["node", "node.exe"]
        npm_commands = ["npm", "npm.cmd", "npm.exe"]
        
        node_found = False
        npm_found = False
        
        for node_cmd in node_commands:
            try:
                result = subprocess.run([node_cmd, "--version"], check=True, capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    node_found = True
                    print(f"✅ Node.js found: {result.stdout.strip()}")
                    break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        for npm_cmd in npm_commands:
            try:
                result = subprocess.run([npm_cmd, "--version"], check=True, capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    npm_found = True
                    print(f"✅ npm found: {result.stdout.strip()}")
                    break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        if not node_found or not npm_found:
            print("❌ Node.js or npm not found. Please install Node.js")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Node.js/npm: {e}")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists with required variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Creating .env file with default settings...")
        
        with open(".env", "w") as f:
            f.write("# Legal AI Research System Environment Variables\n")
            f.write("OPENAI_API_KEY=your-openai-api-key-here\n")
            f.write("\n")
            f.write("# Optional: Customize these if needed\n")
            f.write("# DOCUMENTS_DIR=assets/decisions\n")
            f.write("# CHROMA_DB_PATH=./chroma_db\n")
        
        print("📝 Created .env file. Please add your OpenAI API key to the .env file")
        return False
    
    # Check if OpenAI API key is set
    with open(".env", "r") as f:
        content = f.read()
        if "your-openai-api-key-here" in content or "OPENAI_API_KEY=" not in content:
            print("❌ Please set your OPENAI_API_KEY in the .env file")
            return False
    
    print("✅ Environment file configured")
    return True

def install_frontend_deps():
    """Install frontend dependencies"""
    frontend_dir = Path("legal-ai")
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
            # Use npm.cmd on Windows, npm on other systems
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            subprocess.run([npm_cmd, "install"], cwd=frontend_dir, check=True, shell=True)
            print("✅ Frontend dependencies installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install frontend dependencies")
            return False
    else:
        print("✅ Frontend dependencies already installed")
    
    return True

def create_frontend_env():
    """Create frontend environment file"""
    frontend_dir = Path("legal-ai")
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
    return subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "api_server:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ])

def start_frontend():
    """Start the Next.js frontend"""
    print("🚀 Starting Next.js frontend on http://localhost:3000")
    frontend_dir = Path("legal-ai")
    
    # Use npm.cmd on Windows, npm on other systems
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    
    return subprocess.Popen([
        npm_cmd, "run", "dev"
    ], cwd=frontend_dir, shell=True)

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
