#!/usr/bin/env python3
"""
CanLII Legal Document Scraper

This script scrapes legal documents from CanLII (Canadian Legal Information Institute)
focusing on documents that start with "R. v." (Regina vs. cases).

Features:
- Uses Playwright for handling JavaScript and potential captchas
- Handles pagination to get all documents
- Filters for "R. v." cases only
- Saves HTML content locally with proper file naming
- Includes rate limiting and error handling
"""

import asyncio
import os
import re
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import List, Dict, Optional

from playwright.async_api import async_playwright, Page, Browser
import aiohttp
from asyncio_throttle import Throttler


class CanLIIScraper:
    def __init__(self, output_dir: str = "scraped_documents", delay: float = 2.0):
        """
        Initialize the CanLII scraper.
        
        Args:
            output_dir: Directory to save scraped documents
            delay: Delay between requests in seconds
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.delay = delay
        self.throttler = Throttler(rate_limit=1, period=delay)
        
        # Create subdirectories
        (self.output_dir / "documents").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        
        # Setup logging
        self.log_file = self.output_dir / "logs" / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Resume functionality
        self.progress_file = self.output_dir / "scraping_progress.json"
        
    def log(self, message: str, level: str = "INFO"):
        """Log message to file and console."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system storage."""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        return filename.strip()
    
    def save_progress(self, completed_docs: int, total_docs: int, last_doc_title: str = None):
        """Save current scraping progress to file."""
        progress_data = {
            "completed_docs": completed_docs,
            "total_docs": total_docs,
            "last_doc_title": last_doc_title,
            "timestamp": datetime.now().isoformat()
        }
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
    
    def load_progress(self) -> Dict:
        """Load scraping progress from file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def get_existing_files(self) -> set:
        """Get set of already downloaded filenames."""
        documents_dir = self.output_dir / "documents"
        if not documents_dir.exists():
            return set()
        
        existing_files = set()
        for file_path in documents_dir.glob("*.html"):
            existing_files.add(file_path.name)
        return existing_files
    
    def is_document_downloaded(self, doc_info: Dict[str, str]) -> bool:
        """Check if a document has already been downloaded."""
        filename = f"{doc_info['date']}_{self.sanitize_filename(doc_info['title'])}.html"
        return filename in self.get_existing_files()
    
    async def get_all_document_links(self, page: Page) -> List[Dict[str, str]]:
        """
        Extract all document links from the CanLII page, handling "Show more results" button.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of document dictionaries with title, url, date, and rv_case flag
        """
        self.log("Starting to extract document links...")
        
        # Navigate to the main page
        await page.goto("https://www.canlii.org/on/oncj/nav/date/2024", wait_until="networkidle")
        
        # Accept cookies if present
        try:
            await page.click('button:has-text("Accept all cookies")', timeout=5000)
            await page.wait_for_timeout(1000)
        except:
            self.log("No cookie banner found or already accepted")
        
        all_documents = []
        max_attempts = 10  # Prevent infinite loops
        attempt = 0
        
        # Keep clicking "Show more results" until all documents are loaded
        while attempt < max_attempts:
            attempt += 1
            
            # Extract current page documents
            documents = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('table tbody tr');
                    const documents = [];
                    
                    rows.forEach(row => {
                        const dateCell = row.querySelector('td:first-child');
                        const decisionCell = row.querySelector('td:last-child');
                        
                        if (dateCell && decisionCell) {
                            const link = decisionCell.querySelector('a');
                            if (link) {
                                const title = link.textContent.trim();
                                const url = link.href;
                                const date = dateCell.textContent.trim();
                                
                                documents.push({
                                    date: date,
                                    title: title,
                                    url: url,
                                    rv_case: title.startsWith('R. v.')
                                });
                            }
                        }
                    });
                    
                    return documents;
                }
            """)
            
            # Update our document list (avoid duplicates)
            current_urls = {doc['url'] for doc in all_documents}
            new_docs = [doc for doc in documents if doc['url'] not in current_urls]
            all_documents.extend(new_docs)
            
            self.log(f"Attempt {attempt}: Found {len(documents)} documents on page, {len(all_documents)} total so far")
            
            # Check current status
            page_info = await page.evaluate("""
                () => {
                    const showingText = document.querySelector('body').textContent;
                    const showingMatch = showingText.match(/Showing (\\d+) of (\\d+) items/);
                    
                    // Look for "Show more results" button using text content search
                    const showMoreLink = Array.from(document.querySelectorAll('a, button')).find(el => 
                        el.textContent.toLowerCase().includes('show more') || 
                        el.textContent.toLowerCase().includes('load more') ||
                        el.textContent.toLowerCase().includes('more results')
                    );
                    
                    // Also check for common class names
                    const showMoreByClass = document.querySelector('[class*="show-more"], [class*="load-more"]');
                    
                    return {
                        showing: showingMatch ? parseInt(showingMatch[1]) : null,
                        total: showingMatch ? parseInt(showingMatch[2]) : null,
                        hasShowMore: !!(showMoreLink || showMoreByClass),
                        showMoreText: showMoreLink?.textContent || showMoreByClass?.textContent || null
                    };
                }
            """)
            
            self.log(f"Page info: {page_info}")
            
            # If we have all documents, break
            if page_info['showing'] and page_info['total'] and page_info['showing'] >= page_info['total']:
                self.log(f"Got all {page_info['total']} documents")
                break
            
            # If no "Show more results" button, try scrolling
            if not page_info['hasShowMore']:
                self.log("No 'Show more results' button found, trying scroll...")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(3000)
                
                # Check if scrolling loaded more documents
                new_count = await page.evaluate("document.querySelectorAll('table tbody tr').length")
                if new_count == len(documents):
                    self.log(f"No more documents loaded after scrolling. Got {len(all_documents)} documents total.")
                    break
                continue
            
            # Try to click "Show more results" button
            try:
                self.log(f"Attempting to click 'Show more results' button: {page_info['showMoreText']}")
                
                # Try multiple selectors for the "Show more" button
                clicked = False
                selectors = [
                    '[class*="show-more"]',
                    '[class*="load-more"]',
                    'a[href*="show"]',
                    'button[onclick*="show"]'
                ]
                
                for selector in selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        clicked = True
                        self.log(f"Successfully clicked button with selector: {selector}")
                        break
                    except:
                        continue
                
                # If standard selectors don't work, try finding by text content
                if not clicked:
                    clicked = await page.evaluate("""
                        () => {
                            const links = Array.from(document.querySelectorAll('a, button'));
                            const showMoreElement = links.find(el => 
                                el.textContent.toLowerCase().includes('show more') || 
                                el.textContent.toLowerCase().includes('load more') ||
                                el.textContent.toLowerCase().includes('more results')
                            );
                            if (showMoreElement) {
                                showMoreElement.click();
                                return true;
                            }
                            return false;
                        }
                    """)
                
                if clicked:
                    self.log("Waiting for more documents to load...")
                    await page.wait_for_timeout(3000)  # Wait for new content to load
                    await page.wait_for_load_state("networkidle", timeout=10000)
                else:
                    self.log("Could not find or click 'Show more results' button")
                    break
                    
            except Exception as e:
                self.log(f"Error clicking 'Show more results': {str(e)}")
                break
        
        # Filter for R. v. cases only
        rv_documents = [doc for doc in all_documents if doc['rv_case']]
        self.log(f"Found {len(rv_documents)} R. v. cases out of {len(all_documents)} total documents")
        
        return rv_documents
    
    async def scrape_document(self, page: Page, doc_info: Dict[str, str]) -> bool:
        """
        Scrape a single document and save its HTML content.
        
        Args:
            page: Playwright page object
            doc_info: Document information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.throttler:
                self.log(f"Scraping: {doc_info['title']}")
                
                # Navigate to document page
                await page.goto(doc_info['url'], wait_until="networkidle")
                
                # Wait a bit for any dynamic content to load
                await page.wait_for_timeout(1000)
                
                # Check for captcha or access denied
                page_content = await page.content()
                if "captcha" in page_content.lower() or "access denied" in page_content.lower():
                    self.log(f"Captcha or access denied detected for {doc_info['title']}", "WARNING")
                    # Wait longer and try again
                    await page.wait_for_timeout(5000)
                    await page.reload(wait_until="networkidle")
                    page_content = await page.content()
                
                # Create filename
                filename = f"{doc_info['date']}_{self.sanitize_filename(doc_info['title'])}.html"
                filepath = self.output_dir / "documents" / filename
                
                # Save HTML content
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(page_content)
                
                self.log(f"Saved: {filename}")
                return True
                
        except Exception as e:
            self.log(f"Error scraping {doc_info['title']}: {str(e)}", "ERROR")
            return False
    
    async def run(self, resume: bool = True):
        """Main scraping function."""
        self.log("Starting CanLII scraper...")
        
        # Load previous progress if resuming
        progress = self.load_progress() if resume else {}
        start_index = 0
        
        if resume and progress:
            self.log(f"Resuming from previous session: {progress.get('completed_docs', 0)}/{progress.get('total_docs', 0)} documents completed")
            start_index = progress.get('completed_docs', 0)
        
        async with async_playwright() as p:
            # Launch browser with options to handle captchas better
            browser = await p.chromium.launch(
                headless=False,  # Run in headed mode to handle captchas
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            )
            
            try:
                # Create browser context with realistic user agent
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                
                page = await context.new_page()
                
                # Get all document links
                documents = await self.get_all_document_links(page)
                
                if not documents:
                    self.log("No documents found!", "ERROR")
                    return
                
                # Save document list for reference
                with open(self.output_dir / "document_list.json", "w", encoding="utf-8") as f:
                    json.dump(documents, f, indent=2, ensure_ascii=False)
                
                # Filter out already downloaded documents
                remaining_docs = []
                skipped_count = 0
                
                for i, doc in enumerate(documents):
                    if self.is_document_downloaded(doc):
                        skipped_count += 1
                        self.log(f"Skipping already downloaded: {doc['title']}")
                    else:
                        remaining_docs.append((i, doc))
                
                if skipped_count > 0:
                    self.log(f"Skipped {skipped_count} already downloaded documents")
                
                if not remaining_docs:
                    self.log("All documents have already been downloaded!")
                    return
                
                self.log(f"Starting to scrape {len(remaining_docs)} remaining documents...")
                
                # Scrape each remaining document
                successful = 0
                failed = 0
                total_processed = start_index
                
                for doc_index, doc in remaining_docs:
                    current_index = doc_index + 1
                    self.log(f"Progress: {current_index}/{len(documents)} - {doc['title']}")
                    
                    if await self.scrape_document(page, doc):
                        successful += 1
                        total_processed += 1
                        # Save progress after each successful download
                        self.save_progress(total_processed, len(documents), doc['title'])
                    else:
                        failed += 1
                    
                    # Progress update every 10 documents
                    if current_index % 10 == 0:
                        self.log(f"Progress update: {current_index}/{len(documents)} completed. Success: {successful}, Failed: {failed}")
                
                self.log(f"Scraping completed! Success: {successful}, Failed: {failed}")
                self.log(f"Total documents processed: {total_processed}/{len(documents)}")
                
            finally:
                await browser.close()


async def main():
    """Main entry point."""
    import sys
    
    # Check if user wants to start fresh (no resume)
    resume = True
    if len(sys.argv) > 1 and sys.argv[1] == "--no-resume":
        resume = False
        print("Starting fresh (no resume)")
    else:
        print("Starting with resume functionality enabled")
    
    scraper = CanLIIScraper(output_dir="scraped_documents", delay=2.0)
    await scraper.run(resume=resume)


if __name__ == "__main__":
    asyncio.run(main())
