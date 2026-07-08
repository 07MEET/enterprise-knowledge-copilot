import re
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config.settings import settings
from app.models.document_models import RetrievedChunk
from app.models.response_models import Citation


class ClaimVerificationResult(BaseModel):
    """
    Factual validation verdict from the judge model.
    """

    is_supported: bool
    reason: str


class CitationVerifier:
    """
    Extracts, validates, and rates citations in generated answers.
    """

    def __init__(self):
        """
        Initialize the Gemini client for validation audits.
        """
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.LLM_MODEL

    def verify(
        self,
        answer: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> tuple[list[Citation], float, list[str]]:
        """
        Verify every citation in the answer text.

        Returns:
            citations: List of verified unique citations.
            confidence: Weighted score combining retrieval scores and verification rates.
            unverified_information: Summary list of failed statements.
        """
        # Refusal check
        refusal_phrases = [
            "i don't have enough information",
            "insufficient information",
            "not mentioned in the provided documents",
        ]
        if any(phrase in answer.lower() for phrase in refusal_phrases):
            return [], 0.0, []

        # Regex matching sentence-like structures preceding a chunk ID tag, e.g. "Fact [uuid]"
        pattern = re.compile(
            r"([^.!?\n\-\*]+(?:[.!?]+)?)\s*\[([a-zA-Z0-9\-]+)\]"
        )
        matches = pattern.findall(answer)

        # Map of chunk_id -> RetrievedChunk
        chunk_lookup = {item.chunk.chunk_id: item for item in retrieved_chunks}

        verified_citations = []
        unverified_claims = []
        verified_count = 0
        total_citations = len(matches)
        cited_scores = []

        for claim, chunk_id in matches:
            claim = claim.strip()
            chunk_id = chunk_id.strip()

            retrieved_item = chunk_lookup.get(chunk_id)
            if not retrieved_item:
                unverified_claims.append(
                    f"Claim: '{claim}' (Chunk {chunk_id} was not in retrieval results)"
                )
                continue

            cited_scores.append(retrieved_item.score)

            # LLM-as-a-judge verification
            is_supported, reason = self.verify_claim_against_chunk(
                claim, retrieved_item.chunk.text
            )

            if is_supported:
                verified_count += 1
                metadata = retrieved_item.chunk.metadata
                # Use h1 or section metadata field
                section_val = (
                    metadata.get("h1")
                    or metadata.get("section")
                    or metadata.get("h2")
                )
                verified_citations.append(
                    Citation(
                        source=metadata.get("source", "Unknown"),
                        page=metadata.get("page"),
                        section=section_val,
                    )
                )
            else:
                unverified_claims.append(
                    f"Claim: '{claim}' (Unverified: {reason})"
                )

        # Calculate accuracy metrics
        support_rate = (
            (verified_count / total_citations) if total_citations > 0 else 1.0
        )

        avg_retrieved_score = 0.0
        if cited_scores:
            avg_retrieved_score = sum(cited_scores) / len(cited_scores)
        elif retrieved_chunks:
            avg_retrieved_score = sum(item.score for item in retrieved_chunks) / len(
                retrieved_chunks
            )

        # Normalize score bounds
        avg_retrieved_score = max(0.0, min(1.0, avg_retrieved_score))

        # Confidence = Retrieval Quality * Support Accuracy
        confidence = support_rate * avg_retrieved_score

        # Deduplicate citations
        unique_citations = []
        seen = set()
        for cit in verified_citations:
            key = (cit.source, cit.page, cit.section)
            if key not in seen:
                seen.add(key)
                unique_citations.append(cit)

        return unique_citations, float(confidence), unverified_claims

    def verify_claim_against_chunk(
        self,
        claim: str,
        chunk_text: str,
    ) -> tuple[bool, str]:
        """
        Determine if the chunk text directly supports the claim.
        """
        prompt = (
            f"Evaluate if the following Source Text supports the Claim.\n\n"
            f"Source Text:\n{chunk_text}\n\n"
            f"Claim:\n{claim}\n"
        )

        system_instruction = (
            "You are an expert factual verifier. Determine if the Claim is fully supported "
            "by the Source Text. Answer strictly in JSON matching the schema: "
            "{'is_supported': bool, 'reason': str}. is_supported must be true if and only if "
            "the claim is directly supported or logically entailed by the source text, without assumptions "
            "or outside knowledge. Provide a short reason explaining your decision."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ClaimVerificationResult,
                    temperature=0.0,
                ),
            )
            result = response.parsed
            return result.is_supported, result.reason
        except Exception as e:
            print(f"Claim verification failed: {e}")
            return False, f"API error during verification: {str(e)}"
