from langchain.embeddings import OpenAIEmbeddings 
from langchain.vectorstores import Chroma      
from typing import List, Dict, Any


class VectorService:
    def __init__(self, persist_directory: str = "chroma_db"):
        self.embeddings = OpenAIEmbeddings()
        self.persist_directory = persist_directory
        self.vector_store = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
    
    async def add_schedule_info(self, user_id: str, schedule_text: str):
        # 메타데이터에 user_id 포함
        metadata = {"user_id": user_id, "type": "schedule"}
        self.vector_store.add_texts([schedule_text], metadatas=[metadata])
        self.vector_store.persist()
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
    
async def search_similar_schedules(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        results = self.vector_store.similarity_search_with_score(query_text, k=top_k)
        # 결과를 문서와 유사도 점수 형태로 반환
        return [{"text": doc.page_content, "metadata": doc.metadata, "similarity": score} for doc, score in results]