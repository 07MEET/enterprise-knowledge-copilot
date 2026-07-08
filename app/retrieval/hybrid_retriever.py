from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config.settings import settings
from app.embeddings.factory import get_embedding_model
from app.models.document_models import Chunk, RetrievedChunk
from app.retrieval.bm25_retriever import BM25Retriever
from app.storage.vector_store import VectorStore


class ChunkRelevance(BaseModel):
    """
    Relevance rating for an individual chunk index.
    """

    index: int
    score: float


class RerankingResponse(BaseModel):
    """
    Reranking response model containing chunk rankings.
    """

    rankings: list[ChunkRelevance]


class HybridRetriever:
    """
    Retrieves documents using Dense + Sparse retrieval with RRF and LLM reranking.
    """

    def __init__(self):
        """
        Initialize vector store, sparse retriever, embedding model, and Gemini client.
        """
        self.vector_store = VectorStore()
        self.bm25_retriever = BM25Retriever()
        self.embedder = get_embedding_model()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        dense_k: int = 20,
        sparse_k: int = 20,
        rerank: bool = True,
    ) -> list[RetrievedChunk]:
        """
        Query both dense and sparse indices, fuse with RRF, and optional reranking.
        """
        # 1. Dense retrieval
        query_embedding = self.embedder.embed_query(query)
        dense_results = self.vector_store.similarity_search(
            query_embedding=query_embedding,
            k=dense_k,
        )

        # 2. Sparse retrieval
        if not self.bm25_retriever.bm25:
            self.bm25_retriever.load_index()

        sparse_results = self.bm25_retriever.search(
            query=query,
            k=sparse_k,
        )

        if not dense_results and not sparse_results:
            return []

        # 3. Reciprocal Rank Fusion
        fused_results = self.reciprocal_rank_fusion(
            dense_results,
            sparse_results,
        )

        # If reranking is disabled or database is empty, return top fused results
        if not rerank or not fused_results:
            return fused_results[:top_k]

        # 4. LLM Reranking pass on top 15 fused candidates
        chunks_to_rerank = fused_results[:15]
        reranked_results = self.rerank_chunks(
            query,
            chunks_to_rerank,
        )

        return reranked_results[:top_k]

    def reciprocal_rank_fusion(
        self,
        dense_results: list[RetrievedChunk],
        sparse_results: list[RetrievedChunk],
        k: int = 60,
    ) -> list[RetrievedChunk]:
        """
        Combine two ranked result lists using the Reciprocal Rank Fusion (RRF) formula.
        """
        rrf_scores = {}
        chunk_map = {}

        # Score dense matches
        for rank, retrieved in enumerate(dense_results, start=1):
            chunk_id = retrieved.chunk.chunk_id
            chunk_map[chunk_id] = retrieved.chunk
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (
                1.0 / (k + rank)
            )

        # Score sparse matches
        for rank, retrieved in enumerate(sparse_results, start=1):
            chunk_id = retrieved.chunk.chunk_id
            chunk_map[chunk_id] = retrieved.chunk
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (
                1.0 / (k + rank)
            )

        # Sort candidate IDs by their fused score descending
        sorted_ids = sorted(
            rrf_scores.keys(),
            key=lambda x: rrf_scores[x],
            reverse=True,
        )

        fused = []
        for cid in sorted_ids:
            fused.append(
                RetrievedChunk(
                    chunk=chunk_map[cid],
                    score=rrf_scores[cid],
                    retrieval_method="hybrid",
                )
            )

        return fused

    def rerank_chunks(
        self,
        query: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """
        Rerank a selection of retrieved chunks using Gemini 3.5 Flash as an evaluator.
        """
        if not retrieved_chunks:
            return []

        # Prepare contextual text representation of candidates
        chunks_text_list = []
        for idx, item in enumerate(retrieved_chunks):
            chunks_text_list.append(
                f"--- Chunk Index {idx} ---\n{item.chunk.text}\n"
            )
        chunks_input = "\n".join(chunks_text_list)

        prompt = (
            f"Query: {query}\n\n"
            f"Candidate Chunks with Indices:\n"
            f"{chunks_input}\n"
            f"Rate the relevance of each chunk to answering the query on a scale from 0.0 to 10.0."
        )

        try:
            response = self.client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an expert search engine reranker. Rate each chunk index's relevance "
                        "to the query. Return a JSON object with 'rankings' containing objects with "
                        "'index' and 'score' attributes. Assign a high score (up to 10.0) if the chunk contains "
                        "direct answers or necessary details to address the query. Otherwise, assign low scores."
                    ),
                    response_mime_type="application/json",
                    response_schema=RerankingResponse,
                    temperature=0.0,
                ),
            )

            # Retrieve schema-validated parsed response
            ranking_data = response.parsed

            scored_chunks = []
            score_map = {
                item.index: item.score for item in ranking_data.rankings
            }

            for idx, item in enumerate(retrieved_chunks):
                # Retrieve LLM rating, fallback to 0.0 if not parsed
                llm_score = score_map.get(idx, 0.0)

                retrieved_item = RetrievedChunk(
                    chunk=item.chunk,
                    score=float(llm_score),
                    retrieval_method="reranked",
                )
                scored_chunks.append(retrieved_item)

            # Sort candidate chunks based on Gemini relevance score descending
            scored_chunks.sort(key=lambda x: x.score, reverse=True)
            return scored_chunks

        except Exception as e:
            print(f"Reranking failed: {e}. Falling back to RRF rankings.")
            return retrieved_chunks
