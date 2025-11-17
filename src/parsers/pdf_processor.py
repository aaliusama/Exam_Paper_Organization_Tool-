"""
PDF Processor with OCR Support
Handles both text-based and image-based PDFs
"""

import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import io
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Process PDFs with text extraction and OCR fallback"""

    # Threshold for determining if a page needs OCR (characters per page)
    TEXT_DENSITY_THRESHOLD = 50

    def __init__(self, tesseract_config: str = "--psm 6 --oem 3"):
        """
        Initialize PDF processor

        Args:
            tesseract_config: Tesseract configuration string
                --psm 6: Assume a single uniform block of text
                --oem 3: Use both legacy and LSTM OCR engines
        """
        self.tesseract_config = tesseract_config

    def extract_text_from_page(self, page) -> Tuple[str, bool]:
        """
        Extract text from a pdfplumber page

        Returns:
            Tuple of (extracted_text, is_low_density)
        """
        text = page.extract_text()

        if not text:
            return "", True

        # Check text density
        char_count = len(text.strip())
        is_low_density = char_count < self.TEXT_DENSITY_THRESHOLD

        return text, is_low_density

    def ocr_page(self, pdf_path: Path, page_num: int) -> str:
        """
        Perform OCR on a specific page

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)

        Returns:
            OCR extracted text
        """
        try:
            # Convert PDF page to image
            images = convert_from_path(
                pdf_path,
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=300
            )

            if not images:
                logger.warning(f"No image generated for page {page_num}")
                return ""

            # Perform OCR
            image = images[0]
            text = pytesseract.image_to_string(image, config=self.tesseract_config)

            return text

        except Exception as e:
            logger.error(f"OCR failed for page {page_num}: {str(e)}")
            return ""

    def process_pdf(self, pdf_path: Path, force_ocr: bool = False) -> List[Dict]:
        """
        Process entire PDF with hybrid text extraction and OCR

        Args:
            pdf_path: Path to PDF file
            force_ocr: Force OCR on all pages

        Returns:
            List of page dictionaries with text and metadata
        """
        logger.info(f"Processing: {pdf_path.name}")

        pages_data = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages):
                    logger.debug(f"Processing page {page_num + 1}/{total_pages}")

                    # Try normal text extraction first
                    extracted_text, is_low_density = self.extract_text_from_page(page)

                    # Determine if OCR is needed
                    needs_ocr = force_ocr or is_low_density
                    ocr_text = ""

                    if needs_ocr:
                        logger.info(f"Page {page_num + 1} needs OCR (low text density)")
                        ocr_text = self.ocr_page(pdf_path, page_num)

                    # Use OCR text if extracted text is insufficient
                    final_text = ocr_text if needs_ocr and ocr_text else extracted_text

                    page_data = {
                        'page_number': page_num + 1,
                        'text': final_text,
                        'raw_ocr': ocr_text if needs_ocr else None,
                        'extracted_text': extracted_text,
                        'used_ocr': needs_ocr,
                        'is_low_density': is_low_density
                    }

                    pages_data.append(page_data)

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path.name}: {str(e)}")
            return []

        logger.info(f"Processed {len(pages_data)} pages from {pdf_path.name}")
        return pages_data

    def process_pdf_simple(self, pdf_path: Path) -> str:
        """
        Simple PDF processing - returns all text concatenated

        Args:
            pdf_path: Path to PDF file

        Returns:
            Full text content
        """
        pages = self.process_pdf(pdf_path)
        return "\n\n".join([p['text'] for p in pages if p['text']])

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove page numbers (common patterns)
        text = re.sub(r'\[Turn over\]?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)

        # Clean up
        text = text.strip()

        return text

    @staticmethod
    def split_by_pages(pages_data: List[Dict]) -> Dict[int, str]:
        """
        Split processed pages into a dictionary

        Returns:
            Dictionary mapping page_number -> text
        """
        return {p['page_number']: p['text'] for p in pages_data}


class QuestionPaperProcessor(PDFProcessor):
    """Specialized processor for Question Papers"""

    def extract_questions(self, pages_data: List[Dict]) -> List[Dict]:
        """
        Extract individual questions from processed pages

        Returns:
            List of question dictionaries
        """
        questions = []
        current_question = None

        for page in pages_data:
            text = page['text']
            page_num = page['page_number']

            # Find question numbers (e.g., "1 ", "2 ", etc.)
            # Pattern: number at start of line or after newline
            question_matches = re.finditer(r'^(\d+)\s+(.+?)(?=^\d+\s+|\Z)', text, re.MULTILINE | re.DOTALL)

            for match in question_matches:
                q_num = match.group(1)
                q_text = match.group(2).strip()

                question_data = {
                    'question_number': q_num,
                    'full_text': q_text,
                    'page': page_num,
                    'raw_ocr': page.get('raw_ocr', None)
                }

                questions.append(question_data)

        return questions


class MarkSchemeProcessor(PDFProcessor):
    """Specialized processor for Mark Schemes"""

    def extract_answers(self, pages_data: List[Dict]) -> List[Dict]:
        """
        Extract answers from mark scheme

        Returns:
            List of answer dictionaries
        """
        answers = []

        for page in pages_data:
            text = page['text']
            page_num = page['page_number']

            # Find question/sub-question patterns
            # Pattern: "1", "1(a)", "1(a)(i)", etc.
            answer_pattern = r'(\d+(?:\([a-z]\))?(?:\([ivx]+\))?)\s+(.+?)(?=\d+(?:\([a-z]\))?(?:\([ivx]+\))?\s+|\Z)'
            answer_matches = re.finditer(answer_pattern, text, re.MULTILINE | re.DOTALL)

            for match in answer_matches:
                q_ref = match.group(1)
                answer_text = match.group(2).strip()

                answer_data = {
                    'question_ref': q_ref,
                    'answer_text': answer_text,
                    'page': page_num
                }

                answers.append(answer_data)

        return answers


if __name__ == "__main__":
    # Test the processor
    processor = PDFProcessor()

    # Example usage
    test_pdf = Path("Cambridge-9709/raw_pdfs/2023/may_june/9709_s23_qp_12.pdf")
    if test_pdf.exists():
        pages = processor.process_pdf(test_pdf)
        print(f"Processed {len(pages)} pages")
        for p in pages[:2]:  # Print first 2 pages
            print(f"\nPage {p['page_number']}:")
            print(f"Used OCR: {p['used_ocr']}")
            print(f"Text preview: {p['text'][:200]}...")
