"""
Topic Mapper for Cambridge 9709 Mathematics
Maps questions to syllabus topics based on 2026-2027 syllabus
"""

import re
import logging
from typing import List, Dict, Set
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SyllabusTopic:
    """Represents a syllabus topic"""
    code: str
    title: str
    keywords: List[str]
    paper_codes: List[str]  # Which papers this topic appears in


class TopicMapper:
    """Maps questions to syllabus topics"""

    # Cambridge 9709 Syllabus Structure (2026-2027)
    # Based on Pure Mathematics 1, 2, 3 and Mechanics, Probability & Statistics

    SYLLABUS_TOPICS = {
        # Pure Mathematics 1 (Papers 1 & 3)
        "P1.1": SyllabusTopic(
            code="P1.1",
            title="Quadratics",
            keywords=["quadratic", "discriminant", "completing the square", "parabola", "vertex form"],
            paper_codes=["11", "12", "13"]
        ),
        "P1.2": SyllabusTopic(
            code="P1.2",
            title="Functions",
            keywords=["function", "domain", "range", "composite", "inverse function", "f(x)", "one-to-one"],
            paper_codes=["11", "12", "13"]
        ),
        "P1.3": SyllabusTopic(
            code="P1.3",
            title="Coordinate Geometry",
            keywords=["gradient", "parallel", "perpendicular", "midpoint", "distance", "straight line", "equation of line"],
            paper_codes=["11", "12", "13"]
        ),
        "P1.4": SyllabusTopic(
            code="P1.4",
            title="Circular Measure",
            keywords=["radian", "arc length", "sector", "segment", "circle"],
            paper_codes=["11", "12", "13"]
        ),
        "P1.5": SyllabusTopic(
            code="P1.5",
            title="Trigonometry",
            keywords=["sin", "cos", "tan", "trigonometric", "sine rule", "cosine rule", "triangle"],
            paper_codes=["11", "12", "13"]
        ),
        "P1.6": SyllabusTopic(
            code="P1.6",
            title="Series",
            keywords=["arithmetic progression", "geometric progression", "sequence", "series", "sum to infinity", "AP", "GP"],
            paper_codes=["11", "12", "13"]
        ),
        "P1.7": SyllabusTopic(
            code="P1.7",
            title="Differentiation",
            keywords=["derivative", "differentiate", "gradient", "tangent", "normal", "rate of change", "dy/dx"],
            paper_codes=["11", "12", "13"]
        ),
        "P1.8": SyllabusTopic(
            code="P1.8",
            title="Integration",
            keywords=["integrate", "integration", "area under curve", "definite integral", "indefinite integral"],
            paper_codes=["11", "12", "13"]
        ),

        # Pure Mathematics 2/3 (Papers 3 only for P2, Papers 1 & 3 for P3)
        "P2.1": SyllabusTopic(
            code="P2.1",
            title="Algebra",
            keywords=["binomial", "expansion", "coefficient", "partial fractions", "remainder theorem", "factor theorem"],
            paper_codes=["31", "32", "33"]
        ),
        "P2.2": SyllabusTopic(
            code="P2.2",
            title="Logarithmic and Exponential Functions",
            keywords=["logarithm", "log", "ln", "exponential", "e^x", "natural log"],
            paper_codes=["31", "32", "33"]
        ),
        "P2.3": SyllabusTopic(
            code="P2.3",
            title="Trigonometry (Advanced)",
            keywords=["double angle", "addition formula", "R formula", "sec", "cosec", "cot", "arcsin", "arccos", "arctan"],
            paper_codes=["31", "32", "33"]
        ),
        "P2.4": SyllabusTopic(
            code="P2.4",
            title="Differentiation (Advanced)",
            keywords=["product rule", "quotient rule", "chain rule", "implicit differentiation", "parametric differentiation"],
            paper_codes=["31", "32", "33"]
        ),
        "P2.5": SyllabusTopic(
            code="P2.5",
            title="Integration (Advanced)",
            keywords=["integration by substitution", "integration by parts", "partial fractions integration", "trapezium rule"],
            paper_codes=["31", "32", "33"]
        ),
        "P2.6": SyllabusTopic(
            code="P2.6",
            title="Numerical Solutions",
            keywords=["iterative", "newton-raphson", "numerical method", "convergence"],
            paper_codes=["31", "32", "33"]
        ),

        "P3.1": SyllabusTopic(
            code="P3.1",
            title="Vectors",
            keywords=["vector", "magnitude", "direction", "dot product", "scalar product", "position vector", "unit vector"],
            paper_codes=["31", "32", "33"]
        ),
        "P3.2": SyllabusTopic(
            code="P3.2",
            title="Complex Numbers",
            keywords=["complex number", "imaginary", "argand diagram", "modulus", "argument", "loci"],
            paper_codes=["31", "32", "33"]
        ),
        "P3.3": SyllabusTopic(
            code="P3.3",
            title="Differential Equations",
            keywords=["differential equation", "separable", "dy/dx"],
            paper_codes=["31", "32", "33"]
        ),

        # Mechanics (Papers 4)
        "M1.1": SyllabusTopic(
            code="M1.1",
            title="Forces and Equilibrium",
            keywords=["force", "equilibrium", "resultant", "component", "friction", "normal reaction"],
            paper_codes=["41", "42", "43"]
        ),
        "M1.2": SyllabusTopic(
            code="M1.2",
            title="Kinematics",
            keywords=["velocity", "acceleration", "displacement", "suvat", "projectile", "motion"],
            paper_codes=["41", "42", "43"]
        ),
        "M1.3": SyllabusTopic(
            code="M1.3",
            title="Newton's Laws",
            keywords=["newton", "mass", "F=ma", "momentum", "impulse"],
            paper_codes=["41", "42", "43"]
        ),
        "M1.4": SyllabusTopic(
            code="M1.4",
            title="Energy, Work and Power",
            keywords=["work", "energy", "kinetic energy", "potential energy", "power", "conservation"],
            paper_codes=["41", "42", "43"]
        ),

        # Probability & Statistics 1 (Papers 5 & 6)
        "S1.1": SyllabusTopic(
            code="S1.1",
            title="Data Representation",
            keywords=["histogram", "frequency", "cumulative frequency", "box plot", "stem and leaf"],
            paper_codes=["51", "52", "53", "61", "62", "63"]
        ),
        "S1.2": SyllabusTopic(
            code="S1.2",
            title="Measures of Location and Spread",
            keywords=["mean", "median", "mode", "variance", "standard deviation", "quartile", "interquartile range"],
            paper_codes=["51", "52", "53", "61", "62", "63"]
        ),
        "S1.3": SyllabusTopic(
            code="S1.3",
            title="Probability",
            keywords=["probability", "independent", "mutually exclusive", "conditional probability", "tree diagram", "venn diagram"],
            paper_codes=["51", "52", "53", "61", "62", "63"]
        ),
        "S1.4": SyllabusTopic(
            code="S1.4",
            title="Discrete Random Variables",
            keywords=["random variable", "discrete", "probability distribution", "expectation", "E(X)", "Var(X)"],
            paper_codes=["51", "52", "53", "61", "62", "63"]
        ),
        "S1.5": SyllabusTopic(
            code="S1.5",
            title="Normal Distribution",
            keywords=["normal distribution", "standard normal", "z-score", "standardize", "N(μ, σ²)"],
            paper_codes=["51", "52", "53", "61", "62", "63"]
        ),

        # Probability & Statistics 2 (Papers 6 only)
        "S2.1": SyllabusTopic(
            code="S2.1",
            title="Continuous Random Variables",
            keywords=["continuous random variable", "probability density function", "pdf", "cumulative distribution"],
            paper_codes=["61", "62", "63"]
        ),
        "S2.2": SyllabusTopic(
            code="S2.2",
            title="Sampling and Hypothesis Testing",
            keywords=["sample", "hypothesis test", "null hypothesis", "alternative hypothesis", "significance level", "critical value"],
            paper_codes=["61", "62", "63"]
        ),
        "S2.3": SyllabusTopic(
            code="S2.3",
            title="Linear Combinations of Random Variables",
            keywords=["linear combination", "E(aX + b)", "Var(aX + b)"],
            paper_codes=["61", "62", "63"]
        ),
    }

    def __init__(self):
        """Initialize topic mapper"""
        self.topics = self.SYLLABUS_TOPICS

    def map_question_to_topics(self, question_text: str, answer_text: str = "",
                               paper_code: str = "") -> List[str]:
        """
        Map a question to syllabus topics based on keywords

        Args:
            question_text: The question text
            answer_text: The answer/mark scheme text (optional)
            paper_code: Paper code (e.g., "12", "32") to filter relevant topics

        Returns:
            List of topic codes
        """
        # Combine question and answer text for analysis
        combined_text = f"{question_text} {answer_text}".lower()

        matched_topics = []
        scores = {}

        # Filter topics by paper code if provided
        relevant_topics = self.topics
        if paper_code:
            # Extract paper type (first digit)
            paper_type = paper_code[0] if paper_code else ""
            relevant_topics = {
                code: topic for code, topic in self.topics.items()
                if any(pc.startswith(paper_type) for pc in topic.paper_codes)
            }

        # Score each topic based on keyword matches
        for topic_code, topic in relevant_topics.items():
            score = 0

            for keyword in topic.keywords:
                # Check for keyword matches (with word boundaries)
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                matches = len(re.findall(pattern, combined_text))
                score += matches

            if score > 0:
                scores[topic_code] = score

        # Sort by score and return top matches
        if scores:
            sorted_topics = sorted(scores.items(), key=lambda x: x[1], reverse=True)

            # Return topics with score > threshold or top 2
            threshold = 2
            matched_topics = [
                code for code, score in sorted_topics
                if score >= threshold or sorted_topics.index((code, score)) < 2
            ]

        # If no topics matched, try broader matching
        if not matched_topics:
            matched_topics = self._fallback_matching(combined_text, paper_code)

        return matched_topics[:3]  # Limit to max 3 topics

    def _fallback_matching(self, text: str, paper_code: str = "") -> List[str]:
        """Fallback matching when keyword matching fails"""
        # Default topics based on paper type
        if paper_code:
            paper_type = paper_code[0] if paper_code else ""

            default_topics = {
                "1": ["P1.1", "P1.7"],  # Pure Math 1
                "3": ["P2.1", "P3.1"],  # Pure Math 3
                "4": ["M1.2"],          # Mechanics
                "5": ["S1.3"],          # Stats 1
                "6": ["S2.2"],          # Stats 2
            }

            return default_topics.get(paper_type, ["P1.1"])

        return ["P1.1"]  # Generic fallback

    def get_topic_info(self, topic_code: str) -> Dict:
        """Get information about a topic"""
        if topic_code in self.topics:
            topic = self.topics[topic_code]
            return {
                'code': topic.code,
                'title': topic.title,
                'keywords': topic.keywords,
                'papers': topic.paper_codes
            }
        return {}

    def get_all_topics_by_paper(self, paper_code: str) -> List[Dict]:
        """Get all topics relevant to a paper"""
        paper_type = paper_code[0] if paper_code else ""
        relevant_topics = [
            {
                'code': topic.code,
                'title': topic.title
            }
            for topic in self.topics.values()
            if any(pc.startswith(paper_type) for pc in topic.paper_codes)
        ]
        return relevant_topics


if __name__ == "__main__":
    # Test the mapper
    mapper = TopicMapper()

    test_questions = [
        ("Find the coefficient of x^3 in the expansion of (2 + x)^6.", "12"),
        ("Solve the quadratic equation 2x^2 - 5x + 2 = 0.", "12"),
        ("A particle moves with velocity v = 3t^2 + 2t. Find the acceleration.", "42"),
        ("Find P(X > 5) where X ~ N(10, 4).", "52"),
    ]

    for question, paper in test_questions:
        topics = mapper.map_question_to_topics(question, paper_code=paper)
        print(f"\nQuestion: {question[:60]}...")
        print(f"Paper: {paper}")
        print(f"Topics: {topics}")
        for topic_code in topics:
            info = mapper.get_topic_info(topic_code)
            print(f"  - {info['code']}: {info['title']}")
