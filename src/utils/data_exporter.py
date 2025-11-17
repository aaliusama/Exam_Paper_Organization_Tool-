"""
Data Exporter for Cambridge 9709 Dataset
Exports parsed questions to JSON and CSV formats
"""

import json
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataExporter:
    """Export parsed data to various formats"""

    def __init__(self, output_base_dir: str = "Cambridge-9709"):
        """
        Initialize data exporter

        Args:
            output_base_dir: Base directory for outputs
        """
        self.output_dir = Path(output_base_dir)
        self.json_dir = self.output_dir / "parsed_json"
        self.csv_dir = self.output_dir / "combined_yearly_csv"
        self.master_dir = self.output_dir / "master_dataset"

        # Create directories
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.master_dir.mkdir(parents=True, exist_ok=True)

    def export_paper_json(self, paper_data: Dict, output_path: Path = None) -> Path:
        """
        Export a single paper to JSON

        Args:
            paper_data: Dictionary containing paper information
            output_path: Custom output path (optional)

        Returns:
            Path to saved JSON file
        """
        if output_path is None:
            # Generate filename: 2023_MJ_P12.json
            year = paper_data.get('year', 'unknown')
            session = paper_data.get('session', 'unknown').replace('/', '')
            paper = paper_data.get('paper', 'unknown')

            filename = f"{year}_{session}_{paper}.json"
            output_path = self.json_dir / filename

        # Save JSON with pretty printing
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(paper_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported JSON: {output_path.name}")
        return output_path

    def export_year_csv(self, year: int, papers_data: List[Dict]) -> Path:
        """
        Export all papers for a year to CSV

        Args:
            year: Year
            papers_data: List of paper dictionaries

        Returns:
            Path to saved CSV file
        """
        # Flatten all questions from all papers
        rows = []

        for paper_data in papers_data:
            year_val = paper_data.get('year', year)
            session = paper_data.get('session', '')
            paper = paper_data.get('paper', '')
            variant = paper_data.get('variant', '')

            for question in paper_data.get('questions', []):
                row = {
                    'year': year_val,
                    'session': session,
                    'paper': paper,
                    'variant': variant,
                    'qid': question.get('qid', ''),
                    'question_text': question.get('question_text', ''),
                    'answer_full': question.get('answer_full', ''),
                    'answer_snippet': question.get('answer_snippet', ''),
                    'topics': '|'.join(question.get('topics', [])),  # Join topics with |
                    'page': question.get('page', ''),
                    'marks': question.get('marks', '')
                }
                rows.append(row)

        # Create DataFrame
        df = pd.DataFrame(rows)

        # Save to CSV
        output_path = self.csv_dir / f"{year}_combined.csv"
        df.to_csv(output_path, index=False, encoding='utf-8')

        logger.info(f"Exported CSV for {year}: {len(rows)} questions")
        return output_path

    def export_master_dataset(self, all_papers_data: List[Dict]) -> tuple[Path, Path]:
        """
        Export master dataset (all years combined)

        Args:
            all_papers_data: List of all paper dictionaries

        Returns:
            Tuple of (json_path, csv_path)
        """
        # Master JSON
        master_json_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_papers': len(all_papers_data),
                'total_questions': sum(len(p.get('questions', [])) for p in all_papers_data),
                'years': sorted(list(set(p.get('year') for p in all_papers_data)))
            },
            'papers': all_papers_data
        }

        json_path = self.master_dir / "master_dataset.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(master_json_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported master JSON: {json_path}")

        # Master CSV (flattened)
        rows = []
        for paper_data in all_papers_data:
            year = paper_data.get('year', '')
            session = paper_data.get('session', '')
            paper = paper_data.get('paper', '')
            variant = paper_data.get('variant', '')

            for question in paper_data.get('questions', []):
                row = {
                    'year': year,
                    'session': session,
                    'paper': paper,
                    'variant': variant,
                    'qid': question.get('qid', ''),
                    'question_text': question.get('question_text', ''),
                    'answer_full': question.get('answer_full', ''),
                    'answer_snippet': question.get('answer_snippet', ''),
                    'topics': '|'.join(question.get('topics', [])),
                    'page': question.get('page', ''),
                    'marks': question.get('marks', '')
                }
                rows.append(row)

        df = pd.DataFrame(rows)
        csv_path = self.master_dir / "master_dataset.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')

        logger.info(f"Exported master CSV: {csv_path} ({len(rows)} questions)")

        return json_path, csv_path

    def create_summary_stats(self, all_papers_data: List[Dict]) -> Dict:
        """
        Create summary statistics

        Args:
            all_papers_data: List of all paper dictionaries

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_papers': len(all_papers_data),
            'total_questions': 0,
            'by_year': {},
            'by_paper_type': {},
            'by_topic': {},
            'papers_processed': []
        }

        for paper_data in all_papers_data:
            year = paper_data.get('year', 'unknown')
            session = paper_data.get('session', 'unknown')
            paper = paper_data.get('paper', 'unknown')
            questions = paper_data.get('questions', [])

            # Count questions
            num_questions = len(questions)
            stats['total_questions'] += num_questions

            # By year
            if year not in stats['by_year']:
                stats['by_year'][year] = 0
            stats['by_year'][year] += num_questions

            # By paper type
            if paper not in stats['by_paper_type']:
                stats['by_paper_type'][paper] = 0
            stats['by_paper_type'][paper] += num_questions

            # By topic
            for q in questions:
                for topic in q.get('topics', []):
                    if topic not in stats['by_topic']:
                        stats['by_topic'][topic] = 0
                    stats['by_topic'][topic] += 1

            # Record processed papers
            stats['papers_processed'].append(f"{year}_{session}_{paper}")

        # Save stats
        stats_path = self.master_dir / "summary_statistics.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

        logger.info(f"Summary statistics saved: {stats_path}")

        return stats

    def print_summary(self, stats: Dict):
        """Print summary statistics to console"""
        print("\n" + "="*60)
        print("DATASET SUMMARY")
        print("="*60)
        print(f"Total papers processed: {stats['total_papers']}")
        print(f"Total questions extracted: {stats['total_questions']}")

        print("\nQuestions by Year:")
        for year in sorted(stats['by_year'].keys()):
            print(f"  {year}: {stats['by_year'][year]} questions")

        print("\nQuestions by Paper Type:")
        for paper in sorted(stats['by_paper_type'].keys()):
            print(f"  Paper {paper}: {stats['by_paper_type'][paper]} questions")

        print("\nTop 10 Topics:")
        sorted_topics = sorted(stats['by_topic'].items(), key=lambda x: x[1], reverse=True)
        for topic, count in sorted_topics[:10]:
            print(f"  {topic}: {count} questions")

        print("="*60 + "\n")


if __name__ == "__main__":
    # Test the exporter
    exporter = DataExporter()

    # Sample data
    sample_paper = {
        'year': 2023,
        'session': 'M/J',
        'paper': 'P12',
        'variant': 2,
        'questions': [
            {
                'qid': '1',
                'topics': ['P1.1', 'P1.7'],
                'question_text': 'Sample question 1',
                'answer_full': 'Sample answer 1',
                'answer_snippet': 'Short answer',
                'page': 1,
                'marks': 3
            },
            {
                'qid': '1(a)',
                'topics': ['P1.2'],
                'question_text': 'Sample question 1a',
                'answer_full': 'Sample answer 1a',
                'answer_snippet': 'Short answer',
                'page': 1,
                'marks': 2
            }
        ]
    }

    # Test exports
    exporter.export_paper_json(sample_paper)
    exporter.export_year_csv(2023, [sample_paper])
    stats = exporter.create_summary_stats([sample_paper])
    exporter.print_summary(stats)
