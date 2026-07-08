from google import genai
from google.genai import types

from app.config.settings import settings
from app.models.document_models import RetrievedChunk


class AnswerGenerator:
    """
    Generates answers grounded strictly in retrieved documents using Gemini.
    """

    def __init__(self):
        """
        Initialize the Gemini client and set the LLM model.
        """
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
        for item in retrieved_chunks:
            source = item.chunk.metadata.get("source", "Unknown")
            h1 = item.chunk.metadata.get("h1", "")
            h2 = item.chunk.metadata.get("h2", "")
            section = f"{h1} > {h2}" if h1 and h2 else (h1 or h2 or "Main")

            context_parts.append(
                f"--- Chunk ID: {item.chunk.chunk_id} ---\n"
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
            "2. For every statement or claim you make, you MUST append the chunk ID of the source text that supports it in brackets, "
            "e.g., 'The medical leave policy allows up to 12 weeks of absence [chunk_id_123].'\n"
            "3. If there is no mention of the answer in the documents, or if the documents are insufficient, return exactly: "
            "'I don't have enough information from the provided documents.' Do not make up an answer.\n"
            "4. Do not include citations for general greetings or formatting. Only cite specific facts."
        )

        try:
            response = self.client.models.generate_content(
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
