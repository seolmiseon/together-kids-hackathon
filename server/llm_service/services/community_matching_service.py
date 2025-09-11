import json
from typing import Dict, List, Optional
from datetime import datetime
import logging
from openai import AsyncOpenAI
import os
import sys
from dotenv import load_dotenv
from .vector_service import VectorService

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from prompts.community.community_prompts import (
        USER_INTEREST_ANALYSIS,
        PARENTING_STYLE_ANALYSIS,
        COMMUNITY_CLASSIFICATION,
        MATCHING_ALGORITHM,
        VECTORIZATION_PROMPT
    )
except ImportError:
    # 프롬프트 상수들 직접 정의
    USER_INTEREST_ANALYSIS = """사용자 메시지: {messages}
    교육 관심사와 활동 선호도를 JSON으로 분석해주세요."""
    PARENTING_STYLE_ANALYSIS = """사용자 메시지: {messages}
    양육 스타일을 JSON으로 분석해주세요."""

# 환경변수 로드
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class CommunityMatchingService:
    def __init__(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = AsyncOpenAI(api_key=openai_key)
        else:
            logger.warning("OPENAI_API_KEY not found, AI 분석 기능이 제한됩니다.")
            self.openai_client = None
        
        # Vector Service 초기화
        self.vector_service = VectorService()
        
        # 육아 단계별 분류
        self.parenting_stages = {
            "영유아기_신생아": {"age_range": "0-6개월", "keywords": ["수유", "수면패턴", "기저귀"]},
            "영유아기_영아": {"age_range": "7-18개월", "keywords": ["이유식", "걸음마", "언어발달"]},
            "영유아기_유아": {"age_range": "19개월-2세", "keywords": ["배변훈련", "놀이발달"]},
            "유아기_3세": {"age_range": "3세", "keywords": ["어린이집", "사회성발달"]},
            "유아기_4_5세": {"age_range": "4-5세", "keywords": ["유치원", "학습준비", "창의성발달"]},
            "아동기": {"age_range": "6-8세", "keywords": ["학교적응", "기초학습", "친구관계"]},
            "학령기": {"age_range": "9-12세", "keywords": ["학습심화", "진로탐색", "독립성"]}
        }
        
        # 교육 관심사 분류
        self.education_interests = {
            "학습법": ["몬테소리", "발도르프", "레지오에밀리아"],
            "교육분야": ["언어", "수학", "과학", "예술", "체육"],
            "교육철학": ["자율학습", "구조화학습", "놀이중심"]
        }
        
        # 양육 스타일 분류
        self.parenting_styles = {
            "양육방식": ["자율형", "권위형", "허용형", "방임형"],
            "훈육방법": ["긍정훈육", "자연결과", "논리적결과"],
            "소통방식": ["경청형", "지시형", "협력형"]
        }
        
        # 커뮤니티 분류 체계
        self.community_types = {
            "지역별": ["놀이터모임", "육아품앗이", "체험활동", "공동구매"],
            "관심사별": ["홈스쿨링", "대안교육", "영재교육", "알레르기아동", "다문화가정", "워킹맘"],
            "목적별": ["정보교환", "물품거래", "모임활동"],
            "상황별": ["수면문제", "식습관", "행동교정", "언어지연", "사회성부족"]
        }

    async def analyze_user_profile(self, user_data: Dict) -> Dict:
        """사용자 프로필을 종합 분석하여 매칭용 벡터 생성"""
        try:
            # 1. 아이 연령대 분석
            children_ages = user_data.get('children', [])
            parenting_stage = self._determine_parenting_stage(children_ages)
            
            # 2. 사용자 메시지에서 관심사 추출
            recent_messages = user_data.get('recent_messages', [])
            interests = await self._extract_interests_from_messages(recent_messages)
            
            # 3. 양육 스타일 추론
            parenting_style = await self._infer_parenting_style(recent_messages)
            
            # 4. 상황별 니즈 분석
            current_needs = await self._analyze_current_needs(recent_messages)
            
            user_profile = {
                "user_id": user_data.get('user_id'),
                "parenting_stage": parenting_stage,
                "education_interests": interests.get('education', []),
                "parenting_style": parenting_style,
                "current_needs": current_needs,
                "location": user_data.get('area', ''),
                "activity_preferences": interests.get('activities', []),
                "lifestyle": interests.get('lifestyle', []),
                "timestamp": datetime.now().isoformat()
            }
            
            return user_profile
            
        except Exception as e:
            logger.error(f"❌ 사용자 프로필 분석 실패: {e}")
            return {}

    def _determine_parenting_stage(self, children_ages: List[Dict]) -> str:
        """자녀 연령대를 기반으로 육아 단계 결정"""
        if not children_ages:
            return "예비부모"
        
        # 가장 어린 자녀 기준으로 단계 결정
        youngest_age = min([child.get('age_months', 0) for child in children_ages])
        
        if youngest_age <= 6:
            return "영유아기_신생아"
        elif youngest_age <= 18:
            return "영유아기_영아"
        elif youngest_age <= 24:
            return "영유아기_유아"
        elif youngest_age <= 36:
            return "유아기_3세"
        elif youngest_age <= 60:
            return "유아기_4_5세"
        elif youngest_age <= 96:
            return "아동기"
        else:
            return "학령기"

    async def _extract_interests_from_messages(self, messages: List[str]) -> Dict:
        """메시지에서 교육 관심사와 활동 선호도 추출"""
        try:
            if not messages:
                return {"education": [], "activities": [], "lifestyle": []}
            
            # 프롬프트 기반 AI 분석 시도
            if self.openai_client:
                try:
                    messages_text = "\n".join(messages[-5:])  # 최근 5개 메시지
                    prompt_with_data = USER_INTEREST_ANALYSIS.replace("{messages}", messages_text)
                    
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt_with_data}],
                        temperature=0.3,
                        max_tokens=500
                    )
                    
                    result_text = response.choices[0].message.content
                    # JSON 파싱 시도
                    if "```json" in result_text:
                        json_start = result_text.find("```json") + 7
                        json_end = result_text.find("```", json_start)
                        json_text = result_text[json_start:json_end].strip()
                        return json.loads(json_text)
                    else:
                        return json.loads(result_text)
                except Exception as e:
                    logger.error(f"AI 관심사 분석 실패: {e}")
            
            # OpenAI 없으면 키워드 기반 분석
            return self._extract_interests_by_keywords(messages)
            
        except Exception as e:
            logger.error(f"❌ 관심사 추출 실패: {e}")
            return {"education": [], "activities": [], "lifestyle": []}

    def _extract_interests_by_keywords(self, messages: List[str]) -> Dict:
        """키워드 기반 관심사 추출 (OpenAI 대체용)"""
        combined_text = " ".join(messages).lower()
        
        education_keywords = {
            "몬테소리": ["몬테소리"],
            "발도르프": ["발도르프", "슈타이너"],
            "자율학습": ["자율", "스스로", "알아서"],
            "창의성": ["창의", "상상력", "예술"]
        }
        
        activity_keywords = {
            "실내활동": ["실내", "집에서", "방에서"],
            "야외활동": ["바깥", "야외", "공원", "놀이터"],
            "체험학습": ["체험", "견학", "현장"]
        }
        
        detected_education = []
        detected_activities = []
        
        for category, keywords in education_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                detected_education.append(category)
        
        for category, keywords in activity_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                detected_activities.append(category)
        
        return {
            "education": detected_education,
            "activities": detected_activities,
            "lifestyle": ["건강관리"] if "건강" in combined_text else []
        }

    async def _infer_parenting_style(self, messages: List[str]) -> Dict:
        """메시지 톤과 내용으로 양육 스타일 추론"""
        try:
            if not messages:
                return {"양육방식": "자율형", "소통방식": "경청형"}
            
            # 프롬프트 기반 AI 분석 시도
            if self.openai_client:
                try:
                    messages_text = "\n".join(messages[-5:])  # 최근 5개 메시지
                    prompt_with_data = PARENTING_STYLE_ANALYSIS.replace("{messages}", messages_text)
                    
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt_with_data}],
                        temperature=0.3,
                        max_tokens=300
                    )
                    
                    result_text = response.choices[0].message.content
                    # JSON 파싱 시도
                    if "```json" in result_text:
                        json_start = result_text.find("```json") + 7
                        json_end = result_text.find("```", json_start)
                        json_text = result_text[json_start:json_end].strip()
                        return json.loads(json_text)
                    else:
                        return json.loads(result_text)
                except Exception as e:
                    logger.error(f"AI 양육스타일 분석 실패: {e}")
            
            # 키워드 기반 분석 사용
            return self._infer_style_by_keywords(messages)
            
        except Exception as e:
            logger.error(f"❌ 양육 스타일 추론 실패: {e}")
            return {"양육방식": "자율형", "소통방식": "경청형"}

    def _infer_style_by_keywords(self, messages: List[str]) -> Dict:
        """키워드 기반 양육 스타일 추론"""
        combined_text = " ".join(messages).lower()
        
        # 양육방식 키워드
        if any(keyword in combined_text for keyword in ["규칙", "해야", "시켜", "엄격"]):
            parenting_type = "권위형"
        elif any(keyword in combined_text for keyword in ["자유", "알아서", "스스로"]):
            parenting_type = "자율형"
        else:
            parenting_type = "자율형"
        
        # 소통방식 키워드
        if any(keyword in combined_text for keyword in ["함께", "같이", "우리"]):
            communication = "협력형"
        elif any(keyword in combined_text for keyword in ["들어", "말해", "이야기"]):
            communication = "경청형"
        else:
            communication = "경청형"
        
        return {"양육방식": parenting_type, "소통방식": communication}

    async def _analyze_current_needs(self, messages: List[str]) -> List[str]:
        """현재 겪고 있는 육아 상황/고민 분석"""
        try:
            if not messages:
                return []
            
            recent_text = " ".join(messages[-3:])  # 최근 3개 메시지
            
            # 키워드 기반 빠른 분류
            need_keywords = {
                "수면문제": ["잠", "안 자", "밤에", "깨워", "수면"],
                "식습관": ["밥", "먹기", "편식", "식사", "음식"],
                "행동교정": ["때려", "소리", "울어", "말 안 들", "짜증"],
                "언어발달": ["말", "언어", "대화", "표현", "발음"],
                "사회성": ["친구", "어린이집", "적응", "사회성"],
                "학습": ["공부", "학습", "숫자", "글자", "학교"],
                "건강": ["아파", "감기", "열", "병원", "건강"]
            }
            
            detected_needs = []
            for need, keywords in need_keywords.items():
                if any(keyword in recent_text for keyword in keywords):
                    detected_needs.append(need)
            
            return detected_needs[:3]  # 최대 3개까지
            
        except Exception as e:
            logger.error(f"❌ 현재 니즈 분석 실패: {e}")
            return []

    async def find_matching_communities(self, user_profile: Dict, area: str) -> List[Dict]:
        """사용자 프로필 기반 최적 커뮤니티 매칭 - ChromaDB 활용"""
        try:
            # 1. Vector DB에서 사용자 프로필 기반 커뮤니티 검색
            candidate_communities = await self.vector_service.search_communities_by_profile(
                user_profile, area, top_k=10  # 더 많은 후보 확보
            )
            
            # 2. 각 커뮤니티와 사용자 프로필 매칭 스코어 계산
            scored_communities = []
            for community in candidate_communities:
                score = await self._calculate_match_score_enhanced(user_profile, community)
                if score > 0.1:  # 최소 매칭 기준
                    community['match_score'] = score
                    community['match_reasons'] = self._explain_match_reasons(user_profile, community)
                    scored_communities.append(community)
            
            # 3. 스코어 순으로 정렬하여 상위 5개 반환
            scored_communities.sort(key=lambda x: x['match_score'], reverse=True)
            return scored_communities[:5]
            
        except Exception as e:
            logger.error(f"❌ 커뮤니티 매칭 실패: {e}")
            # 실패 시 데모 데이터 반환
            return await self._get_demo_communities_in_area(area)

    async def _get_demo_communities_in_area(self, area: str) -> List[Dict]:
        """데모용 커뮤니티 데이터 (Vector DB 실패 시 백업)"""
        demo_communities = [
            {
                "community_id": "uijeongbu_montessori",
                "name": "의정부 몬테소리 육아모임",
                "location": area,
                "focus_areas": ["몬테소리", "자율학습", "창의성발달"],
                "target_ages": ["영유아기_유아", "유아기_3세"],
                "member_count": 25,
                "similarity_score": 0.8
            },
            {
                "community_id": "uijeongbu_playground",
                "name": "신곡동 놀이터 품앗이",
                "location": area,
                "focus_areas": ["야외활동", "사회성발달", "놀이"],
                "target_ages": ["유아기_3세", "유아기_4_5세"],
                "member_count": 15,
                "similarity_score": 0.7
            }
        ]
        return demo_communities

    async def _calculate_match_score_enhanced(self, user_profile: Dict, community: Dict) -> float:
        """향상된 매칭 스코어 계산 - Vector DB 결과 활용"""
        try:
            total_score = 0.0
            
            # Vector DB 유사도 점수 활용 (기본 20%)
            similarity_score = community.get('similarity_score', 0.0)
            total_score += similarity_score * 0.2
            
            # 1. 육아 단계 매칭 (30%)
            user_stage = user_profile.get('parenting_stage', '')
            community_ages = community.get('target_ages', [])
            if user_stage in community_ages:
                total_score += 0.3
            elif "모든연령" in community_ages or any("전체" in age for age in community_ages):
                total_score += 0.15
            
            # 2. 교육 관심사 매칭 (25%)
            user_interests = set(user_profile.get('education_interests', []))
            community_focus = set(community.get('focus_areas', []))
            interest_overlap = len(user_interests & community_focus)
            if interest_overlap > 0:
                total_score += 0.25 * min(interest_overlap / 3, 1.0)
            
            # 3. 활동 스타일 매칭 (15%)
            user_activities = set(user_profile.get('activity_preferences', []))
            # community에서 activity_style 추출 (content에서 파싱 필요할 수 있음)
            community_activities = self._extract_activity_style_from_community(community)
            activity_overlap = len(user_activities & community_activities)
            if activity_overlap > 0:
                total_score += 0.15 * min(activity_overlap / 2, 1.0)
            
            # 4. 현재 니즈 매칭 (10%)
            user_needs = set(user_profile.get('current_needs', []))
            if user_needs & community_focus:
                total_score += 0.1
            
            return min(total_score, 1.0)
            
        except Exception as e:
            logger.error(f"❌ 향상된 매칭 스코어 계산 실패: {e}")
            return 0.0
    
    def _extract_activity_style_from_community(self, community: Dict) -> set:
        """커뮤니티 정보에서 활동 스타일 추출"""
        try:
            activity_keywords = {
                "실내활동": ["실내", "교실", "센터", "실습"],
                "야외활동": ["야외", "공원", "놀이터", "바깥"],
                "체험활동": ["체험", "견학", "현장", "탐방"],
                "정보교환": ["정보", "공유", "소통", "상담"],
                "모임활동": ["모임", "정기", "만남", "소모임"]
            }
            
            # 커뮤니티 내용 텍스트
            content_text = community.get('content', '').lower()
            community_name = community.get('name', '').lower()
            focus_areas = ' '.join(community.get('focus_areas', [])).lower()
            
            combined_text = f"{content_text} {community_name} {focus_areas}"
            
            detected_activities = set()
            for activity_type, keywords in activity_keywords.items():
                if any(keyword in combined_text for keyword in keywords):
                    detected_activities.add(activity_type)
            
            return detected_activities
            
        except Exception as e:
            logger.error(f"활동 스타일 추출 실패: {e}")
            return set()

    async def _calculate_match_score(self, user_profile: Dict, community: Dict) -> float:
        """기존 매칭 스코어 계산 (백업용)"""
        try:
            total_score = 0.0
            
            # 1. 육아 단계 매칭 (30%)
            if user_profile.get('parenting_stage') in community.get('target_age', []):
                total_score += 0.3
            elif "모든연령" in community.get('target_age', []):
                total_score += 0.15  # 부분 점수
            
            # 2. 교육 관심사 매칭 (25%)
            user_interests = user_profile.get('education_interests', [])
            community_focus = community.get('focus', [])
            interest_overlap = len(set(user_interests) & set(community_focus))
            if interest_overlap > 0:
                total_score += 0.25 * min(interest_overlap / 3, 1.0)
            
            # 3. 활동 스타일 매칭 (20%)
            user_activities = user_profile.get('activity_preferences', [])
            community_activities = community.get('activity_style', [])
            activity_overlap = len(set(user_activities) & set(community_activities))
            if activity_overlap > 0:
                total_score += 0.2 * min(activity_overlap / 2, 1.0)
            
            # 4. 현재 니즈 매칭 (15%)
            user_needs = user_profile.get('current_needs', [])
            if any(need in community_focus for need in user_needs):
                total_score += 0.15
            
            # 5. 커뮤니티 활성도 (10%)
            member_count = community.get('member_count', 0)
            if member_count >= 20:
                total_score += 0.1
            elif member_count >= 10:
                total_score += 0.05
            
            return min(total_score, 1.0)
            
        except Exception as e:
            logger.error(f"❌ 매칭 스코어 계산 실패: {e}")
            return 0.0

    def _explain_match_reasons(self, user_profile: Dict, community: Dict) -> List[str]:
        """매칭 이유 설명 생성"""
        reasons = []
        
        # 육아 단계 매칭
        if user_profile.get('parenting_stage') in community.get('target_age', []):
            stage_name = self.parenting_stages.get(user_profile['parenting_stage'], {}).get('age_range', '')
            reasons.append(f"{stage_name} 자녀를 둔 부모님들이 많아요")
        
        # 관심사 매칭
        user_interests = user_profile.get('education_interests', [])
        community_focus = community.get('focus', [])
        common_interests = set(user_interests) & set(community_focus)
        if common_interests:
            reasons.append(f"{', '.join(common_interests)} 관심사가 맞아요")
        
        # 현재 니즈 매칭
        user_needs = user_profile.get('current_needs', [])
        matching_needs = [need for need in user_needs if need in community_focus]
        if matching_needs:
            reasons.append(f"{', '.join(matching_needs)} 고민을 함께 나눌 수 있어요")
        
        return reasons[:3]  # 최대 3개 이유

    async def add_community_to_db(self, community_data: Dict) -> bool:
        """새로운 커뮤니티를 Vector DB에 추가"""
        try:
            await self.vector_service.add_community_info(community_data)
            logger.info(f"✅ 커뮤니티 추가됨: {community_data.get('name')}")
            return True
        except Exception as e:
            logger.error(f"❌ 커뮤니티 추가 실패: {e}")
            return False
    
    async def initialize_demo_communities(self, area: str = "의정부시"):
        """데모용 커뮤니티 데이터를 Vector DB에 초기화"""
        demo_communities = [
            {
                "community_id": "uijeongbu_montessori_001",
                "name": "의정부 몬테소리 육아모임",
                "location": f"{area} 신곡동",
                "description": "몬테소리 교육법을 실천하는 3-6세 자녀 부모들의 모임입니다. 자율학습과 창의성 발달을 중시하며, 주 1회 정기 모임을 가집니다.",
                "target_ages": ["영유아기_유아", "유아기_3세", "유아기_4_5세"],
                "focus_areas": ["몬테소리", "자율학습", "창의성발달", "실내활동"],
                "activities": ["몬테소리 교구 체험", "자율학습 환경 만들기", "창의성 발달 활동", "부모 교육"],
                "member_count": 25,
                "meeting_frequency": "주 1회",
                "activity_style": ["실내활동", "체험학습", "정보교환"]
            },
            {
                "community_id": "uijeongbu_playground_002", 
                "name": "신곡동 놀이터 품앗이",
                "location": f"{area} 신곡동",
                "description": "신곡동 지역 놀이터에서 만나는 야외활동 중심의 품앗이 모임입니다. 3-7세 아이들의 사회성 발달과 야외 놀이를 중시합니다.",
                "target_ages": ["유아기_3세", "유아기_4_5세", "아동기"],
                "focus_areas": ["야외활동", "사회성발달", "놀이", "품앗이"],
                "activities": ["놀이터 놀이", "공원 산책", "자연 체험", "아이 돌봄 품앗이"],
                "member_count": 18,
                "meeting_frequency": "주 2-3회",
                "activity_style": ["야외활동", "모임활동", "돌봄지원"]
            },
            {
                "community_id": "uijeongbu_working_mom_003",
                "name": "의정부 워킹맘 소통모임",
                "location": f"{area} 전체",
                "description": "직장과 육아를 병행하는 워킹맘들의 소통과 정서지원 모임입니다. 시간관리, 육아 고민, 직장맘 노하우를 공유합니다.",
                "target_ages": ["영유아기_신생아", "영유아기_영아", "영유아기_유아", "유아기_3세", "유아기_4_5세"],
                "focus_areas": ["워킹맘", "시간관리", "직장육아병행", "정서지원"],
                "activities": ["온라인 소통", "육아 정보 공유", "멘토링", "정서 상담"],
                "member_count": 42,
                "meeting_frequency": "온라인 상시, 오프라인 월 1회",
                "activity_style": ["정보교환", "정서지원", "온라인모임"]
            },
            {
                "community_id": "uijeongbu_sleep_training_004",
                "name": "의정부 수면교육 부모모임", 
                "location": f"{area} 가능동",
                "description": "영유아 수면 문제로 고민하는 부모들의 모임입니다. 수면교육 전문가와 함께하는 프로그램과 수면 고민 상담을 제공합니다.",
                "target_ages": ["영유아기_신생아", "영유아기_영아", "영유아기_유아"],
                "focus_areas": ["수면문제", "수면교육", "야간수유", "잠투정"],
                "activities": ["수면교육 강의", "수면 일지 작성", "개별 상담", "부모 지원"],
                "member_count": 15,
                "meeting_frequency": "격주 1회",
                "activity_style": ["교육프로그램", "상담지원", "정보교환"]
            },
            {
                "community_id": "uijeongbu_language_dev_005",
                "name": "의정부 언어발달 지원모임",
                "location": f"{area} 호원동", 
                "description": "언어발달이 늦은 아이들과 부모를 위한 지원 모임입니다. 언어치료사와 함께하는 프로그램과 가정에서 할 수 있는 언어발달 활동을 제공합니다.",
                "target_ages": ["영유아기_영아", "영유아기_유아", "유아기_3세"],
                "focus_areas": ["언어지연", "언어발달", "말늦은아이", "발음교정"],
                "activities": ["언어발달 놀이", "발음 연습", "책 읽기", "전문가 상담"],
                "member_count": 12,
                "meeting_frequency": "주 1회",
                "activity_style": ["치료지원", "체험학습", "전문상담"]
            }
        ]
        
        # 각 커뮤니티를 Vector DB에 추가
        success_count = 0
        for community in demo_communities:
            if await self.add_community_to_db(community):
                success_count += 1
        
        logger.info(f"✅ 데모 커뮤니티 초기화 완료: {success_count}/{len(demo_communities)}개 추가됨")
        return success_count == len(demo_communities)

# 전역 인스턴스
community_matching_service = CommunityMatchingService()
