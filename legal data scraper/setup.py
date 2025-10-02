#!/usr/bin/env python3
"""
Setup script for CanLII Legal Document Scraper
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Main setup function."""
    print("CanLII Legal Document Scraper Setup")
    print("=" * 40)
    
    # Check if we're in a conda environment
    if "CONDA_DEFAULT_ENV" in os.environ:
        print(f"✓ Conda environment detected: {os.environ['CONDA_DEFAULT_ENV']}")
    else:
        print("⚠ No conda environment detected. Consider activating 'skyc' environment first.")
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Install Playwright browsers
    if not run_command("playwright install chromium", "Installing Playwright Chromium browser"):
        return False
    
    # Create output directory
    os.makedirs("scraped_documents", exist_ok=True)
    os.makedirs("scraped_documents/documents", exist_ok=True)
    os.makedirs("scraped_documents/logs", exist_ok=True)
    print("✓ Created output directories")
    
    print("\n" + "=" * 40)
    print("Setup completed successfully!")
    print("\nTo run the scraper:")
    print("  python canlii_scraper.py")
    print("\nTo run a test with just a few documents:")
    print("  python test_scraper.py")


if __name__ == "__main__":
    main()
