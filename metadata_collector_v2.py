#!/usr/bin/env python3
"""
Metadata Collector v2
Extracts comprehensive metadata from Cambridge A-Level Mathematics exam papers.
Maps questions to syllabus learning outcomes and generates JSON metadata files.
"""

import json
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pdfplumber
from anthropic import Anthropic

# Initialize Anthropic client for AI-powered question analysis
client = None
try:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        client = Anthropic(api_key=api_key)
except Exception as e:
    print(f"Warning: Could not initialize Anthropic client: {e}")
    print("Proceeding without AI-powered syllabus mapping.")


def load_syllabus_outcomes() -> Dict:
    """Load the syllabus outcomes mapping from JSON file."""
    with open("syllabus_outcomes.json", "r") as f:
        return json.load(f)


def extract_pdf_text(pdf_path: str) -> List[Dict[str, any]]:
    """Extract text from PDF with page numbers."""
    pages_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    pages_data.append({
                        "page_number": i,
                        "text": text
                    })
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return pages_data


def parse_paper_code(filename: str) -> Dict[str, str]:
    """Parse paper filename to extract metadata.

    Format: 9709_s25_qp_12.pdf
    Returns: {paper_code, session, year, paper_number, doc_type}
    """
    # Remove .pdf extension
    name = filename.replace(".pdf", "")

    # Pattern: 9709_{session}{year}_{qp/ms}_{paper}
    pattern = r"9709_([smw])(\d{2})_(qp|ms)_(\d{2})"
    match = re.match(pattern, name)

    if not match:
        raise ValueError(f"Invalid filename format: {filename}")

    session_code, year, doc_type, paper = match.groups()

    # Map session codes
    session_map = {
        "s": "May/June",
        "w": "October/November",
        "m": "February/March"
    }

    # Map paper numbers to names
    paper_num = int(paper)
    paper_map = {
        11: "Paper 1 Pure Mathematics 1",
        12: "Paper 1 Pure Mathematics 1",
        13: "Paper 1 Pure Mathematics 1",
        31: "Paper 3 Pure Mathematics 3",
        32: "Paper 3 Pure Mathematics 3",
        33: "Paper 3 Pure Mathematics 3",
        41: "Paper 4 Mechanics",
        42: "Paper 4 Mechanics",
        43: "Paper 4 Mechanics",
        51: "Paper 5 Probability & Statistics 1",
        52: "Paper 5 Probability & Statistics 1",
        53: "Paper 5 Probability & Statistics 1",
        61: "Paper 6 Probability & Statistics 2",
        62: "Paper 6 Probability & Statistics 2",
        63: "Paper 6 Probability & Statistics 2",
    }

    return {
        "paper_code": f"9709/{paper}",
        "session": session_map.get(session_code, "Unknown"),
        "year": f"20{year}",
        "paper_number": paper,
        "paper_name": paper_map.get(paper_num, "Unknown Paper"),
        "doc_type": "question_paper" if doc_type == "qp" else "mark_scheme"
    }


def extract_questions_from_qp(pages_data: List[Dict]) -> List[Dict]:
    """Extract question structure from question paper pages."""
    questions = []

    # Combine all text
    full_text = "\n".join([p["text"] for p in pages_data])

    # Pattern to find questions: number at start of line or after clear spacing
    # Matches: "1 ", "2 ", etc., "1(a)", "2(i)", etc.
    question_pattern = r"^\s*(\d+)\s*[\(\[]?([a-z]|i{1,3}|iv|v)?[\)\]]?"

    current_question = None

    for page in pages_data:
        lines = page["text"].split("\n")

        for line in lines:
            # Check if line starts with a question number
            match = re.match(question_pattern, line, re.MULTILINE)
            if match:
                q_num = match.group(1)
                subpart = match.group(2)

                if not subpart:  # Main question
                    if current_question:
                        questions.append(current_question)

                    current_question = {
                        "question_number": q_num,
                        "page": page["page_number"],
                        "subparts": [],
                        "text": line
                    }
                elif current_question and current_question["question_number"] == q_num:
                    # This is a subpart of the current question
                    current_question["subparts"].append(subpart)
            elif current_question:
                # Continue building question text
                current_question["text"] += " " + line.strip()

    if current_question:
        questions.append(current_question)

    return questions


def extract_marks_from_text(text: str) -> Optional[int]:
    """Extract marks from question text using common patterns."""
    # Patterns: [5], [5 marks], (5), (5 marks)
    patterns = [
        r'\[(\d+)\s*(?:marks?)?\]',
        r'\((\d+)\s*(?:marks?)?\)',
        r'(\d+)\s+marks?'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def extract_answers_from_ms(ms_pages: List[Dict], question_number: str) -> Dict:
    """Extract answer information from mark scheme for a specific question."""
    answers = {"answer_snippet": ""}

    # Find pages containing this question number
    relevant_text = []
    for page in ms_pages:
        if re.search(rf"\b{question_number}\b", page["text"]):
            relevant_text.append(page["text"])

    if relevant_text:
        # Extract first few lines as answer snippet
        combined = " ".join(relevant_text)
        # Clean up and limit to reasonable length
        snippet = " ".join(combined.split()[:50])
        answers["answer_snippet"] = snippet

    return answers


def map_question_to_syllabus_ai(question_text: str, paper_number: str, syllabus: Dict) -> List[str]:
    """Use Claude AI to map a question to syllabus learning outcomes."""
    if not client:
        return []

    # Determine which paper's syllabus to use
    paper_key = f"paper_{paper_number[0]}"
    if paper_key not in syllabus:
        return []

    paper_syllabus = syllabus[paper_key]

    # Create a prompt for Claude
    prompt = f"""You are analyzing a Cambridge A-Level Mathematics exam question to determine which syllabus learning outcomes it tests.

Paper: {paper_syllabus['name']}

Question text:
{question_text}

Available syllabus outcomes:
{json.dumps(paper_syllabus['topics'], indent=2)}

Task: Identify which syllabus outcome codes (e.g., "1.2", "3.5", "4.1") this question primarily tests.
Return ONLY a JSON array of outcome codes, like: ["1.2", "1.5"]

If the question tests multiple topics, include all relevant codes.
Response:"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()

        # Try to parse as JSON
        try:
            outcomes = json.loads(response_text)
            if isinstance(outcomes, list):
                return outcomes
        except json.JSONDecodeError:
            # Try to extract from text
            matches = re.findall(r'"\d+\.\d+"', response_text)
            if matches:
                return [m.strip('"') for m in matches]

    except Exception as e:
        print(f"Error in AI mapping: {e}")

    return []


def map_question_to_syllabus_keywords(question_text: str, paper_number: str) -> List[str]:
    """Fallback: Map questions to syllabus outcomes using keyword matching."""

    text_lower = question_text.lower()
    outcomes = []

    # Paper 1 - Pure Mathematics 1
    if paper_number[0] == "1":
        if any(word in text_lower for word in ["quadratic", "discriminant", "completing the square", "parabola"]):
            outcomes.append("1.1")
        if any(word in text_lower for word in ["function", "domain", "range", "inverse", "composite", "transformation", "translate", "stretch"]):
            outcomes.append("1.2")
        if any(word in text_lower for word in ["circle", "line", "gradient", "perpendicular", "parallel", "coordinate", "midpoint"]):
            outcomes.append("1.3")
        if any(word in text_lower for word in ["radian", "arc", "sector", "circular measure"]):
            outcomes.append("1.4")
        if any(word in text_lower for word in ["sin", "cos", "tan", "trigon", "angle"]):
            outcomes.append("1.5")
        if any(word in text_lower for word in ["series", "binomial", "arithmetic progression", "geometric progression", "sum to infinity", "convergent"]):
            outcomes.append("1.6")
        if any(word in text_lower for word in ["derivative", "differentiat", "gradient", "tangent", "normal", "stationary", "maximum", "minimum", "rate of change"]):
            outcomes.append("1.7")
        if any(word in text_lower for word in ["integral", "integrat", "area under", "volume of revolution"]):
            outcomes.append("1.8")

    # Paper 3 - Pure Mathematics 3
    elif paper_number[0] == "3":
        if any(word in text_lower for word in ["modulus", "partial fraction", "polynomial division", "factor theorem", "remainder theorem"]):
            outcomes.append("3.1")
        if any(word in text_lower for word in ["logarithm", "exponential", "ln", " e^", "log"]):
            outcomes.append("3.2")
        if any(word in text_lower for word in ["sec", "cosec", "cot", "double angle", "compound angle"]):
            outcomes.append("3.3")
        if any(word in text_lower for word in ["product rule", "quotient rule", "parametric", "implicit"]):
            outcomes.append("3.4")
        if any(word in text_lower for word in ["integration by parts", "substitution", "partial fraction"]) and "integrat" in text_lower:
            outcomes.append("3.5")
        if any(word in text_lower for word in ["iteration", "numerical", "root", "convergent sequence"]):
            outcomes.append("3.6")
        if any(word in text_lower for word in ["vector", "scalar product", "magnitude", "position vector", "displacement"]):
            outcomes.append("3.7")
        if any(word in text_lower for word in ["differential equation", "separable", "dy/dx"]):
            outcomes.append("3.8")
        if any(word in text_lower for word in ["complex", "argand", "modulus", "argument", "conjugate", "polar form"]):
            outcomes.append("3.9")

    # Paper 4 - Mechanics
    elif paper_number[0] == "4":
        if any(word in text_lower for word in ["force", "equilibrium", "friction", "coefficient", "normal"]):
            outcomes.append("4.1")
        if any(word in text_lower for word in ["velocity", "acceleration", "displacement", "v-t graph", "s-t graph"]):
            outcomes.append("4.2")
        if any(word in text_lower for word in ["momentum", "collision", "impact", "coalesce"]):
            outcomes.append("4.3")
        if any(word in text_lower for word in ["newton", "mass", "weight", "tension", "thrust", "inclined plane"]):
            outcomes.append("4.4")
        if any(word in text_lower for word in ["work", "energy", "power", "kinetic", "potential", "w = mg"]):
            outcomes.append("4.5")

    # Paper 5 - Probability & Statistics 1
    elif paper_number[0] == "5":
        if any(word in text_lower for word in ["histogram", "stem", "leaf", "box plot", "median", "quartile", "standard deviation", "mean"]):
            outcomes.append("5.1")
        if any(word in text_lower for word in ["permutation", "combination", "arrangement", "selection"]):
            outcomes.append("5.2")
        if any(word in text_lower for word in ["probability", "independent", "conditional", "p(a|b)", "mutually exclusive"]):
            outcomes.append("5.3")
        if any(word in text_lower for word in ["binomial", "geometric", "random variable", "e(x)", "var(x)"]):
            outcomes.append("5.4")
        if any(word in text_lower for word in ["normal distribution", "standard normal", "z-score", "continuity correction"]):
            outcomes.append("5.5")

    # Paper 6 - Probability & Statistics 2
    elif paper_number[0] == "6":
        if any(word in text_lower for word in ["poisson", "po(λ)"]):
            outcomes.append("6.1")
        if any(word in text_lower for word in ["linear combination", "e(ax+b)", "var(ax+b)"]):
            outcomes.append("6.2")
        if any(word in text_lower for word in ["probability density", "pdf", "continuous random"]):
            outcomes.append("6.3")
        if any(word in text_lower for word in ["sample", "population", "unbiased", "confidence interval", "central limit"]):
            outcomes.append("6.4")
        if any(word in text_lower for word in ["hypothesis test", "null hypothesis", "significance", "type i", "type ii"]):
            outcomes.append("6.5")

    return outcomes if outcomes else [f"{paper_number[0]}.1"]  # Default to first topic if no match


def determine_topic_from_outcomes(outcomes: List[str], syllabus: Dict, paper_number: str) -> str:
    """Determine the topic name from syllabus outcomes."""
    if not outcomes:
        return "Unknown"

    paper_key = f"paper_{paper_number[0]}"
    if paper_key not in syllabus:
        return "Unknown"

    # Get the first outcome's topic name
    first_outcome = outcomes[0]
    topics = syllabus[paper_key].get("topics", {})

    if first_outcome in topics:
        return topics[first_outcome]["name"]

    return "Unknown"


def calculate_time_allowed(paper_number: str) -> str:
    """Return standard time allowed for each paper type."""
    time_map = {
        "1": "1 hour 50 minutes",
        "3": "1 hour 50 minutes",
        "4": "1 hour 15 minutes",
        "5": "1 hour 15 minutes",
        "6": "1 hour 15 minutes",
    }
    return time_map.get(paper_number[0], "Unknown")


def calculate_total_marks(paper_number: str) -> int:
    """Return standard total marks for each paper type."""
    marks_map = {
        "1": 75,
        "3": 75,
        "4": 50,
        "5": 50,
        "6": 50,
    }
    return marks_map.get(paper_number[0], 0)


def process_paper_pair(qp_path: str, ms_path: str, syllabus: Dict) -> Dict:
    """Process a question paper and its mark scheme to generate metadata."""

    print(f"\nProcessing: {os.path.basename(qp_path)}")

    # Parse paper information
    paper_info = parse_paper_code(os.path.basename(qp_path))

    # Extract text from both PDFs
    qp_pages = extract_pdf_text(qp_path)
    ms_pages = extract_pdf_text(ms_path)

    if not qp_pages:
        print(f"  ✗ Could not extract text from question paper")
        return None

    # Extract questions
    questions = extract_questions_from_qp(qp_pages)
    print(f"  Found {len(questions)} questions")

    # Process each question
    processed_questions = []

    for q in questions:
        q_num = q["question_number"]

        # Extract marks
        marks = extract_marks_from_text(q["text"])

        # Extract answers from mark scheme
        answers = extract_answers_from_ms(ms_pages, q_num)

        # Map to syllabus outcomes using AI (or fallback to keywords)
        syllabus_outcomes = map_question_to_syllabus_ai(
            q["text"],
            paper_info["paper_number"],
            syllabus
        )

        # Fallback to keyword matching if AI didn't return results
        if not syllabus_outcomes:
            syllabus_outcomes = map_question_to_syllabus_keywords(
                q["text"],
                paper_info["paper_number"]
            )

        # Determine topic
        topic = determine_topic_from_outcomes(
            syllabus_outcomes,
            syllabus,
            paper_info["paper_number"]
        )

        question_data = {
            "question_number": q_num,
            "subparts": q["subparts"],
            "page": q["page"],
            "marks": marks or 0,
            "syllabus_outcomes": syllabus_outcomes,
            "topic": topic,
            "answers": answers
        }

        processed_questions.append(question_data)
        print(f"  Q{q_num}: {len(q['subparts'])} subparts, {marks} marks, outcomes: {syllabus_outcomes}")

    # Build metadata structure
    metadata = {
        "exam_info": {
            "paper_code": paper_info["paper_code"],
            "exam_board": "Cambridge International AS & A Level",
            "subject": "Mathematics",
            "paper_name": paper_info["paper_name"],
            "exam_session": f"{paper_info['session']} {paper_info['year']}",
            "total_marks": calculate_total_marks(paper_info["paper_number"]),
            "time_allowed": calculate_time_allowed(paper_info["paper_number"]),
            "question_paper": os.path.basename(qp_path),
            "mark_scheme": os.path.basename(ms_path),
            "syllabus": "697427-2026-2027-syllabus.pdf"
        },
        "questions": processed_questions,
        "statistics": {
            "total_questions": len(processed_questions),
            "total_marks": sum(q.get("marks", 0) for q in processed_questions)
        }
    }

    return metadata


def find_paper_pairs(papers_dir: str) -> List[Tuple[str, str]]:
    """Find all question paper and mark scheme pairs."""
    pairs = []

    # Find all question papers
    qp_pattern = "**/9709_*_qp_*.pdf"
    qp_files = list(Path(papers_dir).glob(qp_pattern))

    for qp_path in qp_files:
        # Find corresponding mark scheme
        qp_name = qp_path.name
        ms_name = qp_name.replace("_qp_", "_ms_")
        ms_path = qp_path.parent / ms_name

        if ms_path.exists():
            pairs.append((str(qp_path), str(ms_path)))
        else:
            print(f"Warning: No mark scheme found for {qp_name}")

    return sorted(pairs)


def main():
    """Main function to process all papers and generate metadata."""

    print("=" * 70)
    print("Cambridge A-Level Mathematics Metadata Collector v2")
    print("=" * 70)

    # Load syllabus outcomes
    print("\nLoading syllabus outcomes...")
    syllabus = load_syllabus_outcomes()
    print(f"  Loaded outcomes for {len(syllabus)} papers")

    # Find all paper pairs in the Cambridge-9709 directory
    papers_dir = "Cambridge-9709/raw_pdfs"
    if not os.path.exists(papers_dir):
        print(f"\nError: Papers directory not found: {papers_dir}")
        print("Please ensure papers are extracted from zip files.")
        return 1

    print(f"\nScanning for papers in: {papers_dir}")
    pairs = find_paper_pairs(papers_dir)
    print(f"  Found {len(pairs)} paper pairs to process")

    if not pairs:
        print("\nNo papers found to process!")
        return 1

    # Create output directory for metadata
    metadata_dir = "metadata"
    os.makedirs(metadata_dir, exist_ok=True)
    print(f"\nMetadata will be saved to: {metadata_dir}/")

    # Process each pair
    successful = 0
    failed = 0

    for i, (qp_path, ms_path) in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}]", end=" ")

        try:
            metadata = process_paper_pair(qp_path, ms_path, syllabus)

            if metadata:
                # Save metadata to JSON file
                qp_basename = os.path.basename(qp_path).replace(".pdf", "")
                output_file = os.path.join(metadata_dir, f"{qp_basename}_metadata.json")

                with open(output_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                print(f"  ✓ Saved to {output_file}")
                successful += 1
            else:
                failed += 1

        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total: {len(pairs)}")
    print(f"\nMetadata files saved in: {metadata_dir}/")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
