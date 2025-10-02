#!/usr/bin/env python3
"""
Example usage of the HTML to Text Converter

This script demonstrates how to use the converter programmatically.
"""

from html_to_txt_converter import convert_html_to_txt, process_folder
import os

def example_single_file():
    """Example: Convert a single HTML file."""
    html_file = "2024-12-30_R. v. Flaro.html"
    output_file = "example_output.txt"
    
    if os.path.exists(html_file):
        print(f"Converting {html_file} to {output_file}...")
        success = convert_html_to_txt(html_file, output_file)
        if success:
            print("Conversion successful!")
        else:
            print("Conversion failed!")
    else:
        print(f"File {html_file} not found!")

def example_folder():
    """Example: Convert all HTML files in current directory."""
    print("Converting all HTML files in current directory...")
    process_folder(".")

if __name__ == "__main__":
    print("HTML to Text Converter - Example Usage")
    print("=====================================")
    print()
    
    # Example 1: Convert single file
    print("Example 1: Single file conversion")
    example_single_file()
    print()
    
    # Example 2: Convert folder
    print("Example 2: Folder conversion")
    example_folder()
