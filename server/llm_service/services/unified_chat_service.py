from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .vector_service import VectorService
from .session_manager import SessionManager
from .openai_service import OpenAIService
from .prompt_service import PromptService
from .emotion_service import emotion_service
from .location_service import location_service
from ..config.keyword_config import KeywordConfig

logger = logging.getLogger(__name__)

class UnifiedChatService:
    def __init__(self):
        self.vector_service = VectorService()
        self.openai_service = OpenAIService()
        self.prompt_service = PromptService()
        self.session_manager = SessionManager()
        self.location_service = location_service
        
    def classify_intent_and_urgency(self, message: str) -> Dict[str, str]:
        """동적 키워드 기반 의도 분류 (하드코딩 제거)"""
        intent_keywords = KeywordConfig.get_intent_keywords()
        
        # 의도별 키워드 매칭 (확장 가능)
        for intent, keywords in intent_keywords.items():
            if any(word in message for word in keywords):
                urgency = "medium" if intent == "medical" else "low"
                return {"intent": intent, "urgency": urgency}
        
        return {"intent": "general", "urgency": "low"}

    def extract_place_keywords(self, message: str) -> List[str]:
        """메시지에서 장소 관련 키워드 추출 (동적)"""
        place_keywords = []
        
        # 설정에서 모든 장소 키워드 가져오기 (하드코딩 제거)
        place_categories = KeywordConfig.get_place_keywords()
        all_place_words = []
        for category_words in place_categories.values():
            all_place_words.extend(category_words)
        
        # 메시지에서 장소 키워드 찾기
        for word in all_place_words:
            if word in message:
                place_keywords.append(word)
        
        # 장소 추천 요청 키워드 (하드코딩 제거)
        intent_keywords = KeywordConfig.get_intent_keywords()
        if any(word in message for word in intent_keywords["place"]):
            if not place_keywords:
                # AI가 동적으로 결정하도록 변경 (하드코딩 제거)
                place_keywords = self._extract_dynamic_keywords(message)
        
        return place_keywords

    def _extract_dynamic_keywords(self, message: str, user_profile: str = "default") -> List[str]:
        """AI 기반 동적 키워드 추출 (완전 설정 기반)"""
        place_categories = KeywordConfig.get_place_keywords()
        
        # 메시지 컨텍스트로 카테고리 결정
        if any(word in message for word in ["아이", "어린이", "키즈"]):
            return place_categories.get("play", [])
        elif any(word in message for word in ["운동", "체육", "활동"]):
            return place_categories.get("sports", [])
        elif any(word in message for word in ["문화", "체험", "배우"]):
            return place_categories.get("education", [])
        elif any(word in message for word in ["음식", "먹을", "맛있"]):
            return place_categories.get("food", [])
        elif any(word in message for word in ["병원", "아파", "의사"]):
            return place_categories.get("medical", [])
        else:
            # 사용자 프로필 기반 기본값
            return KeywordConfig.get_user_preferences(user_profile)

    async def process_message(
        self, user_id: str, message: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        # 의도 및 긴급도 분석
        classification = self.classify_intent_and_urgency(message)
        intent = classification["intent"]
        urgency = classification["urgency"]

        # 장소 키워드 추출
        place_keywords = self.extract_place_keywords(message)
        print(f"🔍 DEBUG: 추출된 키워드={place_keywords}")

        real_places_info = ""
        places_data = []  # 프론트엔드로 전달할 장소 데이터

        
        if place_keywords and intent == "place" and user_context.get("children"):
            print(f"🔍 DEBUG: 네이버 API 호출 시작...")
            # 사용자 위치 정보 추출
            user_lat, user_lng = self.extract_user_location(user_context)
            print(f"🔍 DEBUG: 위치 정보 lat={user_lat}, lng={user_lng}")
            if user_lat and user_lng:
                # 첫 번째 키워드로 검색 (우선순위 기반)
                search_keyword = place_keywords[0]
                print(f"🔍 DEBUG: '{search_keyword}' 키워드로 검색 중...")
                
                places = await self.location_service.search_nearby_places(search_keyword, user_lat, user_lng)
                print(f"🔍 DEBUG: 검색 결과={len(places) if places else 0}개")

                if places:
                    places_data = places  # 프론트엔드로 전달할 데이터 저장
                    real_places_info = f"\n\n=== 주변 {search_keyword} 정보 ===\n"
                    for place in places:
                        real_places_info += f"• {place['name']}\n"
                        real_places_info += f"  주소: {place['address']}\n"
                        if place["telephone"]:
                            real_places_info += f"  전화: {place['telephone']}\n"
                        if place["description"]:
                            real_places_info += f"  설명: {place['description']}\n"
                        real_places_info += "\n"
                else:
                    print("🔍 DEBUG: 검색 결과가 없음")
        else:
            print(
                f"🔍 DEBUG: API 호출 조건 미충족 - keywords={bool(place_keywords)}, intent={intent}, children={bool(user_context.get('children'))}"
            )

        # 2. SessionManager를 사용해 이전 대화 기록을 가져옵니다.
        conversation_history = self.session_manager.get_conversation_history(user_id)

        # 3. VectorService를 사용해 RAG를 위한 참고 정보를 검색합니다.
        context_info = await self.vector_service.search_similar_documents(message)

        # 4. PromptService를 사용해 최종 시스템 프롬프트를 조합합니다.
        system_prompt_dict = self.prompt_service.get_system_prompt(intent, context_info)

        # 실제 장소 정보가 있으면 시스템 프롬프트에 추가
        if real_places_info:
            system_prompt_dict["content"] += (
                real_places_info
                + "\n위 실제 장소 정보를 참고하여 구체적이고 정확한 추천을 해주세요."
            )

        # 5. 최종 대화 메시지 목록을 구성합니다.
        messages_for_api = (
            [system_prompt_dict]
            + conversation_history
            + [{"role": "user", "content": message}]
        )

        # 6. OpenAI API를 호출하여 AI 응답을 생성합니다.
        ai_response_content = await self.openai_service.generate_chat_response(
            messages_for_api
        )

        # 7. SessionManager를 사용해 새로운 대화 내용을 저장합니다.
        new_history = conversation_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": ai_response_content},
        ]
        self.session_manager.save_conversation_history(user_id, new_history)

        # 8. 최종 결과를 메인 백엔드로 반환합니다.
        result = {
            "user_id": user_id,
            "response": ai_response_content,
            "intent": intent,
            "urgency": urgency,
            "timestamp": datetime.now().isoformat(),
        }

        # 장소 검색 결과가 있으면 포함
        if places_data:
            result["places"] = places_data
            print(f"🔍 DEBUG: 응답에 장소 정보 포함됨: {len(places_data)}개")

        return result

    def extract_user_location(self, user_context: Dict[str, Any]) -> tuple:
        """사용자 컨텍스트에서 위치 정보 추출"""
        children = user_context.get("children", [])
        for child in children:
            if "location" in child:
                lat = child["location"].get("lat")
                lng = child["location"].get("lng")
                if lat and lng:
                    return lat, lng
        return None, None

    async def process_unified_chat(self, message: str, user_id: str) -> str:
        # 1. 감정 분석 추가
        emotion_result = await emotion_service.analyze_emotion_quick(message)

        # 2. 감정에 따른 조언 생성
        emotion_advice = await emotion_service.get_emotion_based_advice(emotion_result)

        # 3. 기존 AI 응답과 결합
        user_context = {"children": []}
        result = await self.process_message(user_id, message, user_context)
        ai_response = result["response"]

        # 4. 감정 기반 개선된 응답 반환
        emotion_text = emotion_result.get(
            "emotion", emotion_result.get("korean", "중립")
        )
        stress_level = emotion_result.get("stress_level", 3)

        enhanced_response = f"{ai_response}\n\n💡 감정 분석: {emotion_text} (스트레스: {stress_level}/5)\n{emotion_advice}"
        return enhanced_response
