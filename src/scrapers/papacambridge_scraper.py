"""
PapaCambridge Scraper for Cambridge 9709 Mathematics Papers
Handles scraping with anti-blocking measures and retry logic
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import re
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PapaCambridgeScraper:
    """Scraper for Cambridge 9709 past papers from PapaCambridge"""

    BASE_URL = "https://pastpapers.papacambridge.com"
    SUBJECT_PATH = "/papers/caie/as-and-a-level-mathematics-9709"

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]

    # Papers to scrape (excluding March-only papers from general list)
    PAPER_CODES = {
        'all_sessions': ['11', '12', '13', '31', '32', '33', '41', '42', '43', '51', '52', '53', '61', '62', '63'],
        'march_only': ['12', '32', '42', '52', '62']
    }

    # Session codes
    SESSIONS = {
        'feb_march': ['m', 'march'],
        'may_june': ['s', 'summer'],
        'oct_nov': ['w', 'winter']
    }

    def __init__(self, output_dir: str = "Cambridge-9709/raw_pdfs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.downloaded_count = 0
        self.failed_downloads = []

    def get_headers(self) -> Dict[str, str]:
        """Get random user agent headers"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

    def fetch_with_retry(self, url: str, max_retries: int = 4, is_binary: bool = False) -> Optional[requests.Response]:
        """Fetch URL with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                delay = 2 ** attempt  # Exponential backoff: 1, 2, 4, 8 seconds
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay")
                    time.sleep(delay)

                # Random delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))

                response = self.session.get(url, headers=self.get_headers(), timeout=30)
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed for {url}")
                    return None
        return None

    def get_available_years(self, start_year: int = 2020, end_year: int = 2025) -> List[int]:
        """Get list of years to scrape"""
        return list(range(start_year, end_year + 1))

    def construct_paper_url(self, year: int, session: str, paper_code: str, doc_type: str) -> str:
        """
        Construct PapaCambridge URL for a specific paper

        Args:
            year: Year (e.g., 2023)
            session: Session code ('s' for summer, 'w' for winter, 'm' for march)
            paper_code: Paper code (e.g., '12', '32')
            doc_type: 'qp' for question paper, 'ms' for mark scheme

        Returns:
            Full URL to the PDF
        """
        # Format: 9709_s23_qp_12.pdf
        year_short = str(year)[-2:]  # Get last 2 digits
        filename = f"9709_{session}{year_short}_{doc_type}_{paper_code}.pdf"

        # PapaCambridge structure: /directories/CAIE/CAIE-pastpapers/upload/9709_s23_qp_12.pdf
        # OR: /viewer/9709_s23_qp_12
        # Let's try both patterns

        # Pattern 1: Direct PDF link (most common)
        url = f"{self.BASE_URL}/directories/CAIE/CAIE-pastpapers/upload/{filename}"
        return url

    def get_session_code(self, session_name: str) -> str:
        """Convert session name to code"""
        session_lower = session_name.lower()
        if any(x in session_lower for x in ['feb', 'mar', 'march']):
            return 'm'
        elif any(x in session_lower for x in ['may', 'jun', 'summer']):
            return 's'
        elif any(x in session_lower for x in ['oct', 'nov', 'winter']):
            return 'w'
        return 's'  # Default to summer

    def download_pdf(self, url: str, output_path: Path) -> bool:
        """Download PDF file"""
        if output_path.exists():
            logger.info(f"File already exists: {output_path.name}")
            return True

        logger.info(f"Downloading: {output_path.name}")
        response = self.fetch_with_retry(url, is_binary=True)

        if response and response.status_code == 200:
            # Check if response is actually a PDF
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type or response.content[:4] == b'%PDF':
                output_path.write_bytes(response.content)
                logger.info(f"✓ Downloaded: {output_path.name}")
                self.downloaded_count += 1
                return True
            else:
                logger.warning(f"Response is not a PDF: {url}")
                return False
        else:
            logger.error(f"Failed to download: {url}")
            self.failed_downloads.append(url)
            return False

    def scrape_year(self, year: int) -> Dict[str, List[str]]:
        """
        Scrape all papers for a given year

        Returns:
            Dictionary with session as key and list of downloaded files
        """
        results = {'may_june': [], 'oct_nov': [], 'feb_march': []}

        # Sessions to scrape
        sessions_to_scrape = [
            ('s', 'may_june', self.PAPER_CODES['all_sessions']),
            ('w', 'oct_nov', self.PAPER_CODES['all_sessions']),
            ('m', 'feb_march', self.PAPER_CODES['march_only'])
        ]

        for session_code, session_name, paper_codes in sessions_to_scrape:
            logger.info(f"\n{'='*60}")
            logger.info(f"Scraping {year} {session_name.replace('_', ' ').title()}")
            logger.info(f"{'='*60}")

            # Create year/session folder
            session_dir = self.output_dir / str(year) / session_name
            session_dir.mkdir(parents=True, exist_ok=True)

            for paper_code in paper_codes:
                # Download QP (Question Paper)
                qp_url = self.construct_paper_url(year, session_code, paper_code, 'qp')
                qp_path = session_dir / f"9709_{session_code}{str(year)[-2:]}_qp_{paper_code}.pdf"

                if self.download_pdf(qp_url, qp_path):
                    results[session_name].append(str(qp_path))

                # Download MS (Mark Scheme)
                ms_url = self.construct_paper_url(year, session_code, paper_code, 'ms')
                ms_path = session_dir / f"9709_{session_code}{str(year)[-2:]}_ms_{paper_code}.pdf"

                if self.download_pdf(ms_url, ms_path):
                    results[session_name].append(str(ms_path))

                # Small delay between papers
                time.sleep(random.uniform(0.5, 1.5))

        return results

    def scrape_all_years(self, start_year: int = 2020, end_year: int = 2025) -> Dict:
        """Scrape all papers from start_year to end_year"""
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Starting scrape: Years {start_year}-{end_year}")
        logger.info(f"# Output directory: {self.output_dir}")
        logger.info(f"{'#'*60}\n")

        all_results = {}
        years = self.get_available_years(start_year, end_year)

        for year in years:
            all_results[year] = self.scrape_year(year)

            # Longer delay between years
            if year != years[-1]:
                time.sleep(random.uniform(2, 4))

        # Print summary
        logger.info(f"\n{'#'*60}")
        logger.info(f"# SCRAPING COMPLETE")
        logger.info(f"# Total files downloaded: {self.downloaded_count}")
        logger.info(f"# Failed downloads: {len(self.failed_downloads)}")
        logger.info(f"{'#'*60}\n")

        if self.failed_downloads:
            logger.warning("Failed URLs:")
            for url in self.failed_downloads:
                logger.warning(f"  - {url}")

        return all_results

    def save_download_log(self, results: Dict, log_path: str = "Cambridge-9709/logs/download_log.txt"):
        """Save download results to log file"""
        log_file = Path(log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, 'w') as f:
            f.write(f"Download Log - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Total files downloaded: {self.downloaded_count}\n")
            f.write(f"Failed downloads: {len(self.failed_downloads)}\n\n")

            f.write("Downloaded by Year:\n")
            f.write("-" * 80 + "\n")
            for year, sessions in sorted(results.items()):
                f.write(f"\n{year}:\n")
                for session, files in sessions.items():
                    f.write(f"  {session}: {len(files)} files\n")

            if self.failed_downloads:
                f.write(f"\n\nFailed URLs:\n")
                f.write("-" * 80 + "\n")
                for url in self.failed_downloads:
                    f.write(f"{url}\n")

        logger.info(f"Download log saved to: {log_file}")


if __name__ == "__main__":
    scraper = PapaCambridgeScraper()
    results = scraper.scrape_all_years(2020, 2025)
    scraper.save_download_log(results)
