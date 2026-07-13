import time
import re
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
        Initialize the audit client and load the Golden Q&A evaluation dataset.
        """
        if settings.USE_LOCAL:
            import ollama
            self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        else:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.LLM_MODEL

        # Golden evaluation dataset aligned with active workspace documents
        self.golden_dataset = [
            {
                "question": "What is the timeline for filing a complaint under the Sexual Harassment Policy?",
                "ground_truth": "A complaint must be made in writing to the Internal Committee within three months from the date of the incident (or the last incident in case of a series of incidents).",
                "expected_refusal": False,
            },
            {
                "question": "Who is the Chief Financial Officer (CFO) of Supreet Chemicals Limited?",
                "ground_truth": "Dineshchandra Manubhai Patel is the Chief Financial Officer (CFO) of Supreet Chemicals Limited.",
                "expected_refusal": False,
            },
            {
                "question": "What happens to the surplus arising out of CSR projects under the CSR Policy?",
                "ground_truth": "Any surplus arising out of the CSR activities shall not form part of the business profit of the Company and shall be ploughed back into the same project or transferred to the Unspent CSR Account.",
                "expected_refusal": False,
            },
            {
                "question": "Who can make a Protected Disclosure under the Whistle Blower Policy?",
                "ground_truth": "Any employee or director of the Company who makes a Protected Disclosure under the Whistle Blower Policy.",
                "expected_refusal": False,
            },
            {
                "question": "What financial parameters are considered for declaring dividends under the Dividend Distribution Policy?",
                "ground_truth": "Key financial parameters include standalone profits of the Company, cash flow status, capital requirements, and debt-to-equity ratios.",
                "expected_refusal": False,
            },
            {
                "question": "What is the threshold for a transaction to be considered a material related party transaction?",
                "ground_truth": "A transaction with a related party is considered material if the transaction to be entered into individually or taken together with previous transactions during a financial year, exceeds ten percent of the annual consolidated turnover of the Company as per the last audited financial statements.",
                "expected_refusal": False,
            },
            {
                "question": "How long are disclosures hosted on the website of Supreet Chemicals Limited under the Archival Policy?",
                "ground_truth": "All disclosures hosted on the website under the listing regulations shall be hosted for a minimum period of 5 years.",
                "expected_refusal": False,
            },
            {
                "question": "What are the two main categories of document preservation under the policy?",
                "ground_truth": "The two main categories are (a) documents whose preservation shall be permanent in nature and (b) documents whose preservation shall be for not less than eight years.",
                "expected_refusal": False,
            },
            {
                "question": "Who are the authorized persons to determine the materiality of an event under the Materiality Policy?",
                "ground_truth": "The Managing Director, Whole-time Directors, Chief Financial Officer, and Company Secretary are authorized to determine the materiality of an event.",
                "expected_refusal": False,
            },
            {
                "question": "What is the company's commitment regarding energy conservation under the Environmental Policy?",
                "ground_truth": "The company commits to reducing specific energy consumption, improving operational efficiency, and increasing the share of renewable energy in its overall energy mix.",
                "expected_refusal": False,
            },
            {
                "question": "What is the policy on conflict of interest for board members?",
                "ground_truth": "Board members must avoid situations where their personal interest conflicts with the interest of the Company, and disclose any relationships or transactions to the Board.",
                "expected_refusal": False,
            },
            {
                "question": "Who acts as the Chief Investor Relations Officer under the Fair Disclosure Code?",
                "ground_truth": "The Compliance Officer / Company Secretary acts as the Chief Investor Relations Officer (CIRO) to deal with dissemination of information and disclosure of UPSI.",
                "expected_refusal": False,
            },
            {
                "question": "What is the role of the Risk Management Committee?",
                "ground_truth": "The Risk Management Committee is responsible for monitoring and reviewing the risk management plan, assessing strategic/operational/financial risks, and reporting to the Board.",
                "expected_refusal": False,
            },
            {
                "question": "What are the criteria for paying commission to Non-Executive Directors?",
                "ground_truth": "The commission is determined based on their attendance, participation in Board meetings, and is subject to the approval of shareholders and the limit of net profits under the Act.",
                "expected_refusal": False,
            },
            {
                "question": "Which unit of Supreet Chemicals Limited was newly added to the reporting boundary in FY 2024-25?",
                "ground_truth": "Unit 2 was newly incorporated within the reporting boundary for disclosures in the FY 2024-25 ESG report.",
                "expected_refusal": False,
            },
            {
                "question": "Are employees allowed to accept gifts under the Code of Conduct?",
                "ground_truth": "Employees must not accept gifts, hospitality, or favors except token gifts of low value that are customary, subject to disclosure to HODs.",
                "expected_refusal": False,
            },
            {
                "question": "What is the standard policy for rollover vacation days?",
                "ground_truth": "There is no information regarding vacation rollover or paid leaves in the provided documents. The system must refuse to answer.",
                "expected_refusal": True,
            },
            {
                "question": "What is the company's password complexity requirement?",
                "ground_truth": "There is no information regarding password complexity or IT security guidelines in the provided documents. The system must refuse to answer.",
                "expected_refusal": True,
            },
            {
                "question": "Who is the company's external auditor for IT systems?",
                "ground_truth": "There is no information regarding external IT systems auditors in the provided documents. The system must refuse to answer.",
                "expected_refusal": True,
            },
            {
                "question": "What is the leave travel allowance policy for management trainees?",
                "ground_truth": "There is no information regarding leave travel allowances or trainee benefit packages in the provided documents. The system must refuse to answer.",
                "expected_refusal": True,
            },
        ]

    def _evaluate_metric(
        self,
        prompt: str,
        system_instruction: str,
    ) -> tuple[float, str]:
        """
        Evaluate a metric using either Ollama or Gemini.
        """
        if settings.USE_LOCAL:
            try:
                res = self.client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    options={"temperature": 0.0, "num_ctx": 8192, "num_predict": 4096}
                )
                from app.utils.json_parser import clean_json_string
                parsed = MetricScore.model_validate_json(clean_json_string(res["message"]["content"]))
                return parsed.score, parsed.reason
            except Exception as e:
                return 0.0, "Evaluation timed out or returned empty response."

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
            "You are a factual verification assistant. Determine if the facts in the Generated Answer contradict or invent claims beyond what is stated in the Retrieved Context.\n"
            "If there are NO contradictions (even if wording or detail differs), output a score of 1.0.\n"
            "If the answer invents fictitious information not supported by the context, output a score of 0.0.\n"
            "Respond ONLY with a JSON object: "
            '{"score": float, "reason": str} '
            "where score is 1.0 or 0.0. Keep the reason under 10 words."
        )
        return self._evaluate_metric(prompt, system_instruction)

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
            "You are an information retrieval assessor. Verify if the core semantic facts in the Ground Truth Answer are mentioned, referenced, or present in the Retrieved Context.\n"
            "If the context contains the necessary facts (even if phrased differently), output 1.0.\n"
            "If the context completely misses the key facts, output 0.0.\n"
            "Respond ONLY with a JSON object: "
            '{"score": float, "reason": str} '
            "where score is 1.0 or 0.0. Keep the reason under 10 words."
        )
        return self._evaluate_metric(prompt, system_instruction)

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
            "You are an answer relevance evaluator. Rate whether the Generated Answer directly answers the User Question.\n"
            "If the answer provides a relevant response to the topic of the question (even if brief or paraphrased), output 1.0.\n"
            "If the answer is completely off-topic or fails to address the question, output 0.0.\n"
            "Respond ONLY with a JSON object: "
            '{"score": float, "reason": str} '
            "where score is 1.0 or 0.0. Keep the reason under 10 words."
        )
        return self._evaluate_metric(prompt, system_instruction)

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
            if exp_refusal and is_refusal:
                faithfulness = 1.0
                faith_reason = "Correctly refused to answer out-of-document query"
                recall = 1.0
                recall_reason = "Correctly identified that context does not contain the answer"
                relevance = 1.0
                rel_reason = "Correctly addressed the query with refusal statement"
            else:
                # Strip citation brackets (e.g. [1], [2], [1] [1]) from answer for grading
                clean_answer = re.sub(r"\[\d+\]", "", response.answer).strip()
                clean_answer = re.sub(r"\s+", " ", clean_answer)
                
                # Run evaluation metrics normally
                faithfulness, faith_reason = self.evaluate_faithfulness(
                    context_text, clean_answer
                )
                recall, recall_reason = self.evaluate_context_recall(
                    context_text, gt
                )
                relevance, rel_reason = self.evaluate_answer_relevance(
                    q, clean_answer
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
