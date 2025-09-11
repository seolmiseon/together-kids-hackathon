
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma   
from typing import List, Dict, Any
from datetime import datetime
import logging
import os


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
    
    async def add_community_info(self, community_data: Dict[str, Any]):
        """커뮤니티 정보를 벡터 DB에 저장"""
        try:
            # 커뮤니티 정보를 검색 가능한 텍스트로 변환
            community_text = self._generate_community_vector_text(community_data)
            
            # 메타데이터 생성
            metadata = {
                "community_id": community_data.get("community_id"),
                "type": "community",
                "name": community_data.get("name"),
                "location": community_data.get("location"),
                "target_ages": ",".join(community_data.get("target_ages", [])),
                "focus_areas": ",".join(community_data.get("focus_areas", [])),
                "member_count": community_data.get("member_count", 0),
                "created_at": datetime.now().isoformat()
            }
            
            # 벡터 DB에 저장
            self.vector_store.add_texts([community_text], metadatas=[metadata])
            self.vector_store.persist()
            logging.info(f"커뮤니티 저장됨: {community_data.get('name')}")
            
        except Exception as e:
            logging.error(f"커뮤니티 저장 실패: {e}")
    
    def _generate_community_vector_text(self, community_data: Dict[str, Any]) -> str:
        """커뮤니티 데이터를 벡터화용 텍스트로 변환"""
        text_parts = []
        
        # 기본 정보
        if community_data.get("name"):
            text_parts.append(f"커뮤니티명: {community_data['name']}")
        
        if community_data.get("location"):
            text_parts.append(f"지역: {community_data['location']}")
        
        if community_data.get("target_ages"):
            text_parts.append(f"대상연령: {', '.join(community_data['target_ages'])}")
        
        if community_data.get("focus_areas"):
            text_parts.append(f"주요관심사: {', '.join(community_data['focus_areas'])}")
        
        if community_data.get("activities"):
            text_parts.append(f"주요활동: {', '.join(community_data['activities'])}")
        
        if community_data.get("description"):
            text_parts.append(f"설명: {community_data['description']}")
        
        # 추가 정보
        if community_data.get("member_count"):
            text_parts.append(f"멤버수: {community_data['member_count']}명")
        
        if community_data.get("meeting_frequency"):
            text_parts.append(f"모임빈도: {community_data['meeting_frequency']}")
        
        if community_data.get("activity_style"):
            text_parts.append(f"활동스타일: {', '.join(community_data['activity_style'])}")
        
        return " | ".join(text_parts)
    
    async def search_communities_by_profile(self, user_profile: Dict[str, Any], area: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """사용자 프로필 기반 커뮤니티 검색"""
        try:
            # 사용자 프로필을 검색 쿼리로 변환
            query_text = self._generate_search_query(user_profile, area)
            
            # 커뮤니티만 필터링하여 검색
            results = self.vector_store.similarity_search_with_score(
                query_text, 
                k=top_k*2,  # 더 많이 검색해서 필터링
                filter={"type": "community"}
            )
            
            # 지역 필터링 및 포맷팅
            filtered_results = []
            for doc, score in results:
                metadata = doc.metadata
                # 지역 매칭 확인
                if area.lower() in metadata.get("location", "").lower():
                    community_info = {
                        "community_id": metadata.get("community_id"),
                        "name": metadata.get("name"),
                        "location": metadata.get("location"),
                        "target_ages": metadata.get("target_ages", "").split(",") if metadata.get("target_ages") else [],
                        "focus_areas": metadata.get("focus_areas", "").split(",") if metadata.get("focus_areas") else [],
                        "member_count": metadata.get("member_count", 0),
                        "similarity_score": 1 - score,  # 점수 변환 (높을수록 유사)
                        "content": doc.page_content
                    }
                    filtered_results.append(community_info)
                
                if len(filtered_results) >= top_k:
                    break
            
            return filtered_results
            
        except Exception as e:
            logging.error(f"커뮤니티 검색 실패: {e}")
            return []
    
    def _generate_search_query(self, user_profile: Dict[str, Any], area: str) -> str:
        """사용자 프로필을 검색 쿼리로 변환"""
        query_parts = []
        
        # 지역 정보
        query_parts.append(f"지역: {area}")
        
        # 육아 단계
        if user_profile.get("parenting_stage"):
            query_parts.append(f"육아단계: {user_profile['parenting_stage']}")
        
        # 교육 관심사
        if user_profile.get("education_interests"):
            query_parts.append(f"교육관심사: {', '.join(user_profile['education_interests'])}")
        
        # 현재 니즈
        if user_profile.get("current_needs"):
            query_parts.append(f"필요한도움: {', '.join(user_profile['current_needs'])}")
        
        # 활동 선호
        if user_profile.get("activity_preferences"):
            query_parts.append(f"선호활동: {', '.join(user_profile['activity_preferences'])}")
        
        return " | ".join(query_parts)
    
    async def get_community_by_id(self, community_id: str) -> Dict[str, Any]:
        """커뮤니티 ID로 상세 정보 조회"""
        try:
            results = self.vector_store.similarity_search(
                community_id,
                k=1,
                filter={"community_id": community_id, "type": "community"}
            )
            
            if results:
                doc = results[0]
                metadata = doc.metadata
                return {
                    "community_id": metadata.get("community_id"),
                    "name": metadata.get("name"),
                    "location": metadata.get("location"),
                    "target_ages": metadata.get("target_ages", "").split(",") if metadata.get("target_ages") else [],
                    "focus_areas": metadata.get("focus_areas", "").split(",") if metadata.get("focus_areas") else [],
                    "member_count": metadata.get("member_count", 0),
                    "content": doc.page_content
                }
            return {}
            
        except Exception as e:
            logging.error(f"커뮤니티 조회 실패: {e}")
            return {}
    
