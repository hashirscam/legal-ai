@echo off
echo HTML to Text Converter for Legal Documents
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.6 or higher and try again
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import bs4, lxml" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install required packages
        pause
        exit /b 1
    )
)

REM Run the converter
if "%1"=="test" (
    echo TEST MODE: Converting 5 HTML files from documents folder...
    python html_to_txt_converter.py --test
) else (
    echo Converting all HTML files from documents to converted_documents...
    python html_to_txt_converter.py
)

echo.
echo Conversion complete!
pause
