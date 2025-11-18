# Cambridge A-Level Mathematics Paper Processing Scripts

This directory contains automated scripts for downloading and processing Cambridge A-Level Mathematics (9709) past papers from 2022-2025.

## Files Overview

### Core Scripts

1. **`downloading_v2.py`** - Web scraper for Papa Cambridge
   - Downloads question papers (QP) and mark schemes (MS)
   - Supports years 2022-2025
   - Handles all sessions: May/June, October/November, February/March
   - Downloads Papers 1, 3, 4, 5, and 6 (variants 1, 2, 3)

2. **`metadata_collector_v2.py`** - PDF metadata extractor
   - Parses question papers and mark schemes
   - Extracts question structure, marks, and answers
   - Maps questions to syllabus learning outcomes
   - Generates JSON metadata files
   - Uses AI-powered mapping (Anthropic Claude) with keyword fallback

3. **`syllabus_outcomes.json`** - Complete syllabus mapping
   - Contains all learning outcomes for Papers 1, 3, 4, 5, 6
   - Structured by paper and topic code (e.g., 1.1, 3.5, 4.2)
   - Extracted from syllabus 697427-2026-2027

### Output

- **`metadata/`** directory - Contains ~125 JSON metadata files
- Each file named: `9709_{session}{year}_qp_{paper}_metadata.json`
- Example: `9709_s25_qp_12_metadata.json`

## Usage

### Downloading Papers

```bash
python3 downloading_v2.py --start-year 2022 --end-year 2025
```

Options:
- `--start-year`: Starting year (default: 2022)
- `--end-year`: Ending year (default: 2025)
- `--output-dir`: Output directory (default: Cambridge-9709/raw_pdfs)

### Generating Metadata

```bash
python3 metadata_collector_v2.py
```

The script will:
1. Scan `Cambridge-9709/raw_pdfs/` for all paper pairs
2. Extract text from PDFs
3. Parse questions and answers
4. Map to syllabus outcomes
5. Save metadata to `metadata/` directory

### Environment Variables

- `ANTHROPIC_API_KEY` (optional) - For AI-powered syllabus mapping
  - If not set, uses keyword-based fallback mapping

## Metadata Structure

Each metadata JSON file contains:

```json
{
  "exam_info": {
    "paper_code": "9709/12",
    "exam_board": "Cambridge International AS & A Level",
    "subject": "Mathematics",
    "paper_name": "Paper 1 Pure Mathematics 1",
    "exam_session": "May/June 2025",
    "total_marks": 75,
    "time_allowed": "1 hour 50 minutes"
  },
  "questions": [
    {
      "question_number": "1",
      "subparts": [],
      "page": 2,
      "marks": 4,
      "syllabus_outcomes": ["1.2"],
      "topic": "Functions - Graph transformations",
      "answers": {
        "answer_snippet": "..."
      }
    }
  ],
  "statistics": {
    "total_questions": 11,
    "total_marks": 75
  }
}
```

## Syllabus Outcomes

### Paper 1 - Pure Mathematics 1
- 1.1: Quadratics
- 1.2: Functions
- 1.3: Coordinate geometry
- 1.4: Circular measure
- 1.5: Trigonometry
- 1.6: Series
- 1.7: Differentiation
- 1.8: Integration

### Paper 3 - Pure Mathematics 3
- 3.1: Algebra
- 3.2: Logarithmic and exponential functions
- 3.3: Trigonometry
- 3.4: Differentiation
- 3.5: Integration
- 3.6: Numerical solution of equations
- 3.7: Vectors
- 3.8: Differential equations
- 3.9: Complex numbers

### Paper 4 - Mechanics
- 4.1: Forces and equilibrium
- 4.2: Kinematics
- 4.3: Momentum
- 4.4: Newton's laws
- 4.5: Energy, work and power

### Paper 5 - Probability & Statistics 1
- 5.1: Representation of data
- 5.2: Permutations and combinations
- 5.3: Probability
- 5.4: Discrete random variables
- 5.5: Normal distribution

### Paper 6 - Probability & Statistics 2
- 6.1: Poisson distribution
- 6.2: Linear combinations of random variables
- 6.3: Continuous random variables
- 6.4: Sampling and estimation
- 6.5: Hypothesis tests

## Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `pdfplumber` - PDF text extraction
- `anthropic` - AI-powered question analysis (optional)
- `beautifulsoup4` - Web scraping
- `requests` - HTTP requests

## Paper Naming Convention

Format: `9709_{session}{year}_{qp/ms}_{paper}.pdf`

- Session codes:
  - `s` = Summer (May/June)
  - `w` = Winter (October/November)
  - `m` = March (February/March)
- Year: Last 2 digits (e.g., `25` for 2025)
- Type: `qp` (question paper) or `ms` (mark scheme)
- Paper: 11-13, 31-33, 41-43, 51-53, 61-63

Examples:
- `9709_s25_qp_12.pdf` - May/June 2025, Paper 1 Variant 2, Question Paper
- `9709_w24_ms_33.pdf` - Oct/Nov 2024, Paper 3 Variant 3, Mark Scheme

## Notes

- The metadata collector uses pattern matching to extract questions
- PDF parsing quality varies depending on source document formatting
- Metadata may require manual review for accuracy
- The keyword fallback provides reasonable accuracy when AI is unavailable
- Generated metadata follows the structure of existing example: `9709_s25_qp_12_metadata.json`

## Total Coverage

- **Years**: 2022, 2023, 2024, 2025
- **Sessions per year**: 3 (May/June, Oct/Nov, Feb/March)
- **Papers**: 1, 3, 4, 5, 6
- **Variants**: 1, 2, 3 (March only has variant 2)
- **Documents**: ~125 question papers + ~125 mark schemes = ~250 PDFs
- **Metadata files**: ~125 JSON files

## Author & License

Created for Cambridge A-Level Mathematics exam paper organization.
Part of the Exam Paper Organization Tool project.
