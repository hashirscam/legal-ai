#!/usr/bin/env python3
"""
HTML to Text Converter for Legal Documents

This script converts HTML files (specifically CanLII legal documents) to a clean text format.
It extracts the main content, removes HTML tags, and formats the text according to a standard pattern.

Usage:
    python html_to_txt_converter.py <input_folder> [output_folder]
    
If output_folder is not specified, converted files will be saved in the same directory as input files.
"""

import os
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
import argparse


def clean_text(text):
    """Clean and normalize text content."""
    # Remove extra whitespace and normalize line breaks
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Clean up specific patterns
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    
    # Remove extra spaces around punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])\s+', r'\1 ', text)
    
    return text.strip()


def extract_citation_info(soup):
    """Extract citation information from the HTML."""
    citation = ""
    url = ""
    
    # Try to find citation in meta tags
    citation_meta = soup.find('meta', {'name': 'DC.Title'})
    if citation_meta:
        citation = citation_meta.get('content', '')
    
    # Try to find URL in meta tags
    url_meta = soup.find('meta', {'name': 'lbh-document-url'})
    if url_meta:
        url = url_meta.get('content', '')
    
    # If not found in meta, try to find in the document content
    if not citation:
        title_h1 = soup.find('h1', class_='main-title')
        if title_h1:
            citation = title_h1.get_text(strip=True)
    
    if not url:
        # Look for citation with URL in the document
        citation_div = soup.find('div', class_='documentMeta-citation')
        if citation_div:
            citation_text = citation_div.get_text()
            url_match = re.search(r'https://canlii\.ca/t/[a-zA-Z0-9]+', citation_text)
            if url_match:
                url = url_match.group(0)
    
    return citation, url


def extract_main_content(soup):
    """Extract the main document content from the HTML."""
    # Look for the main content area
    content_div = soup.find('div', {'id': 'originalDocument'})
    if not content_div:
        content_div = soup.find('div', class_='documentContent')
    
    if not content_div:
        content_div = soup.find('div', class_='documentcontent')
    
    if not content_div:
        # Fallback: look for any div with WordSection1 class
        content_div = soup.find('div', class_='WordSection1')
    
    if not content_div:
        # Last resort: use the body
        content_div = soup.find('body')
    
    if not content_div:
        return ""
    
    # Extract text content with better formatting
    # Use a custom separator that preserves paragraph structure
    text_content = content_div.get_text(separator=' ', strip=True)
    
    # Clean up the text and add proper line breaks
    text_content = clean_and_format_text(text_content)
    
    return text_content


def clean_and_format_text(text):
    """Clean text and add proper formatting."""
    # First, clean up HTML entities and extra whitespace
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Add line breaks for specific patterns
    # Add line break before paragraph numbers
    text = re.sub(r'(\s)(\[\d+\])', r'\n\2', text)
    
    # Add line breaks before section headers (all caps)
    text = re.sub(r'(\s)([A-Z][A-Z\s]{10,}?)(\s)', r'\n\n\2\n', text)
    
    # Add line breaks before section headers ending with colon
    text = re.sub(r'(\s)([A-Z][a-z].*?)(:)(\s)', r'\n\n\2\3\n', text)
    
    # Add line breaks for specific legal document patterns
    text = re.sub(r'(\s)(BETWEEN:)(\s)', r'\n\n\2\n', text)
    text = re.sub(r'(\s)(CITATION:)(\s)', r'\n\2 ', text)
    text = re.sub(r'(\s)(DATE:)(\s)', r'\n\2 ', text)
    text = re.sub(r'(\s)(COURT FILE No\.:)(\s)', r'\n\2 ', text)
    text = re.sub(r'(\s)(Before)(\s)', r'\n\n\2 ', text)
    text = re.sub(r'(\s)(Heard)(\s)', r'\n\2 ', text)
    text = re.sub(r'(\s)(Reasons)(\s)', r'\n\2 ', text)
    
    # Clean up extra spaces around punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])\s+', r'\1 ', text)
    
    # Normalize line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def clean_text_preserve_lines(text):
    """Clean text while preserving important line breaks."""
    # Remove extra whitespace but preserve line breaks
    text = re.sub(r'[ \t]+', ' ', text)  # Replace multiple spaces/tabs with single space
    text = re.sub(r'\n[ \t]+', '\n', text)  # Remove leading spaces from lines
    text = re.sub(r'[ \t]+\n', '\n', text)  # Remove trailing spaces from lines
    
    # Clean up specific patterns
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    
    # Remove extra spaces around punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])\s+', r'\1 ', text)
    
    # Normalize line breaks - keep single line breaks, normalize multiple
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def format_document_text(citation, url, content):
    """Format the document text according to the standard pattern."""
    # Create the header with citation and URL
    header_lines = []
    
    if citation and url:
        header_lines.append(f"{citation}, <{url}>, retrieved on {get_current_date()}")
    elif citation:
        header_lines.append(citation)
    
    header_lines.append("")  # Empty line
    
    # Split content into lines and process
    content_lines = content.split('\n')
    formatted_lines = []
    
    for line in content_lines:
        line = line.strip()
        if not line:
            formatted_lines.append("")
            continue
        
        # Handle specific formatting patterns
        if re.match(r'^\[(\d+)\]\s*', line):
            # This is a paragraph number, keep as is
            formatted_lines.append(line)
        elif re.match(r'^[A-Z][A-Z\s]+$', line) and len(line) > 10:
            # This looks like a section header (all caps)
            formatted_lines.append("")
            formatted_lines.append(line)
            formatted_lines.append("")
        elif re.match(r'^[A-Z][a-z].*:$', line):
            # This looks like a section header ending with colon
            formatted_lines.append("")
            formatted_lines.append(line)
            formatted_lines.append("")
        else:
            formatted_lines.append(line)
    
    # Combine header and content
    result = '\n'.join(header_lines + formatted_lines)
    
    # Final cleanup
    result = re.sub(r'\n{3,}', '\n\n', result)  # Remove excessive line breaks
    
    return result


def get_current_date():
    """Get current date in the format used in the example."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def convert_html_to_txt(html_file_path, output_file_path=None):
    """Convert a single HTML file to text format."""
    try:
        # Read the HTML file
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract citation and URL
        citation, url = extract_citation_info(soup)
        
        # Extract main content
        content = extract_main_content(soup)
        
        if not content:
            print(f"Warning: No content found in {html_file_path}")
            return False
        
        # Format the document
        formatted_text = format_document_text(citation, url, content)
        
        # Determine output file path
        if output_file_path is None:
            html_path = Path(html_file_path)
            output_file_path = html_path.parent / f"{html_path.stem}_converted.txt"
        
        # Write the converted text
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        print(f"Converted: {html_file_path} -> {output_file_path}")
        return True
        
    except Exception as e:
        print(f"Error converting {html_file_path}: {str(e)}")
        return False


def process_folder(input_folder, output_folder=None):
    """Process all HTML files in a folder."""
    input_path = Path(input_folder)
    
    if not input_path.exists():
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return
    
    if not input_path.is_dir():
        print(f"Error: '{input_folder}' is not a directory.")
        return
    
    # Set output folder
    if output_folder is None:
        output_path = input_path
    else:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all HTML files (case-insensitive)
    html_files = list(input_path.glob("*.html")) + list(input_path.glob("*.HTML"))
    # Remove duplicates (Windows filesystem is case-insensitive)
    html_files = list(set(html_files))
    
    if not html_files:
        print(f"No HTML files found in '{input_folder}'")
        return
    
    print(f"Found {len(html_files)} HTML file(s) to convert...")
    
    success_count = 0
    for html_file in html_files:
        # Create output file path
        if output_folder is None:
            output_file = html_file.parent / f"{html_file.stem}_converted.txt"
        else:
            output_file = output_path / f"{html_file.stem}_converted.txt"
        
        if convert_html_to_txt(html_file, output_file):
            success_count += 1
    
    print(f"\nConversion complete: {success_count}/{len(html_files)} files converted successfully.")


def process_folder_test(input_folder, output_folder):
    """Process only 5 HTML files for testing quality."""
    input_path = Path(input_folder)
    
    if not input_path.exists():
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return
    
    if not input_path.is_dir():
        print(f"Error: '{input_folder}' is not a directory.")
        return
    
    # Set output folder
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all HTML files (case-insensitive)
    html_files = list(input_path.glob("*.html")) + list(input_path.glob("*.HTML"))
    # Remove duplicates (Windows filesystem is case-insensitive)
    html_files = list(set(html_files))
    
    if not html_files:
        print(f"No HTML files found in '{input_folder}'")
        return
    
    # Sort files for consistent testing
    html_files.sort()
    
    # Take only first 5 files for testing
    test_files = html_files[:5]
    
    print(f"TEST MODE: Converting only {len(test_files)} files for quality check...")
    print("Files to be converted:")
    for i, file in enumerate(test_files, 1):
        print(f"  {i}. {file.name}")
    print()
    
    success_count = 0
    for html_file in test_files:
        # Create output file path
        output_file = output_path / f"{html_file.stem}_converted.txt"
        
        if convert_html_to_txt(html_file, output_file):
            success_count += 1
    
    print(f"\nTest conversion complete: {success_count}/{len(test_files)} files converted successfully.")
    print(f"Check the '{output_folder}' folder to review the converted files.")
    print("If the quality looks good, run without --test to convert all files.")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert HTML files to text format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python html_to_txt_converter.py                    # Convert all files from documents to converted_documents
  python html_to_txt_converter.py --test             # Test mode: convert only 5 files
  python html_to_txt_converter.py --input custom     # Convert from custom folder to converted_documents
        """
    )
    
    parser.add_argument('--input', default='documents', help='Input folder containing HTML files (default: documents)')
    parser.add_argument('--output', default='converted_documents', help='Output folder for converted files (default: converted_documents)')
    parser.add_argument('--test', action='store_true', help='Test mode: convert only 5 files to check quality')
    
    args = parser.parse_args()
    
    # Process the folder
    if args.test:
        process_folder_test(args.input, args.output)
    else:
        process_folder(args.input, args.output)


if __name__ == "__main__":
    main()
