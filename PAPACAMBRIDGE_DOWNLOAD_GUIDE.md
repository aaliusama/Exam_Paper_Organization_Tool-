# Papa Cambridge Download Guide

Complete guide for downloading Cambridge 9709 Mathematics past papers from Papa Cambridge.

## Table of Contents
- [Quick Start](#quick-start)
- [Understanding the URL Structure](#understanding-the-url-structure)
- [Paper Naming Convention](#paper-naming-convention)
- [Available Papers](#available-papers)
- [Download Methods](#download-methods)
- [Anti-Blocking Strategies](#anti-blocking-strategies)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Using the Automated Scraper

The easiest way to download papers is using the built-in scraper:

```bash
python main.py --mode scrape --start-year 2020 --end-year 2025
```

This will automatically download all available papers with built-in retry logic and anti-blocking measures.

### Manual Download

If you need to download specific papers manually:

```bash
# Download a specific paper
wget https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9709_s23_qp_12.pdf

# Download a mark scheme
wget https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9709_s23_ms_12.pdf
```

## Understanding the URL Structure

Papa Cambridge organizes CAIE past papers in a consistent URL pattern:

```
Base URL: https://pastpapers.papacambridge.com
Path: /directories/CAIE/CAIE-pastpapers/upload/
Filename: {syllabus}_{session}{year}_{type}_{paper}.pdf
```

### Example URLs

**Question Paper:**
```
https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9709_s23_qp_12.pdf
```

**Mark Scheme:**
```
https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9709_s23_ms_12.pdf
```

### URL Components

| Component | Description | Examples |
|-----------|-------------|----------|
| Syllabus | Subject code | `9709` (Mathematics) |
| Session | Exam session code | `s` (May/June), `w` (Oct/Nov), `m` (Feb/Mar) |
| Year | Last 2 digits of year | `23` (2023), `24` (2024) |
| Type | Document type | `qp` (Question Paper), `ms` (Mark Scheme) |
| Paper | Paper code | `12`, `32`, `42`, `52`, `62` |

## Paper Naming Convention

Cambridge 9709 Mathematics uses the following naming structure:

### Format: `9709_{session}{year}_{type}_{paper}.pdf`

**Examples:**
- `9709_s23_qp_12.pdf` → May/June 2023, Question Paper, Paper 12
- `9709_w24_ms_32.pdf` → Oct/Nov 2024, Mark Scheme, Paper 32
- `9709_m22_qp_42.pdf` → Feb/Mar 2022, Question Paper, Paper 42

### Session Codes

| Code | Session | Full Name | Months |
|------|---------|-----------|--------|
| `s` | M/J | May/June Summer | May-June |
| `w` | O/N | October/November Winter | Oct-Nov |
| `m` | F/M | February/March | Feb-Mar |

### Paper Codes

Cambridge 9709 has the following paper types:

| Paper | Components | Topics |
|-------|------------|--------|
| P1 (11/12/13) | Pure Mathematics 1 | Algebra, Functions, Calculus (basic) |
| P3 (31/32/33) | Pure Mathematics 3 | Advanced Pure Math, Vectors, Complex Numbers |
| P4 (41/42/43) | Mechanics | Forces, Kinematics, Dynamics |
| P5 (51/52/53) | Probability & Statistics 1 | Probability, Distributions |
| P6 (61/62/63) | Probability & Statistics 2 | Advanced Statistics, Hypothesis Testing |

**Variant Numbers:**
- **1** (e.g., P11, P31) - Variant 1
- **2** (e.g., P12, P32) - Variant 2
- **3** (e.g., P13, P33) - Variant 3

## Available Papers

### All Sessions (May/June & Oct/Nov)

Full paper range available:
- P11, P12, P13
- P31, P32, P33
- P41, P42, P43
- P51, P52, P53
- P61, P62, P63

### February/March Session (Limited)

Only variant 2 papers available:
- P12, P32, P42, P52, P62

**Note:** Feb/Mar sessions only offer variant 2 for most papers.

## Download Methods

### Method 1: Automated Scraper (Recommended)

The built-in `PapaCambridgeScraper` class handles everything:

```python
from src.scrapers.papacambridge_scraper import PapaCambridgeScraper

scraper = PapaCambridgeScraper(output_dir="Cambridge-9709/raw_pdfs")
results = scraper.scrape_all_years(2020, 2025)
scraper.save_download_log(results)
```

**Features:**
- Automatic retry with exponential backoff
- Random delays to avoid rate limiting
- User-agent rotation
- Progress logging
- Organized folder structure by year/session

### Method 2: Command Line with wget

Download specific papers:

```bash
# Create directory structure
mkdir -p Cambridge-9709/raw_pdfs/2023/may_june

# Download question paper
wget -P Cambridge-9709/raw_pdfs/2023/may_june \
  https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9709_s23_qp_12.pdf

# Download mark scheme
wget -P Cambridge-9709/raw_pdfs/2023/may_june \
  https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9709_s23_ms_12.pdf
```

### Method 3: Python requests

Simple Python script:

```python
import requests
import time

def download_paper(year, session, paper, doc_type):
    """
    Download a single paper

    Args:
        year: Full year (e.g., 2023)
        session: 's', 'w', or 'm'
        paper: Paper code (e.g., '12')
        doc_type: 'qp' or 'ms'
    """
    year_short = str(year)[-2:]
    filename = f"9709_{session}{year_short}_{doc_type}_{paper}.pdf"
    url = f"https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{filename}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {filename}")
        return True
    else:
        print(f"Failed: {filename} (Status: {response.status_code})")
        return False

# Example: Download May/June 2023 Paper 12 QP
download_paper(2023, 's', '12', 'qp')
time.sleep(2)  # Be polite to the server
download_paper(2023, 's', '12', 'ms')
```

## Anti-Blocking Strategies

Papa Cambridge may block rapid automated downloads. Here's how to avoid issues:

### 1. Rate Limiting

**Add delays between requests:**
```python
import time
import random

# Random delay between 1-3 seconds
time.sleep(random.uniform(1, 3))
```

### 2. User-Agent Rotation

**Rotate user agents:**
```python
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Firefox/121.0',
]

headers = {'User-Agent': random.choice(user_agents)}
```

### 3. Exponential Backoff

**Retry failed requests with increasing delays:**
```python
def fetch_with_retry(url, max_retries=4):
    for attempt in range(max_retries):
        try:
            delay = 2 ** attempt  # 1s, 2s, 4s, 8s
            time.sleep(delay)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            continue
```

### 4. Session Reuse

**Reuse connections:**
```python
session = requests.Session()
response = session.get(url, headers=headers)
```

### 5. Respectful Scraping

- **Don't** spam requests (max 1 request per second)
- **Do** add random delays
- **Do** use retry logic
- **Do** log failed downloads for manual retry
- **Don't** run multiple scrapers in parallel

## Troubleshooting

### Error: 403 Forbidden

**Cause:** Server blocking your IP/user-agent

**Solutions:**
1. Wait 10-15 minutes before retrying
2. Change user-agent string
3. Add longer delays between requests
4. Try manual download in browser first

### Error: 404 Not Found

**Cause:** Paper doesn't exist or wrong URL

**Check:**
1. Verify paper code exists for that session
2. Feb/Mar only has variant 2 papers
3. Some older years may have gaps
4. Double-check year/session/paper format

### Error: Timeout

**Cause:** Slow network or server overload

**Solutions:**
1. Increase timeout: `requests.get(url, timeout=60)`
2. Retry after a few minutes
3. Check internet connection

### Error: Invalid PDF

**Cause:** Server returned HTML error page instead of PDF

**Check:**
1. Verify URL in browser
2. Check if `Content-Type` is `application/pdf`
3. Verify response starts with `%PDF`

```python
if response.headers.get('content-type') == 'application/pdf':
    # Save file
elif response.content[:4] == b'%PDF':
    # Save file
else:
    print("Not a valid PDF!")
```

### Downloaded Papers Organized by Session

Expected folder structure after download:

```
Cambridge-9709/raw_pdfs/
├── 2020/
│   ├── feb_march/
│   │   ├── 9709_m20_qp_12.pdf
│   │   ├── 9709_m20_ms_12.pdf
│   │   └── ...
│   ├── may_june/
│   │   ├── 9709_s20_qp_11.pdf
│   │   ├── 9709_s20_ms_11.pdf
│   │   └── ...
│   └── oct_nov/
│       ├── 9709_w20_qp_11.pdf
│       ├── 9709_w20_ms_11.pdf
│       └── ...
├── 2021/
│   └── ...
└── ...
```

## Advanced Tips

### Bulk Download Script

Download all papers for a specific year:

```bash
#!/bin/bash
YEAR=2023
SESSIONS=("s" "w")
PAPERS=("11" "12" "13" "31" "32" "33" "41" "42" "43" "51" "52" "53" "61" "62" "63")

for session in "${SESSIONS[@]}"; do
    for paper in "${PAPERS[@]}"; do
        for type in "qp" "ms"; do
            url="https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9709_${session}${YEAR:2:2}_${type}_${paper}.pdf"
            wget -q "$url" -O "9709_${session}${YEAR:2:2}_${type}_${paper}.pdf" && echo "✓ $paper" || echo "✗ $paper"
            sleep 2
        done
    done
done
```

### Verify Downloads

Check downloaded PDFs are valid:

```bash
# Count PDFs
find Cambridge-9709/raw_pdfs -name "*.pdf" | wc -l

# Check for corrupted PDFs
find Cambridge-9709/raw_pdfs -name "*.pdf" -exec file {} \; | grep -v PDF

# Verify PDF headers
find Cambridge-9709/raw_pdfs -name "*.pdf" -exec head -c 4 {} \; -exec echo {} \; | grep -v "%PDF"
```

## Resources

- **Papa Cambridge:** https://pastpapers.papacambridge.com
- **CAIE Subject Page:** https://pastpapers.papacambridge.com/papers/caie/as-and-a-level-mathematics-9709
- **Syllabus:** 9709 AS/A Level Mathematics (2026-2027)

## Notes

- Papers typically released 3-4 months after exam session
- Not all variants available for all sessions
- Specimen papers may have different naming conventions
- Some years may have missing papers (COVID-19 affected 2020-2021)

## Contributing

Found a better download method or encountered issues? Contributions welcome!

## Legal Notice

This tool is for educational purposes only. Respect Papa Cambridge's terms of service and use responsibly. Papers are copyrighted by Cambridge Assessment International Education.
