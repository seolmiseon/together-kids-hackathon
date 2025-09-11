"""
공동구매 및 나눔 서비스
⭐⭐ 기저귀, 장난감, 육아용품 공동구매 및 나눔 플랫폼
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class ShareType(str, Enum):
    """공유 유형"""
    GROUP_PURCHASE = "group_purchase"  # 공동구매
    SHARING = "sharing"                # 나눔
    EXCHANGE = "exchange"              # 교환
    RENTAL = "rental"                  # 대여

class ItemCategory(str, Enum):
    """아이템 카테고리"""
    DIAPERS = "diapers"                # 기저귀
    BABY_FOOD = "baby_food"            # 이유식/유아식품
    TOYS = "toys"                      # 장난감
    CLOTHES = "clothes"                # 아동복
    BOOKS = "books"                    # 도서
    FURNITURE = "furniture"            # 아동 가구
    STROLLER = "stroller"              # 유모차
    CAR_SEAT = "car_seat"              # 카시트
    FEEDING = "feeding"                # 수유용품
    BATH = "bath"                      # 목욕용품
    EDUCATIONAL = "educational"        # 교육용품
    OUTDOOR = "outdoor"                # 야외활동용품

class ItemStatus(str, Enum):
    """아이템 상태"""
    ACTIVE = "active"                  # 활성
    COMPLETED = "completed"            # 완료
    CANCELLED = "cancelled"            # 취소
    EXPIRED = "expired"                # 만료

class GroupPurchaseShareService:
    def __init__(self):
        # 임시 데이터 저장소 (실제로는 데이터베이스 사용)
        self.items = {}
        self.participants = {}
        
    def create_group_purchase(self, creator_id: str, item_data: Dict) -> str:
        """
        공동구매 생성
        
        Args:
            creator_id: 생성자 ID
            item_data: 아이템 정보
            
        Returns:
            생성된 공동구매 ID
        """
        try:
            item_id = str(uuid.uuid4())
            
            # 기본값 설정
            current_time = datetime.now()
            
            group_purchase = {
                "item_id": item_id,
                "creator_id": creator_id,
                "share_type": ShareType.GROUP_PURCHASE,
                "title": item_data.get("title", ""),
                "description": item_data.get("description", ""),
                "category": item_data.get("category", ItemCategory.DIAPERS),
                "target_quantity": item_data.get("target_quantity", 1),
                "current_participants": 1,  # 생성자 포함
                "price_per_unit": item_data.get("price_per_unit", 0),
                "total_price": item_data.get("total_price", 0),
                "location": item_data.get("location", {}),
                "pickup_location": item_data.get("pickup_location", ""),
                "deadline": item_data.get("deadline", (current_time + timedelta(days=7)).isoformat()),
                "status": ItemStatus.ACTIVE,
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat(),
                "participants": [creator_id],
                "images": item_data.get("images", []),
                "requirements": item_data.get("requirements", ""),
                "contact_method": item_data.get("contact_method", "앱 내 메시지")
            }
            
            self.items[item_id] = group_purchase
            
            logger.info(f"공동구매 생성됨: {item_id}")
            return item_id
            
        except Exception as e:
            logger.error(f"공동구매 생성 오류: {str(e)}")
            return None
    
    def create_sharing_item(self, creator_id: str, item_data: Dict) -> str:
        """
        나눔 아이템 생성
        
        Args:
            creator_id: 생성자 ID
            item_data: 아이템 정보
            
        Returns:
            생성된 나눔 아이템 ID
        """
        try:
            item_id = str(uuid.uuid4())
            current_time = datetime.now()
            
            sharing_item = {
                "item_id": item_id,
                "creator_id": creator_id,
                "share_type": item_data.get("share_type", ShareType.SHARING),
                "title": item_data.get("title", ""),
                "description": item_data.get("description", ""),
                "category": item_data.get("category", ItemCategory.TOYS),
                "condition": item_data.get("condition", "보통"),  # 새것, 좋음, 보통, 나쁨
                "original_price": item_data.get("original_price", 0),
                "sharing_price": item_data.get("sharing_price", 0),  # 나눔은 0, 
                "location": item_data.get("location", {}),
                "pickup_location": item_data.get("pickup_location", ""),
                "available_until": item_data.get("available_until", (current_time + timedelta(days=30)).isoformat()),
                "status": ItemStatus.ACTIVE,
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat(),
                "interested_users": [],
                "images": item_data.get("images", []),
                "age_range": item_data.get("age_range", ""),
                "brand": item_data.get("brand", ""),
                "contact_method": item_data.get("contact_method", "앱 내 메시지")
            }
            
            # 대여인 경우 추가 정보
            if item_data.get("share_type") == ShareType.RENTAL:
                sharing_item.update({
                    "rental_period": item_data.get("rental_period", "1주"),
                    "deposit": item_data.get("deposit", 0)
                })
            
            self.items[item_id] = sharing_item
            
            logger.info(f"나눔 아이템 생성됨: {item_id}")
            return item_id
            
        except Exception as e:
            logger.error(f"나눔 아이템 생성 오류: {str(e)}")
            return None
    
    def join_group_purchase(self, item_id: str, user_id: str, quantity: int = 1) -> bool:
        """
        공동구매 참여
        
        Args:
            item_id: 공동구매 ID
            user_id: 사용자 ID
            quantity: 참여 수량
            
        Returns:
            참여 성공 여부
        """
        try:
            if item_id not in self.items:
                logger.error(f"존재하지 않는 공동구매: {item_id}")
                return False
            
            item = self.items[item_id]
            
            # 공동구매인지 확인
            if item["share_type"] != ShareType.GROUP_PURCHASE:
                logger.error(f"공동구매가 아닌 아이템: {item_id}")
                return False
            
            # 이미 참여했는지 확인
            if user_id in item["participants"]:
                logger.info(f"사용자 {user_id}는 이미 공동구매 {item_id}에 참여했습니다")
                return True
            
            # 목표 수량 확인
            if item["current_participants"] >= item["target_quantity"]:
                logger.warning(f"공동구매 {item_id}가 이미 마감되었습니다")
                return False
            
            # 참여 추가
            item["participants"].append(user_id)
            item["current_participants"] = len(item["participants"])
            item["updated_at"] = datetime.now().isoformat()
            
            # 목표 달성 시 상태 변경
            if item["current_participants"] >= item["target_quantity"]:
                item["status"] = ItemStatus.COMPLETED
            
            logger.info(f"사용자 {user_id}가 공동구매 {item_id}에 참여했습니다")
            return True
            
        except Exception as e:
            logger.error(f"공동구매 참여 오류: {str(e)}")
            return False
    
    def express_interest(self, item_id: str, user_id: str) -> bool:
        """
        나눔 아이템에 관심 표현
        
        Args:
            item_id: 아이템 ID
            user_id: 사용자 ID
            
        Returns:
            관심 표현 성공 여부
        """
        try:
            if item_id not in self.items:
                logger.error(f"존재하지 않는 아이템: {item_id}")
                return False
            
            item = self.items[item_id]
            
            # 나눔/교환/대여 아이템인지 확인
            if item["share_type"] == ShareType.GROUP_PURCHASE:
                logger.error(f"공동구매 아이템에는 관심 표현할 수 없습니다: {item_id}")
                return False
            
            # 이미 관심 표현했는지 확인
            if user_id in item["interested_users"]:
                logger.info(f"사용자 {user_id}는 이미 아이템 {item_id}에 관심을 표현했습니다")
                return True
            
            # 관심 표현 추가
            item["interested_users"].append(user_id)
            item["updated_at"] = datetime.now().isoformat()
            
            logger.info(f"사용자 {user_id}가 아이템 {item_id}에 관심을 표현했습니다")
            return True
            
        except Exception as e:
            logger.error(f"관심 표현 오류: {str(e)}")
            return False
    
    def search_items(self, 
                    user_location: Dict = None,
                    category: str = None,
                    share_type: str = None,
                    max_distance_km: float = 5.0,
                    keyword: str = None) -> List[Dict]:
        """
        아이템 검색
        
        Args:
            user_location: 사용자 위치
            category: 카테고리 필터
            share_type: 공유 유형 필터
            max_distance_km: 최대 거리 (km)
            keyword: 검색 키워드
            
        Returns:
            검색된 아이템 목록
        """
        try:
            filtered_items = []
            
            for item in self.items.values():
                # 활성 상태인 아이템만
                if item["status"] != ItemStatus.ACTIVE:
                    continue
                
                # 카테고리 필터
                if category and item["category"] != category:
                    continue
                
                # 공유 유형 필터
                if share_type and item["share_type"] != share_type:
                    continue
                
                # 키워드 검색
                if keyword:
                    search_text = f"{item['title']} {item['description']}".lower()
                    if keyword.lower() not in search_text:
                        continue
                
                # 거리 필터 (위치 정보가 있는 경우)
                if user_location and item.get("location"):
                    # 실제로는 location_service를 사용해서 거리 계산
                    # 여기서는 간단히 구현
                    pass
                
                filtered_items.append(item)
            
            # 최신 순으로 정렬
            filtered_items.sort(key=lambda x: x["created_at"], reverse=True)
            
            return filtered_items
            
        except Exception as e:
            logger.error(f"아이템 검색 오류: {str(e)}")
            return []
    
    def get_my_items(self, user_id: str) -> Dict:
        """
        내가 등록한/참여한 아이템 목록
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            내 아이템 정보
        """
        try:
            my_created = []  # 내가 등록한 것
            my_participated = []  # 내가 참여한 것
            my_interested = []  # 내가 관심 표현한 것
            
            for item in self.items.values():
                # 내가 등록한 아이템
                if item["creator_id"] == user_id:
                    my_created.append(item)
                
                # 내가 참여한 공동구매
                elif (item["share_type"] == ShareType.GROUP_PURCHASE and 
                      user_id in item.get("participants", [])):
                    my_participated.append(item)
                
                # 내가 관심 표현한 아이템
                elif user_id in item.get("interested_users", []):
                    my_interested.append(item)
            
            return {
                "created": my_created,
                "participated": my_participated,
                "interested": my_interested
            }
            
        except Exception as e:
            logger.error(f"내 아이템 조회 오류: {str(e)}")
            return {"created": [], "participated": [], "interested": []}
    
    def get_popular_categories(self) -> List[Dict]:
        """
        인기 카테고리 조회
        
        Returns:
            인기 카테고리 목록
        """
        try:
            category_counts = {}
            
            for item in self.items.values():
                if item["status"] == ItemStatus.ACTIVE:
                    category = item["category"]
                    category_counts[category] = category_counts.get(category, 0) + 1
            
            # 카테고리별 정렬
            sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {
                    "category": category,
                    "count": count,
                    "name": self._get_category_name(category)
                }
                for category, count in sorted_categories
            ]
            
        except Exception as e:
            logger.error(f"인기 카테고리 조회 오류: {str(e)}")
            return []
    
    def _get_category_name(self, category: str) -> str:
        """카테고리 한글명 반환"""
        category_names = {
            "diapers": "기저귀",
            "baby_food": "이유식/유아식품",
            "toys": "장난감",
            "clothes": "아동복",
            "books": "도서",
            "furniture": "아동 가구",
            "stroller": "유모차",
            "car_seat": "카시트",
            "feeding": "수유용품",
            "bath": "목욕용품",
            "educational": "교육용품",
            "outdoor": "야외활동용품"
        }
        return category_names.get(category, category)

# 전역 인스턴스
group_purchase_service = GroupPurchaseShareService()
