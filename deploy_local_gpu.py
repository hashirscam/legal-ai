#!/usr/bin/env python3
"""
Local GPU Deployment Script for Legal AI Research System
Optimized for RTX 5060 Ti with ngrok tunneling
"""

import subprocess
import sys
import os
import time
import platform
import psutil
import json
import signal
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message, color=Colors.OKGREEN):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(message):
    """Print formatted header"""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f"🚀 {message}", Colors.HEADER)
    print_colored(f"{'='*60}", Colors.HEADER)

def check_gpu():
    """Check if NVIDIA GPU is available"""
    print_header("Checking GPU Availability")
    
    try:
        # Check nvidia-smi
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print_colored("✅ NVIDIA GPU detected!", Colors.OKGREEN)
            print(result.stdout)
            return True
        else:
            print_colored("❌ nvidia-smi not found or failed", Colors.FAIL)
            return False
    except FileNotFoundError:
        print_colored("❌ nvidia-smi not found. Please install NVIDIA drivers.", Colors.FAIL)
        return False

def check_python_version():
    """Check Python version compatibility"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible", Colors.OKGREEN)
        return True
    else:
        print_colored(f"❌ Python {version.major}.{version.minor} is not supported. Please use Python 3.8+", Colors.FAIL)
        return False

def install_gpu_dependencies():
    """Install GPU-optimized dependencies"""
    print_header("Installing GPU-Optimized Dependencies")
    
    gpu_requirements = [
        "torch>=2.0.0",
        "sentence-transformers>=2.2.0",
        "accelerate>=0.20.0",
        "bitsandbytes>=0.41.0",
        "transformers>=4.30.0",
        "pynvml>=11.0.0",  # NVIDIA GPU monitoring
    ]
    
    for package in gpu_requirements:
        print_colored(f"Installing {package}...", Colors.OKBLUE)
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print_colored(f"✅ {package} installed successfully", Colors.OKGREEN)
        except subprocess.CalledProcessError as e:
            print_colored(f"❌ Failed to install {package}: {e}", Colors.FAIL)
            return False
    
    return True

def install_base_requirements():
    """Install base requirements"""
    print_header("Installing Base Requirements")
    
    if os.path.exists("requirements.txt"):
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True)
            print_colored("✅ Base requirements installed successfully", Colors.OKGREEN)
            return True
        except subprocess.CalledProcessError as e:
            print_colored(f"❌ Failed to install requirements: {e}", Colors.FAIL)
            return False
    else:
        print_colored("❌ requirements.txt not found", Colors.FAIL)
        return False

def check_ngrok():
    """Check if ngrok is installed and configured"""
    print_header("Checking Ngrok Installation")
    
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_colored("✅ Ngrok is installed", Colors.OKGREEN)
            print_colored(f"Version: {result.stdout.strip()}", Colors.OKBLUE)
            return True
        else:
            print_colored("❌ Ngrok not working properly", Colors.FAIL)
            return False
    except FileNotFoundError:
        print_colored("❌ Ngrok not found. Please install ngrok first.", Colors.FAIL)
        print_colored("Download from: https://ngrok.com/download", Colors.WARNING)
        return False

def setup_environment():
    """Setup environment variables for GPU deployment"""
    print_header("Setting Up Environment")
    
    env_vars = {
        'CUDA_VISIBLE_DEVICES': '0',  # Use first GPU
        'TOKENIZERS_PARALLELISM': 'false',  # Avoid tokenizer warnings
        'TRANSFORMERS_CACHE': './models_cache',  # Local model cache
        'HF_HOME': './models_cache',  # Hugging Face cache
        'TORCH_HOME': './models_cache',  # PyTorch cache
    }
    
    # Create .env.local file for local deployment
    env_content = []
    
    # Copy existing .env if it exists
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content.extend(f.readlines())
    
    # Add GPU-specific variables
    env_content.append("\n# GPU Deployment Settings\n")
    for key, value in env_vars.items():
        env_content.append(f"{key}={value}\n")
        os.environ[key] = value
    
    # Write to .env.local
    with open('.env.local', 'w') as f:
        f.writelines(env_content)
    
    print_colored("✅ Environment variables configured", Colors.OKGREEN)
    
    # Create models cache directory
    os.makedirs('./models_cache', exist_ok=True)
    print_colored("✅ Models cache directory created", Colors.OKGREEN)

def install_frontend_dependencies():
    """Install frontend dependencies"""
    print_header("Installing Frontend Dependencies")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print_colored("❌ Frontend directory not found", Colors.FAIL)
        return False
    
    try:
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        print_colored("✅ Frontend dependencies installed", Colors.OKGREEN)
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Failed to install frontend dependencies: {e}", Colors.FAIL)
        return False

def create_ngrok_config():
    """Create ngrok configuration file"""
    print_header("Creating Ngrok Configuration")
    
    ngrok_config = {
        "version": "2",
        "tunnels": {
            "legal-ai-backend": {
                "proto": "http",
                "addr": "8000",
                "bind_tls": True,
                "inspect": False
            },
            "legal-ai-frontend": {
                "proto": "http", 
                "addr": "3000",
                "bind_tls": True,
                "inspect": False
            }
        }
    }
    
    # Create ngrok config directory
    ngrok_dir = Path.home() / ".ngrok2"
    ngrok_dir.mkdir(exist_ok=True)
    
    config_file = ngrok_dir / "ngrok.yml"
    
    # Only create if it doesn't exist or update tunnels section
    if config_file.exists():
        try:
            import yaml
            with open(config_file, 'r') as f:
                existing_config = yaml.safe_load(f) or {}
            
            if 'tunnels' not in existing_config:
                existing_config['tunnels'] = {}
            
            # Only add frontend tunnel (remove backend tunnel if it exists)
            if 'legal-ai-backend' in existing_config['tunnels']:
                del existing_config['tunnels']['legal-ai-backend']
            
            existing_config['tunnels'].update(ngrok_config['tunnels'])
            
            with open(config_file, 'w') as f:
                yaml.dump(existing_config, f)
                
        except ImportError:
            # Fallback to simple append if PyYAML not available
            with open(config_file, 'a') as f:
                f.write("\ntunnels:\n")
                f.write("  legal-ai-frontend:\n")
                f.write("    proto: http\n")
                f.write("    addr: 3000\n")
                f.write("    bind_tls: true\n")
                f.write("    inspect: false\n")
    else:
        # Create simple YAML config (frontend only)
        with open(config_file, 'w') as f:
            f.write("version: '2'\n")
            f.write("tunnels:\n")
            f.write("  legal-ai-frontend:\n")
            f.write("    proto: http\n")
            f.write("    addr: 3000\n")
            f.write("    bind_tls: true\n")
            f.write("    inspect: false\n")
    
    print_colored("✅ Ngrok configuration created", Colors.OKGREEN)
    print_colored(f"Config file: {config_file}", Colors.OKBLUE)

def start_ngrok_frontend_tunnel():
    """Start ngrok tunnel for frontend only (backend stays local)"""
    print_header("Starting Ngrok Frontend Tunnel")
    
    try:
        # Start only frontend tunnel
        frontend_process = subprocess.Popen([
            'ngrok', 'http', '3000',
            '--log=stdout',
            '--log-level=info'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)  # Wait for tunnel to establish
        
        print_colored("✅ Ngrok frontend tunnel started", Colors.OKGREEN)
        print_colored("ℹ️  Backend remains local for security and performance", Colors.OKBLUE)
        
        # Get tunnel URL
        try:
            api_result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'], 
                                      capture_output=True, text=True)
            if api_result.returncode == 0:
                tunnels_data = json.loads(api_result.stdout)
                for tunnel in tunnels_data.get('tunnels', []):
                    if tunnel['config']['addr'] == 'localhost:3000':
                        print_colored(f"🌐 Frontend (Public): {tunnel['public_url']}", Colors.OKCYAN)
                        return frontend_process, tunnel['public_url']
            else:
                print_colored("ℹ️  Check ngrok dashboard at http://localhost:4040", Colors.WARNING)
        except:
            print_colored("ℹ️  Check ngrok dashboard at http://localhost:4040", Colors.WARNING)
            
        return frontend_process, None
        
    except Exception as e:
        print_colored(f"❌ Failed to start ngrok frontend tunnel: {e}", Colors.FAIL)
        return None, None

def start_backend():
    """Start the FastAPI backend server"""
    print_header("Starting Backend Server")
    
    try:
        # Set environment variables for GPU
        env = os.environ.copy()
        env.update({
            'CUDA_VISIBLE_DEVICES': '0',
            'TOKENIZERS_PARALLELISM': 'false',
        })
        
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "backend.api_server:app",
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], env=env)
        
        print_colored("✅ Backend server starting on port 8000", Colors.OKGREEN)
        return backend_process
        
    except Exception as e:
        print_colored(f"❌ Failed to start backend: {e}", Colors.FAIL)
        return None

def start_frontend():
    """Start the Next.js frontend server"""
    print_header("Starting Frontend Server")
    
    frontend_dir = Path("frontend")
    
    try:
        frontend_process = subprocess.Popen([
            "npm", "run", "dev"
        ], cwd=frontend_dir)
        
        print_colored("✅ Frontend server starting on port 3000", Colors.OKGREEN)
        return frontend_process
        
    except Exception as e:
        print_colored(f"❌ Failed to start frontend: {e}", Colors.FAIL)
        return None

def create_frontend_env_with_local_backend():
    """Create frontend environment file pointing to local backend"""
    print_header("Configuring Frontend for Local Backend")
    
    try:
        # Always use local backend URL
        backend_url = "http://localhost:8000"
        
        # Create frontend .env.local
        frontend_env_path = Path("frontend") / ".env.local"
        with open(frontend_env_path, 'w') as f:
            f.write(f"NEXT_PUBLIC_API_URL={backend_url}\n")
            f.write("NODE_ENV=development\n")
        
        print_colored(f"✅ Frontend configured with local backend URL: {backend_url}", Colors.OKGREEN)
        print_colored("ℹ️  Frontend will connect to local backend (secure)", Colors.OKBLUE)
        
    except Exception as e:
        print_colored(f"⚠️  Could not configure frontend environment: {e}", Colors.WARNING)
        print_colored("You may need to manually update frontend/.env.local", Colors.WARNING)

def cleanup_processes(*processes):
    """Clean up running processes"""
    print_header("Cleaning Up Processes")
    
    for process in processes:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
                print_colored("✅ Process terminated gracefully", Colors.OKGREEN)
            except subprocess.TimeoutExpired:
                process.kill()
                print_colored("⚠️  Process killed forcefully", Colors.WARNING)
            except Exception as e:
                print_colored(f"❌ Error terminating process: {e}", Colors.FAIL)

def main():
    """Main deployment function"""
    print_colored("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                Legal AI Research System                      ║
    ║              Local GPU Deployment Script                    ║
    ║                  RTX 5060 Ti Optimized                      ║
    ╚══════════════════════════════════════════════════════════════╝
    """, Colors.HEADER)
    
    # Store processes for cleanup
    processes = []
    
    def signal_handler(signum, frame):
        print_colored("\n🛑 Shutdown signal received. Cleaning up...", Colors.WARNING)
        cleanup_processes(*processes)
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Pre-flight checks
        if not check_python_version():
            return False
            
        if not check_gpu():
            print_colored("⚠️  GPU not detected. Continuing with CPU mode...", Colors.WARNING)
        
        if not check_ngrok():
            return False
        
        # Setup environment
        setup_environment()
        
        # Install dependencies
        if not install_base_requirements():
            return False
            
        if not install_gpu_dependencies():
            print_colored("⚠️  GPU dependencies failed. Continuing anyway...", Colors.WARNING)
        
        if not install_frontend_dependencies():
            return False
        
        # Configure ngrok for frontend only
        create_ngrok_config()
        
        # Start ngrok frontend tunnel only
        ngrok_frontend, frontend_url = start_ngrok_frontend_tunnel()
        if ngrok_frontend:
            processes.append(ngrok_frontend)
        
        time.sleep(5)  # Wait for tunnel to stabilize
        
        # Configure frontend to use local backend
        create_frontend_env_with_local_backend()
        
        # Start backend
        backend_process = start_backend()
        if backend_process:
            processes.append(backend_process)
        
        time.sleep(10)  # Wait for backend to start
        
        # Start frontend
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(frontend_process)
        
        # Success message
        print_header("🎉 Deployment Successful!")
        print_colored("Services are starting up...", Colors.OKGREEN)
        print_colored("Local Frontend: http://localhost:3000", Colors.OKCYAN)
        print_colored("Local Backend: http://localhost:8000 (SECURE - Local Only)", Colors.OKGREEN)
        if frontend_url:
            print_colored(f"Public Frontend: {frontend_url}", Colors.OKCYAN)
        print_colored("Ngrok Dashboard: http://localhost:4040", Colors.OKCYAN)
        print_colored("\n🔒 Backend stays local for security and performance", Colors.OKBLUE)
        print_colored("🌐 Frontend is publicly accessible via ngrok", Colors.OKBLUE)
        print_colored("\nPress Ctrl+C to stop all services", Colors.WARNING)
        
        # Keep script running
        try:
            while True:
                time.sleep(1)
                # Check if processes are still running
                for i, process in enumerate(processes):
                    if process and process.poll() is not None:
                        print_colored(f"⚠️  Process {i} has stopped unexpectedly", Colors.WARNING)
        except KeyboardInterrupt:
            pass
        
    except Exception as e:
        print_colored(f"❌ Deployment failed: {e}", Colors.FAIL)
        return False
    finally:
        cleanup_processes(*processes)
    
    return True

if __name__ == "__main__":
    main()
