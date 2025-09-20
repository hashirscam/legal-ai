@echo off
REM Windows batch script to start Legal AI Research System on local GPU with ngrok
REM For RTX 5060 Ti deployment

echo ============================================================
echo Legal AI Research System - Local GPU Deployment
echo RTX 5060 Ti Optimized with Ngrok Tunneling
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "backend\api_server.py" (
    echo ERROR: Please run this script from the legal-ai project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Starting GPU deployment...
echo.

REM Run the deployment script
python deploy_local_gpu.py

if errorlevel 1 (
    echo.
    echo Deployment failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo Deployment completed successfully!
pause
