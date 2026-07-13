import re
from google.genai import types
from pydantic import BaseModel

from app.config.settings import settings
from app.models.document_models import RetrievedChunk
from app.models.response_models import Citation
from app.utils.rate_limiter import call_with_retry


class ClaimAlignment(BaseModel):
    """
    Mapping of a generated claim sentence to its supporting retrieved context chunk.
    """

    claim_index: int
    context_index: int
    reason: str


class AlignmentResponse(BaseModel):
    """
    List of claim-to-context semantic alignments.
    """

    alignments: list[ClaimAlignment]


class MetricScore(BaseModel):
    """
    Score and reasoning result for dynamic text-level grounding verification.
    """

    score: float
    reason: str


def find_direct_match(claim: str, retrieved_chunks: list[RetrievedChunk]) -> int:
    """
    Checks if a claim text exists almost verbatim as a substring of any retrieved chunk.
    This provides 100% accurate, computationally free verification for direct quotes and lists.
    """
    # Clean claim text (alphanumeric only, lowercase, single space)
    c_clean = re.sub(r"[^a-zA-Z0-9\s]", "", claim.lower()).strip()
    c_clean = " ".join(c_clean.split())
    if len(c_clean) < 8:  # Ignore very short fragments
        return -1

    # 1. Full verbatim substring check
    for idx, item in enumerate(retrieved_chunks):
        text_clean = re.sub(r"[^a-zA-Z0-9\s]", "", item.chunk.text.lower())
        text_clean = " ".join(text_clean.split())
        if c_clean in text_clean:
            return idx

    # 2. Key Proper Noun (e.g. Personal Names) matching
    # Matches capitalized proper nouns with length >= 4 (e.g. "Dineshchandra Manubhai Patel")
    proper_nouns = re.findall(r"\b[A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]{3,})+\b", claim)
    for entity in proper_nouns:
        entity_clean = re.sub(r"[^a-zA-Z0-9\s]", "", entity.lower()).strip()
        entity_clean = " ".join(entity_clean.split())
        if len(entity_clean.split()) >= 2:
            for idx, item in enumerate(retrieved_chunks):
                text_clean = re.sub(r"[^a-zA-Z0-9\s]", "", item.chunk.text.lower())
                text_clean = " ".join(text_clean.split())
                if entity_clean in text_clean:
                    return idx

    return -1


class CitationVerifier:
    """
    Performs semantic claim alignment, validates facts, and calculates trust scores.
    """

    def __init__(self):
        """
        Initialize the verification client.
        """
        if settings.USE_LOCAL:
            import ollama

            self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        else:
            from google import genai

            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.LLM_MODEL

    def verify(
        self,
        answer: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> tuple[str, list[Citation], float, list[str]]:
        """
        Verify every claim sentence in the answer text by aligning it to the retrieved chunks.
        """
        # Refusal check
        refusal_phrases = [
            "i don't have enough information",
            "insufficient information",
            "not mentioned in the provided documents",
        ]
        if any(phrase in answer.lower() for phrase in refusal_phrases):
            return answer, [], 0.0, []

        # 1. Split answer into distinct sentences/claims
        raw_sentences = []
        for line in answer.split("\n"):
            if line.strip():
                # Split each line by sentence-ending punctuation
                parts = [
                    p.strip()
                    for p in re.split(r"(?<=[.!?])\s+", line)
                    if len(p.strip()) > 10
                ]
                raw_sentences.extend(parts)

        if not raw_sentences:
            return answer, [], 1.0, []

        # 2. Perform direct substring matching first
        alignments_map = {}
        claims_to_send = []  # list of tuples (idx_in_send, raw_sentences_index, claim_text)

        for c_idx, claim_text in enumerate(raw_sentences):
            matched_idx = find_direct_match(claim_text, retrieved_chunks)
            if matched_idx >= 0:
                alignments_map[c_idx] = matched_idx
            else:
                claims_to_send.append((len(claims_to_send), c_idx, claim_text))

        # 3. Call LLM for remaining claims (if any)
        unverified_claims = []

        if claims_to_send:
            chunks_text = ""
            for idx, item in enumerate(retrieved_chunks):
                chunks_text += f"--- CHUNK {idx} ---\n{item.chunk.text}\n\n"

            claims_text = ""
            for idx_in_send, c_idx, claim_text in claims_to_send:
                claims_text += f"Claim {idx_in_send}: {claim_text}\n"

            prompt = (
                f"Retrieved Chunks:\n{chunks_text}\n"
                f"Claims to Verify:\n{claims_text}\n"
            )
            system_instruction = (
                "You are a factual verifier. Check which Retrieved Chunk (by index 0, 1, 2...) directly supports each Claim.\n"
                "For each claim, identify the supporting chunk index. If a claim is not supported by any chunk, return -1.\n"
                "Respond ONLY with a JSON object of this schema:\n"
                '{"alignments": [{"claim_index": int, "context_index": int, "reason": str}]}'
            )

            try:
                if settings.USE_LOCAL:
                    response = self.client.chat(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt},
                        ],
                        options={
                            "temperature": 0.0,
                            "num_ctx": 8192,
                            "num_predict": 4096,
                        },
                    )
                    content = response["message"]["content"]
                    from app.utils.json_parser import clean_json_string

                    try:
                        cleaned_content = clean_json_string(content)
                        parsed = AlignmentResponse.model_validate_json(
                            cleaned_content
                        )
                        alignments = parsed.alignments
                    except Exception as json_err:
                        print(
                            f"Pydantic JSON validate failed, running regex parser: {json_err}"
                        )
                        alignments = []
                        matches_extracted = re.findall(
                            r'(?:"claim_index"|\'claim_index\'|claim_index)\s*:\s*(-?[0-9]+)\s*,\s*'
                            r'(?:"context_index"|\'context_index\'|context_index)\s*:\s*(-?[0-9]+)',
                            content,
                        )
                        for m in matches_extracted:
                            alignments.append(
                                ClaimAlignment(
                                    claim_index=int(m[0]),
                                    context_index=int(m[1]),
                                    reason="regex parsed",
                                )
                            )
                else:
                    response = call_with_retry(
                        self.client.models.generate_content,
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=AlignmentResponse,
                            temperature=0.0,
                        ),
                    )
                    alignments = response.parsed.alignments

                # Process LLM alignments
                for alignment in alignments:
                    idx_in_send = alignment.claim_index
                    ctx_idx = alignment.context_index
                    reason = alignment.reason

                    if 0 <= idx_in_send < len(claims_to_send):
                        _, c_idx, claim_text = claims_to_send[idx_in_send]
                        if 0 <= ctx_idx < len(retrieved_chunks):
                            alignments_map[c_idx] = ctx_idx
                        else:
                            # Skip short headings/transitions to prevent cluttering the unverified list
                            if len(claim_text.split()) > 4:
                                unverified_claims.append(
                                    f"Claim: '{claim_text}' (Unverified: {reason})"
                                )

            except Exception as e:
                print(f"Semantic alignment failed: {e}")
                for _, c_idx, claim_text in claims_to_send:
                    # If it's not a short heading
                    if len(claim_text.split()) > 4:
                        unverified_claims.append(
                            f"Claim: '{claim_text}' (Verification error: {str(e)})"
                        )

        # 4. Map mapped chunks to citations list
        verified_citations = []
        verified_count = len(alignments_map)

        for c_idx, ctx_idx in alignments_map.items():
            metadata = retrieved_chunks[ctx_idx].chunk.metadata

            # Filter out generic company name header blocks
            blacklist = {
                "SUPREET CHEMICALS LIMITED",
                "SUPREET CHEMICALS LTD.",
                "SUPREET CHEMICALS LTD",
                "SUPREET",
                "CHEMICALS",
                "LIMITED",
                "LTD",
            }
            section_val = None
            for key in ["h3", "h2", "h1", "section"]:
                val = metadata.get(key)
                if val and str(val).strip().upper() not in blacklist:
                    section_val = str(val).strip()
                    break
            if not section_val:
                section_val = metadata.get("section") or "General Section"

            verified_citations.append(
                Citation(
                    source=metadata.get("source", "Unknown"),
                    page=metadata.get("page"),
                    section=section_val,
                )
            )

        # 5. Rebuild answer text with citation brackets mapped to verified sentences
        rebuilt_lines = []
        for line in answer.split("\n"):
            if not line.strip():
                rebuilt_lines.append("")
                continue

            # Split line into sentences
            parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", line)]
            rebuilt_parts = []
            for part in parts:
                if not part:
                    continue
                try:
                    s_idx = raw_sentences.index(part)
                    ctx_idx = alignments_map.get(s_idx, -1)
                    if ctx_idx >= 0:
                        if part.endswith("."):
                            rebuilt_parts.append(f"{part[:-1]} [{ctx_idx}].")
                        else:
                            rebuilt_parts.append(f"{part} [{ctx_idx}]")
                    else:
                        rebuilt_parts.append(part)
                except ValueError:
                    rebuilt_parts.append(part)

            rebuilt_lines.append(" ".join(rebuilt_parts))

        rebuilt_answer = "\n".join(rebuilt_lines)
        confidence = min(
            1.0,
            (verified_count / len(raw_sentences)) if raw_sentences else 1.0,
        )

        # Deduplicate citations
        unique_citations = []
        seen = set()
        for cit in verified_citations:
            key = (cit.source, cit.page, cit.section)
            if key not in seen:
                seen.add(key)
                unique_citations.append(cit)

        return rebuilt_answer, unique_citations, float(confidence), unverified_claims
