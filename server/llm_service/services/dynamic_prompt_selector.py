"""
동적 프롬프트 선택 시스템
사용자 컨텍스트, 시간, 상황에 따라 최적의 프롬프트를 선택
"""
from datetime import datetime, time
from typing import Dict, Optional, List
from enum import Enum
import json

class UserExperienceLevel(Enum):
    BEGINNER = "beginner"      # 신규/초보 사용자
    INTERMEDIATE = "intermediate"  # 일반 사용자  
    EXPERT = "expert"          # 숙련 사용자

class RegionType(Enum):
    URBAN = "urban"           # 도시
    SUBURBAN = "suburban"     # 교외
    RURAL = "rural"          # 시골

class TimeContext(Enum):
    MORNING_RUSH = "morning_rush"     # 아침 바쁜 시간 (7-9시)
    DAYTIME = "daytime"               # 낮 시간 (9-18시)
    EVENING_FAMILY = "evening_family" # 저녁 가족시간 (18-21시)
    NIGHT = "night"                   # 밤 시간 (21-7시)

class DynamicPromptSelector:
    def __init__(self):
        # 프롬프트 변형들을 컨텍스트별로 정의
        self.prompt_variants = {
            "community_name": {
                "default": "COMMUNITY_NAME_GENERATION",
                "beginner_friendly": "COMMUNITY_NAME_FRIENDLY", 
                "expert_brief": "COMMUNITY_NAME_FORMAL",
                "creative": "COMMUNITY_NAME_CREATIVE",
                "rural_context": "COMMUNITY_NAME_RURAL",
                "quick": "COMMUNITY_NAME_QUICK"
            },
            "community_description": {
                "default": "COMMUNITY_DESCRIPTION_GENERATION",
                "detailed": "COMMUNITY_DESCRIPTION_DETAILED",
                "brief": "COMMUNITY_DESCRIPTION_BRIEF", 
                "emotional": "COMMUNITY_DESCRIPTION_EMOTIONAL",
                "practical": "COMMUNITY_DESCRIPTION_PRACTICAL"
            },
            "emergency_assessment": {
                "default": "EMERGENCY_ASSESSMENT_PROMPT",
                "detailed": "EMERGENCY_ASSESSMENT_DETAILED",
                "quick": "EMERGENCY_ASSESSMENT_QUICK",
                "parent_focused": "EMERGENCY_ASSESSMENT_PARENT"
            }
        }
        
        # 컨텍스트 기반 선택 규칙
        self.selection_rules = self._initialize_selection_rules()
    
    def _initialize_selection_rules(self) -> Dict:
        """프롬프트 선택 규칙 초기화"""
        return {
            # 사용자 경험 레벨 기반
            "experience_rules": {
                UserExperienceLevel.BEGINNER: {
                    "community_name": "beginner_friendly",
                    "community_description": "detailed",
                    "emergency_assessment": "detailed"
                },
                UserExperienceLevel.INTERMEDIATE: {
                    "community_name": "default",
                    "community_description": "default", 
                    "emergency_assessment": "default"
                },
                UserExperienceLevel.EXPERT: {
                    "community_name": "expert_brief",
                    "community_description": "brief",
                    "emergency_assessment": "quick"
                }
            },
            
            # 시간대 기반
            "time_rules": {
                TimeContext.MORNING_RUSH: {
                    "community_name": "quick",
                    "community_description": "brief",
                    "emergency_assessment": "quick"
                },
                TimeContext.DAYTIME: {
                    "community_name": "default",
                    "community_description": "default",
                    "emergency_assessment": "default"
                },
                TimeContext.EVENING_FAMILY: {
                    "community_name": "emotional",
                    "community_description": "emotional", 
                    "emergency_assessment": "parent_focused"
                },
                TimeContext.NIGHT: {
                    "community_name": "brief",
                    "community_description": "brief",
                    "emergency_assessment": "detailed"  # 밤엔 응급상황이 더 심각할 수 있음
                }
            },
            
            # 지역 타입 기반
            "region_rules": {
                RegionType.URBAN: {
                    "community_name": "default",
                    "community_description": "practical"
                },
                RegionType.SUBURBAN: {
                    "community_name": "default", 
                    "community_description": "emotional"
                },
                RegionType.RURAL: {
                    "community_name": "rural_context",
                    "community_description": "detailed"
                }
            }
        }
    
    async def select_optimal_prompt(
        self,
        prompt_type: str,
        user_context: Dict,
        situation_context: Optional[Dict] = None
    ) -> str:
        """상황에 맞는 최적의 프롬프트 선택"""
        
        # 1. 기본 프롬프트부터 시작
        selected_variant = "default"
        
        # 2. 사용자 경험 레벨 적용
        experience_level = self._determine_experience_level(user_context)
        if experience_level:
            experience_rule = self.selection_rules["experience_rules"].get(experience_level, {})
            if prompt_type in experience_rule:
                selected_variant = experience_rule[prompt_type]
        
        # 3. 시간 컨텍스트 적용 (우선순위가 더 높음)
        time_context = self._determine_time_context()
        if time_context:
            time_rule = self.selection_rules["time_rules"].get(time_context, {})
            if prompt_type in time_rule:
                selected_variant = time_rule[prompt_type]
        
        # 4. 지역 컨텍스트 적용
        region_type = self._determine_region_type(user_context)
        if region_type:
            region_rule = self.selection_rules["region_rules"].get(region_type, {})
            if prompt_type in region_rule:
                selected_variant = region_rule[prompt_type]
        
        # 5. 특수 상황 컨텍스트 적용 (최고 우선순위)
        if situation_context:
            special_variant = await self._handle_special_situations(
                prompt_type, situation_context, selected_variant
            )
            if special_variant:
                selected_variant = special_variant
        
        # 6. 최종 프롬프트 ID 반환
        prompt_variants = self.prompt_variants.get(prompt_type, {})
        final_prompt = prompt_variants.get(selected_variant, prompt_variants.get("default"))
        
        return final_prompt
    
    def _determine_experience_level(self, user_context: Dict) -> Optional[UserExperienceLevel]:
        """사용자 경험 레벨 판단"""
        # 사용 횟수 기반
        usage_count = user_context.get("usage_count", 0)
        if usage_count < 5:
            return UserExperienceLevel.BEGINNER
        elif usage_count < 20:
            return UserExperienceLevel.INTERMEDIATE
        else:
            return UserExperienceLevel.EXPERT
    
    def _determine_time_context(self) -> TimeContext:
        """현재 시간 기반 컨텍스트 판단"""
        current_hour = datetime.now().hour
        
        if 7 <= current_hour < 9:
            return TimeContext.MORNING_RUSH
        elif 9 <= current_hour < 18:
            return TimeContext.DAYTIME
        elif 18 <= current_hour < 21:
            return TimeContext.EVENING_FAMILY
        else:
            return TimeContext.NIGHT
    
    def _determine_region_type(self, user_context: Dict) -> Optional[RegionType]:
        """사용자 지역 타입 판단"""
        location = user_context.get("location", {})
        address = location.get("address", "")
        
        # 간단한 키워드 기반 판단 (실제로는 더 정교한 분석 필요)
        if any(keyword in address for keyword in ["서울", "부산", "대구", "인천", "광주", "대전", "울산"]):
            return RegionType.URBAN
        elif any(keyword in address for keyword in ["시", "구"]):
            return RegionType.SUBURBAN
        elif any(keyword in address for keyword in ["군", "읍", "면"]):
            return RegionType.RURAL
        
        return None
    
    async def _handle_special_situations(
        self,
        prompt_type: str,
        situation_context: Dict,
        current_variant: str
    ) -> Optional[str]:
        """특수 상황 처리"""
        
        # 응급 상황의 심각도에 따른 프롬프트 선택
        if prompt_type == "emergency_assessment":
            urgency_level = situation_context.get("urgency_level", "normal")
            if urgency_level == "critical":
                return "emergency_assessment_critical"
            elif urgency_level == "high":
                return "emergency_assessment_detailed"
        
        # 커뮤니티 생성 시 특수 상황
        if prompt_type.startswith("community"):
            # 특별한 행사나 시즌이 있는 경우
            season = situation_context.get("season")
            if season == "christmas":
                return f"{prompt_type}_festive"
            elif season == "summer_vacation":
                return f"{prompt_type}_vacation"
        
        # 사용자가 이전에 부정적 피드백을 준 경우
        previous_feedback = situation_context.get("previous_feedback_rating", 5)
        if previous_feedback <= 2:
            # 이전에 만족하지 않았던 경우 다른 스타일 시도
            if "brief" in current_variant:
                return current_variant.replace("brief", "detailed")
            elif "formal" in current_variant:
                return current_variant.replace("formal", "friendly")
        
        return None
    
    async def get_context_analysis(self, user_context: Dict, situation_context: Dict = None) -> Dict:
        """컨텍스트 분석 결과 반환 (디버깅용)"""
        experience_level = self._determine_experience_level(user_context)
        time_context = self._determine_time_context()
        region_type = self._determine_region_type(user_context)
        
        return {
            "user_experience_level": experience_level.value if experience_level else None,
            "time_context": time_context.value,
            "region_type": region_type.value if region_type else None,
            "current_hour": datetime.now().hour,
            "special_situations": situation_context or {}
        }

# 사용 예시
"""
# 동적 프롬프트 선택기 초기화
prompt_selector = DynamicPromptSelector()

# 사용자 컨텍스트 정의
user_context = {
    "user_id": "user123",
    "usage_count": 3,  # 초보 사용자
    "location": {
        "address": "서울시 강남구"  # 도시
    }
}

# 상황 컨텍스트 (선택적)
situation_context = {
    "urgency_level": "normal",
    "previous_feedback_rating": 4,
    "season": "christmas"
}

# 최적 프롬프트 선택
optimal_prompt = await prompt_selector.select_optimal_prompt(
    prompt_type="community_name",
    user_context=user_context,
    situation_context=situation_context
)

print(f"선택된 프롬프트: {optimal_prompt}")
# 결과: COMMUNITY_NAME_FRIENDLY (초보사용자 + 도시 + 일반상황)

# 컨텍스트 분석 확인
context_analysis = await prompt_selector.get_context_analysis(user_context, situation_context)
print(context_analysis)
"""