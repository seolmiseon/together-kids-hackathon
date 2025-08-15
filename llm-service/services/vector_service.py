
import json
import numpy as np
from typing import List, Dict, Any
from services.openai_service import OpenAIService

class VectorService:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.vector_store = []
        self.documents = []
    
    async def add_schedule_info(self, user_id: str, schedule_text: str):
        """스케줄 정보를 벡터DB에 추가"""
        embedding = await self.openai_service.generate_single_embedding(schedule_text)
        
        self.vector_store.append(embedding)
        self.documents.append({
            "user_id": user_id,
            "text": schedule_text,
            "type": "schedule"
        })
        
        print(f"스케줄 저장됨: {user_id} - {schedule_text}")
    
    async def search_similar_schedules(self, query_text: str, top_k: int = 3):
        if not self.vector_store:
            return []
        
        query_embedding = await self.openai_service.generate_single_embedding(query_text)
        
        similarities = []
        for i, stored_embedding in enumerate(self.vector_store):
            similarity = self._calculate_cosine_similarity(query_embedding, stored_embedding)
            similarities.append((i, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for i, similarity in similarities[:top_k]:
            doc = self.documents[i]
            doc["similarity"] = similarity
            results.append(doc)
        
        return results
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
