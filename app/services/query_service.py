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
    # 1. Retrieve relevant contexts using hybrid vector & keyword matching
    retrieved_chunks = retriever.retrieve(question)

    # 2. Generate factual answer citing chunk UUIDs
    raw_answer = generator.generate_answer(question, retrieved_chunks)

    # 3. Audit citations and evaluate factual entailment
    verified_citations, confidence, unverified_info = verifier.verify(
        raw_answer, retrieved_chunks
    )

    # 4. Post-process response to map UUID citation brackets to clean numbers: [1], [2]...
    pattern = re.compile(r"\[([a-zA-Z0-9\-]+)\]")
    cited_ids = pattern.findall(raw_answer)

    chunk_lookup = {item.chunk.chunk_id: item for item in retrieved_chunks}

    id_to_index = {}
    ordered_citations = []
    index_counter = 1
    cleaned_answer = raw_answer

    # Map verified chunk IDs sequentially
    for cid in cited_ids:
        if cid in chunk_lookup and cid not in id_to_index:
            # Check if this citation was flagged as unverified
            is_unverified = any(cid in claim for claim in unverified_info)
            if not is_unverified:
                id_to_index[cid] = index_counter
                metadata = chunk_lookup[cid].chunk.metadata
                section_val = (
                    metadata.get("h1")
                    or metadata.get("section")
                    or metadata.get("h2")
                )
                ordered_citations.append(
                    Citation(
                        source=metadata.get("source", "Unknown"),
                        page=metadata.get("page"),
                        section=section_val,
                    )
                )
                index_counter += 1

    # Replace bracket UUIDs with numbered citation tags
    for cid, idx in id_to_index.items():
        cleaned_answer = cleaned_answer.replace(f"[{cid}]", f"[{idx}]")

    # Clean up and strip any remaining unverified raw bracket tags from the text
    cleaned_answer = pattern.sub("", cleaned_answer)
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