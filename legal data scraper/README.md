# CanLII Legal Document Scraper

A Python-based web scraper for extracting legal documents from CanLII (Canadian Legal Information Institute), specifically targeting "R. v." (Regina vs.) cases from the Ontario Court of Justice for 2024.

## Features

- **Playwright-based scraping**: Uses headful browser automation to handle JavaScript and potential captchas
- **Smart filtering**: Only scrapes documents that start with "R. v." in their titles
- **Robust error handling**: Includes retry logic and comprehensive logging
- **Rate limiting**: Respects server resources with configurable delays
- **Progress tracking**: Real-time progress updates and detailed logging
- **File organization**: Saves documents with sanitized filenames and proper directory structure

## Requirements

- Python 3.8+
- Conda environment (recommended: `skyc`)
- Internet connection

## Installation

1. **Activate your conda environment** (if using conda):
   ```bash
   conda activate skyc
   ```

2. **Run the setup script**:
   ```bash
   python setup.py
   ```

   This will:
   - Install all required Python packages
   - Install Playwright Chromium browser
   - Create necessary output directories

## Usage

### Test Run (Recommended First)

Before running the full scraper, test with a small subset:

```bash
python test_scraper.py
```

This will scrape only the first 5 "R. v." documents to verify everything works correctly.

### Full Scraping

Once the test is successful, run the full scraper:

```bash
python canlii_scraper.py
```

This will:
1. Navigate to the CanLII 2024 Ontario Court of Justice page
2. Extract all document links (handling pagination if needed)
3. Filter for documents starting with "R. v."
4. Scrape each document's HTML content
5. Save files with organized naming: `YYYY-MM-DD_Case_Title.html`

## Output Structure

```
scraped_documents/
├── documents/           # HTML files of scraped documents
├── logs/               # Scraping logs with timestamps
└── document_list.json  # List of all found documents
```

## Configuration

You can modify the scraper behavior by editing the parameters in the scripts:

- `delay`: Time between requests (default: 2.0 seconds)
- `output_dir`: Directory for saved files
- `max_documents`: For testing, limit number of documents

## Handling Captchas

The scraper runs in **headful mode** (visible browser window) to handle potential captchas:

- If a captcha appears, the browser window will be visible
- You can manually solve the captcha
- The scraper will continue automatically after the captcha is resolved

## Expected Results

Based on the analysis of the CanLII website:
- **Total documents in 2024**: ~687
- **"R. v." cases**: ~374 (estimated)
- **File sizes**: Typically 50-200KB per document
- **Total estimated time**: 12-25 minutes (with 2-second delays)

## Troubleshooting

### Common Issues

1. **Browser not found**: Run `playwright install chromium`
2. **Permission errors**: Ensure write permissions in the output directory
3. **Network timeouts**: Check internet connection and consider increasing delays
4. **Captcha blocking**: The headful browser should handle this automatically

### Logs

Check the log files in `scraped_documents/logs/` for detailed information about:
- Progress updates
- Error messages
- Successful downloads
- Captcha encounters

## Legal Considerations

- This scraper is designed for educational and research purposes
- CanLII provides public access to legal documents
- Please respect their terms of service and rate limits
- Consider the server load and use appropriate delays

## Technical Details

### Dependencies

- **Playwright**: Browser automation and JavaScript handling
- **aiohttp**: Async HTTP requests
- **asyncio-throttle**: Rate limiting
- **BeautifulSoup4**: HTML parsing (if needed)
- **pandas**: Data manipulation (if needed)

### Browser Configuration

The scraper uses Chromium with specific flags to:
- Avoid detection as an automated browser
- Handle modern web features
- Provide realistic user agent strings

## Support

If you encounter issues:

1. Check the log files for error details
2. Try running the test scraper first
3. Ensure your conda environment is activated
4. Verify internet connectivity

## License

This project is for educational purposes. Please respect CanLII's terms of service and use responsibly.
