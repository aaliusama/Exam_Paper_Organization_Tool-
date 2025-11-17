#!/usr/bin/env python3
"""
Test script to verify setup and dependencies
"""

import sys
from pathlib import Path

print("="*60)
print("TESTING CAMBRIDGE 9709 SCRAPER SETUP")
print("="*60 + "\n")

# Test 1: Python version
print("1. Python Version:")
print(f"   {sys.version}")
if sys.version_info < (3, 8):
    print("   ⚠ WARNING: Python 3.8+ recommended")
else:
    print("   ✓ OK")

# Test 2: Required packages
print("\n2. Checking Python packages:")
required_packages = [
    'requests',
    'bs4',  # beautifulsoup4
    'pdfplumber',
    'pytesseract',
    'PIL',  # Pillow
    'pdf2image',
    'pandas',
    'google',  # google-api-python-client
    'tqdm'
]

missing_packages = []
for package in required_packages:
    try:
        __import__(package)
        print(f"   ✓ {package}")
    except ImportError:
        print(f"   ✗ {package} - MISSING")
        missing_packages.append(package)

if missing_packages:
    print(f"\n   ⚠ Missing packages: {', '.join(missing_packages)}")
    print("   Run: pip install -r requirements.txt")
else:
    print("   ✓ All packages installed")

# Test 3: Tesseract
print("\n3. Checking Tesseract OCR:")
try:
    import pytesseract
    version = pytesseract.get_tesseract_version()
    print(f"   ✓ Tesseract {version} installed")
except Exception as e:
    print(f"   ✗ Tesseract not found or not configured")
    print(f"   Error: {str(e)}")
    print("   Install:")
    print("   - Ubuntu/Debian: sudo apt-get install tesseract-ocr")
    print("   - macOS: brew install tesseract")
    print("   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")

# Test 4: Project structure
print("\n4. Checking project structure:")
required_dirs = [
    'src/scrapers',
    'src/parsers',
    'src/utils',
    'Cambridge-9709/raw_pdfs',
    'Cambridge-9709/parsed_json',
    'Cambridge-9709/combined_yearly_csv',
    'Cambridge-9709/master_dataset',
    'Cambridge-9709/logs'
]

for dir_path in required_dirs:
    path = Path(dir_path)
    if path.exists():
        print(f"   ✓ {dir_path}")
    else:
        print(f"   ✗ {dir_path} - MISSING")
        path.mkdir(parents=True, exist_ok=True)
        print(f"     (created)")

# Test 5: Import project modules
print("\n5. Testing project imports:")
sys.path.insert(0, str(Path(__file__).parent / 'src'))

modules_to_test = [
    ('scrapers.papacambridge_scraper', 'PapaCambridgeScraper'),
    ('parsers.pdf_processor', 'PDFProcessor'),
    ('parsers.question_parser', 'QuestionParser'),
    ('utils.topic_mapper', 'TopicMapper'),
    ('utils.data_exporter', 'DataExporter'),
    ('utils.drive_uploader', 'DriveUploader'),
]

all_imports_ok = True
for module_name, class_name in modules_to_test:
    try:
        module = __import__(module_name, fromlist=[class_name])
        cls = getattr(module, class_name)
        print(f"   ✓ {module_name}.{class_name}")
    except Exception as e:
        print(f"   ✗ {module_name}.{class_name}")
        print(f"     Error: {str(e)}")
        all_imports_ok = False

# Test 6: Quick functionality test
print("\n6. Testing basic functionality:")
try:
    from utils.topic_mapper import TopicMapper
    mapper = TopicMapper()
    topics = mapper.map_question_to_topics("Find the gradient of y = 3x^2", paper_code="12")
    print(f"   ✓ Topic mapper working (mapped to: {topics})")
except Exception as e:
    print(f"   ✗ Topic mapper failed: {str(e)}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

issues = []
if sys.version_info < (3, 8):
    issues.append("Python version < 3.8")
if missing_packages:
    issues.append(f"Missing packages: {', '.join(missing_packages)}")
if not all_imports_ok:
    issues.append("Some module imports failed")

if issues:
    print("⚠ ISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
    print("\nPlease fix the issues above before running the pipeline.")
else:
    print("✓ ALL TESTS PASSED!")
    print("\nYou're ready to run the pipeline:")
    print("  python main.py --mode all")

print("="*60 + "\n")
