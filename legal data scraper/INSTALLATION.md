# Installation Guide

## Quick Installation (Windows)

1. **Double-click `install.bat`** - This will automatically install all dependencies.

## Manual Installation

If the batch file doesn't work, follow these steps:

### 1. Install Python Dependencies

Open Command Prompt or PowerShell and run:

```bash
pip install playwright==1.40.0
pip install requests==2.31.0
pip install beautifulsoup4==4.12.2
pip install lxml==4.9.3
pip install pandas==2.1.4
pip install aiohttp==3.9.1
pip install asyncio-throttle==1.0.2
```

### 2. Install Playwright Browser

```bash
playwright install chromium
```

### 3. Create Output Directories

```bash
mkdir scraped_documents
mkdir scraped_documents\documents
mkdir scraped_documents\logs
mkdir test_scraped_documents
mkdir test_scraped_documents\documents
mkdir test_scraped_documents\logs
```

## Conda Environment (Recommended)

If you're using conda (especially the `skyc` environment):

```bash
conda activate skyc
pip install -r requirements.txt
playwright install chromium
```

## Testing the Installation

Run the test scraper to verify everything works:

```bash
python test_scraper.py
```

This will:
- Open a browser window
- Navigate to CanLII
- Scrape 5 test documents
- Save them to `test_scraped_documents/`

## Troubleshooting

### Common Issues:

1. **"playwright not found"**: Run `pip install playwright` then `playwright install chromium`
2. **"Permission denied"**: Run Command Prompt as Administrator
3. **"Module not found"**: Make sure you're in the correct directory and Python environment

### Verification Commands:

```bash
python -c "import playwright; print('Playwright OK')"
python -c "import aiohttp; print('aiohttp OK')"
python -c "import asyncio_throttle; print('asyncio-throttle OK')"
```

## Next Steps

Once installation is complete:

1. **Test first**: `python test_scraper.py`
2. **Full scrape**: `python canlii_scraper.py`

The scraper will create a visible browser window to handle any captchas that might appear.
