"""
공동육아 일정 파서 서비스

자연어 메시지에서 시간, 장소, 참석자 정보를 추출하고
그룹 멤버들에게 알림을 보내며 RSVP를 수집합니다.

예시:
- "오늘 저녁 6시에 2동앞 놀이터에서 만나요 시간되는 엄빠들 나와주세요"
- "내일 오전10시부터 뒷공터에서 움직이는 놀이공원이 온데요 누구누구 갈거에요??"
- "이번주말 캐러반체험하러 가려고 참석가능한 엄빠들 어디세요?"
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ScheduleParser:
    """자연어에서 일정 정보를 추출하는 서비스"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = AsyncOpenAI(api_key=api_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API 키가 없습니다. 기본 파싱만 사용합니다.")
    
    def extract_schedule_info(self, message: str) -> Dict[str, Any]:
        """
        자연어 메시지에서 일정 정보 추출
        
        Returns:
            {
                "time": "2024-01-06 18:00",
                "location": "2동앞 놀이터",
                "activity": "놀이터 모임",
                "participants_needed": True,
                "rsvp_required": True,
                "has_time": True,
                "has_location": True
            }
        """
        result = {
            "time": None,
            "location": None,
            "activity": None,
            "participants_needed": False,
            "rsvp_required": False,
            "has_time": False,
            "has_location": False,
            "raw_message": message
        }
        
        # 시간 추출
        time_info = self._extract_time(message)
        if time_info:
            result["time"] = time_info
            result["has_time"] = True
        
        # 장소 추출
        location = self._extract_location(message)
        if location:
            result["location"] = location
            result["has_location"] = True
        
        # 활동 추출
        activity = self._extract_activity(message)
        if activity:
            result["activity"] = activity
        
        # 참석자 필요 여부 (더 많은 표현 인식)
        rsvp_keywords = [
            "나와주세요", "갈거에요", "참석", "참여", "누구", "어디세요", 
            "가실분", "참가", "함께", "모임", "만남", "나오기", "참가하실",
            "참석하실", "가시는", "오시는", "참석 가능", "참여 가능"
        ]
        if any(word in message for word in rsvp_keywords):
            result["participants_needed"] = True
            result["rsvp_required"] = True
        
        return result
    
    def _extract_time(self, message: str) -> Optional[str]:
        """시간 정보 추출"""
        # 패턴 1: "오늘 저녁 6시"
        if "오늘" in message:
            today = datetime.now()
            # 시간 추출
            time_match = re.search(r'(\d+)시', message)
            if time_match:
                hour = int(time_match.group(1))
                if "저녁" in message or "밤" in message:
                    if hour < 12:
                        hour += 12
                return today.replace(hour=hour, minute=0, second=0).isoformat()
        
        # 패턴 2: "내일 오전10시"
        if "내일" in message:
            tomorrow = datetime.now() + timedelta(days=1)
            time_match = re.search(r'오전?(\d+)시|오후?(\d+)시|(\d+)시', message)
            if time_match:
                hour = int(time_match.group(1) or time_match.group(2) or time_match.group(3))
                if "오전" in message and hour == 12:
                    hour = 0
                elif "오후" in message and hour < 12:
                    hour += 12
                return tomorrow.replace(hour=hour, minute=0, second=0).isoformat()
        
        # 패턴 3: "이번주말"
        if "주말" in message or "토요일" in message or "일요일" in message:
            today = datetime.now()
            days_until_weekend = (5 - today.weekday()) % 7  # 금요일까지
            if days_until_weekend == 0:
                days_until_weekend = 7  # 이미 주말이면 다음 주말
            weekend_date = today + timedelta(days=days_until_weekend)
            return weekend_date.replace(hour=10, minute=0, second=0).isoformat()
        
        return None
    
    def _extract_location(self, message: str) -> Optional[str]:
        """장소 정보 추출"""
        # 패턴 1: "2동앞 놀이터"
        location_patterns = [
            r'(\d+동앞?\s*[가-힣\s]+)',  # 2동앞 놀이터
            r'([가-힣]+공터)',  # 뒷공터
            r'([가-힣]+놀이터)',  # 놀이터
            r'([가-힣]+공원)',  # 공원
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_activity(self, message: str) -> Optional[str]:
        """활동 정보 추출"""
        activity_keywords = {
            "놀이터": "놀이터 모임",
            "놀이공원": "놀이공원 체험",
            "캐러반": "캐러반 체험",
            "하원": "하원 도움",
            "등원": "등원 도움",
        }
        
        for keyword, activity in activity_keywords.items():
            if keyword in message:
                return activity
        
        return None
    
    async def parse_with_ai(self, message: str) -> Dict[str, Any]:
        """
        AI를 사용하여 동적 자연어 파싱
        모든 표현 방식을 처리할 수 있도록 AI 기반으로 구현
        """
        if not self.openai_client:
            return self.extract_schedule_info(message)
        
        try:
            prompt = f"""
다음 메시지에서 일정 정보를 추출해주세요. 다양한 표현 방식을 모두 인식해야 합니다.

메시지: {message}

추출할 정보:
- time: ISO 형식 시간 (예: "2024-01-06T18:00:00") 또는 null
- location: 장소명 (정확한 장소명만, 설명 제외)
- activity: 활동 내용
- participants_needed: 참석자 필요 여부 (모임, 만남, 참석, 참여, 나오기, 함께 등 키워드가 있으면 true)
- rsvp_required: 응답 필요 여부 (참석 여부를 묻는 표현이 있으면 true)

주의사항:
- 시간 표현: "오늘", "내일", "이번주말", "주말", "토요일", "일요일", "저녁", "밤", "오전", "오후" 등 모든 표현 인식
- 장소 표현: "2동앞", "뒷공터", "놀이터", "공원", "캐러반" 등 모든 장소 표현 인식
- 참석 요청: "나와주세요", "갈거에요", "참석", "참여", "누구", "어디세요", "가실분", "참가", "함께" 등 모든 표현 인식

JSON 형식으로만 응답하세요:
{{
    "time": "시간 또는 null",
    "location": "장소명 또는 null",
    "activity": "활동 또는 null",
    "participants_needed": true/false,
    "rsvp_required": true/false
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 공동육아 일정 정보를 추출하는 전문가입니다. 다양한 자연어 표현을 모두 인식하고 JSON 형식으로만 응답하세요."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}  # JSON 형식 강제
            )
            
            import json
            content = response.choices[0].message.content
            # JSON 파싱 (마크다운 코드 블록 제거)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            result["raw_message"] = message
            result["has_time"] = result.get("time") is not None and result.get("time") != "null"
            result["has_location"] = result.get("location") is not None and result.get("location") != "null"
            
            return result
            
        except Exception as e:
            logger.error(f"AI 파싱 실패: {e}")
            # 폴백: 기본 파싱 사용
            return self.extract_schedule_info(message)

