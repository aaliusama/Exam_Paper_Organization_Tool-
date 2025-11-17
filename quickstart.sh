#!/bin/bash
# Quick start script for Cambridge 9709 Scraper

echo "=========================================="
echo "Cambridge 9709 Scraper - Quick Start"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install pip"
    exit 1
fi

echo "✓ pip found"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Check Tesseract
echo ""
echo "Checking Tesseract OCR..."
if ! command -v tesseract &> /dev/null; then
    echo "⚠ Tesseract not found!"
    echo ""
    echo "Please install Tesseract:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  macOS: brew install tesseract"
    echo "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
else
    echo "✓ Tesseract found: $(tesseract --version 2>&1 | head -n1)"
fi

# Run test
echo ""
echo "Running setup tests..."
python3 test_setup.py

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To run the pipeline:"
echo "  python3 main.py --mode all"
echo ""
echo "To test scraping only (2023):"
echo "  python3 main.py --mode scrape --start-year 2023 --end-year 2023"
echo ""
