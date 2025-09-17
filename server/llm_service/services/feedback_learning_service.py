"""
사용자 피드백 기반 학습 시스템
AI 응답에 대한 사용자 피드백을 수집하고 분석하여 프롬프트 품질을 개선
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

class FeedbackType(Enum):
    COMMUNITY_NAME = "community_name"
    COMMUNITY_DESCRIPTION = "community_description"
    EMERGENCY_ASSESSMENT = "emergency_assessment"
    CHAT_RESPONSE = "chat_response"

class FeedbackRating(Enum):
    VERY_BAD = 1
    BAD = 2
    NEUTRAL = 3
    GOOD = 4
    VERY_GOOD = 5

class FeedbackLearningService:
    def __init__(self):
        # 실제로는 데이터베이스에 저장하지만, 예시로 메모리 사용
        self.feedback_data = []
        self.prompt_performance = {}
    
    async def collect_feedback(
        self,
        user_id: str,
        feedback_type: FeedbackType,
        prompt_used: str,
        ai_response: str,
        rating: FeedbackRating,
        user_comment: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """사용자 피드백 수집"""
        feedback = {
            "id": f"fb_{datetime.now().timestamp()}",
            "user_id": user_id,
            "feedback_type": feedback_type.value,
            "prompt_used": prompt_used,
            "ai_response": ai_response,
            "rating": rating.value,
            "user_comment": user_comment,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedback_data.append(feedback)
        await self._update_prompt_performance(feedback_type, prompt_used, rating.value)
        
        return feedback["id"]
    
    async def _update_prompt_performance(self, feedback_type: FeedbackType, prompt_used: str, rating: int):
        """프롬프트 성능 메트릭 업데이트"""
        key = f"{feedback_type.value}:{prompt_used}"
        
        if key not in self.prompt_performance:
            self.prompt_performance[key] = {
                "total_ratings": 0,
                "sum_ratings": 0,
                "average_rating": 0,
                "usage_count": 0
            }
        
        perf = self.prompt_performance[key]
        perf["total_ratings"] += 1
        perf["sum_ratings"] += rating
        perf["average_rating"] = perf["sum_ratings"] / perf["total_ratings"]
        perf["usage_count"] += 1
    
    async def get_best_prompt_variant(self, feedback_type: FeedbackType, context: Dict = None) -> str:
        """상황에 맞는 최적의 프롬프트 변형 선택"""
        
        # 1. 기본 프롬프트 후보들
        base_prompts = await self._get_prompt_variants(feedback_type)
        
        # 2. 컨텍스트 기반 필터링
        filtered_prompts = await self._filter_by_context(base_prompts, context)
        
        # 3. 성능 기반 랭킹
        best_prompt = await self._rank_by_performance(filtered_prompts, feedback_type)
        
        return best_prompt
    
    async def _get_prompt_variants(self, feedback_type: FeedbackType) -> List[str]:
        """프롬프트 타입별 변형들 반환"""
        variants = {
            FeedbackType.COMMUNITY_NAME: [
                "COMMUNITY_NAME_GENERATION",
                "COMMUNITY_NAME_FRIENDLY",
                "COMMUNITY_NAME_FORMAL",
                "COMMUNITY_NAME_CREATIVE"
            ],
            FeedbackType.COMMUNITY_DESCRIPTION: [
                "COMMUNITY_DESCRIPTION_GENERATION",
                "COMMUNITY_DESCRIPTION_DETAILED",
                "COMMUNITY_DESCRIPTION_BRIEF",
                "COMMUNITY_DESCRIPTION_EMOTIONAL"
            ]
        }
        
        return variants.get(feedback_type, ["DEFAULT"])
    
    async def _filter_by_context(self, prompts: List[str], context: Dict = None) -> List[str]:
        """컨텍스트에 따른 프롬프트 필터링"""
        if not context:
            return prompts
        
        filtered = []
        
        for prompt in prompts:
            # 사용자 경험 레벨에 따른 필터링
            if context.get('user_experience') == 'beginner':
                if 'FRIENDLY' in prompt or 'DETAILED' in prompt:
                    filtered.append(prompt)
            elif context.get('user_experience') == 'expert':
                if 'BRIEF' in prompt or 'FORMAL' in prompt:
                    filtered.append(prompt)
            else:
                filtered.append(prompt)
        
        return filtered if filtered else prompts
    
    async def _rank_by_performance(self, prompts: List[str], feedback_type: FeedbackType) -> str:
        """성능 기반 프롬프트 랭킹"""
        best_prompt = prompts[0]
        best_score = 0
        
        for prompt in prompts:
            key = f"{feedback_type.value}:{prompt}"
            perf = self.prompt_performance.get(key, {"average_rating": 3.0, "usage_count": 0})
            
            # 평균 평점과 사용 횟수를 고려한 점수 계산
            confidence = min(perf["usage_count"] / 10, 1.0)  # 최대 10회까지만 신뢰도 반영
            score = perf["average_rating"] * confidence + 3.0 * (1 - confidence)  # 기본값 3.0
            
            if score > best_score:
                best_score = score
                best_prompt = prompt
        
        return best_prompt
    
    async def analyze_feedback_trends(self, feedback_type: FeedbackType = None) -> Dict:
        """피드백 트렌드 분석"""
        filtered_data = self.feedback_data
        
        if feedback_type:
            filtered_data = [fb for fb in filtered_data if fb["feedback_type"] == feedback_type.value]
        
        if not filtered_data:
            return {"message": "분석할 피드백이 없습니다"}
        
        # 평균 평점 계산
        avg_rating = sum(fb["rating"] for fb in filtered_data) / len(filtered_data)
        
        # 가장 많은 불만사항 추출
        negative_feedback = [fb for fb in filtered_data if fb["rating"] <= 2 and fb["user_comment"]]
        common_issues = await self._extract_common_issues(negative_feedback)
        
        # 성능이 좋은 프롬프트 찾기
        top_prompts = sorted(
            self.prompt_performance.items(),
            key=lambda x: x[1]["average_rating"],
            reverse=True
        )[:5]
        
        return {
            "total_feedback": len(filtered_data),
            "average_rating": round(avg_rating, 2),
            "common_issues": common_issues,
            "top_performing_prompts": [
                {"prompt": prompt.split(":")[1], "rating": data["average_rating"]}
                for prompt, data in top_prompts
            ]
        }
    
    async def _extract_common_issues(self, negative_feedback: List[Dict]) -> List[str]:
        """부정적 피드백에서 공통 이슈 추출"""
        # 실제로는 NLP 분석이나 키워드 추출 사용
        # 여기서는 간단한 키워드 매칭 예시
        
        common_keywords = {}
        issue_keywords = ["딱딱", "어려워", "이해 안", "부자연", "너무 길", "너무 짧", "도움 안"]
        
        for fb in negative_feedback:
            comment = fb.get("user_comment", "")
            for keyword in issue_keywords:
                if keyword in comment:
                    common_keywords[keyword] = common_keywords.get(keyword, 0) + 1
        
        # 가장 자주 언급된 이슈들 반환
        sorted_issues = sorted(common_keywords.items(), key=lambda x: x[1], reverse=True)
        return [issue for issue, count in sorted_issues[:3]]

# 사용 예시
"""
# 1. 피드백 수집
feedback_service = FeedbackLearningService()

await feedback_service.collect_feedback(
    user_id="user123",
    feedback_type=FeedbackType.COMMUNITY_NAME,
    prompt_used="COMMUNITY_NAME_GENERATION",
    ai_response="새싹어린이집 모임",
    rating=FeedbackRating.BAD,
    user_comment="너무 딱딱해요, 더 친근하게 해주세요",
    context={"user_experience": "beginner", "region": "urban"}
)

# 2. 최적 프롬프트 선택
best_prompt = await feedback_service.get_best_prompt_variant(
    FeedbackType.COMMUNITY_NAME,
    context={"user_experience": "beginner"}
)

# 3. 피드백 트렌드 분석
trends = await feedback_service.analyze_feedback_trends(FeedbackType.COMMUNITY_NAME)
"""