from google import genai
from google.genai import types

from app.config.settings import settings
from app.models.document_models import RetrievedChunk
from app.utils.rate_limiter import call_with_retry


class AnswerGenerator:
    """
    Generates answers grounded strictly in retrieved documents using Gemini or Ollama.
    """

    def __init__(self):
        """
        Initialize the generation client and set the LLM model.
        """
        if settings.USE_LOCAL:
            import ollama
            self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        else:
            from google import genai
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.LLM_MODEL

    def generate_answer(
        self,
        query: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> str:
        """
        Synthesize a grounded response citing supporting chunks.
        """
        if not retrieved_chunks:
            return (
                "I don't have enough information from the provided documents."
            )

        # Assemble the retrieval context text
        context_parts = []
        for idx, item in enumerate(retrieved_chunks):
            source = item.chunk.metadata.get("source", "Unknown")
            h1 = item.chunk.metadata.get("h1", "")
            h2 = item.chunk.metadata.get("h2", "")
            section = f"{h1} > {h2}" if h1 and h2 else (h1 or h2 or "Main")

            context_parts.append(
                f"--- Chunk Index {idx} ---\n"
                f"Source: {source}\n"
                f"Section: {section}\n"
                f"Text:\n{item.chunk.text}\n"
            )
        context_str = "\n".join(context_parts)

        # Build prompt body
        prompt = (
            f"User Question: {query}\n\n"
            f"Retrieved Documents:\n"
            f"{context_str}\n"
        )

        system_instruction = (
            "You are a helpful and strict Enterprise Knowledge Assistant. Your job is to answer the user's question "
            "based ONLY on the provided Retrieved Documents.\n\n"
            "Rules:\n"
            "1. Rely only on clear facts mentioned in the documents. Do not assume or extrapolate.\n"
            "2. Write a detailed, comprehensive, and well-structured answer. Use clear paragraphs, bullet points, or numbered lists "
            "to explain all relevant details from the provided documents. Avoid overly brief one-sentence answers.\n"
            "3. For every statement or claim you make, you MUST append the exact chunk index in brackets, "
            "e.g., '[0]' or '[1]' (do NOT write the word 'chunk'). Only cite at the end of factual assertions. "
            "Write the answer naturally. Do NOT write or mention raw metadata, page numbers, or section header names inside the text "
            "(e.g., do NOT write 'as stated in Section X' or 'according to Page Y'). Use ONLY the bracketed citation numbers (e.g. [0]).\n"
            "4. If there is no mention of the answer in the documents, or if the documents are insufficient, return exactly: "
            "'I don't have enough information from the provided documents.' Do not make up an answer.\n"
            "5. Do not include citations for general greetings or formatting. Only cite specific facts.\n"
            "6. CRITICAL: Do NOT output any thinking, analysis, reasoning, or <think> tags. Start your response directly with the factual answer.\n"
            "7. If the user's query is a keyword, topic, or phrase (e.g., 'harassment policy') rather than a complete question, "
            "interpret it as a request to describe, explain, or summarize that policy/topic in detail based on the documents."
        )

        if settings.USE_LOCAL:
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt},
                    ],
                    options={"temperature": 0.0, "num_ctx": 8192, "num_predict": 4096},
                )
                return response["message"]["content"].strip()
            except Exception as e:
                print(f"Local generation failed: {e}")
                return (
                    "I don't have enough information from the provided documents."
                )

        from google.genai import types
        try:
            response = call_with_retry(
                self.client.models.generate_content,
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0,  # Zero temperature helps prevent hallucinations
                ),
            )
            return response.text.strip()
        except Exception as e:
            print(f"Generation failed: {e}")
            return (
                "I don't have enough information from the provided documents."
            )
