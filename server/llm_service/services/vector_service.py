from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma   
from typing import List, Dict, Any
from datetime import datetime
import logging


class VectorService:
    def __init__(self, persist_directory: str = "chroma_db"):
        self.embeddings = OpenAIEmbeddings()
        self.persist_directory = persist_directory
        self.vector_store = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
    
    async def add_schedule_info(self, user_id: str, schedule_text: str, intent: str = "schedule", urgency: str = "low"):
    # 임베딩 단위 길이 체크 (예: 20~300자)
        if not (20 <= len(schedule_text) <= 300):
            logging.warning(f"임베딩 단위 길이 초과/미만: {len(schedule_text)}자")
            return
        try:
          metadata = {"user_id": user_id, "type": "schedule", "intent": intent, "urgency": urgency, "created_at": datetime.now().isoformat()}
          self.vector_store.add_texts([schedule_text], metadatas=[metadata])
          self.vector_store.persist()
          logging.info(f"스케줄 저장됨: {user_id} - {schedule_text}")
        except Exception as e:
          logging.error(f"스케줄 저장 실패: {e}")
    
    async def search_similar_schedules(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        results = self.vector_store.similarity_search_with_score(query_text, k=top_k)
        return [{"text": doc.page_content, "metadata": doc.metadata, "similarity": score} for doc, score in results]
    
    async def search_similar_documents(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """통합 문서 검색 메서드"""
        return await self.search_similar_schedules(query_text, top_k)
    
