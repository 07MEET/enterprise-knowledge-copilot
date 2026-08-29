from pydantic import BaseModel

from app.config.settings import settings
from app.embeddings.factory import get_embedding_model
from app.llm.provider import llm
from app.models.document_models import RetrievedChunk

# DLL collision fix: Load and initialize PyTorch (embeddings) BEFORE importing chromadb (VectorStore)
_dummy_embedder = get_embedding_model()

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
        Initialize vector store, sparse retriever, and embedding model.
        The LLM client is provided by the shared llm singleton.
        """
        self.embedder = get_embedding_model()
        self.vector_store = VectorStore()
        self.bm25_retriever = BM25Retriever()

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        dense_k: int = 25,
        sparse_k: int = 25,
        rerank: bool = True,
    ) -> list[RetrievedChunk]:
        """
        Query both dense and sparse indices, fuse with RRF, and optional reranking.
        Returns the top-k most relevant chunks across all indexed documents.
        The LLM downstream is responsible for citing only what is relevant.
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
            query=query,
        )

        # RAG Optimization: Inject first page of primary document for overview queries
        fused_results = self.inject_first_page_context(fused_results, query)

        # If reranking is disabled, running locally, or database is empty, return top fused results
        if not rerank or settings.USE_LOCAL or not fused_results:
            return fused_results[:top_k]

        # 4. LLM Reranking pass on top 5 fused candidates
        chunks_to_rerank = fused_results[:5]
        reranked_results = self.rerank_chunks(
            query,
            chunks_to_rerank,
        )

        return reranked_results[:top_k]

    def inject_first_page_context(
        self,
        fused_results: list[RetrievedChunk],
        query: str,
    ) -> list[RetrievedChunk]:
        """
        RAG Optimization: If the query is asking about overview metadata (e.g., author, summary, title),
        ensure that the first page (Page 1) of the primary matched document is injected into the context.
        """
        if not fused_results:
            return fused_results

        # Check if the query contains overview keywords
        overview_keywords = {"author", "authors", "write", "writer", "wrote", "publish", "publisher", "summary", "summarize", "abstract", "title"}
        query_words = set(query.lower().replace("-", " ").replace("_", " ").split())
        is_overview_query = bool(overview_keywords & query_words)

        if not is_overview_query:
            return fused_results

        # Identify the primary document name from the top-ranked retrieved chunks
        primary_doc = fused_results[0].chunk.metadata.get("source")
        if not primary_doc:
            return fused_results

        # Fetch Page 1 chunks for this primary document from ChromaDB.
        # We set limit=1000 to ensure we pull all chunks of this document before filtering in Python.
        try:
            p1_results = self.vector_store.collection.get(
                where={"source": primary_doc},
                limit=1000,
                include=["metadatas", "documents"]
            )
            
            p1_chunks = []
            if p1_results and p1_results.get("ids"):
                ids = p1_results["ids"]
                documents = p1_results["documents"]
                metadatas = p1_results["metadatas"]
                for i in range(len(ids)):
                    meta = metadatas[i] or {}
                    page_str = str(meta.get("page", ""))
                    if page_str == "1" or page_str.startswith("1-"):
                        from app.models.document_models import Chunk
                        chunk = Chunk(chunk_id=ids[i], text=documents[i], metadata=meta)
                        p1_chunks.append(
                            RetrievedChunk(
                                chunk=chunk,
                                score=10.0,  # high score to prioritize
                                retrieval_method="first_page_injection"
                            )
                        )
            
            if p1_chunks:
                print(f"[RAG] Injected {len(p1_chunks)} Page 1 chunks for '{primary_doc}' due to overview query.")
                # We filter out any chunks that are already in the fused_results to prevent duplicates,
                # then prepend the Page 1 chunks to the results.
                p1_ids = {rc.chunk.chunk_id for rc in p1_chunks}
                filtered_fused = [rc for rc in fused_results if rc.chunk.chunk_id not in p1_ids]
                return p1_chunks + filtered_fused
        except Exception as e:
            print(f"[RAG] Failed to inject first page context: {e}")
            
        return fused_results

    def reciprocal_rank_fusion(
        self,
        dense_results: list[RetrievedChunk],
        sparse_results: list[RetrievedChunk],
        query: str = "",
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

        # 4. Exact-match Keyword Boosting (General/Domain-Agnostic)
        # Prioritize chunks containing exact/rare words from the user query
        import re
        import string
        clean_query = query.lower().replace("-", " ").replace("_", " ").replace("/", " ")
        query_words = [w.strip(string.punctuation) for w in clean_query.split()]
        stopwords = {
            "what", "who", "whom", "whose", "which", "where", "when", "why", "how", 
            "this", "that", "these", "those", "does", "doing", "did", "have", "has", 
            "had", "the", "and", "for", "are", "were", "was", "is", "a", "an", "of", "in", "to", "on"
        }
        significant_words = [w for w in query_words if len(w) >= 1 and w not in stopwords]
        
        if significant_words:
            for chunk_id, score in rrf_scores.items():
                text = chunk_map[chunk_id].text.lower()
                match_count = 0
                for word in significant_words:
                    if re.search(r'\b' + re.escape(word) + r'\b', text):
                        match_count += 1
                if match_count > 0:
                    # Boost score by up to 2.0x based on ratio of matched words
                    boost = 1.0 + (match_count / len(significant_words))
                    rrf_scores[chunk_id] = score * boost

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
        Rerank retrieved chunks using the configured LLM as a relevance judge.
        """
        if not retrieved_chunks:
            return []

        chunks_text_list = [
            f"--- Chunk Index {idx} ---\n{item.chunk.text}\n"
            for idx, item in enumerate(retrieved_chunks)
        ]
        chunks_input = "\n".join(chunks_text_list)

        system_instruction = (
            "You are an expert search engine reranker. Rate each chunk index's relevance "
            "to the query. Return a JSON object with 'rankings' containing objects with "
            "'index' and 'score' attributes. Assign a high score (up to 10.0) if the chunk contains "
            "direct answers or necessary details to address the query. Otherwise, assign low scores."
        )
        user_prompt = (
            f"Query: {query}\n\n"
            f"Candidate Chunks with Indices:\n{chunks_input}\n"
            f"Rate the relevance of each chunk to answering the query on a scale from 0.0 to 10.0."
        )

        try:
            content = llm.chat(
                system_prompt=system_instruction,
                user_prompt=user_prompt,
                temperature=0.0,
                json_mode=True,
            )
            from app.utils.json_parser import clean_json_string
            ranking_data = RerankingResponse.model_validate_json(clean_json_string(content))

            score_map = {item.index: item.score for item in ranking_data.rankings}
            scored_chunks = [
                RetrievedChunk(
                    chunk=item.chunk,
                    score=float(score_map.get(idx, 0.0)),
                    retrieval_method="reranked",
                )
                for idx, item in enumerate(retrieved_chunks)
            ]
            scored_chunks.sort(key=lambda x: x.score, reverse=True)
            return scored_chunks

        except Exception as e:
            print(f"Reranking failed: {e}. Falling back to RRF rankings.")
            return retrieved_chunks


