import time
from pathlib import Path
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config.settings import settings
from app.models.response_models import QueryResponse
from app.services.query_service import answer_question, retriever


class MetricScore(BaseModel):
    """
    Structured model scoring report returned by the judge LLM.
    """

    score: float
    reason: str


class RAGEvaluator:
    """
    RAG Evaluation runner executing metric checks (Faithfulness, Context Recall, Answer Relevance).
    """

    def __init__(self):
        """
        Initialize the Gemini audit client and load the Golden Q&A evaluation dataset.
        """
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.LLM_MODEL

        # Golden evaluation dataset
        self.golden_dataset = [
            {
                "question": "What is the policy for rollover vacation days?",
                "ground_truth": "Employees can roll over up to 5 vacation days to the next calendar year, which must be used by March 31st.",
                "expected_refusal": False,
            },
            {
                "question": "How do I report a security incident?",
                "ground_truth": "Security incidents must be reported immediately to security@company.com or via the internal Incident Portal within 24 hours.",
                "expected_refusal": False,
            },
            {
                "question": "What is the standard policy rollback threshold?",
                "ground_truth": "There is no information regarding a policy rollback threshold. The system must refuse to answer.",
                "expected_refusal": True,
            },
        ]

    def evaluate_faithfulness(
        self,
        context: str,
        answer: str,
    ) -> tuple[float, str]:
        """
        Evaluate if the generated answer is fully grounded in the retrieved context.
        """
        prompt = (
            f"Retrieved Context:\n{context}\n\n"
            f"Generated Answer:\n{answer}\n"
        )
        system_instruction = (
            "You are a strict QA auditor. Evaluate if the Generated Answer is fully grounded in "
            "the Retrieved Context. If the answer contains any facts, numbers, or assertions NOT "
            "found in the context, rate faithfulness low. Return a JSON object matching schema: "
            "{'score': float, 'reason': str} where score is between 0.0 and 1.0."
        )
        try:
            res = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=MetricScore,
                    temperature=0.0,
                ),
            )
            return res.parsed.score, res.parsed.reason
        except Exception as e:
            return 0.0, f"Error: {e}"

    def evaluate_context_recall(
        self,
        context: str,
        ground_truth: str,
    ) -> tuple[float, str]:
        """
        Evaluate if the retrieved context contains all facts from the ground truth answer.
        """
        prompt = (
            f"Retrieved Context:\n{context}\n\n"
            f"Ground Truth Answer:\n{ground_truth}\n"
        )
        system_instruction = (
            "You are an information retrieval judge. Check if the Retrieved Context contains "
            "all the key factual information listed in the Ground Truth Answer. If facts from the "
            "ground truth are missing in the context, penalize the recall. Return a JSON object: "
            "{'score': float, 'reason': str} where score is between 0.0 and 1.0."
        )
        try:
            res = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=MetricScore,
                    temperature=0.0,
                ),
            )
            return res.parsed.score, res.parsed.reason
        except Exception as e:
            return 0.0, f"Error: {e}"

    def evaluate_answer_relevance(
        self,
        question: str,
        answer: str,
    ) -> tuple[float, str]:
        """
        Evaluate if the generated answer directly addresses the user question.
        """
        prompt = (
            f"User Question: {question}\n\n"
            f"Generated Answer:\n{answer}\n"
        )
        system_instruction = (
            "You are a customer satisfaction auditor. Rate whether the Generated Answer directly "
            "and clearly addresses the User Question. Penalize if the answer is circular, vague, or "
            "avoids the question. Return a JSON object: {'score': float, 'reason': str} where score "
            "is between 0.0 and 1.0."
        )
        try:
            res = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=MetricScore,
                    temperature=0.0,
                ),
            )
            return res.parsed.score, res.parsed.reason
        except Exception as e:
            return 0.0, f"Error: {e}"

    def run_evaluation(
        self, output_path: str = "docs/evaluation_report.md"
    ) -> dict:
        """
        Execute evaluation metrics over the golden dataset and write report.
        """
        results = []
        total_faithfulness = 0.0
        total_recall = 0.0
        total_relevance = 0.0
        total_latency = 0.0
        correct_refusals = 0
        expected_refusals_count = 0

        print(f"Running evaluation on {len(self.golden_dataset)} queries...")

        for idx, item in enumerate(self.golden_dataset):
            q = item["question"]
            gt = item["ground_truth"]
            exp_refusal = item.get("expected_refusal", False)

            start_time = time.time()
            response = answer_question(q)
            latency = time.time() - start_time
            total_latency += latency

            # Fetch retrieved contexts text
            retrieved = retriever.retrieve(q)
            context_text = "\n\n".join([c.chunk.text for c in retrieved])

            # Check if answer was a refusal
            is_refusal = (
                "don't have enough information" in response.answer.lower()
            )
            if exp_refusal:
                expected_refusals_count += 1
                if is_refusal:
                    correct_refusals += 1

            # Run evaluation metrics
            faithfulness, faith_reason = self.evaluate_faithfulness(
                context_text, response.answer
            )
            recall, recall_reason = self.evaluate_context_recall(
                context_text, gt
            )
            relevance, rel_reason = self.evaluate_answer_relevance(
                q, response.answer
            )

            total_faithfulness += faithfulness
            total_recall += recall
            total_relevance += relevance

            results.append(
                {
                    "index": idx,
                    "question": q,
                    "answer": response.answer,
                    "ground_truth": gt,
                    "latency": latency,
                    "confidence": response.confidence,
                    "faithfulness": faithfulness,
                    "faithfulness_reason": faith_reason,
                    "context_recall": recall,
                    "context_recall_reason": recall_reason,
                    "answer_relevance": relevance,
                    "answer_relevance_reason": rel_reason,
                    "refused_correctly": (
                        is_refusal == exp_refusal if exp_refusal else True
                    ),
                }
            )

        count = len(self.golden_dataset)
        avg_faithfulness = total_faithfulness / count if count > 0 else 0.0
        avg_recall = total_recall / count if count > 0 else 0.0
        avg_relevance = total_relevance / count if count > 0 else 0.0
        avg_latency = total_latency / count if count > 0 else 0.0
        refusal_acc = (
            (correct_refusals / expected_refusals_count)
            if expected_refusals_count > 0
            else 1.0
        )

        summary = {
            "average_faithfulness": avg_faithfulness,
            "average_context_recall": avg_recall,
            "average_answer_relevance": avg_relevance,
            "average_latency": avg_latency,
            "refusal_accuracy": refusal_acc,
            "total_evaluated": count,
        }

        self.generate_report(results, summary, output_path)
        return summary

    def generate_report(
        self, results: list, summary: dict, output_path: str
    ) -> None:
        """
        Write detailed report to a markdown file.
        """
        report_lines = [
            "# RAG Pipeline Evaluation Report",
            f"\nGenerated on: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Overall Metrics Summary\n",
            f"- **Average Faithfulness (Groundedness)**: {summary['average_faithfulness']:.2%}",
            f"- **Average Context Recall**: {summary['average_context_recall']:.2%}",
            f"- **Average Answer Relevance**: {summary['average_answer_relevance']:.2%}",
            f"- **Average Latency**: {summary['average_latency']:.2f} seconds",
            f"- **Refusal Accuracy**: {summary['refusal_accuracy']:.2%}",
            f"- **Total Evaluated Cases**: {summary['total_evaluated']}",
            "\n## Detailed Case Audits\n",
        ]

        for r in results:
            report_lines.extend(
                [
                    f"### Case {r['index'] + 1}: {r['question']}",
                    f"- **Answer**: {r['answer']}",
                    f"- **Ground Truth**: {r['ground_truth']}",
                    f"- **Latency**: {r['latency']:.2f}s | **System Confidence**: {r['confidence']:.2f}",
                    f"- **Metrics**:",
                    f"  - **Faithfulness**: {r['faithfulness']:.2%} ({r['faithfulness_reason']})",
                    f"  - **Context Recall**: {r['context_recall']:.2%} ({r['context_recall_reason']})",
                    f"  - **Answer Relevance**: {r['answer_relevance']:.2%} ({r['answer_relevance_reason']})",
                    "\n---\n",
                ]
            )

        report_path = Path(output_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(report_lines), encoding="utf-8")
        print(f"Saved evaluation report to {output_path}")
