#!/usr/bin/env python3
"""
Check scraping progress and show statistics
"""

import json
from pathlib import Path

def check_progress():
    """Check current scraping progress."""
    output_dir = Path("scraped_documents")
    progress_file = output_dir / "scraping_progress.json"
    document_list_file = output_dir / "document_list.json"
    documents_dir = output_dir / "documents"
    
    print("=" * 60)
    print("SCRAPING PROGRESS REPORT")
    print("=" * 60)
    
    # Check if progress file exists
    if progress_file.exists():
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                progress = json.load(f)
            
            print(f"Last session progress:")
            print(f"  Completed: {progress.get('completed_docs', 0)}")
            print(f"  Total: {progress.get('total_docs', 0)}")
            print(f"  Last document: {progress.get('last_doc_title', 'Unknown')}")
            print(f"  Last update: {progress.get('timestamp', 'Unknown')}")
        except Exception as e:
            print(f"Error reading progress file: {e}")
    else:
        print("No progress file found (first run)")
    
    print()
    
    # Check document list
    if document_list_file.exists():
        try:
            with open(document_list_file, "r", encoding="utf-8") as f:
                documents = json.load(f)
            print(f"Total documents in list: {len(documents)}")
        except Exception as e:
            print(f"Error reading document list: {e}")
    else:
        print("No document list found")
    
    print()
    
    # Check downloaded files
    if documents_dir.exists():
        downloaded_files = list(documents_dir.glob("*.html"))
        print(f"Downloaded files: {len(downloaded_files)}")
        
        if downloaded_files:
            print("\nRecent downloads:")
            # Sort by modification time, newest first
            recent_files = sorted(downloaded_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
            for file in recent_files:
                print(f"  - {file.name}")
    else:
        print("No documents directory found")
    
    print()
    print("=" * 60)
    print("To resume scraping, run: python canlii_scraper.py")
    print("To start fresh, run: python canlii_scraper.py --no-resume")
    print("=" * 60)

if __name__ == "__main__":
    check_progress()
