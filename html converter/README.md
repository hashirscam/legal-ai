# HTML to Text Converter for Legal Documents

This script converts HTML files (specifically CanLII legal documents) to a clean text format that matches the standard pattern used in legal document processing.

## Features

- Converts HTML files to clean, readable text format
- Extracts citation information and URLs
- Preserves document structure and formatting
- Processes entire folders of HTML files
- Handles CanLII legal document format specifically

## Installation

1. Install Python 3.6 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Convert all HTML files from `documents` folder to `converted_documents` folder:
```bash
python html_to_txt_converter.py
```

### Test Mode

Convert only 5 files to check quality before processing all files:
```bash
python html_to_txt_converter.py --test
```

### Custom Folders

Convert from custom input folder:
```bash
python html_to_txt_converter.py --input custom_folder
```

Convert to custom output folder:
```bash
python html_to_txt_converter.py --output custom_output
```

### Command Line Arguments

- `--input`: Input folder containing HTML files (default: documents)
- `--output`: Output folder for converted files (default: converted_documents)
- `--test`: Test mode - convert only 5 files for quality check

## Examples

```bash
# Convert all files from documents to converted_documents
python html_to_txt_converter.py

# Test mode: convert only 5 files to check quality
python html_to_txt_converter.py --test

# Convert from custom folder to converted_documents
python html_to_txt_converter.py --input my_html_files

# Convert from documents to custom output folder
python html_to_txt_converter.py --output my_converted_files
```

## Output Format

The script converts HTML files to text format with:

1. **Header**: Citation and URL information
2. **Document Content**: Clean text with proper formatting
3. **Structure**: Preserved paragraph numbers, section headers, and legal document formatting

### Example Output

```
R. v. Flaro, 2024 ONCJ 686 (CanLII), <https://canlii.ca/t/k8z63>, retrieved on 2025-10-02

ONTARIO COURT OF JUSTICE

CITATION: R. v. Flaro, 2024 ONCJ 686
DATE: 2024 12 30
COURT FILE No.: 23- 39102393

BETWEEN:

HIS MAJESTY THE KING

— AND —

CHAD FLARO

Before Justice Julien R. Lalande
Heard on October 30th and November 22nd 2024
Reasons for Judgment released on December 30th 2024

[1] Mr. Flaro was convicted after trial of 11 firearms-related offences...
```

## File Naming

- Input files: `*.html` or `*.HTML`
- Output files: `{original_name}_converted.txt`

## Requirements

- Python 3.6+
- beautifulsoup4
- lxml

## Notes

- The script is specifically designed for CanLII legal documents
- It extracts content from the main document area and formats it appropriately
- Citation information is automatically extracted from HTML meta tags
- The script handles various HTML structures commonly found in legal documents
