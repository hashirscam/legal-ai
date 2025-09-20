# 🚀 Local GPU Deployment Guide - Legal AI Research System

Deploy your Legal AI Research System on your local RTX 5060 Ti with ngrok tunneling for external access.

## 📋 Prerequisites

### 1. Hardware Requirements
- **NVIDIA RTX 5060 Ti** (or compatible GPU)
- **16GB+ RAM** recommended
- **10GB+ free disk space**

### 2. Software Requirements
- **Python 3.8+** (3.9-3.11 recommended)
- **Node.js 18+** and npm
- **NVIDIA Drivers** (latest version)
- **CUDA Toolkit 11.8+** (optional but recommended)
- **Git**

### 3. Required Accounts
- **OpenAI API Key** (required for LLM functionality)
- **Ngrok Account** (free tier available)

---

## 🛠️ Step-by-Step Installation

### Step 1: Install NVIDIA Drivers and CUDA

1. **Download and install latest NVIDIA drivers:**
   - Visit: https://www.nvidia.com/drivers
   - Select RTX 5060 Ti and your OS
   - Download and install

2. **Verify GPU detection:**
   ```bash
   nvidia-smi
   ```
   You should see your RTX 5060 Ti listed.

3. **Install CUDA Toolkit (Optional but recommended):**
   - Visit: https://developer.nvidia.com/cuda-downloads
   - Download CUDA 11.8 or 12.x
   - Follow installation instructions

### Step 2: Install Ngrok

1. **Download ngrok:**
   - Visit: https://ngrok.com/download
   - Download for your operating system

2. **Install ngrok:**
   
   **Windows:**
   ```powershell
   # Extract to a folder and add to PATH, or use chocolatey:
   choco install ngrok
   ```
   
   **Linux/Mac:**
   ```bash
   # Using package manager or manual install
   wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
   tar xvzf ngrok-v3-stable-linux-amd64.tgz
   sudo mv ngrok /usr/local/bin
   ```

3. **Sign up and get auth token:**
   - Sign up at: https://dashboard.ngrok.com/signup
   - Copy your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken

4. **Configure ngrok:**
   ```bash
   ngrok authtoken YOUR_AUTH_TOKEN_HERE
   ```

### Step 3: Clone and Setup the Project

1. **Navigate to your project:**
   ```bash
   cd /path/to/your/legal-ai
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Or create .env manually
   ```

3. **Edit .env file and add your API keys:**
   ```bash
   # Required
   OPENAI_API_KEY=your-openai-api-key-here
   
   # Optional
   GEMINI_API_KEY=your-gemini-api-key-here
   GEMINI_MODEL=gemini-2.5-flash
   
   # GPU Settings (will be auto-configured)
   CUDA_VISIBLE_DEVICES=0
   TOKENIZERS_PARALLELISM=false
   ```

### Step 4: Run the Automated Deployment

The easiest way is to use our automated deployment script:

```bash
python deploy_local_gpu.py
```

This script will:
- ✅ Check all prerequisites
- ✅ Install GPU-optimized dependencies
- ✅ Configure ngrok tunnels
- ✅ Setup environment variables
- ✅ Start all services
- ✅ Provide access URLs

---

## 🔧 Manual Deployment (Alternative)

If you prefer manual control:

### Step 1: Install Dependencies

```bash
# Install GPU-optimized requirements
pip install -r requirements-gpu.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 2: Configure Ngrok

```bash
# Copy ngrok config to the right location
mkdir -p ~/.ngrok2
cp ngrok.yml ~/.ngrok2/ngrok.yml
```

### Step 3: Start Services Manually

**Terminal 1 - Start Ngrok Frontend Tunnel:**
```bash
ngrok http 3000 --log=stdout
```

**Terminal 2 - Start Backend (Local Only):**
```bash
# Set GPU environment variables
export CUDA_VISIBLE_DEVICES=0
export TOKENIZERS_PARALLELISM=false

# Start FastAPI server
python -m uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 - Configure and Start Frontend:**
```bash
cd frontend

# Configure frontend to use local backend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start Next.js
npm run dev
```

---

## 🌐 Access Your Application

After successful deployment, you'll have access to:

### Local Access:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000 (SECURE - Local Only)
- **API Documentation:** http://localhost:8000/docs

### External Access (via ngrok):
- **Frontend:** https://your-frontend-id.ngrok.io
- **Ngrok Dashboard:** http://localhost:4040

### Security Model:
- **Frontend:** Publicly accessible via ngrok (safe to share)
- **Backend:** Local only (secure, not exposed to internet)
- **Data Processing:** All AI processing happens locally on your GPU

### Sharing Access:
Share the ngrok frontend URL with others to give them access to your locally hosted Legal AI system! The backend remains secure on your local machine.

---

## 🔍 Monitoring and Troubleshooting

### GPU Monitoring:
```bash
# Monitor GPU usage
nvidia-smi -l 1

# Check GPU memory
nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv
```

### Service Health Checks:
```bash
# Check backend health
curl http://localhost:8000/health

# Check ngrok tunnels
curl http://localhost:4040/api/tunnels
```

### Common Issues:

#### 1. GPU Not Detected
```bash
# Verify drivers
nvidia-smi

# Check CUDA installation
nvcc --version

# Reinstall drivers if needed
```

#### 2. Ngrok Auth Issues
```bash
# Reconfigure auth token
ngrok authtoken YOUR_AUTH_TOKEN_HERE

# Check config
ngrok config check
```

#### 3. Port Already in Use
```bash
# Find and kill processes using ports 3000 or 8000
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Kill process by PID
taskkill /PID <PID_NUMBER> /F
```

#### 4. CORS Issues
The backend is already configured to accept ngrok domains. If you still face CORS issues:
1. Check that frontend `.env.local` has the correct backend URL
2. Restart both frontend and backend services
3. Clear browser cache

#### 5. Out of GPU Memory
```bash
# Monitor memory usage
nvidia-smi

# Reduce batch sizes in code or restart services
```

---

## ⚡ Performance Optimization

### GPU Settings for RTX 5060 Ti:
```bash
# Add to your .env file:
TRANSFORMERS_CACHE=./models_cache
HF_HOME=./models_cache
TORCH_HOME=./models_cache

# Enable memory optimization
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Model Caching:
Models will be cached locally in `./models_cache/` to avoid re-downloading.

### Memory Management:
The RTX 5060 Ti has 16GB VRAM, which should handle most models. If you encounter OOM errors:
1. Restart the application to clear GPU memory
2. Reduce batch sizes in the configuration
3. Use model quantization options

---

## 🛑 Stopping the Services

### Automated Script:
Press `Ctrl+C` in the terminal running `deploy_local_gpu.py`

### Manual Shutdown:
1. Stop ngrok tunnels (`Ctrl+C` in respective terminals)
2. Stop backend server (`Ctrl+C`)
3. Stop frontend server (`Ctrl+C`)

### Clean GPU Memory:
```bash
# Clear GPU memory if needed
nvidia-smi --gpu-reset
```

---

## 🔐 Security Considerations

1. **API Keys:** Never commit `.env` files with real API keys
2. **Ngrok URLs:** These are public - don't share sensitive data
3. **Firewall:** Ensure your local firewall allows the required ports
4. **Updates:** Keep ngrok and dependencies updated

---

## 🆘 Support

If you encounter issues:

1. **Check logs:**
   - Backend logs in terminal
   - Ngrok logs at http://localhost:4040
   - Browser console for frontend errors

2. **Verify setup:**
   ```bash
   # Run deployment script in check mode
   python deploy_local_gpu.py --check-only
   ```

3. **Common solutions:**
   - Restart all services
   - Clear browser cache
   - Check API key validity
   - Ensure GPU drivers are updated

---

## 🎉 Success!

You now have a fully functional Legal AI Research System running on your local RTX 5060 Ti, accessible from anywhere via ngrok tunnels!

The system provides:
- ⚡ GPU-accelerated performance
- 🌐 Global accessibility via ngrok
- 📊 Real-time progress tracking
- 🔍 Comprehensive legal research capabilities
- 💾 Local data control and privacy
