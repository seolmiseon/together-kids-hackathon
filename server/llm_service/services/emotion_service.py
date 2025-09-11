import requests
import json
import logging
from typing import Dict, Optional
from datetime import datetime
from .prompt_service import prompt_service_instance
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(env_path)
print(f"Loading .env from: {env_path}")


logger = logging.getLogger(__name__)


class EmotionAnalysisService:
    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
        if not self.hf_token:
            logger.warning(
                "HUGGINGFACE_API_TOKEN not found, will use fallback emotion analysis"
            )
            self.hf_token = None

        self.headers = (
            {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json",
            }
            if self.hf_token
            else None
        )
        self.prompt_service = prompt_service_instance
        self.openai_client = AsyncOpenAI() if os.getenv("OPENAI_API_KEY") else None
        # 한국어 감정 분석 모델들
        self.emotion_models = {
            "korean": "j-hartmann/emotion-english-distilroberta-base",
            #    "korean": "nlptown/bert-base-multilingual-uncased-sentiment",
        }

        # 육아 관련 감정 매핑
        self.parenting_emotion_map = {
            "joy": {"korean": "기쁨", "stress_level": 1, "advice_type": "celebration"},
            "sadness": {
                "korean": "슬픔/우울",
                "stress_level": 4,
                "advice_type": "comfort",
            },
            "anger": {
                "korean": "짜증/분노",
                "stress_level": 5,
                "advice_type": "stress_relief",
            },
            "fear": {
                "korean": "걱정/불안",
                "stress_level": 4,
                "advice_type": "reassurance",
            },
            "surprise": {
                "korean": "놀람",
                "stress_level": 2,
                "advice_type": "information",
            },
            "disgust": {
                "korean": "피로/지침",
                "stress_level": 3,
                "advice_type": "rest",
            },
        }


async def analyze_emotion_quick(self, text: str) -> Dict:
    """
    빠른 감정 분석 (HuggingFace 모델만 사용)
    프롬프트 없이 단순 분류만 수행
    """
    if not self.hf_token:
        return self._get_fallback_emotion_with_keywords(text)

    try:
        model_url = self.emotion_models["korean"]
        api_url = f"https://api-inference.huggingface.co/models/{model_url}"

        payload = {"inputs": text}

        response = requests.post(
            api_url, headers=self.headers, json=payload, timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return self._process_emotion_result(result, text)
        else:
            logger.error(f"HuggingFace API error: {response.status_code}")
            return self._get_fallback_emotion_with_keywords(text)

    except Exception as e:
        logger.error(f"Emotion analysis failed: {str(e)}")
        return self._get_fallback_emotion_with_keywords(text)

    def _get_fallback_emotion_with_keywords(self, text: str) -> Dict:

        emotion_keywords = {
            "기쁨": ["기뻐", "행복", "좋아", "웃어", "즐거", "신나"],
            "슬픔": ["슬퍼", "우울", "눈물", "힘들", "속상"],
            "분노": ["화나", "짜증", "열받", "빡쳐", "성가"],
            "걱정": ["걱정", "불안", "두려", "무서", "염려"],
            "피로": ["지쳐", "피곤", "힘들", "못하겠", "포기"],
        }

        detected_emotion = "중립"
        max_score = 0

        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
        if score > max_score:
            max_score = score
            detected_emotion = emotion

        # 감정을 영어로 매핑
        korean_to_english = {
            "기쁨": "joy",
            "슬픔": "sadness",
            "분노": "anger",
            "걱정": "fear",
            "피로": "disgust",
            "중립": "neutral",
        }

        emotion_en = korean_to_english.get(detected_emotion, "neutral")
        confidence = min(0.8, max_score * 0.2) if max_score > 0 else 0.5

        mapped_emotion = self.parenting_emotion_map.get(
            emotion_en, {"korean": "중립", "stress_level": 3, "advice_type": "general"}
        )

        return {
            "emotion": mapped_emotion["korean"],
            "emotion_en": emotion_en,
            "confidence": confidence,
            "stress_level": self._calculate_parenting_stress(
                mapped_emotion, confidence, text
            ),
            "advice_type": mapped_emotion.get("advice_type", "general"),
            "parenting_context": self._detect_parenting_context(text),
            "timestamp": datetime.now().isoformat(),
            "original_text_length": len(text),
            "fallback": True,
        }


# 기존 analyze_for_community_matching 위에 추가
async def analyze_emotion_detailed(self, text: str, use_llm: bool = False) -> Dict:
    """
    상세 감정 분석 (LLM + 기존 HuggingFace 결합)
    """
    # 1단계: 기존 빠른 분석
    quick_result = await self.analyze_emotion_quick(text)

    # 2단계: 확신도가 낮거나 LLM 요청시 정밀 분석
    if use_llm and self.openai_client and quick_result.get("confidence", 0) < 0.8:
        llm_result = await self._llm_emotion_analysis(text, quick_result)
        return {**quick_result, "llm_enhancement": llm_result}

    return quick_result


async def _llm_emotion_analysis(self, text: str, base_result: Dict) -> Dict:
    """LLM을 활용한 정밀 감정 분석"""
    try:
        system_prompt = self.prompt_service.get_system_prompt(
            intent="emotion", context_info=f"기초 분석 결과: {base_result}"
        )

        messages = [
            system_prompt,
            {"role": "user", "content": f"분석할 텍스트: {text}"},
        ]

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, temperature=0.3
        )

        return {
            "detailed_analysis": response.choices[0].message.content,
            "method": "llm_enhanced",
        }

    except Exception as e:
        logger.error(f"LLM emotion analysis failed: {e}")
        return {"error": str(e), "method": "llm_failed"}


async def analyze_for_community_matching(self, message_data: Dict) -> Dict:
    """커뮤니티 매칭을 위한 감정 + 상황 분석"""
    text = message_data.get("message", "")

    # 기본 감정 분석
    emotion_result = await self.analyze_emotion_detailed(text, use_llm=True)

    # 커뮤니티 매칭 정보 추가
    matching_info = {
        "location": message_data.get("location", ""),
        "parenting_stage": message_data.get("parenting_stage", ""),
        "preferred_group_type": self._suggest_group_type(emotion_result),
        "support_priority": self._determine_support_priority(emotion_result),
        "matching_urgency": self._calculate_matching_urgency(emotion_result),
    }

    return {**emotion_result, "community_matching": matching_info}

    def _suggest_group_type(self, emotion_result: Dict) -> str:
        """감정 상태에 따른 추천 그룹 유형"""

    stress_level = emotion_result.get("stress_level", 3)
    advice_type = emotion_result.get("advice_type", "general")

    if stress_level >= 4:
        return "support_group"  # 지지 그룹
    elif advice_type == "celebration":
        return "sharing_group"  # 경험 공유 그룹
    else:
        return "general_community"  # 일반 커뮤니티

    def _determine_support_priority(self, emotion_result: Dict) -> str:
        """지원 우선순위 결정"""

    stress_level = emotion_result.get("stress_level", 3)
    confidence = emotion_result.get("confidence", 0.5)

    if stress_level >= 4 and confidence > 0.7:
        return "immediate"  # 즉시 지원
    elif stress_level >= 3:
        return "moderate"  # 보통 우선순위
    else:
        return "low"  # 낮은 우선순위

    def _calculate_matching_urgency(self, emotion_result: Dict) -> str:

        stress_level = emotion_result.get("stress_level", 3)
        advice_type = emotion_result.get("advice_type", "general")
        confidence = emotion_result.get("confidence", 0.5)

    # 긴급도 점수 계산
    urgency_score = 0

    if stress_level >= 4:
        urgency_score += 2
    elif stress_level >= 3:
        urgency_score += 1

    if advice_type in ["stress_relief", "comfort"]:
        urgency_score += 1

    if confidence > 0.8:
        urgency_score += 1

    # 긴급도 결정
    if urgency_score >= 4:
        return "urgent"  # 긴급
    elif urgency_score >= 2:
        return "moderate"  # 보통
    else:
        return "low"  # 낮음

    def _process_emotion_result(self, hf_result: list, original_text: str) -> Dict:
        """HuggingFace 결과를 육아 맞춤형으로 가공"""

    try:
        if not hf_result or len(hf_result) == 0:
            return self._get_fallback_emotion_with_keywords(original_text)

        # 가장 높은 확률의 감정 선택
        top_emotion = max(hf_result[0], key=lambda x: x["score"])
        emotion_label = top_emotion["label"].lower()
        confidence = top_emotion["score"]

        # 육아 맞춤 감정 매핑
        mapped_emotion = self._map_to_parenting_emotion(emotion_label)

        # 육아 스트레스 레벨 계산
        stress_level = self._calculate_parenting_stress(
            mapped_emotion, confidence, original_text
        )

        # 맞춤 조언 타입 결정
        advice_type = mapped_emotion.get("advice_type", "general")

        return {
            "emotion": mapped_emotion["korean"],
            "emotion_en": emotion_label,
            "confidence": round(confidence, 3),
            "stress_level": stress_level,
            "advice_type": advice_type,
            "parenting_context": self._detect_parenting_context(original_text),
            "timestamp": datetime.now().isoformat(),
            "original_text_length": len(original_text),
        }

    except Exception as e:
        logger.error(f"Processing emotion result failed: {str(e)}")
        return self._get_fallback_emotion_with_keywords(original_text)

    # 나머지 기존 메서드들은 그대로...
    def _map_to_parenting_emotion(self, emotion_label: str) -> Dict:
        """감정을 육아 맥락에 맞게 매핑"""

    emotion_mapping = {
        "sadness": "sadness",
        "sad": "sadness",
        "anger": "anger",
        "angry": "anger",
        "fear": "fear",
        "fearful": "fear",
        "worried": "fear",
        "joy": "joy",
        "happy": "joy",
        "excited": "joy",
        "surprise": "surprise",
        "surprised": "surprise",
        "disgust": "disgust",
        "tired": "disgust",
        "exhausted": "disgust",
    }

    mapped_key = emotion_mapping.get(emotion_label, "sadness")
    return self.parenting_emotion_map.get(
        mapped_key, self.parenting_emotion_map["sadness"]
    )

    def _calculate_parenting_stress(
        self, emotion_data: Dict, confidence: float, text: str
    ) -> int:
        """육아 스트레스 레벨 계산 (1-5점)"""

    base_stress = emotion_data.get("stress_level", 3)

    stress_keywords = {
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

    keyword_weight = 0
    for keyword, weight in stress_keywords.items():
        if keyword in text:
            keyword_weight += weight

    confidence_factor = confidence if confidence > 0.7 else 0.5
    final_stress = min(5, max(1, int(base_stress + keyword_weight * confidence_factor)))

    return final_stress

    def _detect_parenting_context(self, text: str) -> str:
        """육아 상황 맥락 감지"""

    context_keywords = {
        "수유": "feeding",
        "기저귀": "diaper",
        "잠": "sleep",
        "울": "crying",
        "아파": "health",
        "놀이": "play",
        "유치원": "daycare",
        "학교": "school",
        "병원": "medical",
        "예방접종": "vaccination",
    }

    for keyword, context in context_keywords.items():
        if keyword in text:
            return context
    return "general"


async def get_emotion_based_advice(self, emotion_result: Dict) -> str:
    """감정 분석 결과를 바탕으로 맞춤 조언 생성"""
    # 기존 조언 로직 그대로...
    advice_templates = {
        "comfort": [
            "힘든 시간을 보내고 계시는군요. 잠시 휴식을 취하시는 건 어떨까요?",
            "육아는 정말 어려운 일이에요. 주변의 도움을 받는 것도 좋은 방법입니다.",
        ],
        "stress_relief": [
            "스트레스가 많이 쌓인 것 같아요. 근처에 산책할 수 있는 공원을 찾아보실까요?",
            "잠시 아이를 맡기고 혼자만의 시간을 가져보세요.",
        ],
        "celebration": [
            "정말 기쁜 일이네요! 이런 순간들이 육아의 보람이죠.",
            "좋은 부모가 되기 위해 노력하시는 모습이 멋져요!",
        ],
    }

    advice_type = emotion_result.get("advice_type", "general")
    if advice_type in advice_templates:
        import random

        return random.choice(advice_templates[advice_type])

    return "항상 최선을 다하고 계시는 것 같아요. 육아는 쉽지 않지만 충분히 잘하고 계십니다."


# 전역 인스턴스
emotion_service = EmotionAnalysisService()
