from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from llm_service.services.vector_service import VectorService
from llm_service.services.openai_service import OpenAIService
from llm_service.services.prompt_service import PromptService
from llm_service.services.session_manager import SessionManager
from llm_service.models.community_models import HelpRequest, CommunityResponse, HelpRequestCreate


class UnifiedChatService:
    def __init__(self):
        self.vector_service = VectorService()
        self.openai_service = OpenAIService()
        self.prompt_service = PromptService()
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
            ],
            "childcare": [
                "육아", "아이", "놀이", "수면", "이유식", "기저귀",
                "발달", "성장", "교육", "훈육", "습관", "수유", "잠"
            ],
            "community": [
                "함께", "공동", "도움", "부탁", "나눔", "품앗이",
                "이웃", "아파트", "단지", "맘카페"
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
    
    async def process_message(self, user_id: str, message: str, chat_mode: str = "auto") -> Dict[str, Any]:
        # 의도 및 긴급도 분석
        classification = self.classify_intent_and_urgency(message)
        intent = classification["intent"]
        urgency = classification["urgency"]
        
        # 모드 결정
        if chat_mode == "auto":
            # 긴급도가 높으면 커뮤니티 우선, 일반적이면 AI 우선
            if urgency == "high":
                chat_mode = "community_first"
            elif any(keyword in message for keyword in ["경험", "후기", "추천", "어디", "누구"]):
                chat_mode = "community_first"
            else:
                chat_mode = "ai_first"
        
        result = {
            "user_id": user_id,
            "message": message,
            "intent": intent,
            "urgency": urgency,
            "mode": chat_mode,
            "responses": []
        }
        
        # 모드별 처리
        if chat_mode == "ai_only" or chat_mode == "ai_first":
            ai_response = await self._process_ai_chat(user_id, message, intent, urgency)
            result["responses"].append({
                "type": "ai",
                "content": ai_response,
                "timestamp": datetime.now()
            })
        
        if chat_mode == "community_only" or chat_mode == "community_first" or urgency == "high":
            community_response = await self._process_community_request(user_id, message, intent, urgency)
            result["responses"].append({
                "type": "community",
                "content": community_response,
                "timestamp": datetime.now()
            })
        
        return result
    
    async def _process_ai_chat(self, user_id: str, message: str, intent: str, urgency: str) -> Dict[str, Any]: 
        # 대화 기록 가져오기
        conversation_history = self.session_manager.get_conversation_history(user_id)
        
        # 사용자 메시지 추가
        conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # RAG 검색 및 프롬프트 향상
        enhanced_history = await self._enhance_with_context(
            message, user_id, conversation_history, intent
        )
        
        # AI 응답 생성
        ai_response = await self.openai_service.generate_chat_response(enhanced_history)
        
        # AI 응답을 대화 기록에 추가
        enhanced_history.append({
            "role": "assistant", 
            "content": ai_response
        })
        
        # 세션 저장
        self.session_manager.save_conversation_history(user_id, enhanced_history)
        
        return {
            "response": ai_response,
            "context_used": True if intent != "general" else False,
            "suggestion": self._get_suggestion(intent, urgency)
        }
    
    async def _process_community_request(self, user_id: str, message: str, intent: str, urgency: str) -> Dict[str, Any]:  
        # 긴급 상황이면 즉시 도움 요청 생성
        if urgency == "high":
            # 응급 상황 AI 판단
            emergency_assessment = await self.openai_service.emergency_assessment(message)
            
            # 긴급 도움 요청 생성
            help_request = await self._create_help_request(
                user_id, 
                f"긴급: {message}", 
                message, 
                intent, 
                urgency
            )
            
            return {
                "status": "emergency_alert_sent",
                "request_id": help_request.request_id,
                "ai_assessment": emergency_assessment,
                "message": "긴급 알림이 모든 엄마들에게 전송되었습니다!",
                "recommendation": "AI 분석을 참고하시고, 필요시 즉시 119에 신고하세요."
            }
        
        else:
            # 일반 도움 요청
            help_request = await self._create_help_request(
                user_id,
                f"{intent} 관련 도움 요청",
                message,
                intent,
                urgency
            )
            
            # 관련 경험 있는 엄마들 찾기
            similar_experiences = await self._find_similar_experiences(intent, message)
            
            return {
                "status": "help_request_created",
                "request_id": help_request.request_id,
                "similar_experiences": similar_experiences,
                "message": "관련 경험 있는 엄마들에게 알림을 보냈어요! 곧 답변이 올 거예요 💕",
                "estimated_response_time": "평균 10분"
            }
    
    async def _enhance_with_context(self, message: str, user_id: str, conversation_history: List[Dict], intent: str) -> List[Dict]:
        
        # 벡터 검색으로 관련 정보 찾기
        if intent in ["schedule", "medical"]:
            search_results = await self.vector_service.search_similar_schedules(message)
            
            if search_results:
                context_info = "\n\n관련 경험 정보:\n"
                for result in search_results:
                    context_info += f"- {result['user_id']}: {result['text']}\n"
                
                # 시스템 프롬프트 향상
                if len(conversation_history) == 1:
                    system_prompt = self.prompt_service.get_prompt_for_intent(intent, context_info)
                    conversation_history.insert(0, system_prompt)
                elif conversation_history[0]["role"] == "system":
                    conversation_history[0]["content"] += context_info
        
        # 시스템 프롬프트가 없으면 추가
        if not conversation_history or conversation_history[0]["role"] != "system":
            system_prompt = self.prompt_service.get_prompt_for_intent(intent)
            conversation_history.insert(0, system_prompt)
        
        return conversation_history
    
    async def _create_help_request(self, user_id: str, title: str, message: str, category: str, urgency: str) -> HelpRequest:
        """도움 요청 생성"""
        
        help_request = HelpRequest(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            urgency=urgency,
            created_at=datetime.now(),
            status="active"
        )
        
        # Redis에 저장
        await self._save_help_request(help_request)
        
        # 관련 엄마들에게 알림
        await self._notify_relevant_moms(help_request)
        
        return help_request
    
    async def _save_help_request(self, help_request: HelpRequest):
        """도움 요청 저장"""
        key = f"help_request:{help_request.request_id}"
        self.session_manager.redis_client.hset(key, mapping={
            "user_id": help_request.user_id,
            "title": help_request.title,
            "message": help_request.message,
            "category": help_request.category,
            "urgency": help_request.urgency,
            "created_at": help_request.created_at.isoformat(),
            "status": help_request.status
        })
        
        # 24시간 후 만료
        self.session_manager.redis_client.expire(key, 86400)
    
    async def _notify_relevant_moms(self, help_request: HelpRequest):
        # 실제 구현에서는 푸시 알림, 이메일 등
        notification = {
            "type": "help_request",
            "request_id": help_request.request_id,
            "category": help_request.category,
            "urgency": help_request.urgency,
            "title": help_request.title,
            "message": "새로운 도움 요청이 있어요! 💝"
        }
        
        # 모든 사용자에게 알림 (실제로는 관련 사용자만)
        all_users = ["mom1", "mom2", "mom3"]  # 실제로는 DB에서 조회
        for user_id in all_users:
            if user_id != help_request.user_id:  # 본인 제외
                notification_key = f"notifications:{user_id}"
                self.session_manager.redis_client.lpush(notification_key, str(notification))
    
    async def _find_similar_experiences(self, intent: str, message: str) -> List[Dict]:
        """유사 경험 찾기"""
        # 벡터 검색으로 유사한 경험 찾기
        if intent in ["schedule", "medical"]:
            return await self.vector_service.search_similar_schedules(message)
        return []
    
    def _get_suggestion(self, intent: str, urgency: str) -> str:
        if urgency == "high":
            return "응급 상황으로 보입니다. 커뮤니티에도 도움을 요청하시겠어요?"
        elif intent == "medical":
            return "다른 엄마들의 경험도 들어보시겠어요?"
        elif intent == "schedule":
            return "비슷한 상황의 엄마들과 스케줄을 공유해보세요!"
        else:
            return "더 구체적인 도움이 필요하시면 커뮤니티에 질문해보세요!"
