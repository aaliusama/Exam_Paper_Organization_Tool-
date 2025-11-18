#!/usr/bin/env python3
"""
Enhanced Metadata Collector with AI-Powered Extraction
Extracts comprehensive metadata from Cambridge A-Level Mathematics exam papers
including detailed subpart structures, accurate marks, and complete answers.

Uses Claude AI to analyze PDFs and generate metadata matching the exact structure
of the example file: 9709_s25_qp_12_metadata.json
"""

import json
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pdfplumber
from anthropic import Anthropic

# Initialize Anthropic client
client = None
try:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("This enhanced version requires Claude API for accurate extraction.")
        sys.exit(1)
    client = Anthropic(api_key=api_key)
except Exception as e:
    print(f"ERROR: Could not initialize Anthropic client: {e}")
    sys.exit(1)


def load_syllabus_outcomes() -> Dict:
    """Load the syllabus outcomes mapping from JSON file."""
    with open("syllabus_outcomes.json", "r") as f:
        return json.load(f)


def load_example_structure() -> Dict:
    """Load the example metadata structure to use as a reference."""
    example_file = "9709_s25_qp_12_metadata.json"
    if os.path.exists(example_file):
        with open(example_file, "r") as f:
            return json.load(f)
    return {}


def extract_pdf_pages_as_images_and_text(pdf_path: str) -> List[Dict]:
    """Extract both text and visual information from PDF pages."""
    pages_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                pages_data.append({
                    "page_number": i,
                    "text": text,
                    "width": page.width,
                    "height": page.height
                })
    except Exception as e:
        print(f"Error extracting from {pdf_path}: {e}")
    return pages_data


def parse_paper_code(filename: str) -> Dict[str, str]:
    """Parse paper filename to extract metadata."""
    name = filename.replace(".pdf", "")
    pattern = r"9709_([smw])(\d{2})_(qp|ms)_(\d{2})"
    match = re.match(pattern, name)

    if not match:
        raise ValueError(f"Invalid filename format: {filename}")

    session_code, year, doc_type, paper = match.groups()

    session_map = {
        "s": "May/June",
        "w": "October/November",
        "m": "February/March"
    }

    paper_num = int(paper)
    paper_map = {
        11: "Paper 1 Pure Mathematics 1", 12: "Paper 1 Pure Mathematics 1", 13: "Paper 1 Pure Mathematics 1",
        31: "Paper 3 Pure Mathematics 3", 32: "Paper 3 Pure Mathematics 3", 33: "Paper 3 Pure Mathematics 3",
        41: "Paper 4 Mechanics", 42: "Paper 4 Mechanics", 43: "Paper 4 Mechanics",
        51: "Paper 5 Probability & Statistics 1", 52: "Paper 5 Probability & Statistics 1", 53: "Paper 5 Probability & Statistics 1",
        61: "Paper 6 Probability & Statistics 2", 62: "Paper 6 Probability & Statistics 2", 63: "Paper 6 Probability & Statistics 2",
    }

    return {
        "paper_code": f"9709/{paper}",
        "session": session_map.get(session_code, "Unknown"),
        "year": f"20{year}",
        "paper_number": paper,
        "paper_name": paper_map.get(paper_num, "Unknown Paper"),
        "doc_type": "question_paper" if doc_type == "qp" else "mark_scheme"
    }


def extract_metadata_with_ai(qp_pages: List[Dict], ms_pages: List[Dict],
                              paper_info: Dict, syllabus: Dict,
                              example_structure: Dict) -> Dict:
    """Use Claude AI to extract complete metadata from question paper and mark scheme."""

    # Combine question paper text (first 10 pages should be enough)
    qp_text = "\n\n=== PAGE BREAK ===\n\n".join([
        f"PAGE {p['page_number']}:\n{p['text']}"
        for p in qp_pages[:min(len(qp_pages), 15)]
    ])

    # Combine mark scheme text (first 15 pages)
    ms_text = "\n\n=== PAGE BREAK ===\n\n".join([
        f"PAGE {p['page_number']}:\n{p['text']}"
        for p in ms_pages[:min(len(ms_pages), 20)]
    ])

    # Get relevant syllabus section
    paper_key = f"paper_{paper_info['paper_number'][0]}"
    paper_syllabus = syllabus.get(paper_key, {})

    # Create comprehensive prompt
    prompt = f"""You are analyzing a Cambridge A-Level Mathematics exam paper to extract complete metadata.

PAPER INFORMATION:
- Paper: {paper_info['paper_name']}
- Session: {paper_info['session']} {paper_info['year']}
- Paper Code: {paper_info['paper_code']}

SYLLABUS TOPICS FOR THIS PAPER:
{json.dumps(paper_syllabus.get('topics', {}), indent=2)}

EXAMPLE METADATA STRUCTURE (follow this EXACTLY):
{json.dumps(example_structure.get('questions', [])[:2], indent=2)}

QUESTION PAPER TEXT:
{qp_text}

MARK SCHEME TEXT:
{ms_text}

TASK:
Extract complete metadata for ALL questions in this paper. Return a JSON object with this EXACT structure:

{{
  "questions": [
    {{
      "question_number": "1",
      "subparts": [],  // or ["a", "b"] if question has subparts
      "page": 2,  // page number where question appears
      "marks": 4,  // total marks for question
      "syllabus_outcomes": ["1.2"],  // which syllabus topics this tests
      "topic": "Functions - Graph transformations",  // descriptive topic
      "answers": {{
        "answer_snippet": "..."  // key answer from mark scheme
      }},
      // IF question has subparts, include:
      "subpart_details": [
        {{
          "subpart": "a",
          "marks": 2,
          "syllabus_outcomes": ["1.2"],
          "answers": {{
            "answer_snippet": "..."
          }}
        }}
      ],
      // IF subparts have sub-subparts (i, ii, iii), include:
      "subsubpart_details": [...]
    }}
  ],
  "syllabus_outcome_summary": {{
    "1.1": {{
      "topic": "Quadratics",
      "questions": ["2", "11a"]
    }}
  }},
  "statistics": {{
    "total_questions": 11,
    "total_subparts": 24,
    "marks_distribution": {{
      "quadratics": 6,
      "functions": 11,
      ...
    }}
  }}
}}

IMPORTANT INSTRUCTIONS:
1. Extract EVERY question from the paper (usually 10-11 questions for Papers 1/3, 6-8 for Papers 4/5/6)
2. For each question, find its page number, total marks, subparts (if any)
3. Map each question to syllabus outcome codes (e.g., "1.2", "3.5") based on the topic it tests
4. Extract answer snippets from the mark scheme
5. If a question has subparts (a, b, c), create subpart_details array
6. If subparts have sub-subparts (i, ii), create subsubpart_details array
7. Create syllabus_outcome_summary grouping questions by outcome
8. Calculate statistics including marks_distribution by topic
9. Return ONLY valid JSON, no explanations

Begin extraction:"""

    try:
        print(f"    Sending to Claude AI for analysis...")

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=16000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Try to extract JSON from response
        # Sometimes Claude wraps JSON in code blocks
        if "```json" in response_text:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        elif "```" in response_text:
            json_match = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

        # Parse JSON
        metadata = json.loads(response_text)
        print(f"    ✓ Successfully extracted {len(metadata.get('questions', []))} questions")

        return metadata

    except json.JSONDecodeError as e:
        print(f"    ✗ Failed to parse JSON response: {e}")
        print(f"    Response preview: {response_text[:500]}...")
        return None
    except Exception as e:
        print(f"    ✗ Error in AI extraction: {e}")
        return None


def calculate_time_allowed(paper_number: str) -> str:
    """Return standard time allowed for each paper type."""
    time_map = {"1": "1 hour 50 minutes", "3": "1 hour 50 minutes",
                "4": "1 hour 15 minutes", "5": "1 hour 15 minutes", "6": "1 hour 15 minutes"}
    return time_map.get(paper_number[0], "Unknown")


def calculate_total_marks(paper_number: str) -> int:
    """Return standard total marks for each paper type."""
    marks_map = {"1": 75, "3": 75, "4": 50, "5": 50, "6": 50}
    return marks_map.get(paper_number[0], 0)


def process_paper_pair_enhanced(qp_path: str, ms_path: str, syllabus: Dict, example_structure: Dict) -> Dict:
    """Process a question paper and mark scheme using AI to generate complete metadata."""

    print(f"\nProcessing: {os.path.basename(qp_path)}")

    # Parse paper information
    paper_info = parse_paper_code(os.path.basename(qp_path))

    # Extract from both PDFs
    print(f"  Extracting text from PDFs...")
    qp_pages = extract_pdf_pages_as_images_and_text(qp_path)
    ms_pages = extract_pdf_pages_as_images_and_text(ms_path)

    if not qp_pages or not ms_pages:
        print(f"  ✗ Failed to extract PDF content")
        return None

    print(f"  Question Paper: {len(qp_pages)} pages")
    print(f"  Mark Scheme: {len(ms_pages)} pages")

    # Use AI to extract complete metadata
    ai_metadata = extract_metadata_with_ai(qp_pages, ms_pages, paper_info, syllabus, example_structure)

    if not ai_metadata:
        return None

    # Build complete metadata structure
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
        "questions": ai_metadata.get("questions", []),
        "syllabus_outcome_summary": ai_metadata.get("syllabus_outcome_summary", {}),
        "statistics": ai_metadata.get("statistics", {
            "total_questions": len(ai_metadata.get("questions", [])),
            "total_marks": sum(q.get("marks", 0) for q in ai_metadata.get("questions", []))
        })
    }

    return metadata


def find_paper_pairs(papers_dir: str, year: str = None, session: str = None) -> List[tuple]:
    """Find question paper and mark scheme pairs, optionally filtered by year/session."""
    pairs = []
    qp_pattern = "**/9709_*_qp_*.pdf"

    for qp_path in Path(papers_dir).glob(qp_pattern):
        # Apply filters if specified
        if year and f"/{year}/" not in str(qp_path):
            continue
        if session and f"/{session}/" not in str(qp_path):
            continue

        ms_name = qp_path.name.replace("_qp_", "_ms_")
        ms_path = qp_path.parent / ms_name

        if ms_path.exists():
            pairs.append((str(qp_path), str(ms_path)))

    return sorted(pairs)


def main():
    """Main function to process papers with enhanced AI extraction."""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced AI-powered metadata extraction")
    parser.add_argument("--year", type=str, help="Process specific year (e.g., 2022)")
    parser.add_argument("--session", type=str, help="Process specific session (may_june, oct_nov, feb_march)")
    parser.add_argument("--paper", type=str, help="Process specific paper file")
    parser.add_argument("--output-dir", type=str, default="metadata_enhanced", help="Output directory")
    args = parser.parse_args()

    print("=" * 70)
    print("Enhanced AI-Powered Metadata Collector")
    print("=" * 70)

    # Load resources
    print("\nLoading resources...")
    syllabus = load_syllabus_outcomes()
    example_structure = load_example_structure()
    print(f"  ✓ Syllabus outcomes loaded")
    print(f"  ✓ Example structure loaded")

    # Find papers to process
    papers_dir = "Cambridge-9709/raw_pdfs"

    if args.paper:
        # Process single paper
        qp_path = args.paper
        ms_path = qp_path.replace("_qp_", "_ms_")
        pairs = [(qp_path, ms_path)] if os.path.exists(ms_path) else []
    else:
        pairs = find_paper_pairs(papers_dir, args.year, args.session)

    print(f"\nFound {len(pairs)} paper pairs to process")

    if not pairs:
        print("No papers found!")
        return 1

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Process each pair
    successful = 0
    failed = 0

    for i, (qp_path, ms_path) in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}]")

        try:
            metadata = process_paper_pair_enhanced(qp_path, ms_path, syllabus, example_structure)

            if metadata:
                qp_basename = os.path.basename(qp_path).replace(".pdf", "")
                output_file = os.path.join(args.output_dir, f"{qp_basename}_metadata.json")

                with open(output_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                print(f"  ✓ Saved to {output_file}")
                successful += 1
            else:
                print(f"  ✗ Failed to generate metadata")
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
    print(f"\nEnhanced metadata saved in: {args.output_dir}/")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
