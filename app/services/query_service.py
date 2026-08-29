import re

from app.generation.generator import AnswerGenerator
from app.llm.provider import llm
from app.models.response_models import Citation, QueryResponse
from app.retrieval.hybrid_retriever import HybridRetriever
from app.verification.verifier import CitationVerifier

# Initialize pipeline components once globally to leverage connection pooling
retriever = HybridRetriever()
generator = AnswerGenerator()
verifier = CitationVerifier()


def _needs_rewriting(question: str) -> bool:
    """Quick heuristic: does this query look like it needs LLM correction?"""
    words = question.strip().split()
    # Already long enough and has no obvious issues → skip rewrite
    if len(words) >= 4:
        # Check for repeated characters suggesting typos (e.g. "jeppppa")
        import re
        has_repeat = bool(re.search(r'(.)\1{2,}', question))  # 3+ same char in a row
        # Check if very short words dominate (e.g. "wht r thr authrs")
        short_word_ratio = sum(1 for w in words if len(w) <= 2) / len(words)
        if not has_repeat and short_word_ratio < 0.5:
            return False  # Query looks clean, no rewrite needed
    return True


def _rewrite_query(question: str) -> str:
    """
    Use the LLM to normalize the user's question before retrieval.
    Only called when the query looks malformed (typos, abbreviations, grammar).
    Returns the rewritten query, or the original if rewriting fails.
    """
    from app.llm.provider import provider_override
    from app.config.settings import settings
    
    override = provider_override.get()
    active_provider = override.lower() if override else settings.LLM_PROVIDER.lower()
    
    if active_provider == "local" or not _needs_rewriting(question):
        return question
    try:
        import json
        result = llm.chat(
            system_prompt=(
                "You are a query normalizer for a document search system. "
                "Fix any spelling mistakes and grammar in the user's question. "
                "Do NOT change the meaning or add any new information. "
                "Return a JSON object in this exact schema: {\"corrected_query\": \"your corrected query here\"}."
            ),
            user_prompt=question,
            temperature=0.0,
            max_tokens=128,
            json_mode=True,
        )
        data = json.loads(result.strip())
        rewritten = data.get("corrected_query", "").strip()
        return rewritten if rewritten else question
    except Exception:
        return question


def _answer_question_internal(question: str, fast_mode: bool = False) -> QueryResponse:
    """
    Execute the end-to-end Enterprise RAG pipeline internally.
    """
    # 0. Rewrite query to fix typos and grammar before retrieval
    rewritten_question = _rewrite_query(question)

    # 1. Retrieve relevant contexts using hybrid vector & keyword matching
    retrieved_chunks = retriever.retrieve(rewritten_question, rerank=False)

    # 1b. Ambiguity check — if chunks span many unrelated documents and the
    # query is too vague to resolve, ask the user to be more specific.
    if retrieved_chunks:
        unique_sources = list(dict.fromkeys(
            c.chunk.metadata.get("source", "Unknown") for c in retrieved_chunks
        ))
        # Vague if: >2 distinct docs retrieved AND query is short or has no
        # specific subject that points to one document.
        # Check BOTH the original and rewritten question so typos don't block answers.
        query_words = rewritten_question.strip().split()
        query_is_vague = len(query_words) <= 6 and not any(
            # check if any source filename keyword appears in either form of query
            word.lower() in rewritten_question.lower() or word.lower() in question.lower()
            for source in unique_sources
            for word in source.replace("-", " ").replace("_", " ").replace(".pdf", "").split()
            if len(word) > 3
        )
        if len(unique_sources) > 2 and query_is_vague:
            doc_list = "\n".join(f"  • {s}" for s in unique_sources)
            examples = []
            for s in unique_sources[:2]:
                clean_name = s.replace(".pdf", "").replace("-", " ").replace("_", " ").title()
                examples.append(f"  • *\"Tell me about {clean_name}...\"*")
            examples_str = "\n".join(examples)
            
            clarification = (
                f"Your question **\"{question}\"** is too broad — I found relevant content "
                f"across {len(unique_sources)} different documents:\n\n{doc_list}\n\n"
                f"Please refine your question by specifying which document or topic you mean. "
                f"For example:\n{examples_str}"
            )
            return QueryResponse(
                answer=clarification,
                citations=[],
                confidence=0.0,
                unverified_information=[],
                model_used=llm.get_last_model_used(),
            )



    # 2. Generate factual answer citing chunk UUIDs
    raw_answer = generator.generate_answer(rewritten_question, retrieved_chunks)

    # 3. Audit citations and evaluate factual entailment
    if fast_mode:
        rebuilt_answer = raw_answer
        verified_citations = []
        unverified_info = []
        confidence = 0.95
        
        # In fast mode, parse bracket indices directly from the raw output
        pattern = re.compile(r"\[([0-9]+)\]")
        for match in pattern.finditer(raw_answer):
            try:
                idx = int(match.group(1))
                if 0 <= idx < len(retrieved_chunks):
                    # We add placeholders to verified_citations; the final mapper below
                    # will correctly populate clean citation objects
                    chunk = retrieved_chunks[idx].chunk
                    verified_citations.append(
                        Citation(
                            source=chunk.metadata.get("source", "Unknown"),
                            page=chunk.metadata.get("page"),
                            section=chunk.metadata.get("h1") or chunk.metadata.get("h2") or "N/A",
                            snippet=chunk.text
                        )
                    )
            except Exception:
                pass
    else:
        rebuilt_answer, verified_citations, confidence, unverified_info = verifier.verify(
            raw_answer, retrieved_chunks, query=rewritten_question
        )

    # 4. Post-process response to map index citation brackets (e.g. [0], [1]) to clean numbers: [1], [2]...
    pattern = re.compile(r"(?:\[|【)([0-9]+)(?:\]|】)")
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
            
            section_val = None
            for key in ["h3", "h2", "h1", "section"]:
                val = metadata.get(key)
                if val and len(str(val).strip()) > 2:
                    section_val = str(val).strip()
                    break
            if not section_val:
                section_val = metadata.get("section") or "General Section"

            ordered_citations.append(
                Citation(
                    source=metadata.get("source", "Unknown"),
                    page=metadata.get("page"),
                    section=section_val,
                    snippet=retrieved_chunks[idx].chunk.text,
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
            model_used=llm.get_last_model_used(),
        )

    # Fallback to verifier citations if parsing matches were not substituted
    if not ordered_citations and verified_citations:
        ordered_citations = verified_citations

    # --- Source-relevance filter ---
    # For each citation, extract meaningful keywords from the source filename and
    # check if any appear in the answer text. This drops citations from documents
    # that are clearly unrelated to the answer topic (e.g., company policy PDFs
    # cited in a research paper answer because of incidental BM25 keyword matches).
    if len(ordered_citations) >= 2:
        import re as _re
        from collections import Counter

        # Common words to exclude from filename keyword matching
        _skip = {
            'code', 'for', 'the', 'and', 'of', 'to', 'a', 'an', 'in',
            'on', 'at', 'by', 'with', 'from', 'this', 'that', 'pdf',
        }

        # Collect all words (≥4 chars) from the cleaned answer
        answer_words = set(
            _re.findall(r'\b[a-z]{4,}\b', cleaned_answer.lower())
        )

        def _source_relevant(source: str) -> bool:
            """True if any meaningful word from the source filename appears in the answer."""
            fname_words = set(
                _re.findall(r'\b[a-z]{4,}\b', source.lower())
            ) - _skip
            return bool(fname_words & answer_words)

        relevant = [c for c in ordered_citations if _source_relevant(c.source)]
        # Only apply if the filter keeps at least one citation
        if relevant:
            ordered_citations = relevant
        else:
            # Fallback: majority-source filter (handles edge cases)
            source_counts = Counter(c.source for c in ordered_citations)
            dominant_source, dominant_count = source_counts.most_common(1)[0]
            if dominant_count / len(ordered_citations) >= 0.6:
                ordered_citations = [
                    c for c in ordered_citations
                    if c.source == dominant_source or source_counts[c.source] > 1
                ]

    return QueryResponse(
        answer=cleaned_answer,
        citations=ordered_citations,
        confidence=confidence,
        unverified_information=unverified_info,
        model_used=llm.get_last_model_used(),
    )



def answer_question(question: str, llm_provider: str | None = None, fast_mode: bool = False) -> QueryResponse:
    """
    Wrapper that manages thread-safe LLM provider overrides.
    """
    if llm_provider:
        from app.llm.provider import provider_override
        token = provider_override.set(llm_provider)
        try:
            return _answer_question_internal(question, fast_mode)
        finally:
            provider_override.reset(token)
    else:
        return _answer_question_internal(question, fast_mode)

import json

def _stream_answer_question_internal(question: str, history: list[dict] = None):
    """
    Execute the RAG pipeline and yield streaming tokens, followed by a final JSON metadata payload.
    """
    rewritten_question = _rewrite_query(question)
    retrieved_chunks = retriever.retrieve(rewritten_question, rerank=False)

    if not retrieved_chunks:
        yield "I don't have enough information from the provided documents."
        yield "\n\n__METADATA__:" + json.dumps({
            "citations": [],
            "model_used": llm.get_last_model_used()
        })
        return

    # Yield chunks from the generator
    full_answer = ""
    token_generator = generator.generate_answer(rewritten_question, retrieved_chunks, stream=True, history=history)
    for chunk in token_generator:
        full_answer += chunk
        yield chunk
        
    # Now parse the citations from the full_answer (fast_mode equivalent)
    citations = []
    pattern = re.compile(r"(?:\[|【)([0-9]+)(?:\]|】)")
    
    id_to_index = {}
    index_counter = 1
    
    for match in pattern.finditer(full_answer):
        try:
            idx = int(match.group(1))
            if 0 <= idx < len(retrieved_chunks) and idx not in id_to_index:
                id_to_index[idx] = index_counter
                c = retrieved_chunks[idx].chunk
                citations.append(
                    Citation(
                        id=index_counter,
                        source=c.metadata.get("source", "Unknown"),
                        page=c.metadata.get("page"),
                        section=c.metadata.get("h1") or c.metadata.get("h2") or "N/A",
                        snippet=c.text
                    ).model_dump()
                )
                index_counter += 1
        except ValueError:
            pass

    yield "\n\n__METADATA__:" + json.dumps({
        "citations": citations,
        "citation_mapping": id_to_index,
        "model_used": llm.get_last_model_used()
    })

def stream_answer_question(question: str, history: list[dict] = None, llm_provider: str | None = None):
    """
    Wrapper for streaming that manages thread-safe LLM provider overrides.
    """
    if llm_provider:
        from app.llm.provider import provider_override
        provider_override.set(llm_provider)
    yield from _stream_answer_question_internal(question, history)