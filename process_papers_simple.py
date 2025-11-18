#!/usr/bin/env python3
"""
Simple processor for Feb/March 2022 papers using PyPDF2
"""

import re
import json
import PyPDF2
from pathlib import Path
from typing import List, Dict, Optional


class SimpleQuestionPart:
    """Simple question part representation"""
    def __init__(self, qid: str, question_text: str):
        self.qid = qid
        self.question_text = question_text
        self.answer_full = ""
        self.answer_snippet = ""
        self.topics = []
        self.page = 0
        self.marks = None

    def to_dict(self):
        return {
            'qid': self.qid,
            'question_text': self.question_text,
            'answer_full': self.answer_full,
            'answer_snippet': self.answer_snippet,
            'topics': self.topics,
            'page': self.page,
            'marks': self.marks
        }


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using PyPDF2"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text


def extract_marks(text: str) -> Optional[int]:
    """Extract marks from text like [3] or [4 marks]"""
    match = re.search(r'\[(\d+)\s*(?:mark|mk|m)?s?\]', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def parse_questions_simple(text: str) -> List[SimpleQuestionPart]:
    """
    Simple question parser
    Extract main questions (1, 2, 3, etc.) and sub-parts (a), (b), (i), (ii)
    """
    questions = []
    lines = text.split('\n')

    current_question = None
    current_text = []

    # Pattern to match question numbers
    main_q_pattern = re.compile(r'^\s*(\d+)\s+(.*)$')
    sub_q_pattern = re.compile(r'^\s*\(([a-z]|[ivxlcdm]+)\)\s+(.*)$')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for main question (1, 2, 3, etc.)
        main_match = main_q_pattern.match(line)
        if main_match and len(main_match.group(1)) <= 2:  # Question number shouldn't be too long
            # Save previous question
            if current_question and current_text:
                current_question.question_text = ' '.join(current_text)
                current_question.marks = extract_marks(current_question.question_text)
                questions.append(current_question)

            # Start new question
            qid = main_match.group(1)
            current_question = SimpleQuestionPart(qid, "")
            current_text = [main_match.group(2)]
            continue

        # Check for sub-question
        sub_match = sub_q_pattern.match(line)
        if sub_match and current_question:
            # Save previous if exists
            if current_text:
                if current_question.question_text:
                    # This is a sub-part, create new question
                    sub_qid = f"{current_question.qid}({sub_match.group(1)})"
                    new_q = SimpleQuestionPart(sub_qid, sub_match.group(2))
                    current_question = new_q
                    current_text = [sub_match.group(2)]
                else:
                    current_question.question_text = ' '.join(current_text)
                    current_question.marks = extract_marks(current_question.question_text)
                    questions.append(current_question)

                    sub_qid = f"{current_question.qid.split('(')[0]}({sub_match.group(1)})"
                    current_question = SimpleQuestionPart(sub_qid, "")
                    current_text = [sub_match.group(2)]
            continue

        # Continue current question text
        if current_question:
            current_text.append(line)

    # Save last question
    if current_question and current_text:
        current_question.question_text = ' '.join(current_text)
        current_question.marks = extract_marks(current_question.question_text)
        questions.append(current_question)

    return questions


def parse_mark_scheme_simple(text: str) -> Dict[str, str]:
    """Simple mark scheme parser"""
    answers = {}
    lines = text.split('\n')

    current_qid = None
    current_answer = []

    # Pattern for question identifiers in mark scheme
    qid_pattern = re.compile(r'^\s*(\d+)\s*(?:\(([a-z]|[ivxlcdm]+)\))?\s*')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts with question number
        match = qid_pattern.match(line)
        if match:
            # Save previous answer
            if current_qid and current_answer:
                answers[current_qid] = ' '.join(current_answer)

            # Extract QID
            main_num = match.group(1)
            sub_part = match.group(2)
            if sub_part:
                current_qid = f"{main_num}({sub_part})"
            else:
                current_qid = main_num

            # Get rest of line as start of answer
            rest = line[match.end():]
            current_answer = [rest] if rest else []
        elif current_qid:
            current_answer.append(line)

    # Save last answer
    if current_qid and current_answer:
        answers[current_qid] = ' '.join(current_answer)

    return answers


def map_simple_topics(question_text: str, paper_code: str) -> List[str]:
    """
    Simple topic mapping based on keywords
    Maps to Cambridge 9709 syllabus topics
    """
    topics = []
    text_lower = question_text.lower()

    # Determine paper type from code
    paper_type = paper_code[0] if paper_code else '1'

    # Pure Math 1 topics (Papers 1, 3)
    if paper_type in ['1', '3']:
        if any(word in text_lower for word in ['quadratic', 'factor', 'roots', 'discriminant']):
            topics.append('P1.1')
        if any(word in text_lower for word in ['function', 'composite', 'inverse', 'domain', 'range']):
            topics.append('P1.2')
        if any(word in text_lower for word in ['coordinate', 'straight line', 'gradient', 'perpendicular']):
            topics.append('P1.3')
        if any(word in text_lower for word in ['circle', 'tangent', 'chord']):
            topics.append('P1.4')
        if any(word in text_lower for word in ['sequence', 'series', 'arithmetic', 'geometric', 'progression']):
            topics.append('P1.5')
        if any(word in text_lower for word in ['differentiation', 'derivative', 'gradient', 'tangent', 'normal']):
            topics.append('P1.6')
        if any(word in text_lower for word in ['integration', 'integral', 'area under curve']):
            topics.append('P1.7')
        if any(word in text_lower for word in ['trigonometry', 'sin', 'cos', 'tan', 'radians', 'degrees']):
            topics.append('P1.8')

    # Pure Math 2/3 topics (Papers 3)
    if paper_type == '3':
        if any(word in text_lower for word in ['logarithm', 'exponential', 'ln', 'log']):
            topics.append('P2.1')
        if any(word in text_lower for word in ['algebraic', 'partial fractions', 'polynomial']):
            topics.append('P2.2')
        if any(word in text_lower for word in ['trigonometric identities', 'double angle', 'addition formula']):
            topics.append('P2.3')

    # Mechanics topics (Papers 4, 5)
    if paper_type in ['4', '5']:
        if any(word in text_lower for word in ['force', 'newton', 'equilibrium', 'friction']):
            topics.append('M1.1')
        if any(word in text_lower for word in ['kinematics', 'velocity', 'acceleration', 'displacement']):
            topics.append('M1.2')
        if any(word in text_lower for word in ['projectile', 'trajectory']):
            topics.append('M1.3')
        if any(word in text_lower for word in ['work', 'energy', 'power', 'momentum']):
            topics.append('M1.4')

    # Statistics topics (Papers 6)
    if paper_type == '6':
        if any(word in text_lower for word in ['probability', 'permutation', 'combination']):
            topics.append('S1.1')
        if any(word in text_lower for word in ['discrete', 'binomial', 'poisson', 'distribution']):
            topics.append('S1.2')
        if any(word in text_lower for word in ['normal distribution', 'standard normal', 'z-score']):
            topics.append('S1.3')
        if any(word in text_lower for word in ['sample', 'mean', 'variance', 'standard deviation']):
            topics.append('S1.4')
        if any(word in text_lower for word in ['hypothesis', 'test', 'significance', 'p-value']):
            topics.append('S1.5')

    return topics if topics else ['General']


def process_paper(paper_code: str):
    """Process a single Feb/March 2022 paper"""
    base_dir = Path("Cambridge-9709")

    qp_path = base_dir / "raw_pdfs" / "2022" / "feb_march" / f"9709_m22_qp_{paper_code}.pdf"
    ms_path = base_dir / "raw_pdfs" / "2022" / "feb_march" / f"9709_m22_ms_{paper_code}.pdf"

    print(f"\n{'='*80}")
    print(f"Processing Feb/March 2022 Paper P{paper_code}")
    print(f"{'='*80}\n")

    # Extract text from question paper
    print("Extracting text from question paper...")
    qp_text = extract_text_from_pdf(qp_path)

    # Parse questions
    print("Parsing questions...")
    questions = parse_questions_simple(qp_text)
    print(f"  Found {len(questions)} question parts")

    # Extract text from mark scheme
    print("Extracting text from mark scheme...")
    ms_text = extract_text_from_pdf(ms_path)

    # Parse mark scheme
    print("Parsing mark scheme answers...")
    answers = parse_mark_scheme_simple(ms_text)
    print(f"  Found {len(answers)} answers")

    # Match answers to questions
    print("Matching answers to questions...")
    for question in questions:
        if question.qid in answers:
            question.answer_full = answers[question.qid]
            # Create snippet (first 100 chars)
            question.answer_snippet = question.answer_full[:100]

    # Map topics
    print("Mapping syllabus topics...")
    for question in questions:
        question.topics = map_simple_topics(question.question_text, paper_code)

    # Create paper data structure
    paper_data = {
        'year': 2022,
        'session': 'F/M',
        'paper': f'P{paper_code}',
        'variant': int(paper_code[1]),
        'questions': [q.to_dict() for q in questions]
    }

    # Save JSON
    output_dir = base_dir / "parsed_json"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"2022_FM_P{paper_code}.json"
    with open(output_file, 'w') as f:
        json.dump(paper_data, f, indent=2)

    print(f"\n✓ Successfully processed P{paper_code}")
    print(f"  Questions extracted: {len(questions)}")
    print(f"  Output: {output_file}")

    return paper_data


def main():
    """Process all Feb/March 2022 papers"""
    papers = ['32', '42', '52', '62']

    print("\n" + "#"*80)
    print("# PROCESSING FEB/MARCH 2022 PAPERS (P32, P42, P52, P62)")
    print("#"*80)

    for paper_code in papers:
        try:
            process_paper(paper_code)
        except Exception as e:
            print(f"\n✗ Error processing P{paper_code}: {e}")

    print("\n" + "#"*80)
    print("# PROCESSING COMPLETE")
    print("#"*80 + "\n")


if __name__ == "__main__":
    main()
