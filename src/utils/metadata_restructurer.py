"""
Metadata Restructurer - Converts flat question list to hierarchical structure
Transforms qid-based structure to question_number with subparts
"""

import re
from typing import Dict, List, Optional
from collections import defaultdict


class MetadataRestructurer:
    """Restructures question metadata into hierarchical format"""

    @staticmethod
    def parse_qid(qid: str) -> tuple:
        """
        Parse question ID into components

        Args:
            qid: Question ID (e.g., "7", "7(a)", "7(a)(i)")

        Returns:
            Tuple of (question_number, subparts_list)
            Example: "7(a)(ii)" -> ("7", ["a", "ii"])
        """
        # Match patterns like: 7, 7(a), 7(a)(i), 7(a)(ii)
        match = re.match(r'^(\d+)(.*)$', qid)
        if not match:
            return (qid, [])

        question_number = match.group(1)
        remainder = match.group(2)

        # Extract subparts
        subparts = []
        subpart_matches = re.findall(r'\(([a-z]+|i+|iv|v|vi+|ix|x)\)', remainder)
        subparts = subpart_matches

        return (question_number, subparts)

    @staticmethod
    def group_questions_by_number(questions: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group questions by main question number

        Args:
            questions: List of question dictionaries with qid

        Returns:
            Dictionary mapping question_number to list of questions/subparts
        """
        grouped = defaultdict(list)

        for q in questions:
            qid = q.get('qid', '')
            question_number, _ = MetadataRestructurer.parse_qid(qid)
            grouped[question_number].append(q)

        return dict(grouped)

    @staticmethod
    def get_main_question_data(questions: List[Dict]) -> Dict:
        """
        Extract main question data from a group

        Args:
            questions: List of questions with same question number

        Returns:
            Dictionary with main question metadata
        """
        # Sort by qid length to get the simplest one first (main question)
        sorted_qs = sorted(questions, key=lambda q: len(q.get('qid', '')))
        main_q = sorted_qs[0]

        # Collect all unique subparts
        all_subparts = []
        for q in questions:
            _, subparts = MetadataRestructurer.parse_qid(q.get('qid', ''))
            if subparts and subparts[0] not in all_subparts:
                all_subparts.append(subparts[0])

        # Get total marks
        total_marks = sum(q.get('marks', 0) for q in questions)

        # Get page (use minimum page number)
        pages = [q.get('page', 0) for q in questions if q.get('page', 0) > 0]
        page = min(pages) if pages else 0

        # Get topics (union of all topics)
        all_topics = []
        for q in questions:
            topics = q.get('topics', [])
            if isinstance(topics, list):
                all_topics.extend(topics)
        unique_topics = list(set(all_topics))

        # Determine main topic description
        topic_description = MetadataRestructurer.get_topic_description(unique_topics)

        return {
            'question_number': main_q.get('qid', '').split('(')[0],
            'subparts': all_subparts if all_subparts else [],
            'page': page,
            'marks': total_marks,
            'syllabus_outcomes': unique_topics,
            'topic': topic_description
        }

    @staticmethod
    def get_topic_description(topic_codes: List[str]) -> str:
        """
        Convert topic codes to human-readable description

        Args:
            topic_codes: List of topic codes (e.g., ["P1.7", "P1.8"])

        Returns:
            Human-readable topic description
        """
        # Topic code to description mapping
        topic_map = {
            # Pure Math 1
            'P1.1': 'Quadratics',
            'P1.2': 'Functions',
            'P1.3': 'Coordinate Geometry',
            'P1.4': 'Circular Measure',
            'P1.5': 'Trigonometry - Identities and equations',
            'P1.6': 'Series',
            'P1.7': 'Differentiation',
            'P1.8': 'Integration',
            # Pure Math 2/3
            'P2.1': 'Algebra',
            'P2.2': 'Logarithmic and Exponential Functions',
            'P2.3': 'Trigonometry - Advanced',
            'P2.4': 'Differentiation - Advanced',
            'P2.5': 'Integration - Advanced',
            'P2.6': 'Numerical Solutions',
            'P3.1': 'Vectors',
            'P3.2': 'Complex Numbers',
            'P3.3': 'Differential Equations',
            # Mechanics
            'M1.1': 'Forces and Equilibrium',
            'M1.2': 'Kinematics',
            'M1.3': 'Newton\'s Laws',
            'M1.4': 'Energy, Work and Power',
            # Statistics
            'S1.1': 'Data Representation',
            'S1.2': 'Measures of Location and Spread',
            'S1.3': 'Probability',
            'S1.4': 'Discrete Random Variables',
            'S1.5': 'Normal Distribution',
            'S2.1': 'Continuous Random Variables',
            'S2.2': 'Sampling and Hypothesis Testing',
            'S2.3': 'Linear Combinations',
        }

        if not topic_codes:
            return "General"

        # Get descriptions for all codes
        descriptions = []
        for code in topic_codes:
            if code in topic_map:
                descriptions.append(topic_map[code])

        if not descriptions:
            return "General Mathematics"

        # Return first description or combined if multiple
        if len(descriptions) == 1:
            return descriptions[0]
        else:
            # Combine related topics
            return " / ".join(descriptions[:2])  # Limit to 2 for readability

    @staticmethod
    def create_subpart_detail(question: Dict) -> Dict:
        """
        Create subpart detail object

        Args:
            question: Question dictionary

        Returns:
            Subpart detail object
        """
        qid = question.get('qid', '')
        _, subparts = MetadataRestructurer.parse_qid(qid)

        # Get the first subpart letter (e.g., "a" from "7(a)" or "7(a)(i)")
        subpart = subparts[0] if subparts else ""

        # Handle nested subparts like 7(a)(i)
        if len(subparts) > 1:
            subpart = f"{subparts[0]}({subparts[1]})"

        detail = {
            'subpart': subpart if subpart else qid,
            'marks': question.get('marks', 0),
            'syllabus_outcomes': question.get('topics', []),
            'answers': {
                'answer_snippet': question.get('answer_snippet', '') or question.get('answer_full', '')[:200]
            }
        }

        # Add enhanced metadata if available
        if 'difficulty' in question:
            detail['difficulty'] = question['difficulty']
            detail['difficulty_confidence'] = question.get('difficulty_confidence', 0)

        if 'question_types' in question:
            detail['question_types'] = question['question_types']

        if 'concepts' in question:
            detail['concepts'] = question['concepts']

        if 'key_terms' in question:
            detail['key_terms'] = question['key_terms']

        if 'math_notation' in question:
            detail['math_notation'] = question['math_notation']

        if 'required_knowledge' in question:
            detail['required_knowledge'] = question['required_knowledge']

        # Add full question text if needed
        if question.get('question_text'):
            detail['question_text'] = question['question_text']

        # Add full answer if needed
        if question.get('answer_full'):
            detail['answers']['answer_full'] = question['answer_full']

        return detail

    @staticmethod
    def restructure_paper(paper_data: Dict) -> Dict:
        """
        Restructure paper data to hierarchical format

        Args:
            paper_data: Original paper data with flat question list

        Returns:
            Restructured paper data with hierarchical questions
        """
        original_questions = paper_data.get('questions', [])

        # Group by question number
        grouped = MetadataRestructurer.group_questions_by_number(original_questions)

        # Build hierarchical structure
        hierarchical_questions = []

        for question_num in sorted(grouped.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            question_group = grouped[question_num]

            # Get main question data
            main_data = MetadataRestructurer.get_main_question_data(question_group)

            # Create subpart details
            subpart_details = []
            for q in sorted(question_group, key=lambda x: x.get('qid', '')):
                detail = MetadataRestructurer.create_subpart_detail(q)
                subpart_details.append(detail)

            main_data['subpart_details'] = subpart_details

            hierarchical_questions.append(main_data)

        # Build new paper structure
        restructured = {
            'year': paper_data.get('year'),
            'session': paper_data.get('session'),
            'paper': paper_data.get('paper'),
            'variant': paper_data.get('variant'),
            'questions': hierarchical_questions
        }

        # Preserve paper stats if available
        if 'paper_stats' in paper_data:
            restructured['paper_stats'] = paper_data['paper_stats']

        return restructured


def restructure_paper_metadata(input_data: Dict) -> Dict:
    """
    Convenience function to restructure paper metadata

    Args:
        input_data: Original paper data

    Returns:
        Restructured paper data
    """
    restructurer = MetadataRestructurer()
    return restructurer.restructure_paper(input_data)


if __name__ == "__main__":
    # Example usage
    import json
    import sys

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.json', '_restructured.json')

        with open(input_file, 'r') as f:
            data = json.load(f)

        restructured = restructure_paper_metadata(data)

        with open(output_file, 'w') as f:
            json.dump(restructured, f, indent=2)

        print(f"Restructured {input_file} -> {output_file}")
        print(f"Questions: {len(restructured.get('questions', []))}")
    else:
        print("Usage: python metadata_restructurer.py <input.json> [output.json]")
