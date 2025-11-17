# Quick Start Guide

## ⚡ Get Started in 3 Steps

### Step 1: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Tesseract OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract
```

### Step 2: Verify Setup

```bash
python test_setup.py
```

All checks should pass ✓

### Step 3: Run Pipeline

**Test with 2023 first (recommended):**
```bash
python main.py --start-year 2023 --end-year 2023
```

**Run complete pipeline (2020-2025):**
```bash
python main.py
```

---

## 📁 What You'll Get

After running, you'll have:

```
Cambridge-9709/
├── raw_pdfs/              # Downloaded PDFs (2GB)
├── parsed_json/           # Individual papers (500MB)
├── combined_yearly_csv/   # Yearly CSVs (100MB)
├── master_dataset/        # Master JSON + CSV (150MB)
└── logs/                  # Execution logs
```

---

## 🎯 Common Commands

```bash
# Complete pipeline (everything)
python main.py --mode all

# Download PDFs only
python main.py --mode scrape

# Parse existing PDFs
python main.py --mode parse --skip-scrape

# Export datasets
python main.py --mode export

# Upload to Google Drive
python main.py --mode upload

# Specific year range
python main.py --start-year 2023 --end-year 2024
```

---

## 📊 Expected Output

- **Papers:** ~500-600 papers
- **Questions:** ~3,000-5,000 questions
- **Time:** 3-5 hours for full pipeline
- **Storage:** ~5GB total

---

## 🔧 Troubleshooting

**"No module named 'bs4'"**
```bash
pip install -r requirements.txt
```

**"Tesseract not found"**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

**503 errors when scraping**
- Built-in retry logic will handle this
- Wait a few minutes if persistent

---

## 📖 More Information

- **Technical details:** README.md
- **Usage examples:** USAGE_GUIDE.md
- **Project overview:** PROJECT_SUMMARY.md

---

## ✅ Verification Checklist

Before running:

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Tesseract OCR installed
- [ ] Test passes (`python test_setup.py`)
- [ ] ~5GB disk space available

Ready to go! 🚀
