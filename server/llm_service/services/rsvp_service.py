"""
RSVP 수집 및 관리 서비스

일정에 대한 참석/불참 응답을 수집하고 관리합니다.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from firebase_admin import firestore
import firebase_admin

logger = logging.getLogger(__name__)


class RSVPService:
    """RSVP 수집 및 관리 서비스"""
    
    def __init__(self):
        if not firebase_admin._apps:
            try:
                from ...backend.main import cred
                firebase_admin.initialize_app(cred)
            except Exception as e:
                logger.warning(f"Firebase 초기화 실패: {e}")
        
        self.db = firestore.client() if firebase_admin._apps else None
    
    async def create_schedule_with_rsvp(
        self,
        creator_id: str,
        schedule_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        RSVP가 필요한 일정 생성
        
        Args:
            creator_id: 일정 생성자 ID
            schedule_info: 일정 정보
            
        Returns:
            생성된 일정 ID
        """
        if not self.db:
            logger.error("Firestore 연결이 없어 일정을 생성할 수 없습니다.")
            return None
        
        try:
            schedule_id = f"schedule_{int(datetime.now().timestamp() * 1000)}"
            
            schedule_data = {
                "schedule_id": schedule_id,
                "creator_id": creator_id,
                "time": schedule_info.get("time"),
                "location": schedule_info.get("location"),
                "activity": schedule_info.get("activity"),
                "rsvp_required": schedule_info.get("rsvp_required", False),
                "created_at": firestore.SERVER_TIMESTAMP,
                "rsvp_responses": {},  # {user_id: "attending" | "not_attending" | "maybe"}
                "attending_count": 0,
                "not_attending_count": 0,
                "maybe_count": 0
            }
            
            # Firestore에 일정 저장
            self.db.collection("schedules").document(schedule_id).set(schedule_data)
            
            logger.info(f"일정 생성 완료: {schedule_id}")
            return schedule_id
            
        except Exception as e:
            logger.error(f"일정 생성 실패: {e}")
            return None
    
    async def submit_rsvp(
        self,
        schedule_id: str,
        user_id: str,
        response: str  # "attending", "not_attending", "maybe"
    ) -> Dict[str, Any]:
        """
        RSVP 응답 제출
        
        Args:
            schedule_id: 일정 ID
            user_id: 사용자 ID
            response: 응답 ("attending", "not_attending", "maybe")
            
        Returns:
            응답 결과
        """
        if not self.db:
            return {"success": False, "message": "Firestore 연결 실패"}
        
        if response not in ["attending", "not_attending", "maybe"]:
            return {"success": False, "message": "잘못된 응답 형식입니다. (attending, not_attending, maybe)"}
        
        try:
            schedule_ref = self.db.collection("schedules").document(schedule_id)
            schedule_doc = schedule_ref.get()
            
            if not schedule_doc.exists:
                return {"success": False, "message": "일정을 찾을 수 없습니다."}
            
            schedule_data = schedule_doc.to_dict()
            rsvp_responses = schedule_data.get("rsvp_responses", {})
            
            # 이전 응답이 있으면 카운트 감소
            previous_response = rsvp_responses.get(user_id)
            if previous_response:
                count_key = f"{previous_response}_count"
                current_count = schedule_data.get(count_key, 0)
                schedule_ref.update({count_key: max(0, current_count - 1)})
            
            # 새 응답 저장
            rsvp_responses[user_id] = response
            count_key = f"{response}_count"
            current_count = schedule_data.get(count_key, 0)
            
            # Firestore 업데이트
            schedule_ref.update({
                "rsvp_responses": rsvp_responses,
                count_key: current_count + 1,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"RSVP 응답 저장 완료: {schedule_id} - {user_id} - {response}")
            
            return {
                "success": True,
                "message": "RSVP 응답이 저장되었습니다.",
                "schedule_id": schedule_id,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"RSVP 응답 저장 실패: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_schedule_rsvp_status(self, schedule_id: str) -> Dict[str, Any]:
        """
        일정의 RSVP 상태 조회
        
        Args:
            schedule_id: 일정 ID
            
        Returns:
            RSVP 상태 정보
        """
        if not self.db:
            return {"success": False, "message": "Firestore 연결 실패"}
        
        try:
            schedule_ref = self.db.collection("schedules").document(schedule_id)
            schedule_doc = schedule_ref.get()
            
            if not schedule_doc.exists:
                return {"success": False, "message": "일정을 찾을 수 없습니다."}
            
            schedule_data = schedule_doc.to_dict()
            
            return {
                "success": True,
                "schedule_id": schedule_id,
                "attending_count": schedule_data.get("attending_count", 0),
                "not_attending_count": schedule_data.get("not_attending_count", 0),
                "maybe_count": schedule_data.get("maybe_count", 0),
                "total_responses": len(schedule_data.get("rsvp_responses", {})),
                "rsvp_responses": schedule_data.get("rsvp_responses", {})
            }
            
        except Exception as e:
            logger.error(f"RSVP 상태 조회 실패: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_user_rsvp_status(self, user_id: str) -> List[Dict[str, Any]]:
        """
        사용자가 응답한 모든 RSVP 일정 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            사용자의 RSVP 일정 목록
        """
        if not self.db:
            return []
        
        try:
            schedules_ref = self.db.collection("schedules")
            # 사용자 ID가 rsvp_responses에 포함된 일정만 조회
            schedules_stream = schedules_ref.stream()
            
            user_schedules = []
            for schedule_doc in schedules_stream:
                schedule_data = schedule_doc.to_dict()
                rsvp_responses = schedule_data.get("rsvp_responses", {})
                
                if user_id in rsvp_responses:
                    user_schedules.append({
                        "schedule_id": schedule_doc.id,
                        "time": schedule_data.get("time"),
                        "location": schedule_data.get("location"),
                        "activity": schedule_data.get("activity"),
                        "response": rsvp_responses[user_id],
                        "created_at": schedule_data.get("created_at")
                    })
            
            return user_schedules
            
        except Exception as e:
            logger.error(f"사용자 RSVP 일정 조회 실패: {e}")
            return []


# 전역 인스턴스
rsvp_service = RSVPService()

