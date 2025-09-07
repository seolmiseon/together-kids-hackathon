from typing import List, Dict, Any, Optional
from datetime import datetime

from .vector_service import VectorService
from .session_manager import SessionManager
from .openai_service import OpenAIService
from .prompt_service import prompt_service_instance
from .naver_place_service import NaverPlaceService



class UnifiedChatService:
    def __init__(self):
        self.vector_service = VectorService()
        self.openai_service = OpenAIService()
        self.prompt_service = prompt_service_instance
        self.session_manager = SessionManager()
        self.naver_place_service = NaverPlaceService()
        
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
            "place": [
                "가고", "추천", "알려줘", "어디", "찾아", "근처", "주변",
                "놀이터", "수영장", "카페", "맛집", "식당", "병원", "도서관",
                "키즈카페", "공원", "박물관", "체험관", "마트", "쇼핑몰",
                "뮤지컬", "공연", "극장", "문화센터", "공연장"
            ]
        }
        
        # 장소별 검색 키워드 매핑 (네이버 API가 잘 인식하는 키워드 우선)
        self.place_keywords = {
            "놀이터": ["놀이터", "어린이놀이터", "놀이", "그네", "미끄럼틀"],
            "수영장": ["수영장", "수영", "물놀이", "워터파크"],
            "카페": ["카페", "까페", "커피", "음료", "디저트", "커피숍", "가고싶어", "가고 싶어"],
            "맛집": ["맛집", "식당", "음식", "먹을곳", "점심", "저녁"],
            "병원": ["병원", "소아과", "진료", "의원"],
            "도서관": ["도서관", "책", "독서"],
            "키즈카페": ["키즈카페", "실내놀이터", "아이놀이"],
            "공원": ["공원", "산책", "나들이"],
            "박물관": ["박물관", "전시", "체험"],
            "마트": ["마트", "쇼핑", "장보기", "마켓"],
            "뮤지컬": ["뮤지컬", "아동극"],
            "극장": ["극장", "연극", "공연장"],
            "문화센터": ["문화센터", "콘서트", "마술"]
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
    
    def extract_place_keywords(self, message: str) -> List[str]:
        """메시지에서 장소 관련 키워드 추출"""
        found_keywords = []
        
        for place_type, keywords in self.place_keywords.items():
            if any(keyword in message for keyword in keywords):
                found_keywords.append(place_type)
        
        # 중복 제거하고 반환
        return list(set(found_keywords))
    
    async def process_message(self, user_id: str, message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        # 의도 및 긴급도 분석
        classification = self.classify_intent_and_urgency(message)
        intent = classification["intent"]
        urgency = classification["urgency"]
        
        print(f"🔍 DEBUG: 메시지='{message}'")
        print(f"🔍 DEBUG: intent='{intent}', urgency='{urgency}'")
        
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
                places = await self.naver_place_service.search_nearby_places(search_keyword, user_lat, user_lng)
                print(f"🔍 DEBUG: 검색 결과={len(places) if places else 0}개")
                
                if places:
                    places_data = places  # 프론트엔드로 전달할 데이터 저장
                    real_places_info = f"\n\n=== 주변 {search_keyword} 정보 ===\n"
                    for place in places:
                        real_places_info += f"• {place['name']}\n"
                        real_places_info += f"  주소: {place['address']}\n"
                        if place['telephone']:
                            real_places_info += f"  전화: {place['telephone']}\n"
                        if place['description']:
                            real_places_info += f"  설명: {place['description']}\n"
                        real_places_info += "\n"
                else:
                    print("🔍 DEBUG: 검색 결과가 없음")
        else:
            print(f"🔍 DEBUG: API 호출 조건 미충족 - keywords={bool(place_keywords)}, intent={intent}, children={bool(user_context.get('children'))}")

       # 2. SessionManager를 사용해 이전 대화 기록을 가져옵니다.
        conversation_history = self.session_manager.get_conversation_history(user_id)
        
        # 3. VectorService를 사용해 RAG를 위한 참고 정보를 검색합니다.
        context_info = await self.vector_service.search_similar_documents(message)

        # 4. PromptService를 사용해 최종 시스템 프롬프트를 조합합니다.
        system_prompt_dict = self.prompt_service.get_system_prompt(intent, context_info)
        
        # 실제 장소 정보가 있으면 시스템 프롬프트에 추가
        if real_places_info:
            system_prompt_dict["content"] += real_places_info + "\n위 실제 장소 정보를 참고하여 구체적이고 정확한 추천을 해주세요."
        
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
        result = {
            "user_id": user_id,
            "response": ai_response_content,
            "intent": intent,
            "urgency": urgency,
            "timestamp": datetime.now().isoformat()
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
