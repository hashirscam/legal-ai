#!/usr/bin/env python3
"""
Demo script to show the scraping process working
This is a simplified version for demonstration
"""

import asyncio
import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Mock the imports for demo purposes
class MockThrottler:
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system storage."""
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    if len(filename) > 200:
        filename = filename[:200]
    return filename.strip()

def log_message(message: str, level: str = "INFO"):
    """Simple logging function."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Sample data that would be extracted from the website
sample_documents = [
    {
        "date": "2024-12-30",
        "title": "R. v. Flaro",
        "url": "https://www.canlii.org/en/on/oncj/doc/2024/2024oncj686/2024oncj686.html",
        "rv_case": True
    },
    {
        "date": "2024-12-24", 
        "title": "R. v. Lal",
        "url": "https://www.canlii.org/en/on/oncj/doc/2024/2024oncj724/2024oncj724.html",
        "rv_case": True
    },
    {
        "date": "2024-12-23",
        "title": "R. v. Foster", 
        "url": "https://www.canlii.org/en/on/oncj/doc/2024/2024oncj664/2024oncj664.html",
        "rv_case": True
    }
]

def demo_scraper():
    """Demonstrate the scraping process."""
    log_message("Starting CanLII Demo Scraper...")
    
    # Create output directory
    output_dir = Path("demo_scraped_documents")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "documents").mkdir(exist_ok=True)
    
    log_message(f"Created output directory: {output_dir}")
    
    # Filter R. v. documents (already filtered in sample)
    rv_documents = [doc for doc in sample_documents if doc['rv_case']]
    log_message(f"Found {len(rv_documents)} R. v. documents to scrape")
    
    # Save document list
    with open(output_dir / "document_list.json", "w", encoding="utf-8") as f:
        json.dump(rv_documents, f, indent=2, ensure_ascii=False)
    
    log_message("Saved document list to document_list.json")
    
    # Simulate scraping each document
    for i, doc in enumerate(rv_documents, 1):
        log_message(f"Progress: {i}/{len(rv_documents)} - {doc['title']}")
        
        # Create filename
        filename = f"{doc['date']}_{sanitize_filename(doc['title'])}.html"
        filepath = output_dir / "documents" / filename
        
        # Simulate HTML content (in real scraper, this would be from Playwright)
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{doc['title']}</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>{doc['title']}</h1>
    <p>Date: {doc['date']}</p>
    <p>URL: {doc['url']}</p>
    <p>This is a demo of the scraped content. In the real scraper, this would contain the full legal document HTML.</p>
    <div class="document-content">
        <h2>Case Summary</h2>
        <p>This would contain the actual legal document content from CanLII.</p>
    </div>
</body>
</html>"""
        
        # Save HTML content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        file_size = os.path.getsize(filepath)
        log_message(f"Saved: {filename} ({file_size:,} bytes)")
    
    log_message("Demo scraping completed successfully!")
    
    # Show results
    print("\n" + "=" * 60)
    print("DEMO SCRAPING RESULTS")
    print("=" * 60)
    print(f"Documents scraped: {len(rv_documents)}")
    print(f"Output directory: {output_dir}")
    print("\nFiles created:")
    
    for file in output_dir.glob("**/*"):
        if file.is_file():
            size = os.path.getsize(file)
            print(f"  - {file.relative_to(output_dir)} ({size:,} bytes)")
    
    print(f"\nThis demonstrates the scraper functionality.")
    print(f"The real scraper would use Playwright to:")
    print(f"  1. Navigate to CanLII website")
    print(f"  2. Handle JavaScript and captchas")
    print(f"  3. Extract all document links")
    print(f"  4. Download each document's HTML")
    print(f"  5. Save with organized filenames")

if __name__ == "__main__":
    demo_scraper()
