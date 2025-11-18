"""
Enhanced Metadata Generator for Cambridge 9709 Questions
Uses open-source Hugging Face models to add rich metadata without Claude API

Features:
- Difficulty classification (Easy/Medium/Hard)
- Question type identification (Proof, Calculation, Sketch, Show that, etc.)
- Concept extraction and key terms
- Math notation detection
- Required knowledge topics
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

# Lazy imports for ML models (only load when needed)
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers not installed. Install with: pip install transformers torch")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetadataEnhancer:
    """Enhanced metadata generator using open-source NLP models"""

    # Question type patterns (rule-based fallback)
    QUESTION_PATTERNS = {
        'proof': [
            r'\bprove\b', r'\bshow that\b', r'\bverify that\b',
            r'\bdemonstrate\b', r'\bjustify\b', r'\bexplain why\b'
        ],
        'calculation': [
            r'\bcalculate\b', r'\bfind\b', r'\bdetermine\b',
            r'\bsolve\b', r'\bcompute\b', r'\bevaluate\b'
        ],
        'sketch': [
            r'\bsketch\b', r'\bdraw\b', r'\bgraph\b', r'\bplot\b',
            r'\billustrate\b', r'\bdiagram\b'
        ],
        'show_that': [
            r'\bshow that\b', r'\bprove that\b', r'\bverify that\b'
        ],
        'state': [
            r'\bstate\b', r'\bwrite down\b', r'\bgive\b', r'\blist\b'
        ],
        'explain': [
            r'\bexplain\b', r'\bdescribe\b', r'\binterpret\b',
            r'\bcomment on\b', r'\bdiscuss\b'
        ]
    }

    # Math concept keywords
    CONCEPT_KEYWORDS = {
        'algebra': [
            'polynomial', 'quadratic', 'equation', 'inequality', 'factor',
            'expand', 'simplify', 'expression', 'binomial', 'coefficient'
        ],
        'calculus': [
            'derivative', 'differentiate', 'integrate', 'integration',
            'gradient', 'rate of change', 'stationary point', 'maximum',
            'minimum', 'area under curve', 'volume'
        ],
        'trigonometry': [
            'sin', 'cos', 'tan', 'sine', 'cosine', 'tangent',
            'radian', 'angle', 'triangle', 'identity'
        ],
        'vectors': [
            'vector', 'magnitude', 'direction', 'dot product', 'cross product',
            'scalar product', 'position vector', 'unit vector'
        ],
        'complex_numbers': [
            'complex', 'imaginary', 'modulus', 'argument', 'conjugate',
            'real part', 'imaginary part'
        ],
        'probability': [
            'probability', 'random', 'distribution', 'expected value',
            'variance', 'standard deviation', 'normal distribution'
        ],
        'statistics': [
            'mean', 'median', 'mode', 'range', 'hypothesis test',
            'significance', 'correlation', 'regression', 'sample'
        ],
        'mechanics': [
            'force', 'velocity', 'acceleration', 'mass', 'momentum',
            'energy', 'work', 'power', 'friction', 'tension'
        ],
        'geometry': [
            'circle', 'line', 'coordinate', 'distance', 'midpoint',
            'perpendicular', 'parallel', 'tangent', 'normal'
        ]
    }

    def __init__(self, use_ml_models: bool = True, model_cache_dir: Optional[str] = None):
        """
        Initialize metadata enhancer

        Args:
            use_ml_models: Whether to use ML models (requires transformers)
            model_cache_dir: Directory to cache downloaded models
        """
        self.use_ml_models = use_ml_models and TRANSFORMERS_AVAILABLE
        self.model_cache_dir = model_cache_dir or str(Path.home() / '.cache' / 'huggingface')

        # Lazy-loaded models
        self._difficulty_classifier = None
        self._text_classifier = None

        if self.use_ml_models:
            logger.info("MetadataEnhancer initialized with ML models enabled")
        else:
            logger.info("MetadataEnhancer initialized in rule-based mode (no ML models)")

    def _load_difficulty_classifier(self):
        """Load difficulty classification model (lazy loading)"""
        if self._difficulty_classifier is None and self.use_ml_models:
            try:
                # Using a general text classification model
                # We'll use zero-shot classification for difficulty
                logger.info("Loading zero-shot classification model...")
                self._difficulty_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    cache_dir=self.model_cache_dir
                )
                logger.info("Difficulty classifier loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}. Using rule-based fallback.")
                self.use_ml_models = False

    def classify_difficulty(self, question_text: str, answer_text: str = "",
                          marks: int = 0) -> Tuple[str, float]:
        """
        Classify question difficulty

        Args:
            question_text: Question text
            answer_text: Answer/solution text
            marks: Marks allocated

        Returns:
            Tuple of (difficulty_level, confidence_score)
        """
        # Rule-based baseline using marks
        if marks:
            if marks <= 3:
                rule_difficulty = "Easy"
            elif marks <= 6:
                rule_difficulty = "Medium"
            else:
                rule_difficulty = "Hard"
        else:
            rule_difficulty = "Medium"

        # If ML models available, use them for refinement
        if self.use_ml_models:
            try:
                self._load_difficulty_classifier()
                if self._difficulty_classifier:
                    # Prepare text for classification
                    text = f"Question: {question_text[:500]}"  # Limit length
                    if answer_text:
                        text += f"\nSolution: {answer_text[:300]}"

                    # Zero-shot classification
                    result = self._difficulty_classifier(
                        text,
                        candidate_labels=["easy math problem", "medium difficulty math problem",
                                        "hard math problem", "very difficult math problem"],
                        multi_label=False
                    )

                    # Map labels to difficulty
                    label_map = {
                        "easy math problem": "Easy",
                        "medium difficulty math problem": "Medium",
                        "hard math problem": "Hard",
                        "very difficult math problem": "Hard"
                    }

                    ml_difficulty = label_map.get(result['labels'][0], "Medium")
                    confidence = result['scores'][0]

                    # Combine ML and rule-based
                    if confidence > 0.7:
                        return ml_difficulty, confidence
                    else:
                        # Low confidence, use rule-based
                        return rule_difficulty, 0.5

            except Exception as e:
                logger.warning(f"Difficulty classification failed: {e}")

        # Fallback to rule-based
        return rule_difficulty, 0.5

    def classify_question_type(self, question_text: str) -> List[str]:
        """
        Identify question types (can have multiple)

        Args:
            question_text: Question text

        Returns:
            List of question types
        """
        question_lower = question_text.lower()
        types = []

        for qtype, patterns in self.QUESTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    types.append(qtype)
                    break  # Don't duplicate same type

        # Default if no type found
        if not types:
            types.append('calculation')

        return list(set(types))  # Remove duplicates

    def extract_concepts(self, question_text: str, answer_text: str = "") -> List[str]:
        """
        Extract mathematical concepts from question

        Args:
            question_text: Question text
            answer_text: Answer text (optional)

        Returns:
            List of concept categories
        """
        text = (question_text + " " + answer_text).lower()
        concepts = []

        for concept, keywords in self.CONCEPT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    concepts.append(concept)
                    break  # Don't duplicate same concept

        return list(set(concepts))

    def extract_key_terms(self, question_text: str, max_terms: int = 10) -> List[str]:
        """
        Extract key mathematical terms from question

        Args:
            question_text: Question text
            max_terms: Maximum number of terms to return

        Returns:
            List of key terms
        """
        # Math-specific term patterns
        patterns = [
            r'\b[a-z]+(?:tion|ive|ial|ity|ent|ence)\b',  # Mathematical suffixes
            r'\b(?:coefficient|constant|variable|parameter|function|equation)\b',
            r'\b(?:theorem|formula|law|rule|principle)\b',
            r'\b(?:maximum|minimum|gradient|intercept|asymptote)\b',
        ]

        terms = []
        for pattern in patterns:
            matches = re.findall(pattern, question_text.lower())
            terms.extend(matches)

        # Also extract capitalized terms (might be important)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', question_text)
        terms.extend([t.lower() for t in capitalized])

        # Remove duplicates and limit
        unique_terms = list(set(terms))[:max_terms]

        return unique_terms

    def detect_math_notation(self, question_text: str) -> Dict[str, bool]:
        """
        Detect types of mathematical notation used

        Args:
            question_text: Question text

        Returns:
            Dictionary of notation types and presence
        """
        notation = {
            'has_fractions': bool(re.search(r'\d+/\d+|\\frac', question_text)),
            'has_exponents': bool(re.search(r'\^\d+|x²|x³', question_text)),
            'has_radicals': bool(re.search(r'√|\\sqrt', question_text)),
            'has_greek_letters': bool(re.search(r'[α-ωΑ-Ω]|\\alpha|\\beta|\\theta|\\pi', question_text)),
            'has_integrals': bool(re.search(r'∫|\\int', question_text)),
            'has_derivatives': bool(re.search(r'd[xy]/d[xy]|\\frac\{d', question_text)),
            'has_vectors': bool(re.search(r'\\vec|\\mathbf|\bi\b|\bj\b|\bk\b(?=\s)', question_text)),
            'has_matrices': bool(re.search(r'\\begin\{matrix\}|\[.*\].*\[.*\]', question_text)),
        }

        return notation

    def estimate_required_knowledge(self, paper_code: str, topics: List[str],
                                   concepts: List[str]) -> List[str]:
        """
        Estimate prerequisite knowledge required

        Args:
            paper_code: Paper code (e.g., "12", "32")
            topics: Topic codes
            concepts: Extracted concepts

        Returns:
            List of required knowledge areas
        """
        knowledge = []

        # Paper-specific prerequisites
        if paper_code.startswith('1'):  # Pure Math 1
            knowledge.extend(['algebra', 'basic_calculus', 'functions'])
        elif paper_code.startswith('3'):  # Pure Math 3
            knowledge.extend(['advanced_algebra', 'calculus', 'trigonometry'])
        elif paper_code.startswith('4'):  # Mechanics
            knowledge.extend(['vectors', 'calculus', 'physics_basics'])
        elif paper_code.startswith('5'):  # Probability 1
            knowledge.extend(['probability_theory', 'statistics_basics'])
        elif paper_code.startswith('6'):  # Probability 2
            knowledge.extend(['probability_theory', 'hypothesis_testing', 'distributions'])

        # Add concept-specific knowledge
        concept_map = {
            'calculus': ['limits', 'differentiation', 'integration'],
            'vectors': ['vector_operations', 'geometry'],
            'complex_numbers': ['algebra', 'trigonometry'],
            'probability': ['combinatorics', 'set_theory'],
        }

        for concept in concepts:
            if concept in concept_map:
                knowledge.extend(concept_map[concept])

        return list(set(knowledge))

    def enhance_question_metadata(self, question_data: Dict) -> Dict:
        """
        Add enhanced metadata to a question

        Args:
            question_data: Original question data dictionary

        Returns:
            Enhanced question data with additional metadata
        """
        enhanced = question_data.copy()

        question_text = question_data.get('question_text', '')
        answer_text = question_data.get('answer_full', '')
        marks = question_data.get('marks', 0)
        paper = question_data.get('paper', '')
        paper_code = paper.replace('P', '') if paper else ''
        topics = question_data.get('topics', [])

        # Add difficulty
        difficulty, confidence = self.classify_difficulty(question_text, answer_text, marks)
        enhanced['difficulty'] = difficulty
        enhanced['difficulty_confidence'] = round(confidence, 2)

        # Add question types
        enhanced['question_types'] = self.classify_question_type(question_text)

        # Add concepts
        enhanced['concepts'] = self.extract_concepts(question_text, answer_text)

        # Add key terms
        enhanced['key_terms'] = self.extract_key_terms(question_text)

        # Add notation analysis
        enhanced['math_notation'] = self.detect_math_notation(question_text)

        # Add required knowledge
        enhanced['required_knowledge'] = self.estimate_required_knowledge(
            paper_code, topics, enhanced['concepts']
        )

        # Add text statistics
        enhanced['text_stats'] = {
            'question_length': len(question_text),
            'answer_length': len(answer_text),
            'question_word_count': len(question_text.split()),
            'answer_word_count': len(answer_text.split()) if answer_text else 0,
        }

        return enhanced

    def enhance_paper_metadata(self, paper_data: Dict) -> Dict:
        """
        Add enhanced metadata to all questions in a paper

        Args:
            paper_data: Paper data dictionary

        Returns:
            Enhanced paper data
        """
        enhanced = paper_data.copy()

        logger.info(f"Enhancing metadata for {paper_data.get('year')} "
                   f"{paper_data.get('session')} {paper_data.get('paper')}")

        # Enhance each question
        enhanced_questions = []
        for question in paper_data.get('questions', []):
            enhanced_q = self.enhance_question_metadata(question)
            enhanced_questions.append(enhanced_q)

        enhanced['questions'] = enhanced_questions

        # Add paper-level statistics
        enhanced['paper_stats'] = self._generate_paper_stats(enhanced_questions)

        return enhanced

    def _generate_paper_stats(self, questions: List[Dict]) -> Dict:
        """Generate aggregate statistics for a paper"""
        if not questions:
            return {}

        stats = {
            'total_questions': len(questions),
            'difficulty_distribution': {
                'Easy': 0,
                'Medium': 0,
                'Hard': 0
            },
            'question_type_distribution': {},
            'concept_distribution': {},
            'average_marks': 0,
            'total_marks': 0,
        }

        total_marks = 0
        all_types = []
        all_concepts = []

        for q in questions:
            # Difficulty
            diff = q.get('difficulty', 'Medium')
            stats['difficulty_distribution'][diff] += 1

            # Question types
            q_types = q.get('question_types', [])
            all_types.extend(q_types)

            # Concepts
            concepts = q.get('concepts', [])
            all_concepts.extend(concepts)

            # Marks
            marks = q.get('marks', 0)
            total_marks += marks

        # Calculate type distribution
        for qtype in set(all_types):
            stats['question_type_distribution'][qtype] = all_types.count(qtype)

        # Calculate concept distribution
        for concept in set(all_concepts):
            stats['concept_distribution'][concept] = all_concepts.count(concept)

        # Calculate average marks
        stats['total_marks'] = total_marks
        stats['average_marks'] = round(total_marks / len(questions), 2) if questions else 0

        return stats

    def save_enhanced_metadata(self, enhanced_data: Dict, output_path: str):
        """
        Save enhanced metadata to JSON file

        Args:
            enhanced_data: Enhanced paper data
            output_path: Output file path
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Enhanced metadata saved to: {output_path}")


# Convenience function
def enhance_metadata_for_paper(input_json: str, output_json: str,
                               use_ml_models: bool = True) -> Dict:
    """
    Enhance metadata for a single paper JSON file

    Args:
        input_json: Path to input JSON file
        output_json: Path to output JSON file
        use_ml_models: Whether to use ML models

    Returns:
        Enhanced paper data
    """
    # Load original data
    with open(input_json, 'r', encoding='utf-8') as f:
        paper_data = json.load(f)

    # Enhance
    enhancer = MetadataEnhancer(use_ml_models=use_ml_models)
    enhanced = enhancer.enhance_paper_metadata(paper_data)

    # Save
    enhancer.save_enhanced_metadata(enhanced, output_json)

    return enhanced


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.json', '_enhanced.json')

        print(f"Enhancing: {input_file}")
        enhanced = enhance_metadata_for_paper(input_file, output_file)
        print(f"Saved to: {output_file}")
        print(f"Enhanced {len(enhanced.get('questions', []))} questions")
    else:
        print("Usage: python metadata_enhancer.py <input.json> [output.json]")
        print("\nExample:")
        print("  python metadata_enhancer.py Cambridge-9709/parsed_json/2023_M_J_P12.json")
