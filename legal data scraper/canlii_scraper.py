#!/usr/bin/env python3
"""
CanLII Legal Document Scraper - 2025 Edition

This script scrapes legal documents from CanLII (Canadian Legal Information Institute)
focusing on documents that start with "R. v." (Regina vs. cases) for the year 2025.

Features:
- Uses Playwright for handling JavaScript and potential captchas
- Handles pagination to get all documents
- Filters for "R. v." cases only
- Saves HTML content locally with proper file naming
- Includes rate limiting and error handling
- Resume functionality to continue from where you left off
- Start from specific document index
- Interactive mode to choose starting document

Usage Examples:
    # Basic usage (with resume)
    python canlii_scraper.py
    
    # Start fresh without resume
    python canlii_scraper.py --no-resume
    
    # Start from a specific document index (0-based)
    python canlii_scraper.py --start-from 100
    
    # Interactive mode to choose starting document
    python canlii_scraper.py --interactive
    
    # List first 20 documents with indices
    python canlii_scraper.py --list-docs
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
        await page.goto("https://www.canlii.org/on/oncj/nav/date/2025", wait_until="networkidle")
        
        # Wait a bit longer for any dynamic content
        await page.wait_for_timeout(3000)
        
        # Check if we got redirected or blocked
        current_url = page.url
        if "captcha" in current_url.lower() or "challenge" in current_url.lower():
            self.log("CAPTCHA challenge detected, waiting for resolution...", "WARNING")
            await page.wait_for_timeout(10000)  # Wait 10 seconds for CAPTCHA resolution
            await page.wait_for_load_state("networkidle")
        
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
            
            # Check current status with better error handling
            try:
                page_info = await page.evaluate("""
                    () => {
                        try {
                            const body = document.querySelector('body');
                            if (!body) {
                                return { error: 'No body element found' };
                            }
                            
                            const showingText = body.textContent || '';
                            const showingMatch = showingText.match(/Showing (\\d+) of (\\d+) items/);
                            
                            // Look for "Show more results" button using text content search
                            const allElements = document.querySelectorAll('a, button');
                            const showMoreLink = Array.from(allElements).find(el => {
                                try {
                                    return el.textContent && (
                                        el.textContent.toLowerCase().includes('show more') || 
                                        el.textContent.toLowerCase().includes('load more') ||
                                        el.textContent.toLowerCase().includes('more results')
                                    );
                                } catch (e) {
                                    return false;
                                }
                            });
                            
                            // Also check for common class names
                            const showMoreByClass = document.querySelector('[class*="show-more"], [class*="load-more"]');
                            
                            return {
                                showing: showingMatch ? parseInt(showingMatch[1]) : null,
                                total: showingMatch ? parseInt(showingMatch[2]) : null,
                                hasShowMore: !!(showMoreLink || showMoreByClass),
                                showMoreText: showMoreLink?.textContent || showMoreByClass?.textContent || null,
                                bodyTextLength: showingText.length,
                                elementsCount: allElements.length
                            };
                        } catch (e) {
                            return { error: e.message };
                        }
                    }
                """)
            except Exception as e:
                self.log(f"Error evaluating page info: {str(e)}", "ERROR")
                page_info = {"error": str(e)}
            
            self.log(f"Page info: {page_info}")
            
            # Handle errors in page evaluation
            if 'error' in page_info:
                self.log(f"Page evaluation error: {page_info['error']}", "ERROR")
                # Try to get basic page info for debugging
                try:
                    page_title = await page.title()
                    page_url = page.url
                    self.log(f"Current page: {page_title} - {page_url}")
                    
                    # Check if we're on the right page
                    if "2025" not in page_url:
                        self.log("Warning: Not on 2025 page, redirecting...", "WARNING")
                        await page.goto("https://www.canlii.org/on/oncj/nav/date/2025", wait_until="networkidle")
                        await page.wait_for_timeout(2000)
                        continue
                except:
                    pass
                break
            
            # If we have all documents, break
            if page_info.get('showing') and page_info.get('total') and page_info['showing'] >= page_info['total']:
                self.log(f"Got all {page_info['total']} documents")
                break
            
            # If no "Show more results" button, try scrolling
            if not page_info.get('hasShowMore', False):
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
                self.log(f"Attempting to click 'Show more results' button: {page_info.get('showMoreText', 'Unknown')}")
                
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
                                el.textContent && (
                                    el.textContent.toLowerCase().includes('show more') || 
                                    el.textContent.toLowerCase().includes('load more') ||
                                    el.textContent.toLowerCase().includes('more results')
                                )
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
        
        # Debug: Check what we actually found
        if len(all_documents) == 0:
            self.log("No documents found at all. Checking page content...", "WARNING")
            try:
                # Get page content for debugging
                page_content = await page.content()
                self.log(f"Page content length: {len(page_content)}")
                
                # Check if there are any table rows
                table_rows = await page.evaluate("document.querySelectorAll('table tbody tr').length")
                self.log(f"Table rows found: {table_rows}")
                
                # Check if we're on the right page
                page_url = page.url
                page_title = await page.title()
                self.log(f"Current URL: {page_url}")
                self.log(f"Page title: {page_title}")
                
                # Check for error messages and get page content
                error_elements = await page.evaluate("""
                    () => {
                        const errorTexts = [];
                        const body = document.querySelector('body');
                        if (body) {
                            const text = body.textContent.toLowerCase();
                            if (text.includes('no results') || text.includes('no documents') || text.includes('not found')) {
                                errorTexts.push('No results message found');
                            }
                            if (text.includes('error') || text.includes('404')) {
                                errorTexts.push('Error message found');
                            }
                            if (text.includes('captcha') || text.includes('challenge')) {
                                errorTexts.push('CAPTCHA challenge detected');
                            }
                        }
                        return errorTexts;
                    }
                """)
                if error_elements:
                    self.log(f"Potential issues detected: {error_elements}")
                
                # Get a sample of the page content for debugging
                page_text = await page.evaluate("document.body.textContent")
                self.log(f"Page text sample (first 500 chars): {page_text[:500]}")
                
                # Check if there are any forms or different page structures
                forms_count = await page.evaluate("document.querySelectorAll('form').length")
                divs_count = await page.evaluate("document.querySelectorAll('div').length")
                self.log(f"Forms found: {forms_count}, Divs found: {divs_count}")
                
                # Check if this might be a CAPTCHA page
                if "captcha" in page_text.lower() or "challenge" in page_text.lower():
                    self.log("CAPTCHA challenge detected in page content. The scraper may need manual intervention.", "ERROR")
                    self.log("Try running the scraper in non-headless mode (it already runs in headed mode) and solve any CAPTCHAs manually.", "INFO")
                
                # Check if there might not be any documents for this year yet
                if "2025" in page_url and not any("captcha" in text.lower() for text in [page_text, page_url]):
                    self.log("No 2025 documents found. This might be because:", "INFO")
                    self.log("1. It's early in 2025 and no cases have been published yet", "INFO")
                    self.log("2. The page structure has changed", "INFO")
                    self.log("3. There's a different URL structure for 2025", "INFO")
                    self.log("Consider trying 2024 instead: python canlii_scraper.py", "INFO")
                
            except Exception as e:
                self.log(f"Error during debugging: {str(e)}", "ERROR")
        
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
    
    async def run(self, resume: bool = True, start_from_index: int = None):
        """Main scraping function."""
        self.log("Starting CanLII scraper...")
        
        # Load previous progress if resuming
        progress = self.load_progress() if resume else {}
        start_index = 0
        
        # If a specific start index is provided, use it (overrides resume)
        if start_from_index is not None:
            start_index = start_from_index
            self.log(f"Starting from user-specified index: {start_index}")
        elif resume and progress:
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
                
                # Apply start_index filter and skip already downloaded documents
                remaining_docs = []
                skipped_count = 0
                start_index_skipped = 0
                
                for i, doc in enumerate(documents):
                    # Skip documents before start_index
                    if i < start_index:
                        start_index_skipped += 1
                        continue
                        
                    if self.is_document_downloaded(doc):
                        skipped_count += 1
                        self.log(f"Skipping already downloaded: {doc['title']}")
                    else:
                        remaining_docs.append((i, doc))
                
                if start_index_skipped > 0:
                    self.log(f"Skipped {start_index_skipped} documents due to start index {start_index}")
                if skipped_count > 0:
                    self.log(f"Skipped {skipped_count} already downloaded documents")
                
                if not remaining_docs:
                    self.log("All documents have already been downloaded or are before the start index!")
                    return
                
                self.log(f"Starting to scrape {len(remaining_docs)} remaining documents from index {start_index}...")
                
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


async def list_documents_preview(scraper: CanLIIScraper):
    """List first 20 documents with their indices for user reference."""
    print("Fetching document list from CanLII...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            documents = await scraper.get_all_document_links(page)
            
            print(f"\nFound {len(documents)} total R. v. documents for 2025")
            print("\nFirst 20 documents:")
            print("-" * 80)
            print(f"{'Index':<6} {'Date':<12} {'Title'}")
            print("-" * 80)
            
            for i, doc in enumerate(documents[:20]):
                print(f"{i:<6} {doc['date']:<12} {doc['title']}")
            
            if len(documents) > 20:
                print(f"... and {len(documents) - 20} more documents")
            
            print(f"\nTo start from a specific document, use: --start-from <index>")
            print(f"For interactive selection, use: --interactive")
            
        finally:
            await browser.close()


async def interactive_document_selection(scraper: CanLIIScraper):
    """Interactive mode to let user choose starting document."""
    print("Fetching document list from CanLII...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            documents = await scraper.get_all_document_links(page)
            
            print(f"\nFound {len(documents)} total R. v. documents for 2025")
            
            while True:
                print("\nOptions:")
                print("1. List first 20 documents")
                print("2. Search by date (YYYY-MM-DD)")
                print("3. Search by title (partial match)")
                print("4. Enter specific index")
                print("5. Exit")
                
                choice = input("\nEnter your choice (1-5): ").strip()
                
                if choice == "1":
                    print("\nFirst 20 documents:")
                    print("-" * 80)
                    print(f"{'Index':<6} {'Date':<12} {'Title'}")
                    print("-" * 80)
                    
                    for i, doc in enumerate(documents[:20]):
                        print(f"{i:<6} {doc['date']:<12} {doc['title']}")
                    
                    if len(documents) > 20:
                        print(f"... and {len(documents) - 20} more documents")
                
                elif choice == "2":
                    date_search = input("Enter date (YYYY-MM-DD): ").strip()
                    matches = [(i, doc) for i, doc in enumerate(documents) if date_search in doc['date']]
                    
                    if matches:
                        print(f"\nFound {len(matches)} documents for date '{date_search}':")
                        print("-" * 80)
                        print(f"{'Index':<6} {'Date':<12} {'Title'}")
                        print("-" * 80)
                        
                        for i, doc in matches[:10]:  # Show first 10 matches
                            print(f"{i:<6} {doc['date']:<12} {doc['title']}")
                        
                        if len(matches) > 10:
                            print(f"... and {len(matches) - 10} more matches")
                    else:
                        print(f"No documents found for date '{date_search}'")
                
                elif choice == "3":
                    title_search = input("Enter title search term: ").strip().lower()
                    matches = [(i, doc) for i, doc in enumerate(documents) if title_search in doc['title'].lower()]
                    
                    if matches:
                        print(f"\nFound {len(matches)} documents matching '{title_search}':")
                        print("-" * 80)
                        print(f"{'Index':<6} {'Date':<12} {'Title'}")
                        print("-" * 80)
                        
                        for i, doc in matches[:10]:  # Show first 10 matches
                            print(f"{i:<6} {doc['date']:<12} {doc['title']}")
                        
                        if len(matches) > 10:
                            print(f"... and {len(matches) - 10} more matches")
                    else:
                        print(f"No documents found matching '{title_search}'")
                
                elif choice == "4":
                    try:
                        index = int(input(f"Enter index (0-{len(documents)-1}): ").strip())
                        if 0 <= index < len(documents):
                            doc = documents[index]
                            print(f"\nSelected document {index}:")
                            print(f"Date: {doc['date']}")
                            print(f"Title: {doc['title']}")
                            
                            confirm = input("\nStart scraping from this document? (y/n): ").strip().lower()
                            if confirm == 'y':
                                return index
                        else:
                            print(f"Invalid index. Must be between 0 and {len(documents)-1}")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
                
                elif choice == "5":
                    return None
                
                else:
                    print("Invalid choice. Please enter 1-5.")
        
        finally:
            await browser.close()


async def main():
    """Main entry point."""
    import sys
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="CanLII Legal Document Scraper for 2025")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh without resuming from previous session")
    parser.add_argument("--start-from", type=int, help="Start scraping from a specific document index (0-based)")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode to choose starting document")
    parser.add_argument("--list-docs", action="store_true", help="List first 20 documents with their indices and exit")
    
    args = parser.parse_args()
    
    resume = not args.no_resume
    start_from_index = args.start_from
    
    scraper = CanLIIScraper(output_dir="scraped_documents", delay=2.0)
    
    # Handle list documents option
    if args.list_docs:
        await list_documents_preview(scraper)
        return
    
    # Handle interactive mode
    if args.interactive:
        start_from_index = await interactive_document_selection(scraper)
        if start_from_index is None:
            print("No document selected. Exiting.")
            return
    
    if start_from_index is not None:
        print(f"Starting from document index: {start_from_index}")
        resume = False  # Don't resume when starting from specific index
    elif resume:
        print("Starting with resume functionality enabled")
    else:
        print("Starting fresh (no resume)")
    
    await scraper.run(resume=resume, start_from_index=start_from_index)


if __name__ == "__main__":
    asyncio.run(main())
