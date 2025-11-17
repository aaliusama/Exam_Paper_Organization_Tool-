"""
Advanced Question Parser
Extracts questions and sub-parts from Cambridge 9709 papers
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QuestionPart:
    """Represents a question or sub-question"""
    qid: str  # e.g., "1", "1(a)", "1(a)(i)"
    question_text: str
    answer_full: str = ""
    answer_snippet: str = ""
    topics: List[str] = None
    page: int = 0
    raw_ocr: str = ""
    marks: Optional[int] = None

    def __post_init__(self):
        if self.topics is None:
            self.topics = []

    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)


class QuestionParser:
    """Parse questions from processed PDF text"""

    # Regex patterns for question identification
    QUESTION_PATTERNS = {
        'main': r'^(\d+)\s+',  # Main question: "1 ", "2 ", etc.
        'sub_a': r'^\s*\(([a-z])\)\s*',  # Sub-part: "(a) ", "(b) ", etc.
        'sub_i': r'^\s*\(([ivxlcdm]+)\)\s*',  # Sub-sub-part: "(i) ", "(ii) ", etc.
        'combined': r'^(\d+)\s*\(([a-z])\)\s*(?:\(([ivxlcdm]+)\)\s*)?',  # Combined: "1(a)(i)"
    }

    # Marks pattern
    MARKS_PATTERN = r'\[(\d+)\s*(?:mark|mk|m)s?\]'

    def __init__(self):
        self.questions = []

    @staticmethod
    def normalize_qid(qid: str) -> str:
        """Normalize question ID to standard format"""
        # Remove spaces
        qid = qid.replace(' ', '')
        # Ensure consistent format: "1(a)(i)"
        return qid

    @staticmethod
    def parse_qid_level(qid: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """
        Parse question ID into components

        Args:
            qid: Question ID like "1", "1(a)", "1(a)(i)"

        Returns:
            Tuple of (main_num, sub_letter, sub_roman)
        """
        # Pattern: main(sub)(subsub)
        match = re.match(r'^(\d+)(?:\(([a-z])\))?(?:\(([ivxlcdm]+)\))?$', qid.lower())

        if match:
            main_num = int(match.group(1))
            sub_letter = match.group(2)
            sub_roman = match.group(3)
            return main_num, sub_letter, sub_roman

        return None, None, None

    def extract_marks(self, text: str) -> Optional[int]:
        """Extract marks from text"""
        match = re.search(self.MARKS_PATTERN, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def split_into_questions(self, text: str, page_num: int = 1) -> List[QuestionPart]:
        """
        Split text into individual questions and sub-parts

        Args:
            text: Full text from page(s)
            page_num: Page number

        Returns:
            List of QuestionPart objects
        """
        questions = []
        lines = text.split('\n')

        current_qid = None
        current_text = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # Try to match question patterns
            qid_found = None

            # Pattern 1: "1(a)(i)" - full notation
            match = re.match(r'^(\d+\([a-z]\)(?:\([ivxlcdm]+\))?)\s+(.+)', line)
            if match:
                qid_found = match.group(1)
                text_start = match.group(2)

            # Pattern 2: "1 " - main question
            elif re.match(r'^(\d+)\s+', line):
                match = re.match(r'^(\d+)\s+(.+)', line)
                qid_found = match.group(1)
                text_start = match.group(2)

            # Pattern 3: "(a) " - sub-question
            elif re.match(r'^\(([a-z])\)\s+', line):
                match = re.match(r'^\(([a-z])\)\s+(.+)', line)
                if current_qid and current_qid.isdigit():
                    # Append to current main question
                    qid_found = f"{current_qid}({match.group(1)})"
                    text_start = match.group(2)

            # Pattern 4: "(i) " - sub-sub-question
            elif re.match(r'^\(([ivxlcdm]+)\)\s+', line):
                match = re.match(r'^\(([ivxlcdm]+)\)\s+(.+)', line)
                if current_qid and '(' in current_qid:
                    # Append to current sub-question
                    main_part = current_qid.split(')')[0] + ')'
                    qid_found = f"{main_part}({match.group(1)})"
                    text_start = match.group(2)

            # If we found a new question ID
            if qid_found:
                # Save previous question
                if current_qid and current_text:
                    full_text = ' '.join(current_text).strip()
                    marks = self.extract_marks(full_text)
                    questions.append(QuestionPart(
                        qid=self.normalize_qid(current_qid),
                        question_text=full_text,
                        page=page_num,
                        marks=marks
                    ))

                # Start new question
                current_qid = qid_found
                current_text = [text_start]

            else:
                # Continue current question
                if current_qid:
                    current_text.append(line)

            i += 1

        # Save last question
        if current_qid and current_text:
            full_text = ' '.join(current_text).strip()
            marks = self.extract_marks(full_text)
            questions.append(QuestionPart(
                qid=self.normalize_qid(current_qid),
                question_text=full_text,
                page=page_num,
                marks=marks
            ))

        return questions

    def parse_question_paper(self, pages_data: List[Dict]) -> List[QuestionPart]:
        """
        Parse entire question paper

        Args:
            pages_data: List of page dictionaries from PDFProcessor

        Returns:
            List of QuestionPart objects
        """
        all_questions = []

        for page_data in pages_data:
            text = page_data['text']
            page_num = page_data['page_number']
            raw_ocr = page_data.get('raw_ocr', '')

            # Extract questions from this page
            page_questions = self.split_into_questions(text, page_num)

            # Add raw OCR to questions
            for q in page_questions:
                q.raw_ocr = raw_ocr

            all_questions.extend(page_questions)

        logger.info(f"Extracted {len(all_questions)} questions/sub-questions")
        return all_questions


class MarkSchemeParser:
    """Parse mark schemes and match to questions"""

    def __init__(self):
        self.answers = {}

    @staticmethod
    def normalize_qid(qid: str) -> str:
        """Normalize question ID"""
        # Remove spaces and standardize
        qid = qid.replace(' ', '')
        # Handle different formats
        qid = re.sub(r'\s*\(\s*([a-z])\s*\)\s*', r'(\1)', qid)
        qid = re.sub(r'\s*\(\s*([ivxlcdm]+)\s*\)\s*', r'(\1)', qid)
        return qid

    def extract_answer_snippet(self, answer_text: str, max_lines: int = 3) -> str:
        """
        Generate short answer snippet from full answer

        Args:
            answer_text: Full answer text
            max_lines: Maximum number of lines to include

        Returns:
            Short snippet
        """
        # Split by newlines or sentences
        lines = answer_text.split('\n')

        # Take first few non-empty lines
        snippet_lines = []
        for line in lines:
            line = line.strip()
            if line and len(snippet_lines) < max_lines:
                snippet_lines.append(line)

        snippet = ' '.join(snippet_lines)

        # Truncate if too long
        if len(snippet) > 200:
            snippet = snippet[:197] + "..."

        return snippet

    def parse_mark_scheme(self, pages_data: List[Dict]) -> Dict[str, Dict]:
        """
        Parse mark scheme and extract answers

        Args:
            pages_data: List of page dictionaries from PDFProcessor

        Returns:
            Dictionary mapping qid -> answer data
        """
        answers = {}

        for page_data in pages_data:
            text = page_data['text']
            page_num = page_data['page_number']

            # Split by question references
            # Pattern: "1", "1(a)", "1(a)(i)", etc. at start of line
            pattern = r'^(\d+(?:\([a-z]\))?(?:\([ivxlcdm]+\))?)\s+(.+?)(?=^\d+(?:\([a-z]\))?(?:\([ivxlcdm]+\))?\s+|\Z)'

            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)

            for match in matches:
                qid = self.normalize_qid(match.group(1))
                answer_text = match.group(2).strip()

                # Generate snippet
                snippet = self.extract_answer_snippet(answer_text)

                answers[qid] = {
                    'answer_full': answer_text,
                    'answer_snippet': snippet,
                    'page': page_num
                }

        logger.info(f"Extracted {len(answers)} answers from mark scheme")
        return answers

    def match_answers_to_questions(self, questions: List[QuestionPart],
                                   answers: Dict[str, Dict]) -> List[QuestionPart]:
        """
        Match mark scheme answers to questions

        Args:
            questions: List of QuestionPart objects
            answers: Dictionary of answers from mark scheme

        Returns:
            Updated questions with answers
        """
        matched_count = 0

        for question in questions:
            qid = question.qid

            if qid in answers:
                answer_data = answers[qid]
                question.answer_full = answer_data['answer_full']
                question.answer_snippet = answer_data['answer_snippet']
                matched_count += 1

        logger.info(f"Matched {matched_count}/{len(questions)} questions with answers")
        return questions


if __name__ == "__main__":
    # Test the parser
    sample_text = """
    1  Find the coefficient of x^3 in the expansion of (2 + x)^6. [3]

    (a) Solve the equation 2x^2 - 5x + 2 = 0. [2]

    (b) Hence solve 2(y + 1)^2 - 5(y + 1) + 2 = 0. [3]

    2  The equation of a curve is y = 3x^2 - 12x + 5.

    (i) Express 3x^2 - 12x + 5 in the form a(x - b)^2 + c. [3]

    (ii) State the coordinates of the minimum point. [2]
    """

    parser = QuestionParser()
    questions = parser.split_into_questions(sample_text)

    print(f"Found {len(questions)} questions:")
    for q in questions:
        print(f"\nQID: {q.qid}")
        print(f"Text: {q.question_text[:80]}...")
        print(f"Marks: {q.marks}")
