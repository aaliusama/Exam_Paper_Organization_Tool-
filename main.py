#!/usr/bin/env python3
"""
Cambridge 9709 Mathematics Past Papers - Complete Pipeline
Main orchestrator script for scraping, parsing, and uploading

Usage:
    python main.py --mode all           # Run complete pipeline
    python main.py --mode scrape        # Only scrape papers
    python main.py --mode parse         # Only parse existing PDFs
    python main.py --mode upload        # Only upload to Drive
    python main.py --year 2023          # Process specific year
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict
import json
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scrapers.papacambridge_scraper import PapaCambridgeScraper
from parsers.pdf_processor import PDFProcessor, QuestionPaperProcessor, MarkSchemeProcessor
from parsers.question_parser import QuestionParser, MarkSchemeParser
from utils.topic_mapper import TopicMapper
from utils.data_exporter import DataExporter
from utils.drive_uploader import DriveUploader
from utils.metadata_enhancer import MetadataEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Cambridge-9709/logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Main orchestrator for the complete pipeline"""

    def __init__(self, base_dir: str = "Cambridge-9709", use_enhanced_metadata: bool = False):
        """
        Initialize pipeline orchestrator

        Args:
            base_dir: Base directory for all outputs
            use_enhanced_metadata: Whether to use ML-based metadata enhancement
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

        # Initialize components
        self.scraper = PapaCambridgeScraper(output_dir=str(self.base_dir / "raw_pdfs"))
        self.pdf_processor = PDFProcessor()
        self.qp_processor = QuestionPaperProcessor()
        self.ms_processor = MarkSchemeProcessor()
        self.question_parser = QuestionParser()
        self.ms_parser = MarkSchemeParser()
        self.topic_mapper = TopicMapper()
        self.exporter = DataExporter(output_base_dir=str(self.base_dir))
        self.drive_uploader = DriveUploader()
        self.metadata_enhancer = MetadataEnhancer(use_ml_models=use_enhanced_metadata)
        self.use_enhanced_metadata = use_enhanced_metadata

        # Storage for processed data
        self.all_papers_data = []

    def scrape_papers(self, start_year: int = 2020, end_year: int = 2025):
        """
        Step 1: Scrape all papers from PapaCambridge

        Args:
            start_year: Start year
            end_year: End year
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 1: SCRAPING PAPERS FROM PAPACAMBRIDGE")
        logger.info("="*80 + "\n")

        results = self.scraper.scrape_all_years(start_year, end_year)
        self.scraper.save_download_log(results)

        return results

    def parse_paper_pair(self, qp_path: Path, ms_path: Path) -> Dict:
        """
        Parse a QP+MS pair

        Args:
            qp_path: Path to question paper PDF
            ms_path: Path to mark scheme PDF

        Returns:
            Dictionary with parsed paper data
        """
        # Extract metadata from filename
        # Format: 9709_s23_qp_12.pdf
        filename = qp_path.stem
        parts = filename.split('_')

        if len(parts) >= 4:
            session_code = parts[1][0]  # 's', 'w', or 'm'
            year_short = parts[1][1:]   # '23'
            paper_code = parts[3]        # '12'

            # Convert to full year
            year = 2000 + int(year_short)

            # Convert session code
            session_map = {'s': 'M/J', 'w': 'O/N', 'm': 'F/M'}
            session = session_map.get(session_code, 'Unknown')

            # Extract variant
            variant = int(paper_code[1]) if len(paper_code) > 1 else 0
            paper = f"P{paper_code}"
        else:
            logger.warning(f"Could not parse filename: {filename}")
            return None

        logger.info(f"\nProcessing: {year} {session} Paper {paper}")

        # Process QP
        logger.info("  Processing question paper...")
        qp_pages = self.qp_processor.process_pdf(qp_path)

        if not qp_pages:
            logger.error(f"  Failed to process QP: {qp_path}")
            return None

        # Parse questions
        questions = self.question_parser.parse_question_paper(qp_pages)

        # Process MS
        logger.info("  Processing mark scheme...")
        ms_pages = self.ms_processor.process_pdf(ms_path)

        if ms_pages:
            # Parse answers
            answers = self.ms_parser.parse_mark_scheme(ms_pages)

            # Match answers to questions
            questions = self.ms_parser.match_answers_to_questions(questions, answers)
        else:
            logger.warning(f"  Failed to process MS: {ms_path}")

        # Map topics
        logger.info("  Mapping topics...")
        for question in questions:
            topics = self.topic_mapper.map_question_to_topics(
                question.question_text,
                question.answer_full,
                paper_code
            )
            question.topics = topics

        # Build paper data structure
        paper_data = {
            'year': year,
            'session': session,
            'paper': paper,
            'variant': variant,
            'questions': [q.to_dict() for q in questions]
        }

        logger.info(f"  ✓ Extracted {len(questions)} questions")

        # Enhance metadata if enabled
        if self.use_enhanced_metadata:
            logger.info("  Enhancing metadata with ML models...")
            paper_data = self.metadata_enhancer.enhance_paper_metadata(paper_data)
            logger.info("  ✓ Metadata enhanced")

        return paper_data

    def parse_all_papers(self, start_year: int = 2020, end_year: int = 2025):
        """
        Step 2: Parse all downloaded PDFs

        Args:
            start_year: Start year
            end_year: End year
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 2: PARSING PDFs WITH OCR")
        logger.info("="*80 + "\n")

        raw_pdfs_dir = self.base_dir / "raw_pdfs"

        if not raw_pdfs_dir.exists():
            logger.error(f"Raw PDFs directory not found: {raw_pdfs_dir}")
            return []

        all_papers = []

        # Find all QP PDFs
        qp_files = sorted(raw_pdfs_dir.rglob("*_qp_*.pdf"))

        logger.info(f"Found {len(qp_files)} question papers to process\n")

        for qp_path in tqdm(qp_files, desc="Processing papers"):
            # Find corresponding MS
            ms_path = Path(str(qp_path).replace('_qp_', '_ms_'))

            if not ms_path.exists():
                logger.warning(f"Mark scheme not found for: {qp_path.name}")
                continue

            # Parse the pair
            paper_data = self.parse_paper_pair(qp_path, ms_path)

            if paper_data:
                all_papers.append(paper_data)

                # Export individual paper JSON
                self.exporter.export_paper_json(paper_data)

        self.all_papers_data = all_papers

        logger.info(f"\n✓ Processed {len(all_papers)} papers successfully")

        return all_papers

    def export_datasets(self):
        """
        Step 3: Export combined datasets

        """
        logger.info("\n" + "="*80)
        logger.info("STEP 3: EXPORTING DATASETS")
        logger.info("="*80 + "\n")

        if not self.all_papers_data:
            logger.error("No papers data to export")
            return

        # Group by year
        papers_by_year = {}
        for paper in self.all_papers_data:
            year = paper['year']
            if year not in papers_by_year:
                papers_by_year[year] = []
            papers_by_year[year].append(paper)

        # Export yearly CSVs
        logger.info("Exporting yearly CSV files...")
        for year, papers in papers_by_year.items():
            self.exporter.export_year_csv(year, papers)

        # Export master dataset
        logger.info("Exporting master dataset...")
        json_path, csv_path = self.exporter.export_master_dataset(self.all_papers_data)

        # Create summary statistics
        logger.info("Creating summary statistics...")
        stats = self.exporter.create_summary_stats(self.all_papers_data)
        self.exporter.print_summary(stats)

        logger.info("\n✓ All exports completed")

    def upload_to_drive(self):
        """
        Step 4: Upload to Google Drive
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 4: UPLOADING TO GOOGLE DRIVE")
        logger.info("="*80 + "\n")

        # Check for credentials
        if not Path('credentials.json').exists():
            logger.warning("credentials.json not found!")
            logger.warning("To upload to Google Drive:")
            logger.warning("1. Go to https://console.cloud.google.com/")
            logger.warning("2. Create OAuth2 credentials for Desktop app")
            logger.warning("3. Download as credentials.json")
            logger.warning("\nSkipping upload step...")
            return

        # Authenticate
        if not self.drive_uploader.authenticate():
            logger.error("Failed to authenticate with Google Drive")
            return

        # Upload dataset
        self.drive_uploader.upload_dataset(str(self.base_dir))

        logger.info("\n✓ Upload completed")

    def run_full_pipeline(self, start_year: int = 2020, end_year: int = 2025,
                         skip_scrape: bool = False, skip_upload: bool = False):
        """
        Run the complete pipeline

        Args:
            start_year: Start year
            end_year: End year
            skip_scrape: Skip scraping step (use existing PDFs)
            skip_upload: Skip upload step
        """
        logger.info("\n" + "#"*80)
        logger.info("# CAMBRIDGE 9709 MATHEMATICS - COMPLETE PIPELINE")
        logger.info(f"# Processing years: {start_year} - {end_year}")
        logger.info("#"*80 + "\n")

        try:
            # Step 1: Scrape (optional)
            if not skip_scrape:
                self.scrape_papers(start_year, end_year)
            else:
                logger.info("Skipping scrape step (using existing PDFs)")

            # Step 2: Parse
            self.parse_all_papers(start_year, end_year)

            # Step 3: Export
            self.export_datasets()

            # Step 4: Upload (optional)
            if not skip_upload:
                self.upload_to_drive()
            else:
                logger.info("Skipping upload step")

            logger.info("\n" + "#"*80)
            logger.info("# PIPELINE COMPLETED SUCCESSFULLY!")
            logger.info("#"*80 + "\n")

        except Exception as e:
            logger.error(f"\n\nPIPELINE FAILED: {str(e)}", exc_info=True)
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Cambridge 9709 Mathematics Past Papers - Complete Pipeline'
    )

    parser.add_argument(
        '--mode',
        choices=['all', 'scrape', 'parse', 'export', 'upload'],
        default='all',
        help='Pipeline mode (default: all)'
    )

    parser.add_argument(
        '--start-year',
        type=int,
        default=2020,
        help='Start year (default: 2020)'
    )

    parser.add_argument(
        '--end-year',
        type=int,
        default=2025,
        help='End year (default: 2025)'
    )

    parser.add_argument(
        '--skip-scrape',
        action='store_true',
        help='Skip scraping step (use existing PDFs)'
    )

    parser.add_argument(
        '--skip-upload',
        action='store_true',
        help='Skip Google Drive upload'
    )

    parser.add_argument(
        '--enhanced-metadata',
        action='store_true',
        help='Enable enhanced metadata using ML models (requires transformers)'
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = PipelineOrchestrator(use_enhanced_metadata=args.enhanced_metadata)

    # Run based on mode
    if args.mode == 'all':
        orchestrator.run_full_pipeline(
            args.start_year,
            args.end_year,
            skip_scrape=args.skip_scrape,
            skip_upload=args.skip_upload
        )
    elif args.mode == 'scrape':
        orchestrator.scrape_papers(args.start_year, args.end_year)
    elif args.mode == 'parse':
        orchestrator.parse_all_papers(args.start_year, args.end_year)
    elif args.mode == 'export':
        orchestrator.export_datasets()
    elif args.mode == 'upload':
        orchestrator.upload_to_drive()


if __name__ == "__main__":
    main()
