"""
일정 알림 전송 서비스

그룹 멤버들에게 일정 알림을 전송하는 기능을 제공합니다.
Firestore에 알림 저장 + FCM 푸시 알림 전송
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from firebase_admin import firestore, messaging
import firebase_admin

logger = logging.getLogger(__name__)


class NotificationService:
    """일정 알림 전송 서비스"""
    
    def __init__(self):
        if not firebase_admin._apps:
            try:
                from ...backend.main import cred
                firebase_admin.initialize_app(cred)
            except Exception as e:
                logger.warning(f"Firebase 초기화 실패: {e}")
        
        self.db = firestore.client() if firebase_admin._apps else None
    
    async def send_schedule_notification(
        self,
        user_id: str,
        schedule_info: Dict[str, Any],
        member_ids: List[str]
    ) -> Dict[str, Any]:
        """
        그룹 멤버들에게 일정 알림 전송
        
        Args:
            user_id: 일정 생성자 ID
            schedule_info: 일정 정보
            member_ids: 알림을 받을 멤버 ID 목록
            
        Returns:
            알림 전송 결과
        """
        if not self.db:
            logger.error("Firestore 연결이 없어 알림을 전송할 수 없습니다.")
            return {"success": False, "message": "Firestore 연결 실패", "sent_count": 0}
        
        if not member_ids:
            logger.warning("알림을 받을 멤버가 없습니다.")
            return {"success": True, "message": "알림 대상 없음", "sent_count": 0}
        
        try:
            # 일정 정보에서 알림 메시지 생성
            time_str = schedule_info.get("time", "시간 미정")
            location_str = schedule_info.get("location", "장소 미정")
            activity_str = schedule_info.get("activity", "활동")
            
            # 시간 포맷팅
            if time_str and time_str != "null":
                try:
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    time_str = dt.strftime("%Y년 %m월 %d일 %H시 %M분")
                except:
                    pass
            
            # 알림 메시지 생성
            title = f"📅 {activity_str or '일정'} 초대"
            message = f"{time_str}\n장소: {location_str}"
            if schedule_info.get("rsvp_required"):
                message += "\n\n참석 여부를 알려주세요!"
            
            sent_count = 0
            failed_count = 0
            fcm_sent_count = 0
            fcm_failed_count = 0
            
            # 각 멤버에게 알림 전송
            for member_id in member_ids:
                try:
                    alert = {
                        "id": int(datetime.now().timestamp() * 1000) + sent_count,
                        "type": "schedule_invite",
                        "title": title,
                        "message": message,
                        "time": firestore.SERVER_TIMESTAMP,
                        "isRead": False,
                        "schedule_info": {
                            "time": schedule_info.get("time"),
                            "location": schedule_info.get("location"),
                            "activity": schedule_info.get("activity"),
                            "rsvp_required": schedule_info.get("rsvp_required", False),
                            "created_by": user_id,
                            "schedule_id": schedule_info.get("schedule_id")
                        }
                    }
                    
                    # 1. Firestore에 알림 저장
                    self.db.collection("users").document(member_id).collection("notifications").add(alert)
                    sent_count += 1
                    
                    # 2. FCM 푸시 알림 전송 (토큰이 있는 경우)
                    fcm_success = await self._send_fcm_notification(member_id, title, message, schedule_info)
                    if fcm_success:
                        fcm_sent_count += 1
                    else:
                        fcm_failed_count += 1
                    
                    logger.info(f"알림 전송 완료: {member_id} (FCM: {'성공' if fcm_success else '실패/토큰없음'})")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"멤버 {member_id}에게 알림 전송 실패: {e}")
            
            result = {
                "success": True,
                "message": f"{sent_count}명에게 알림 전송 완료 (FCM: {fcm_sent_count}명)",
                "sent_count": sent_count,
                "failed_count": failed_count,
                "fcm_sent_count": fcm_sent_count,
                "fcm_failed_count": fcm_failed_count,
                "total_members": len(member_ids)
            }
            
            logger.info(f"일정 알림 전송 완료: {result}")
            return result
            
        except Exception as e:
            logger.error(f"일정 알림 전송 중 오류 발생: {e}")
            return {"success": False, "message": str(e), "sent_count": 0}
    
    async def _send_fcm_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        schedule_info: Dict[str, Any]
    ) -> bool:
        """
        FCM 푸시 알림 전송
        
        Args:
            user_id: 사용자 ID
            title: 알림 제목
            body: 알림 본문
            schedule_info: 일정 정보
            
        Returns:
            전송 성공 여부
        """
        if not self.db:
            return False
        
        try:
            # 사용자의 FCM 토큰 조회
            user_ref = self.db.collection("users").document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                logger.warning(f"사용자 {user_id}를 찾을 수 없습니다.")
                return False
            
            user_data = user_doc.to_dict()
            fcm_tokens = user_data.get("fcm_tokens", [])  # 여러 기기 지원을 위해 배열
            
            if not fcm_tokens:
                logger.info(f"사용자 {user_id}의 FCM 토큰이 없습니다.")
                return False
            
            # FCM 메시지 생성
            # 여러 토큰에 전송 (멀티캐스트)
            messages = []
            for token in fcm_tokens:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    data={
                        "type": "schedule_invite",
                        "schedule_id": str(schedule_info.get("schedule_id", "")),
                        "time": str(schedule_info.get("time", "")),
                        "location": str(schedule_info.get("location", "")),
                        "activity": str(schedule_info.get("activity", "")),
                        "rsvp_required": str(schedule_info.get("rsvp_required", False))
                    },
                    token=token,
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(
                            channel_id="schedule_notifications",
                            sound="default",
                            priority="high"
                        )
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                sound="default",
                                badge=1
                            )
                        )
                    )
                )
                messages.append(message)
            
            # FCM 전송 (멀티캐스트)
            if messages:
                response = messaging.send_all(messages)
                logger.info(f"FCM 전송 성공: {response.success_count}개 성공, {response.failure_count}개 실패")
                
                # 실패한 토큰 제거 (만료된 토큰 등)
                if response.failure_count > 0:
                    failed_tokens = []
                    for idx, result in enumerate(response.responses):
                        if not result.success:
                            failed_tokens.append(fcm_tokens[idx])
                            logger.warning(f"FCM 전송 실패 토큰: {fcm_tokens[idx][:20]}... - {result.exception}")
                    
                    # 실패한 토큰 제거
                    if failed_tokens:
                        valid_tokens = [t for t in fcm_tokens if t not in failed_tokens]
                        user_ref.update({"fcm_tokens": valid_tokens})
                        logger.info(f"만료된 FCM 토큰 {len(failed_tokens)}개 제거됨")
                
                return response.success_count > 0
            
            return False
            
        except messaging.UnregisteredError:
            # 등록되지 않은 토큰 - 사용자 문서에서 제거
            logger.warning(f"등록되지 않은 FCM 토큰: {user_id}")
            user_ref.update({"fcm_tokens": []})
            return False
        except Exception as e:
            logger.error(f"FCM 알림 전송 실패: {e}")
            return False


# 전역 인스턴스
notification_service = NotificationService()

