import datetime
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import hashlib


class CacheService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./data/chroma_cache")
        self.cache_collection = self.client.get_or_create_collection(
            name="answer_cache", metadata={"hnsw:space": "cosine"}
        )
        self.openai = OpenAI()

    def get_cache_key(self, query: str) -> str:
        """질문을 해시값으로 변환 (정확히 같은 질문 판별)"""
        return hashlib.md5(query.encode()).hexdigest()

    def search_similar_cache(self, query: str, threshold: float = 0.90) -> dict | None:
        """유사한 캐시된 답변 검색"""

        # 1. 질문을 벡터로 변환
        embedding = (
            self.openai.embeddings.create(model="text-embedding-3-small", input=query)
            .data[0]
            .embedding
        )

        # 2. ChromaDB에서 유사 질문 검색
        results = self.cache_collection.query(query_embeddings=[embedding], n_results=1)

        # 3. 유사도 체크
        if results["distances"][0]:
            similarity = 1 - results["distances"][0][0]  # cosine distance → similarity

            if similarity >= threshold:
                return {
                    "cached": True,
                    "answer": results["documents"][0][0],
                    "similarity": similarity,
                    "original_query": results["metadatas"][0][0]["query"],
                }

        return None

    def save_cache(self, query: str, answer: str):
        """새 답변을 캐시에 저장"""

        # 1. 질문을 벡터로 변환
        embedding = (
            self.openai.embeddings.create(model="text-embedding-3-small", input=query)
            .data[0]
            .embedding
        )

        # 2. ChromaDB에 저장
        cache_key = self.get_cache_key(query)

        self.cache_collection.upsert(
            ids=[cache_key],
            embeddings=[embedding],
            documents=[answer],
            metadatas=[{"query": query, "timestamp": datetime.now().isoformat()}],
        )
