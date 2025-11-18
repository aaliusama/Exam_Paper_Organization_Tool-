#!/usr/bin/env python3
"""
Downloading Script v2
Downloads Cambridge A-Level Mathematics (9709) past papers from Papa Cambridge.
Supports downloading question papers and mark schemes for specified years and sessions.
"""

import os
import re
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class PapaCambridgeDownloader:
    """Downloader for Cambridge past papers from Papa Cambridge website."""

    BASE_URL = "https://pastpapers.papacambridge.com"
    SUBJECT_URL = f"{BASE_URL}/papers/caie/as-and-a-level-mathematics-9709"

    # Paper numbers for each paper type
    PAPER_VARIANTS = {
        "1": ["11", "12", "13"],
        "3": ["31", "32", "33"],
        "4": ["41", "42", "43"],
        "5": ["51", "52", "53"],
        "6": ["61", "62", "63"]
    }

    # March session only has variant 2
    MARCH_PAPERS = ["12", "32", "42", "52", "62"]

    # Session mappings
    SESSION_CODES = {
        "may_june": "s",
        "oct_nov": "w",
        "feb_march": "m"
    }

    def __init__(self, output_dir: str = "Cambridge-9709/raw_pdfs"):
        """Initialize the downloader.

        Args:
            output_dir: Directory to save downloaded files
        """
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_year_urls(self, start_year: int, end_year: int) -> List[Tuple[str, str]]:
        """Get URLs for each year's papers.

        Args:
            start_year: Starting year (e.g., 2022)
            end_year: Ending year (e.g., 2025)

        Returns:
            List of (year, url) tuples
        """
        year_urls = []
        for year in range(start_year, end_year + 1):
            year_url = f"{self.SUBJECT_URL}/{year}"
            year_urls.append((str(year), year_url))
        return year_urls

    def get_session_urls(self, year: str) -> List[Tuple[str, str, str]]:
        """Get URLs for all sessions in a year.

        Args:
            year: Year as string (e.g., "2022")

        Returns:
            List of (year, session, url) tuples
        """
        session_urls = []

        for session_name, session_code in self.SESSION_CODES.items():
            session_url = f"{self.SUBJECT_URL}/{year}/{session_name}"
            session_urls.append((year, session_name, session_url))

        return session_urls

    def fetch_page(self, url: str, max_retries: int = 3) -> str:
        """Fetch a web page with retries.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            HTML content as string
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"    Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed to fetch {url}: {e}")

    def find_pdf_links(self, html: str, base_url: str) -> List[Tuple[str, str]]:
        """Find all PDF download links on a page.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of (filename, url) tuples
        """
        soup = BeautifulSoup(html, 'html.parser')
        pdf_links = []

        # Find all links to PDFs
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Check if it's a PDF link
            if href.endswith('.pdf') or '/pdf/' in href.lower():
                full_url = urljoin(base_url, href)

                # Extract filename from URL or link text
                filename = os.path.basename(urlparse(full_url).path)
                if not filename.endswith('.pdf'):
                    filename = link.get_text(strip=True)

                pdf_links.append((filename, full_url))

        return pdf_links

    def filter_papers(self, pdf_links: List[Tuple[str, str]], year: str, session: str) -> List[Tuple[str, str]]:
        """Filter PDF links to only include relevant question papers and mark schemes.

        Args:
            pdf_links: List of (filename, url) tuples
            year: Year (e.g., "2022")
            session: Session name (e.g., "may_june")

        Returns:
            Filtered list of (filename, url) tuples
        """
        session_code = self.SESSION_CODES[session]
        year_short = year[2:]  # "2022" -> "22"

        filtered = []

        # Determine which papers to look for
        if session == "feb_march":
            target_papers = self.MARCH_PAPERS
        else:
            # All paper variants
            target_papers = []
            for variants in self.PAPER_VARIANTS.values():
                target_papers.extend(variants)

        for filename, url in pdf_links:
            # Pattern: 9709_s22_qp_12.pdf or 9709_s22_ms_12.pdf
            pattern = rf"9709_{session_code}{year_short}_(qp|ms)_(\d{{2}})\.pdf"
            match = re.search(pattern, filename, re.IGNORECASE)

            if match:
                doc_type = match.group(1).lower()
                paper_num = match.group(2)

                # Check if this paper should be downloaded
                if paper_num in target_papers:
                    # Normalize filename
                    normalized = f"9709_{session_code}{year_short}_{doc_type}_{paper_num}.pdf"
                    filtered.append((normalized, url))

        return filtered

    def download_file(self, url: str, output_path: str, max_retries: int = 3) -> bool:
        """Download a file with retries.

        Args:
            url: URL to download from
            output_path: Local path to save file
            max_retries: Maximum number of retry attempts

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=60, stream=True)
                response.raise_for_status()

                # Create parent directory if needed
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Download with progress
                total_size = int(response.headers.get('content-length', 0))

                with open(output_path, 'wb') as f:
                    if total_size == 0:
                        f.write(response.content)
                    else:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)

                return True

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"      Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"      ✗ Failed: {e}")
                    return False

    def download_session(self, year: str, session: str, session_url: str) -> Tuple[int, int]:
        """Download all papers for a specific session.

        Args:
            year: Year as string
            session: Session name
            session_url: URL for the session page

        Returns:
            Tuple of (successful_downloads, failed_downloads)
        """
        print(f"\n  {session.replace('_', ' ').title()} {year}")
        print(f"    URL: {session_url}")

        try:
            # Fetch the session page
            html = self.fetch_page(session_url)

            # Find all PDF links
            pdf_links = self.find_pdf_links(html, session_url)
            print(f"    Found {len(pdf_links)} PDF links")

            # Filter to get only relevant papers
            filtered_links = self.filter_papers(pdf_links, year, session)
            print(f"    Filtered to {len(filtered_links)} relevant papers")

            if not filtered_links:
                print("    No papers found for this session")
                return 0, 0

            # Download each paper
            successful = 0
            failed = 0

            session_code = self.SESSION_CODES[session]
            year_short = year[2:]

            for filename, url in filtered_links:
                # Create output path: Cambridge-9709/raw_pdfs/2022/may_june/9709_s22_qp_12.pdf
                output_path = os.path.join(
                    self.output_dir,
                    year,
                    session,
                    filename
                )

                # Skip if already exists
                if os.path.exists(output_path):
                    print(f"    ✓ {filename} (already exists)")
                    successful += 1
                    continue

                # Download
                print(f"    ↓ {filename}...", end=" ")
                if self.download_file(url, output_path):
                    print("✓")
                    successful += 1
                else:
                    print("✗")
                    failed += 1

                # Be nice to the server
                time.sleep(0.5)

            return successful, failed

        except Exception as e:
            print(f"    ✗ Error processing session: {e}")
            return 0, 0

    def download_year(self, year: str) -> Tuple[int, int]:
        """Download all papers for a specific year.

        Args:
            year: Year as string (e.g., "2022")

        Returns:
            Tuple of (successful_downloads, failed_downloads)
        """
        print(f"\n{'=' * 60}")
        print(f"Year: {year}")
        print(f"{'=' * 60}")

        total_successful = 0
        total_failed = 0

        # Get all session URLs for this year
        session_urls = self.get_session_urls(year)

        for year, session, session_url in session_urls:
            successful, failed = self.download_session(year, session, session_url)
            total_successful += successful
            total_failed += failed

        return total_successful, total_failed

    def download_range(self, start_year: int, end_year: int) -> Dict[str, int]:
        """Download papers for a range of years.

        Args:
            start_year: Starting year (e.g., 2022)
            end_year: Ending year (e.g., 2025)

        Returns:
            Dictionary with download statistics
        """
        print("\n" + "=" * 70)
        print("Cambridge A-Level Mathematics (9709) Paper Downloader")
        print("=" * 70)
        print(f"Years: {start_year} - {end_year}")
        print(f"Output: {self.output_dir}")
        print("=" * 70)

        total_successful = 0
        total_failed = 0

        for year in range(start_year, end_year + 1):
            successful, failed = self.download_year(str(year))
            total_successful += successful
            total_failed += failed

        # Summary
        print("\n" + "=" * 70)
        print("DOWNLOAD COMPLETE")
        print("=" * 70)
        print(f"Total successful: {total_successful}")
        print(f"Total failed: {total_failed}")
        print(f"Output directory: {self.output_dir}")
        print("=" * 70)

        return {
            "successful": total_successful,
            "failed": total_failed,
            "total": total_successful + total_failed
        }


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download Cambridge A-Level Mathematics papers from Papa Cambridge"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2022,
        help="Starting year (default: 2022)"
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2025,
        help="Ending year (default: 2025)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="Cambridge-9709/raw_pdfs",
        help="Output directory (default: Cambridge-9709/raw_pdfs)"
    )

    args = parser.parse_args()

    # Validate years
    if args.start_year > args.end_year:
        print("Error: start-year must be <= end-year")
        return 1

    if args.start_year < 2000 or args.end_year > 2030:
        print("Error: Years must be between 2000 and 2030")
        return 1

    # Create downloader and run
    downloader = PapaCambridgeDownloader(output_dir=args.output_dir)

    try:
        results = downloader.download_range(args.start_year, args.end_year)
        return 0 if results["failed"] == 0 else 1

    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
