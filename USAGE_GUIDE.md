# Usage Guide - Cambridge 9709 Scraper

## Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
- Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
- Add Tesseract to PATH

### Step 3: Verify Installation

```bash
python test_setup.py
```

All tests should pass ✓

---

## Quick Start Examples

### Example 1: Complete Pipeline (2020-2025)

Run everything - scrape, parse, export, upload:

```bash
python main.py --mode all
```

**What it does:**
1. Downloads all PDFs from PapaCambridge (2020-2025)
2. Processes PDFs with OCR
3. Extracts questions and matches with mark schemes
4. Maps to syllabus topics
5. Exports to JSON and CSV
6. Uploads to Google Drive (if configured)

**Expected time:** 3-5 hours

---

### Example 2: Test with Single Year (2023)

Test the pipeline on a single year first:

```bash
python main.py --mode all --start-year 2023 --end-year 2023
```

**Expected time:** 30-45 minutes

---

### Example 3: Scrape Only

Just download PDFs without parsing:

```bash
python main.py --mode scrape --start-year 2020 --end-year 2025
```

**Output:** PDFs in `Cambridge-9709/raw_pdfs/{year}/{session}/`

---

### Example 4: Parse Existing PDFs

If you already have PDFs, just parse them:

```bash
python main.py --mode parse
```

**Requirement:** PDFs must be in `Cambridge-9709/raw_pdfs/` with correct naming

---

### Example 5: Export Only

Re-export datasets from parsed data:

```bash
python main.py --mode export
```

---

### Example 6: Skip Scraping (Use Existing PDFs)

Parse existing PDFs and export:

```bash
python main.py --mode all --skip-scrape
```

---

### Example 7: Skip Upload

Run everything except Google Drive upload:

```bash
python main.py --mode all --skip-upload
```

---

## Understanding the Output

### Directory Structure

After running, you'll have:

```
Cambridge-9709/
├── raw_pdfs/
│   ├── 2020/
│   │   ├── may_june/
│   │   │   ├── 9709_s20_qp_12.pdf
│   │   │   ├── 9709_s20_ms_12.pdf
│   │   │   └── ...
│   │   ├── oct_nov/
│   │   └── feb_march/
│   ├── 2021/
│   └── ...
│
├── parsed_json/
│   ├── 2020_MJ_P12.json
│   ├── 2020_MJ_P13.json
│   └── ...
│
├── combined_yearly_csv/
│   ├── 2020_combined.csv
│   ├── 2021_combined.csv
│   └── ...
│
├── master_dataset/
│   ├── master_dataset.json
│   ├── master_dataset.csv
│   └── summary_statistics.json
│
└── logs/
    ├── pipeline.log
    └── download_log.txt
```

### JSON Format Example

`2023_MJ_P12.json`:
```json
{
  "year": 2023,
  "session": "M/J",
  "paper": "P12",
  "variant": 2,
  "questions": [
    {
      "qid": "1",
      "topics": ["P2.1"],
      "question_text": "Find the coefficient of x^3 in the expansion of (2 + x)^6.",
      "answer_full": "Using binomial theorem: (2+x)^6 = ... coefficient = 160",
      "answer_snippet": "160",
      "raw_ocr": null,
      "page": 1,
      "marks": 3
    },
    {
      "qid": "1(a)",
      "topics": ["P1.1"],
      "question_text": "Solve 2x^2 - 5x + 2 = 0",
      "answer_full": "Using quadratic formula or factoring: x = 2 or x = 0.5",
      "answer_snippet": "x = 2 or x = 1/2",
      "raw_ocr": null,
      "page": 1,
      "marks": 2
    }
  ]
}
```

### CSV Format

All questions flattened into single table:

| year | session | paper | variant | qid    | question_text | answer_full | answer_snippet | topics    | page | marks |
|------|---------|-------|---------|--------|---------------|-------------|----------------|-----------|------|-------|
| 2023 | M/J     | P12   | 2       | 1      | Find the...   | Using...    | 160            | P2.1      | 1    | 3     |
| 2023 | M/J     | P12   | 2       | 1(a)   | Solve...      | Using...    | x = 2 or 1/2   | P1.1      | 1    | 2     |

---

## Google Drive Setup

### Prerequisites

- Google account
- Google Cloud Console access

### Step-by-Step Setup

#### 1. Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Enter project name: "Cambridge-9709-Scraper"
4. Click "Create"

#### 2. Enable Google Drive API

1. In Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on it and click "Enable"

#### 3. Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: External
   - App name: "Cambridge 9709 Scraper"
   - User support email: your email
   - Developer contact: your email
   - Click "Save and Continue"
   - Scopes: Leave default, click "Save and Continue"
   - Test users: Add your email
   - Click "Save and Continue"

4. Back to "Create OAuth client ID":
   - Application type: "Desktop app"
   - Name: "Cambridge 9709 Desktop"
   - Click "Create"

5. Download credentials:
   - Click "Download JSON"
   - Save as `credentials.json` in project root

#### 4. First Authentication

```bash
python main.py --mode upload
```

- Browser will open
- Sign in to Google account
- Grant permissions
- Token saved to `token.json`
- Future runs won't require browser

#### 5. Verify Upload

Check your Google Drive folder:
https://drive.google.com/drive/folders/1Gv3FJ7MiAicT1eA_B6MxfaA8ShrDlrki

You should see:
- `raw_pdfs/` folder
- `parsed_json/` folder
- `combined_yearly_csv/` folder
- `master_dataset/` folder

---

## Troubleshooting

### Issue: "503 Service Unavailable" when scraping

**Cause:** PapaCambridge is blocking requests

**Solution:**
- Built-in retry logic should handle this
- If persistent, wait 5-10 minutes
- Check if site is accessible in browser

---

### Issue: OCR not working

**Symptoms:**
- Empty text extraction
- "Tesseract not found" error

**Solution:**
```bash
# Verify Tesseract installation
tesseract --version

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Test manually
tesseract sample.png output
```

---

### Issue: Import errors

**Symptoms:**
- "No module named 'pandas'"
- "No module named 'bs4'"

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify
python test_setup.py
```

---

### Issue: Google Drive authentication fails

**Symptoms:**
- "credentials.json not found"
- "Authentication failed"

**Solution:**
1. Verify `credentials.json` is in project root
2. Check file is valid JSON
3. Re-download from Google Cloud Console
4. Delete `token.json` and retry

---

### Issue: PDFs not downloading

**Symptoms:**
- "Failed to download" messages
- Empty folders

**Possible causes:**
1. Network issues - retry later
2. URL structure changed - check PapaCambridge site
3. Papers don't exist for that year/session

**Solution:**
- Check `Cambridge-9709/logs/download_log.txt`
- Verify URLs manually in browser
- Some papers (especially Feb/March) only have limited variants

---

### Issue: Question parsing incorrect

**Symptoms:**
- Questions split incorrectly
- Missing sub-parts

**Solution:**
- Check `raw_ocr` field in JSON output
- May need manual review for complex layouts
- OCR quality depends on PDF quality

---

## Advanced Usage

### Custom Processing

You can use individual components:

```python
from src.scrapers.papacambridge_scraper import PapaCambridgeScraper
from src.parsers.pdf_processor import PDFProcessor
from src.utils.topic_mapper import TopicMapper

# Download specific paper
scraper = PapaCambridgeScraper()
scraper.scrape_year(2023)

# Process specific PDF
processor = PDFProcessor()
pages = processor.process_pdf("path/to/paper.pdf")

# Map topics
mapper = TopicMapper()
topics = mapper.map_question_to_topics(
    "Solve the quadratic equation",
    paper_code="12"
)
```

### Batch Processing

Process specific years:

```bash
# 2023-2024 only
python main.py --start-year 2023 --end-year 2024

# Single year
python main.py --start-year 2023 --end-year 2023
```

---

## Performance Tips

### Speed Up Processing

1. **Use SSD:** Store data on SSD for faster I/O
2. **Skip Upload:** Use `--skip-upload` during testing
3. **Process in batches:** Do one year at a time
4. **Parallel processing:** (future enhancement)

### Reduce Storage

1. Delete raw PDFs after parsing:
   ```bash
   rm -rf Cambridge-9709/raw_pdfs/
   ```

2. Keep only master dataset:
   ```bash
   # Keep only master files
   find Cambridge-9709 -type f ! -path "*/master_dataset/*" -delete
   ```

---

## Getting Help

1. **Check logs:**
   - `Cambridge-9709/logs/pipeline.log`
   - `Cambridge-9709/logs/download_log.txt`

2. **Run diagnostics:**
   ```bash
   python test_setup.py
   ```

3. **Verify setup:**
   - Python 3.8+
   - All dependencies installed
   - Tesseract installed
   - Sufficient disk space (~5GB for 2020-2025)

---

## Next Steps

After successful run:

1. **Verify data quality:**
   - Open sample JSON files
   - Check CSV in spreadsheet software
   - Review topic mappings

2. **Use the data:**
   - Import CSV into database
   - Load JSON for analysis
   - Build question bank application

3. **Customize:**
   - Modify topic mappings in `src/utils/topic_mapper.py`
   - Adjust question parsing in `src/parsers/question_parser.py`
   - Add custom export formats in `src/utils/data_exporter.py`

---

## FAQ

**Q: How long does the complete pipeline take?**
A: 3-5 hours for 2020-2025 (depends on network speed and computer)

**Q: How much disk space needed?**
A: ~5GB for 2020-2025 (raw PDFs + processed data)

**Q: Can I run this on Windows?**
A: Yes, but you need to install Tesseract separately

**Q: What if some papers are missing?**
A: Check `download_log.txt` - some sessions may not have all variants

**Q: Can I customize topic mappings?**
A: Yes, edit `src/utils/topic_mapper.py` and modify keyword lists

**Q: Is this legal?**
A: For educational use only. Respect PapaCambridge's terms of service.

**Q: Can I contribute?**
A: Yes! Fork the repo and submit pull requests

---

## Support

For issues or questions:
- Check this guide
- Review logs
- Test setup with `python test_setup.py`
- Check README.md for technical details
