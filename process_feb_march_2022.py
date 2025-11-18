#!/usr/bin/env python3
"""
Process specific Feb/March 2022 papers (P32, P42, P52, P62)
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parsers.pdf_processor import PDFProcessor, QuestionPaperProcessor, MarkSchemeProcessor
from parsers.question_parser import QuestionParser, MarkSchemeParser
from utils.topic_mapper import TopicMapper
from utils.data_exporter import DataExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_single_paper(paper_code: str, base_dir: Path):
    """
    Process a single Feb/March 2022 paper

    Args:
        paper_code: Paper code like '32', '42', '52', '62'
        base_dir: Base directory containing raw_pdfs
    """
    # Construct file paths
    qp_path = base_dir / "raw_pdfs" / "2022" / "feb_march" / f"9709_m22_qp_{paper_code}.pdf"
    ms_path = base_dir / "raw_pdfs" / "2022" / "feb_march" / f"9709_m22_ms_{paper_code}.pdf"

    if not qp_path.exists():
        logger.error(f"Question paper not found: {qp_path}")
        return None

    if not ms_path.exists():
        logger.error(f"Mark scheme not found: {ms_path}")
        return None

    logger.info(f"\n{'='*80}")
    logger.info(f"Processing Feb/March 2022 Paper P{paper_code}")
    logger.info(f"{'='*80}\n")

    # Initialize processors
    qp_processor = QuestionPaperProcessor()
    ms_processor = MarkSchemeProcessor()
    question_parser = QuestionParser()
    ms_parser = MarkSchemeParser()
    topic_mapper = TopicMapper()
    exporter = DataExporter(output_base_dir=str(base_dir))

    # Process Question Paper
    logger.info("Processing question paper...")
    qp_pages = qp_processor.process_pdf(qp_path)

    if not qp_pages:
        logger.error(f"Failed to process question paper: {qp_path}")
        return None

    # Parse questions
    logger.info("Parsing questions...")
    questions = question_parser.parse_question_paper(qp_pages)
    logger.info(f"  Found {len(questions)} questions")

    # Process Mark Scheme
    logger.info("Processing mark scheme...")
    ms_pages = ms_processor.process_pdf(ms_path)

    if ms_pages:
        # Parse answers
        logger.info("Parsing mark scheme answers...")
        answers = ms_parser.parse_mark_scheme(ms_pages)

        # Match answers to questions
        logger.info("Matching answers to questions...")
        questions = ms_parser.match_answers_to_questions(questions, answers)
    else:
        logger.warning(f"Failed to process mark scheme: {ms_path}")

    # Map topics (syllabus outcomes)
    logger.info("Mapping syllabus topics...")
    for question in questions:
        topics = topic_mapper.map_question_to_topics(
            question.question_text,
            question.answer_full,
            paper_code
        )
        question.topics = topics

    # Build paper data structure
    year = 2022
    session = 'F/M'
    paper = f"P{paper_code}"
    variant = int(paper_code[1]) if len(paper_code) > 1 else 0

    paper_data = {
        'year': year,
        'session': session,
        'paper': paper,
        'variant': variant,
        'questions': [q.to_dict() for q in questions]
    }

    # Export individual paper JSON
    logger.info("Exporting paper data...")
    json_path = exporter.export_paper_json(paper_data)

    logger.info(f"\n✓ Successfully processed P{paper_code}")
    logger.info(f"  Questions extracted: {len(questions)}")
    logger.info(f"  Saved to: {json_path}")

    return paper_data


def main():
    """Process all Feb/March 2022 papers"""
    base_dir = Path("Cambridge-9709")

    # Papers to process
    papers = ['32', '42', '52', '62']

    logger.info("\n" + "#"*80)
    logger.info("# PROCESSING FEB/MARCH 2022 PAPERS (P32, P42, P52, P62)")
    logger.info("#"*80 + "\n")

    results = {}

    for paper_code in papers:
        result = process_single_paper(paper_code, base_dir)
        if result:
            results[paper_code] = result

    logger.info("\n" + "#"*80)
    logger.info(f"# PROCESSING COMPLETE - {len(results)}/{len(papers)} papers processed")
    logger.info("#"*80 + "\n")

    return results


if __name__ == "__main__":
    main()
