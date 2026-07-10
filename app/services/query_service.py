import re

from app.generation.generator import AnswerGenerator
from app.models.response_models import Citation, QueryResponse
from app.retrieval.hybrid_retriever import HybridRetriever
from app.verification.verifier import CitationVerifier

# Initialize pipeline components once globally to leverage connection pooling
retriever = HybridRetriever()
generator = AnswerGenerator()
verifier = CitationVerifier()


def answer_question(question: str) -> QueryResponse:
    """
    Execute the end-to-end Enterprise RAG pipeline:
    Retrieve -> Fuse & Rerank -> Generate -> Verify Citations -> Format Response.
    """
    # 0. Expand acronyms in query for robust term matching
    expanded_query = question
    expanded_lower = question.lower()
    if "cfo" in expanded_lower:
        expanded_query = re.sub(r"(?i)\bcfo\b", "Chief Financial Officer (CFO)", expanded_query)
    if "ceo" in expanded_lower:
        expanded_query = re.sub(r"(?i)\bceo\b", "Chief Executive Officer (CEO)", expanded_query)
    if "coo" in expanded_lower:
        expanded_query = re.sub(r"(?i)\bcoo\b", "Chief Operating Officer (COO)", expanded_query)

    # 1. Retrieve relevant contexts using hybrid vector & keyword matching
    retrieved_chunks = retriever.retrieve(expanded_query)

    # 2. Generate factual answer citing chunk UUIDs
    raw_answer = generator.generate_answer(expanded_query, retrieved_chunks)

    # 3. Audit citations and evaluate factual entailment
    rebuilt_answer, verified_citations, confidence, unverified_info = verifier.verify(
        raw_answer, retrieved_chunks
    )

    # 4. Post-process response to map index citation brackets (e.g. [0], [1]) to clean numbers: [1], [2]...
    pattern = re.compile(r"\[([0-9]+)\]")
    cited_indexes = [int(idx) for idx in pattern.findall(rebuilt_answer)]

    id_to_index = {}
    ordered_citations = []
    index_counter = 1
    cleaned_answer = rebuilt_answer

    # Map verified chunk indexes sequentially
    for idx in cited_indexes:
        if idx < len(retrieved_chunks) and idx not in id_to_index:
            id_to_index[idx] = index_counter
            metadata = retrieved_chunks[idx].chunk.metadata
            
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

            ordered_citations.append(
                Citation(
                    source=metadata.get("source", "Unknown"),
                    page=metadata.get("page"),
                    section=section_val,
                )
            )
            index_counter += 1

    # Replace bracket indexes with sequential numbered citation tags in a single pass
    def replace_tag(match):
        idx = int(match.group(1))
        if idx in id_to_index:
            return f"[{id_to_index[idx]}]"
        return ""

    cleaned_answer = pattern.sub(replace_tag, cleaned_answer)
    
    # Strip any lines that contain only isolated bracket citations (e.g. "[3]" or "* [1]")
    cleaned_lines = []
    for line in cleaned_answer.split("\n"):
        # Strip list symbols, numbers, and whitespace
        stripped = re.sub(r"[\*\-\d\.\s]+", "", line).strip()
        # Strip citation brackets
        stripped = re.sub(r"\[[0-9]+\]", "", stripped).strip()
        if not stripped and re.search(r"\[[0-9]+\]", line):
            # Line contains only brackets/list marks, skip it
            continue
        cleaned_lines.append(line)
    
    cleaned_answer = "\n".join(cleaned_lines)
    cleaned_answer = cleaned_answer.replace("  ", " ").strip()

    # If the response indicates refusal due to missing info, return empty citations
    refusal_phrases = [
        "i don't have enough information",
        "insufficient information",
    ]
    if any(phrase in cleaned_answer.lower() for phrase in refusal_phrases):
        return QueryResponse(
            answer="I don't have enough information from the provided documents.",
            citations=[],
            confidence=0.0,
            unverified_information=[],
        )

    # Fallback to verifier citations if parsing matches were not substituted
    if not ordered_citations and verified_citations:
        ordered_citations = verified_citations

    return QueryResponse(
        answer=cleaned_answer,
        citations=ordered_citations,
        confidence=confidence,
        unverified_information=unverified_info,
    )