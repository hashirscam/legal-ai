@echo off
echo CanLII Legal Document Scraper - Installation
echo ============================================

echo.
echo Installing Python dependencies...
pip install playwright==1.40.0 requests==2.31.0 beautifulsoup4==4.12.2 lxml==4.9.3 pandas==2.1.4 aiohttp==3.9.1 asyncio-throttle==1.0.2

echo.
echo Installing Playwright browsers...
playwright install chromium

echo.
echo Creating output directories...
mkdir scraped_documents 2>nul
mkdir scraped_documents\documents 2>nul
mkdir scraped_documents\logs 2>nul
mkdir test_scraped_documents 2>nul
mkdir test_scraped_documents\documents 2>nul
mkdir test_scraped_documents\logs 2>nul

echo.
echo Installation completed!
echo.
echo To test the scraper:
echo   python test_scraper.py
echo.
echo To run the full scraper:
echo   python canlii_scraper.py
echo.
pause
