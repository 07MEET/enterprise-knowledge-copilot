from app.llm.provider import llm
from app.models.document_models import RetrievedChunk


class AnswerGenerator:
    """
    Generates answers grounded strictly in retrieved documents.
    Uses the unified LLMClient — switch providers via LLM_PROVIDER in .env.
    """

    def generate_answer(
        self,
        query: str,
        retrieved_chunks: list[RetrievedChunk],
        stream: bool = False,
        history: list[dict] = None,
    ):
        """
        Synthesize a grounded response citing supporting chunks.
        """
        if not retrieved_chunks:
            return "I don't have enough information from the provided documents."

        # Group context by source document so the LLM sees document boundaries clearly
        context_parts = []
        for idx, item in enumerate(retrieved_chunks):
            source = item.chunk.metadata.get("source", "Unknown")
            h1 = item.chunk.metadata.get("h1", "")
            h2 = item.chunk.metadata.get("h2", "")
            section = f"{h1} > {h2}" if h1 and h2 else (h1 or h2 or "Main")

            context_parts.append(
                f"━━━ CHUNK [{idx}] ━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📄 DOCUMENT: {source}\n"
                f"📑 Section : {section}\n"
                f"─────────────────────────────────────────\n"
                f"{item.chunk.text}\n"
            )
        context_str = "\n".join(context_parts)

        system_instruction = (
            "You are a strict Enterprise Knowledge Assistant. Answer the user's question "
            "using ONLY the Retrieved Chunks below. You also have access to previous conversation turns to understand follow-up questions contextually.\n\n"
            "Guidelines:\n"
            "- Write a detailed, well-structured answer grounded strictly in the retrieved chunks.\n"
            "- Focus directly on answering the user's question.\n"
            "- Do not invent facts or extrapolate beyond what is explicitly stated in the context.\n\n"
            "Citation Rules:\n"
            "- After every factual claim, write the chunk index in brackets: [0], [1], [2] etc.\n"
            "- If a claim is supported by multiple chunks, cite at most 1 to 3 of the most relevant chunks. DO NOT list every single chunk (e.g. do not write [1][2][3][4][5][6][7][8][9]).\n"
            "- Do not mention section names, page numbers, or metadata in the answer text.\n"
            "- Do NOT output <think> tags or reasoning preamble. Start directly with the answer.\n\n"
            "Refusal Rule:\n"
            "- If the retrieved chunks do not contain enough information to answer the question, state that you do not have enough information."
        )

        user_prompt = (
            f"User Question: {query}\n\n"
            f"Retrieved Chunks:\n"
            f"{context_str}\n"
        )

        try:
            return llm.chat(
                system_prompt=system_instruction,
                user_prompt=user_prompt,
                temperature=0.0,
                stream=stream,
                history=history,
            )
        except Exception as e:
            print(f"Generation failed: {e}")
            if stream:
                def error_gen():
                    yield "I don't have enough information from the provided documents."
                return error_gen()
            return "I don't have enough information from the provided documents."
