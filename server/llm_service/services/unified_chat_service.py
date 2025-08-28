from typing import List, Dict, Any, Optional
from datetime import datetime

from .vector_service import VectorService
from .session_manager import SessionManager
from .openai_service import OpenAIService
from .prompt_service import prompt_service_instance



class UnifiedChatService:
    def __init__(self):
        self.vector_service = VectorService()
        self.openai_service = OpenAIService()
        self.prompt_service = prompt_service_instance
        self.session_manager = SessionManager()
        
        # 통합 키워드 분류 (중복 제거)
        self.unified_keywords = {
            "medical": [
                "아프다", "열", "반점", "기침", "콧물", "설사", "구토",
                "피부", "발진", "병원", "약", "진료", "응급", "아파서", 
                "몸살", "감기", "열", "병원", "늦겠어", "급한일"
            ],
            "schedule": [
                "스케줄", "등원", "하원", "조절", "변경", "도움",
                "회사", "출장", "바꾸고", "대신", "못가요", "어려워요"
            ]
            
        }
        
        # 긴급도 키워드
        self.urgency_keywords = {
            "high": [
                "응급", "급해요", "즉시", "당장", "119", "응급실",
                "고열", "39도", "40도", "의식", "경련", "토혈"
            ],
            "medium": [
                "빨리", "오늘", "병원", "아파요", "힘들어요"
            ]
        }
    
    def classify_intent_and_urgency(self, message: str) -> Dict[str, str]:     
        # 의도 분류
        intent = "general"
        for category, keywords in self.unified_keywords.items():
            if any(keyword in message for keyword in keywords):
                intent = category
                break
        
        # 긴급도 분류
        urgency = "low"
        for level, keywords in self.urgency_keywords.items():
            if any(keyword in message for keyword in keywords):
                urgency = level
                break
        
        # 의료 관련은 기본 medium
        if intent == "medical" and urgency == "low":
            urgency = "medium"
        
        return {"intent": intent, "urgency": urgency}
    
    async def process_message(self, user_id: str, message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        # 의도 및 긴급도 분석
        classification = self.classify_intent_and_urgency(message)
        intent = classification["intent"]
        urgency = classification["urgency"]
        
       # 2. SessionManager를 사용해 이전 대화 기록을 가져옵니다.
        conversation_history = self.session_manager.get_conversation_history(user_id)
        
        # 3. VectorService를 사용해 RAG를 위한 참고 정보를 검색합니다.
        context_info = await self.vector_service.search_similar_documents(message)

        # 4. PromptService를 사용해 최종 시스템 프롬프트를 조합합니다.
        system_prompt_dict = self.prompt_service.get_system_prompt(intent, context_info)
        
        # 5. 최종 대화 메시지 목록을 구성합니다.
        messages_for_api = [system_prompt_dict] + conversation_history + [{"role": "user", "content": message}]

        # 6. OpenAI API를 호출하여 AI 응답을 생성합니다.
        ai_response_content = await self.openai_service.generate_chat_response(messages_for_api)
        
        # 7. SessionManager를 사용해 새로운 대화 내용을 저장합니다.
        new_history = conversation_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": ai_response_content}
        ]
        self.session_manager.save_conversation_history(user_id, new_history)

        # 8. 최종 결과를 메인 백엔드로 반환합니다.
        return {
            "user_id": user_id,
            "response": ai_response_content,
            "intent": intent,
            "urgency": urgency,
            "timestamp": datetime.now().isoformat()
        }
