#!/bin/bash
# Linux/Mac shell script to start Legal AI Research System on local GPU with ngrok
# For RTX 5060 Ti deployment

echo "============================================================"
echo "Legal AI Research System - Local GPU Deployment"
echo "RTX 5060 Ti Optimized with Ngrok Tunneling"
echo "============================================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Check if we're in the right directory
if [ ! -f "backend/api_server.py" ]; then
    echo "ERROR: Please run this script from the legal-ai project root directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "Starting GPU deployment..."
echo

# Run the deployment script
$PYTHON_CMD deploy_local_gpu.py

if [ $? -ne 0 ]; then
    echo
    echo "Deployment failed. Please check the error messages above."
    exit 1
fi

echo
echo "Deployment completed successfully!"
