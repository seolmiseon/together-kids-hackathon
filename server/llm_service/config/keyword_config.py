# 키워드 설정 파일 (하드코딩 제거)
from typing import Dict, List

class KeywordConfig:
    """동적 키워드 설정 클래스"""
    
    # 의도 분류 키워드 (확장 가능)
    INTENT_KEYWORDS = {
        "medical": ["아파", "병원", "응급", "열", "감기", "의사", "약국"],
        "schedule": ["스케줄", "등원", "시간", "일정", "계획", "예약"],
        "place": ["어디", "추천", "놀이터", "갈만한", "좋은곳", "장소"],
        "general": []  # 기타
    }
    
    # 장소 카테고리별 키워드 (확장 가능)
    PLACE_KEYWORDS = {
        "education": ["도서관", "학원", "문화센터", "박물관", "체험관"],
        "play": ["놀이터", "키즈카페", "놀이방", "키즈존", "테마파크"],
        "sports": ["수영장", "체육관", "공원", "운동장", "스포츠센터"],
        "food": ["카페", "식당", "푸드코트", "베이커리", "아이스크림"],
        "medical": ["병원", "소아과", "치과", "약국", "응급실"],
        "shopping": ["마트", "백화점", "쇼핑몰", "장난감가게", "키즈샵"],
        "care": ["어린이집", "유치원", "초등학교", "돌봄센터"]
    }
    
    # 사용자 프로필별 우선순위 (개인화)
    USER_PREFERENCES = {
        "default": ["키즈카페", "놀이터", "도서관"],
        "active": ["공원", "수영장", "체육관"],
        "educational": ["도서관", "박물관", "문화센터"],
        "social": ["키즈카페", "놀이방", "커뮤니티센터"]
    }

    @classmethod
    def get_intent_keywords(cls) -> Dict[str, List[str]]:
        return cls.INTENT_KEYWORDS
    
    @classmethod  
    def get_place_keywords(cls) -> Dict[str, List[str]]:
        return cls.PLACE_KEYWORDS
    
    @classmethod
    def get_user_preferences(cls, user_type: str = "default") -> List[str]:
        return cls.USER_PREFERENCES.get(user_type, cls.USER_PREFERENCES["default"])