import argparse

from app.evaluation.evaluator import RAGEvaluator


def main():
    """
    Run evaluation suite and output report metrics.
    """
    parser = argparse.ArgumentParser(description="Evaluate the RAG pipeline.")
    parser.add_argument(
        "--output",
        type=str,
        default="docs/evaluation_report.md",
        help="Path to output markdown report",
    )
    args = parser.parse_args()

    evaluator = RAGEvaluator()
    evaluator.run_evaluation(output_path=args.output)


if __name__ == "__main__":
    main()
