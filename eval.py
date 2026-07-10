# Initialize PyTorch CUDA first to prevent library conflicts (ChromaDB / gRPC) that cause segmentation faults on Windows
import torch
from sentence_transformers import SentenceTransformer
device = "cuda" if torch.cuda.is_available() else "cpu"
_ = SentenceTransformer("BAAI/bge-large-en-v1.5", device=device)

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
