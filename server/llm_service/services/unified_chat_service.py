from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .vector_service import VectorService
from .session_manager import SessionManager
from .openai_service import OpenAIService
from .prompt_service import PromptService
from .emotion_service import emotion_service
from .location_service import location_service
from .schedule_parser import ScheduleParser
from .query_transformer import QueryTransformer
from .group_member_service import group_member_service
from .notification_service import notification_service
from .rsvp_service import rsvp_service
from ..config.keyword_config import KeywordConfig

logger = logging.getLogger(__name__)

class UnifiedChatService:
    def __init__(self):
        self.vector_service = VectorService()
        self.openai_service = OpenAIService()
        self.prompt_service = PromptService()
        self.session_manager = SessionManager()
        self.location_service = location_service
        self.schedule_parser = ScheduleParser()  # 일정 파서 추가
        self.query_transformer = QueryTransformer()  # 쿼리 변환기 추가
        
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
        
        # 일정 관련 메시지인 경우 일정 정보 추출 및 처리 (AI 기반 동적 처리)
        schedule_info = None
        # 모든 표현을 인식할 수 있도록 AI 기반으로 의도 판단
        try:
            schedule_info = await self.schedule_parser.parse_with_ai(message)
            if schedule_info.get("has_time") or schedule_info.get("has_location") or schedule_info.get("rsvp_required"):
                logger.info(f"📅 일정 정보 추출: {schedule_info}")
                
                # 일정 정보가 추출되면 Firestore에 저장하고 그룹 멤버에게 알림 보내기
                if schedule_info.get("has_time") or schedule_info.get("has_location"):
                    try:
                        # 일정을 Firestore에 저장 (RSVP가 필요한 경우)
                        schedule_id = None
                        if schedule_info.get("rsvp_required"):
                            schedule_id = await rsvp_service.create_schedule_with_rsvp(
                                creator_id=user_id,
                                schedule_info=schedule_info
                            )
                            if schedule_id:
                                schedule_info["schedule_id"] = schedule_id
                                logger.info(f"📅 일정 저장 완료: {schedule_id}")
                        
                        # RSVP가 필요한 경우 그룹 멤버에게 알림 전송
                        if schedule_info.get("rsvp_required"):
                            # 그룹 멤버 조회
                            group_members = await group_member_service.get_group_members(user_id, user_context)
                            member_ids = [member["user_id"] for member in group_members]
                            
                            if member_ids:
                                # 알림에 schedule_id 포함
                                notification_result = await notification_service.send_schedule_notification(
                                    user_id=user_id,
                                    schedule_info=schedule_info,
                                    member_ids=member_ids
                                )
                                logger.info(f"📢 RSVP 일정 알림 전송 완료: {notification_result}")
                            else:
                                logger.info("📢 RSVP 필요한 일정이지만 알림 대상 멤버가 없습니다.")
                    except Exception as e:
                        logger.error(f"일정 저장 및 알림 전송 실패: {e}")
        except Exception as e:
            logger.error(f"일정 파싱 실패: {e}")

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
                # 자연어 쿼리에서 핵심 키워드만 추출 (Query Transformation)
                # 예: "5살 아이와 가기 좋은 공원" → "공원"
                if place_keywords:
                    # 첫 번째 키워드를 사용하되, 전체 메시지에서 더 정확한 키워드 추출 시도
                    raw_keyword = place_keywords[0]
                    # 자연어 쿼리 전체를 AI로 변환하여 더 정확한 키워드 추출
                    transformed_keyword = await self.query_transformer.transform_query(message)
                    search_keyword = transformed_keyword if transformed_keyword else raw_keyword
                else:
                    # 키워드가 없으면 메시지 전체를 변환
                    search_keyword = await self.query_transformer.transform_query(message)
                
                print(f"🔍 DEBUG: 원본 쿼리: '{message}'")
                print(f"🔍 DEBUG: 변환된 키워드: '{search_keyword}'")
                
                # 좌표 타입 검증 (Float로 강제)
                try:
                    user_lat = float(user_lat)
                    user_lng = float(user_lng)
                except (ValueError, TypeError):
                    logger.error(f"좌표 타입 오류: lat={user_lat}, lng={user_lng}")
                    user_lat, user_lng = None, None
                
                if user_lat and user_lng:
                    places = await self.location_service.search_nearby_places(
                        search_keyword, user_lat, user_lng
                    )
                print(f"🔍 DEBUG: 검색 결과={len(places) if places else 0}개")

                if places:
                    places_data = places  # 프론트엔드로 전달할 데이터 저장
                    real_places_info = f"\n\n=== 주변 {search_keyword} 정보 ===\n"
                    for place in places:
                        real_places_info += f"• {place['name']}\n"
                        real_places_info += f"  주소: {place['address']}\n"
                        if place.get("telephone"):
                            real_places_info += f"  전화: {place['telephone']}\n"
                        if place.get("description"):
                            real_places_info += f"  설명: {place['description']}\n"
                        # 좌표 정보가 있으면 표시 (메타데이터 무결성 확인용)
                        if place.get("lat") and place.get("lng"):
                            real_places_info += f"  좌표: {place['lat']:.6f}, {place['lng']:.6f}\n"
                        real_places_info += "\n"
                    
                    # 장소 정보를 ChromaDB에 저장할 때 좌표를 메타데이터에 포함 (선택적)
                    # 향후 하버사인 계산을 위해 좌표 정보 보존
                else:
                    print("🔍 DEBUG: 검색 결과가 없음")
        else:
            print(
                f"🔍 DEBUG: API 호출 조건 미충족 - keywords={bool(place_keywords)}, intent={intent}, children={bool(user_context.get('children'))}"
            )

        # 2. SessionManager를 사용해 이전 대화 기록을 가져옵니다.
        conversation_history = self.session_manager.get_conversation_history(user_id)

        # 3. VectorService를 사용해 RAG를 위한 참고 정보를 검색합니다.
        # RRF Hybrid Search 사용 (Vector + BM25 + RRF)
        context_info = await self.vector_service.search_similar_documents(
            message, top_k=5, use_hybrid=True
        )

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
