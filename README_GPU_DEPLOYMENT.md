# 🚀 Quick Start - Local GPU Deployment

Deploy your Legal AI Research System on your RTX 5060 Ti with ngrok in just a few steps!

## 🎯 One-Click Deployment

### Windows Users:
```cmd
# Double-click or run in Command Prompt:
start_local_gpu.bat
```

### Linux/Mac Users:
```bash
# Make executable and run:
chmod +x start_local_gpu.sh
./start_local_gpu.sh
```

### Or use Python directly:
```bash
python deploy_local_gpu.py
```

## 📋 Prerequisites Checklist

Before running the deployment script, ensure you have:

- [ ] **RTX 5060 Ti** with latest NVIDIA drivers installed
- [ ] **Python 3.8+** installed
- [ ] **Node.js 18+** and npm installed  
- [ ] **Ngrok** installed and authenticated
- [ ] **OpenAI API Key** ready
- [ ] **10GB+ free disk space**

## 🔑 Required Setup

1. **Get OpenAI API Key:**
   - Visit: https://platform.openai.com/api-keys
   - Create new key and copy it

2. **Install and setup Ngrok:**
   - Download from: https://ngrok.com/download
   - Sign up at: https://dashboard.ngrok.com/signup
   - Get auth token: https://dashboard.ngrok.com/get-started/your-authtoken
   - Run: `ngrok authtoken YOUR_AUTH_TOKEN`

3. **Create .env file:**
   ```bash
   # In your project root, create .env file:
   OPENAI_API_KEY=your-openai-api-key-here
   ```

## 🎉 What the Script Does

The automated deployment script will:

1. ✅ **Check Prerequisites** - Verify GPU, Python, Node.js, ngrok
2. ✅ **Install Dependencies** - GPU-optimized packages
3. ✅ **Configure Environment** - Set up GPU settings
4. ✅ **Start Ngrok Tunnels** - Create public URLs
5. ✅ **Launch Backend** - FastAPI server on port 8000
6. ✅ **Launch Frontend** - Next.js on port 3000
7. ✅ **Display URLs** - Show local and public access links

## 🌐 Access Points

After successful deployment:

### Local Access:
- **Application:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Public Access (via Ngrok):
- **Application:** https://random-id.ngrok.io
- **API:** https://another-id.ngrok.io
- **Ngrok Dashboard:** http://localhost:4040

## ⚡ Performance Features

Your RTX 5060 Ti deployment includes:

- 🚀 **GPU-Accelerated Models** - Faster inference
- 💾 **Local Model Caching** - No re-downloads
- 🔧 **Memory Optimization** - Efficient VRAM usage
- 📊 **Real-time Monitoring** - GPU usage tracking
- 🌐 **Global Access** - Share via ngrok URLs

## 🛑 Stopping Services

Press `Ctrl+C` in the deployment script terminal to stop all services gracefully.

## 🆘 Troubleshooting

### Common Issues:

1. **GPU Not Found:**
   ```bash
   nvidia-smi  # Should show your RTX 5060 Ti
   ```

2. **Ngrok Not Authenticated:**
   ```bash
   ngrok authtoken YOUR_AUTH_TOKEN
   ```

3. **Port Already in Use:**
   ```bash
   # Windows:
   netstat -ano | findstr :3000
   taskkill /PID <PID> /F
   
   # Linux/Mac:
   lsof -ti:3000 | xargs kill
   ```

4. **Out of Memory:**
   - Restart the deployment script
   - Check GPU memory: `nvidia-smi`

## 📖 Full Documentation

For detailed setup instructions, troubleshooting, and advanced configuration, see:
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

## 🎯 Ready to Deploy?

Run the deployment script and start using your GPU-powered Legal AI Research System accessible from anywhere!

```bash
python deploy_local_gpu.py
```
