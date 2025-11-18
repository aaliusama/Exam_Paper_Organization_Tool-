# Cambridge 9709 Mathematics Past Papers - Automated Scraper + Parser

Complete automated pipeline for scraping, parsing, and organizing Cambridge AS/A Level Mathematics 9709 past papers (2020-2025) from PapaCambridge, with OCR support for image-based papers.

## Features

- **Automated Scraping**: Downloads all QP + MS for papers P11-P63 (2020-2025)
- **OCR Support**: Handles both text-based and scanned image PDFs using Tesseract
- **Question Parsing**: Extracts questions with sub-parts (1, 1(a), 1(a)(i), etc.)
- **Mark Scheme Matching**: Automatically matches answers to questions
- **Topic Mapping**: Maps questions to 9709 syllabus topics (2026-2027)
- **Enhanced Metadata** (NEW): AI-powered metadata using open-source Hugging Face models
  - Difficulty classification (Easy/Medium/Hard)
  - Question type identification (Proof, Calculation, Sketch, etc.)
  - Concept extraction and key terms
  - Math notation detection
  - Required knowledge estimation
- **Multiple Formats**: Exports to JSON and CSV
- **Google Drive Integration**: Uploads organized dataset to Drive

## Project Structure

```
Exam_Paper_Organization_Tool-/
├── main.py                          # Main orchestrator script
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── src/
│   ├── scrapers/
│   │   └── papacambridge_scraper.py # Web scraper
│   ├── parsers/
│   │   ├── pdf_processor.py         # PDF + OCR processor
│   │   └── question_parser.py       # Question/answer parser
│   └── utils/
│       ├── topic_mapper.py          # Syllabus topic mapper
│       ├── data_exporter.py         # JSON/CSV exporter
│       └── drive_uploader.py        # Google Drive uploader
└── Cambridge-9709/                  # Output directory
    ├── raw_pdfs/                    # Downloaded PDFs
    │   └── {year}/
    │       └── {session}/
    ├── parsed_json/                 # Individual paper JSONs
    ├── combined_yearly_csv/         # Yearly CSV files
    ├── master_dataset/              # Master JSON + CSV
    └── logs/                        # Log files
```

## Installation

### Prerequisites

- Python 3.8+
- Tesseract OCR

### Install Tesseract

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
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start - Run Complete Pipeline

```bash
python main.py --mode all
```

This will:
1. Scrape all papers (2020-2025)
2. Parse PDFs with OCR
3. Export to JSON/CSV
4. Upload to Google Drive (if configured)

### Run Individual Steps

**Scrape only:**
```bash
python main.py --mode scrape
```

**Parse existing PDFs:**
```bash
python main.py --mode parse
```

**Export datasets:**
```bash
python main.py --mode export
```

**Upload to Drive:**
```bash
python main.py --mode upload
```

### Options

```bash
# Process specific year range
python main.py --start-year 2023 --end-year 2025

# Skip scraping (use existing PDFs)
python main.py --mode all --skip-scrape

# Skip upload
python main.py --mode all --skip-upload

# Enable enhanced metadata (requires transformers)
python main.py --mode all --enhanced-metadata
```

### Enhanced Metadata (NEW!)

Get AI-powered metadata for each question using open-source models:

```bash
# Install ML dependencies (optional)
pip install transformers torch

# Run with enhanced metadata
python main.py --mode parse --enhanced-metadata
```

See [ENHANCED_METADATA_GUIDE.md](ENHANCED_METADATA_GUIDE.md) for full documentation.

## Google Drive Setup (Optional)

To enable Google Drive upload:

1. **Create Google Cloud Project:**
   - Go to https://console.cloud.google.com/
   - Create a new project
   - Enable Google Drive API

2. **Create OAuth2 Credentials:**
   - Go to APIs & Services → Credentials
   - Create OAuth 2.0 Client ID (Desktop app)
   - Download credentials JSON

3. **Save Credentials:**
   - Save downloaded file as `credentials.json` in project root

4. **First Run:**
   - Run pipeline with upload enabled
   - Browser will open for authentication
   - Grant permissions
   - Token saved for future runs

## Output Format

### JSON Structure (per paper)

```json
{
  "year": 2023,
  "session": "M/J",
  "paper": "P12",
  "variant": 2,
  "questions": [
    {
      "qid": "1(a)(i)",
      "topics": ["P1.1", "P1.3"],
      "question_text": "Find the coefficient of x^3...",
      "answer_full": "Using binomial theorem...",
      "answer_snippet": "Coefficient is 160",
      "raw_ocr": "...",
      "page": 3,
      "marks": 3
    }
  ]
}
```

### CSV Columns

- `year`: Year (2020-2025)
- `session`: Session (M/J, O/N, F/M)
- `paper`: Paper code (P11, P12, etc.)
- `variant`: Variant number
- `qid`: Question ID (1, 1(a), 1(a)(i), etc.)
- `question_text`: Full question text
- `answer_full`: Complete answer from mark scheme
- `answer_snippet`: Short answer summary (1-3 lines)
- `topics`: Pipe-separated topic codes (P1.1|P1.7)
- `page`: Page number
- `marks`: Marks allocated

## Topic Codes (9709 Syllabus 2026-2027)

### Pure Mathematics 1 (Papers 1 & 3)
- `P1.1`: Quadratics
- `P1.2`: Functions
- `P1.3`: Coordinate Geometry
- `P1.4`: Circular Measure
- `P1.5`: Trigonometry
- `P1.6`: Series
- `P1.7`: Differentiation
- `P1.8`: Integration

### Pure Mathematics 2/3 (Papers 3)
- `P2.1`: Algebra
- `P2.2`: Logarithmic and Exponential Functions
- `P2.3`: Trigonometry (Advanced)
- `P2.4`: Differentiation (Advanced)
- `P2.5`: Integration (Advanced)
- `P2.6`: Numerical Solutions
- `P3.1`: Vectors
- `P3.2`: Complex Numbers
- `P3.3`: Differential Equations

### Mechanics (Papers 4)
- `M1.1`: Forces and Equilibrium
- `M1.2`: Kinematics
- `M1.3`: Newton's Laws
- `M1.4`: Energy, Work and Power

### Probability & Statistics (Papers 5 & 6)
- `S1.1`: Data Representation
- `S1.2`: Measures of Location and Spread
- `S1.3`: Probability
- `S1.4`: Discrete Random Variables
- `S1.5`: Normal Distribution
- `S2.1`: Continuous Random Variables (Paper 6 only)
- `S2.2`: Sampling and Hypothesis Testing (Paper 6 only)
- `S2.3`: Linear Combinations (Paper 6 only)

## Session Coverage

- **May/June (M/J)**: All papers (P11-P63)
- **October/November (O/N)**: All papers (P11-P63)
- **February/March (F/M)**: Limited papers (P12, P32, P42, P52, P62 only)

## Troubleshooting

### OCR Issues

If OCR is not working:
```bash
# Check Tesseract installation
tesseract --version

# Test OCR
tesseract test_image.png output
```

### Scraping Errors (503)

PapaCambridge may block rapid requests:
- Built-in retry logic handles temporary blocks
- Random delays between requests
- User-agent rotation

If persistent issues:
- Wait a few minutes between runs
- Check if site is accessible in browser

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

## Logs

All operations are logged to:
- `Cambridge-9709/logs/pipeline.log` - Main pipeline log
- `Cambridge-9709/logs/download_log.txt` - Scraping log

## Performance

Typical processing times (approximate):

- **Scraping**: ~2-3 hours for 2020-2025 (depends on network)
- **Parsing with OCR**: ~30-60 minutes for 2020-2025
- **Export**: ~1-2 minutes
- **Upload**: ~30-60 minutes (depends on network)

**Total**: ~3-5 hours for complete pipeline

## License

This project is for educational purposes only. Respect PapaCambridge's terms of service and use responsibly.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues or questions:
- Check logs in `Cambridge-9709/logs/`
- Review error messages
- Ensure all dependencies installed correctly

## Documentation

- [README.md](README.md) - Main documentation (this file)
- [PAPACAMBRIDGE_DOWNLOAD_GUIDE.md](PAPACAMBRIDGE_DOWNLOAD_GUIDE.md) - Detailed download guide
- [ENHANCED_METADATA_GUIDE.md](ENHANCED_METADATA_GUIDE.md) - AI metadata features
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Detailed usage instructions

## Acknowledgments

- PapaCambridge for providing past papers
- Cambridge Assessment International Education
- Tesseract OCR project
- Hugging Face for open-source ML models
