# Resume Functionality Guide

The CanLII scraper now includes resume functionality to continue scraping from where it left off instead of starting over.

## Features

- **Automatic Resume**: The scraper automatically detects already downloaded documents and skips them
- **Progress Tracking**: Saves progress after each successful download
- **Smart Detection**: Checks existing files to determine what's already been downloaded
- **Flexible Options**: Can start fresh or resume from previous session

## How to Use

### Resume Scraping (Default)
```bash
python canlii_scraper.py
```
This will automatically resume from where the previous session left off.

### Start Fresh
```bash
python canlii_scraper.py --no-resume
```
This will start from the beginning, but will still skip already downloaded files.

### Check Progress
```bash
python check_progress.py
```
This shows the current status of downloaded files and progress.

## How It Works

1. **File Detection**: The scraper checks the `scraped_documents/documents/` directory for existing HTML files
2. **Progress Tracking**: Saves progress to `scraped_documents/scraping_progress.json` after each successful download
3. **Smart Skipping**: When resuming, it skips documents that already exist as files
4. **Error Recovery**: If the scraper encounters access denied errors, you can simply restart it and it will continue from the last successful download

## Files Created

- `scraping_progress.json`: Contains progress information (completed count, total count, last document, timestamp)
- `document_list.json`: Complete list of all documents to be scraped
- `documents/*.html`: Individual scraped documents

## Example Output

When resuming, you'll see output like:
```
Starting with resume functionality enabled
Resuming from previous session: 123/374 documents completed
Skipped 123 already downloaded documents
Starting to scrape 251 remaining documents...
Progress: 124/374 - R. v. NextDocument
```

## Troubleshooting

- If you want to re-download a specific document, delete its HTML file and run the scraper
- If you want to start completely fresh, delete the `scraping_progress.json` file and run with `--no-resume`
- The scraper will automatically handle access denied errors by continuing from the last successful download
