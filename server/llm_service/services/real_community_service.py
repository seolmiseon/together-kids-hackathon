"""
실제 위치 기반 커뮤니티 매칭 서비스
GPS 위치추적 기반으로 진짜 공동육아 플랫폼 구현
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from openai import AsyncOpenAI
import os
import sys
from dotenv import load_dotenv
from .vector_service import VectorService
from .location_service import location_service

# 환경변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

class RealCommunityMatchingService:
    def __init__(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = AsyncOpenAI(api_key=openai_key)
        else:
            logger.warning("OPENAI_API_KEY not found, AI 분석 기능이 제한됩니다.")
            self.openai_client = None
        
        # Vector Service 초기화
        self.vector_service = VectorService()
        
        # 위치 기반 커뮤니티 유형
        self.community_types = {
            "same_apartment": {
                "name": "같은 아파트 품앗이",
                "description": "같은 아파트 단지 거주민들의 공동육아",
                "max_distance_minutes": 5,  # 단지 내 이동
                "keywords": ["품앗이", "공동돌봄", "이웃", "단지", "아파트"]
            },
            "same_daycare": {
                "name": "같은 어린이집 학부모",
                "description": "같은 어린이집을 다니는 아이들의 부모",
                "max_distance_minutes": 10,  # 어린이집 주변
                "keywords": ["어린이집", "학부모", "등하원", "교육", "돌봄"]
            },
            "same_playground": {
                "name": "같은 놀이터 엄마들",
                "description": "같은 놀이터를 이용하는 부모들",
                "max_distance_minutes": 10,  # 놀이터 주변
                "keywords": ["놀이터", "야외활동", "놀이", "엄마", "아빠"]
            },
            "neighborhood": {
                "name": "동네 육아 모임",
                "description": "같은 동네에서 육아하는 부모들",
                "max_distance_minutes": 15,  # 도보 15분
                "keywords": ["동네", "지역", "육아", "모임", "정보공유"]
            },
            "working_parents": {
                "name": "워킹맘/워킹대디",
                "description": "직장 다니는 부모들의 긴급돌봄",
                "max_distance_minutes": 20,  # 조금 더 넓은 범위
                "keywords": ["워킹맘", "워킹대디", "긴급돌봄", "직장", "맞벌이"]
            }
        }
        
    async def create_location_based_community(self, user_location: Dict, community_type: str, user_profile: Dict) -> Optional[Dict]:
        """
        사용자 위치 기반으로 실제 커뮤니티 생성
        
        Args:
            user_location: {"latitude": float, "longitude": float, "address": str}
            community_type: 커뮤니티 유형
            user_profile: 사용자 프로필
            
        Returns:
            생성된 커뮤니티 정보
        """
        if community_type not in self.community_types:
            logger.error(f"지원하지 않는 커뮤니티 유형: {community_type}")
            return None
        
        # 지원 지역 확인
        is_supported, area_name = location_service.is_location_supported(
            user_location["latitude"], user_location["longitude"]
        )
        
        if not is_supported:
            logger.warning(f"지원하지 않는 지역: {user_location['address']}")
            return None
        
        community_info = self.community_types[community_type]
        
        # 위치 기반 커뮤니티 ID 생성
        community_id = f"{area_name}_{community_type}_{int(user_location['latitude']*10000)}_{int(user_location['longitude']*10000)}"
        
        # 커뮤니티 이름 동적 생성
        community_name = await self._generate_location_based_name(
            user_location, community_info, area_name
        )
        
        community = {
            "community_id": community_id,
            "name": community_name,
            "type": community_type,
            "location": {
                "latitude": user_location["latitude"],
                "longitude": user_location["longitude"],
                "address": user_location["address"],
                "area": area_name
            },
            "description": await self._generate_community_description(
                user_location, community_info, user_profile
            ),
            "target_ages": user_profile.get("child_ages", []),
            "focus_areas": community_info["keywords"],
            "max_distance_minutes": community_info["max_distance_minutes"],
            "created_at": datetime.now().isoformat(),
            "creator_profile": {
                "user_id": user_profile.get("user_id"),
                "parenting_style": user_profile.get("parenting_style", []),
                "interests": user_profile.get("interests", [])
            },
            "member_count": 1,  # 실제 생성자 1명부터 시작
            "real_members": [user_profile.get("user_id")],  # 실제 회원 목록
            "activity_style": community_info["keywords"][:3]
        }
        
        return community
    
    async def _generate_location_based_name(self, location: Dict, community_info: Dict, area_name: str) -> str:
        """
        위치 기반 커뮤니티 이름 동적 생성
        """
        if not self.openai_client:
            return f"{area_name} {community_info['name']}"
        
        try:
            prompt = f"""
사용자 위치: {location['address']}
지역: {area_name}
커뮤니티 유형: {community_info['name']}

위 정보를 바탕으로 실제적이고 친근한 커뮤니티 이름을 생성해주세요.
- 구체적인 동네명이나 아파트명은 제외
- 지역의 특성을 반영
- 부모들이 쉽게 이해할 수 있는 이름
- 15자 이내로 간결하게

예시: "도봉구 품앗이", "노원구 놀이터 모임", "의정부 워킹맘"

커뮤니티 이름:"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.7
            )
            
            name = response.choices[0].message.content.strip().replace('"', '')
            return name
            
        except Exception as e:
            logger.error(f"커뮤니티 이름 생성 오류: {str(e)}")
            return f"{area_name} {community_info['name']}"
    
    async def _generate_community_description(self, location: Dict, community_info: Dict, user_profile: Dict) -> str:
        """
        위치 기반 커뮤니티 설명 동적 생성
        """
        if not self.openai_client:
            return community_info['description']
        
        try:
            prompt = f"""
사용자 위치: {location['address']}
커뮤니티 유형: {community_info['name']}
사용자 관심사: {user_profile.get('interests', [])}
자녀 연령: {user_profile.get('child_ages', [])}

위 정보를 바탕으로 공동육아 플랫폼에 맞는 커뮤니티 설명을 작성해주세요.
- 실제 지역 기반임을 강조
- 공동육아의 구체적 활동 포함
- 부모들이 참여하고 싶어할 만한 내용
- 100자 이내로 간결하게

커뮤니티 설명:"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            
            description = response.choices[0].message.content.strip().replace('"', '')
            return description
            
        except Exception as e:
            logger.error(f"커뮤니티 설명 생성 오류: {str(e)}")
            return community_info['description']
    
    async def find_nearby_communities(self, user_location: Dict, max_distance_minutes: int = 15) -> List[Dict]:
        """
        사용자 위치 기반 근처 커뮤니티 찾기
        
        Args:
            user_location: 사용자 위치 정보
            max_distance_minutes: 최대 거리 (분)
            
        Returns:
            근처 커뮤니티 목록
        """
        try:
            # Vector DB에서 모든 커뮤니티 조회
            all_communities = await self.vector_service.get_all_communities()
            
            nearby_communities = []
            
            for community in all_communities:
                if "location" not in community:
                    continue
                
                # 거리 계산
                if location_service.is_within_walking_distance(
                    user_location["latitude"], user_location["longitude"],
                    community["location"]["latitude"], community["location"]["longitude"],
                    max_distance_minutes
                ):
                    # 거리 정보 추가
                    distance_meters = location_service.calculate_distance(
                        user_location["latitude"], user_location["longitude"],
                        community["location"]["latitude"], community["location"]["longitude"]
                    )
                    walking_minutes = location_service.calculate_walking_time(distance_meters)
                    
                    community_with_distance = community.copy()
                    community_with_distance.update({
                        "distance_meters": distance_meters,
                        "walking_minutes": walking_minutes
                    })
                    
                    nearby_communities.append(community_with_distance)
            
            # 거리순 정렬
            nearby_communities.sort(key=lambda x: x["distance_meters"])
            
            return nearby_communities
            
        except Exception as e:
            logger.error(f"근처 커뮤니티 검색 오류: {str(e)}")
            return []
    
    async def join_community(self, community_id: str, user_id: str) -> bool:
        """
        커뮤니티 가입
        
        Args:
            community_id: 커뮤니티 ID
            user_id: 사용자 ID
            
        Returns:
            가입 성공 여부
        """
        try:
            # 커뮤니티 정보 조회
            community = await self.vector_service.get_community_by_id(community_id)
            if not community:
                return False
            
            # 이미 가입된 회원인지 확인
            real_members = community.get("real_members", [])
            if user_id in real_members:
                logger.info(f"사용자 {user_id}는 이미 커뮤니티 {community_id}의 회원입니다")
                return True
            
            # 회원 추가
            real_members.append(user_id)
            community["real_members"] = real_members
            community["member_count"] = len(real_members)
            community["updated_at"] = datetime.now().isoformat()
            
            # 커뮤니티 정보 업데이트
            success = await self.vector_service.update_community(community_id, community)
            
            if success:
                logger.info(f"사용자 {user_id}가 커뮤니티 {community_id}에 가입했습니다")
            
            return success
            
        except Exception as e:
            logger.error(f"커뮤니티 가입 오류: {str(e)}")
            return False
    
    async def create_and_add_community(self, user_location: Dict, community_type: str, user_profile: Dict) -> Optional[str]:
        """
        위치 기반 커뮤니티 생성 및 Vector DB 추가
        
        Args:
            user_location: 사용자 위치
            community_type: 커뮤니티 유형
            user_profile: 사용자 프로필
            
        Returns:
            생성된 커뮤니티 ID
        """
        try:
            # 커뮤니티 생성
            community = await self.create_location_based_community(
                user_location, community_type, user_profile
            )
            
            if not community:
                return None
            
            # Vector DB에 추가
            success = await self.vector_service.add_community_info(community)
            
            if success:
                logger.info(f"위치 기반 커뮤니티 생성됨: {community['community_id']}")
                return community["community_id"]
            else:
                logger.error("커뮤니티 Vector DB 추가 실패")
                return None
                
        except Exception as e:
            logger.error(f"커뮤니티 생성 및 추가 오류: {str(e)}")
            return None

# 전역 인스턴스
real_community_service = RealCommunityMatchingService()
