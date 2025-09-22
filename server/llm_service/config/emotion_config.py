# 감정 분석 설정 파일 (하드코딩 제거)
from typing import Dict, List

class EmotionConfig:
    """감정 분석 설정 클래스"""
    
    # 육아 관련 감정 매핑
    PARENTING_EMOTION_MAP = {
        "joy": {"korean": "기쁨", "stress_level": 1, "advice_type": "celebration"},
        "sadness": {"korean": "슬픔/우울", "stress_level": 4, "advice_type": "comfort"},
        "anger": {"korean": "짜증/분노", "stress_level": 5, "advice_type": "stress_relief"},
        "fear": {"korean": "걱정/불안", "stress_level": 4, "advice_type": "reassurance"},
        "surprise": {"korean": "놀람", "stress_level": 2, "advice_type": "information"},
        "disgust": {"korean": "피로/지침", "stress_level": 3, "advice_type": "rest"},
    }
    
    # 한국어 감정 키워드
    KOREAN_EMOTION_KEYWORDS = {
        "기쁨": ["기뻐", "행복", "좋아", "웃어", "즐거", "신나"],
        "슬픔": ["슬퍼", "우울", "눈물", "힘들", "속상"],
        "분노": ["화나", "짜증", "열받", "빡쳐", "성가"],
        "걱정": ["걱정", "불안", "두려", "무서", "염려"],
        "피로": ["지쳐", "피곤", "힘들", "못하겠", "포기"],
    }
    
    # 한국어-영어 감정 매핑
    KOREAN_TO_ENGLISH_EMOTIONS = {
        "기쁨": "joy",
        "슬픔": "sadness", 
        "분노": "anger",
        "걱정": "fear",
        "피로": "disgust",
    }
    
    # 감정 분석 모델 설정
    EMOTION_MODELS = {
        "korean": "j-hartmann/emotion-english-distilroberta-base",
        "multilingual": "nlptown/bert-base-multilingual-uncased-sentiment",
    }
    
    # 감정별 조언 타입
    ADVICE_TYPES = {
        "celebration": "축하와 격려",
        "comfort": "위로와 공감",
        "stress_relief": "스트레스 해소",
        "reassurance": "안심과 지지",
        "information": "정보 제공",
        "rest": "휴식 권유"
    }
    
    # 스트레스 키워드 가중치
    STRESS_KEYWORDS = {
        "힘들": 1,
        "지쳐": 1,
        "못하겠": 2,
        "우울": 1,
        "화나": 1,
        "짜증": 1,
        "스트레스": 1,
        "포기": 2,
        "울어": 0.5,
        "아파": 1,
        "걱정": 0.5,
        "불안": 1,
    }

    @classmethod
    def get_parenting_emotions(cls) -> Dict:
        return cls.PARENTING_EMOTION_MAP
    
    @classmethod
    def get_korean_keywords(cls) -> Dict[str, List[str]]:
        return cls.KOREAN_EMOTION_KEYWORDS
        
    @classmethod
    def get_korean_to_english_mapping(cls) -> Dict[str, str]:
        return cls.KOREAN_TO_ENGLISH_EMOTIONS
        
    @classmethod
    def get_emotion_models(cls) -> Dict[str, str]:
        return cls.EMOTION_MODELS
        
    @classmethod
    def get_advice_types(cls) -> Dict[str, str]:
        return cls.ADVICE_TYPES
        
    @classmethod
    def get_stress_keywords(cls) -> Dict[str, float]:
        return cls.STRESS_KEYWORDS