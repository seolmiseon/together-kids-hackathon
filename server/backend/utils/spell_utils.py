import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from math import radians, cos, sin, asin, sqrt
from fastapi import HTTPException
from firebase_admin import firestore
import firebase_admin

# 로거 설정
logger = logging.getLogger(__name__)



def get_firestore_client():
    """Firestore 클라이언트를 안전하게 가져오는 함수"""
    try:
        if firebase_admin._apps:
            return firestore.client()
        else:
            logger.warning("Firebase가 초기화되지 않았습니다.")
            return None
    except Exception as e:
        logger.error(f"Firestore 클라이언트 가져오기 실패: {e}")
        return None

def get_db():
    """데이터베이스 클라이언트를 가져오는 헬퍼 함수"""
    return get_firestore_client()

async def gps_safety_spell(user_id: str, child_name: str, location: str, safe_zone: str = None):
    """GPS 안전구역 이탈 알림"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Firebase 연결을 사용할 수 없습니다.")
    alert = {
        "id": int(datetime.now().timestamp() * 1000),
        "type": "safety",
        "title": f"🚨 {child_name} 안전구역 이탈",
        "message": f"현재 위치: {location}",
        "time": firestore.SERVER_TIMESTAMP,
        "isRead": False
    }

    db.collection("users").document(user_id).collection("notifications").add(alert)
    return f"GPS 알림 생성 완료: {child_name}"

async def schedule_conflict_spell(user_id: str, conflict_details: str, date: str = None):
    """일정 충돌 알림"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Firebase 연결을 사용할 수 없습니다.")
    alert = {
        "id": int(datetime.now().timestamp() * 1000),
        "type": "schedule",
        "title": "⏰ 일정 충돌 발생!",
        "message": conflict_details,
        "time": firestore.SERVER_TIMESTAMP,
        "isRead": False
    }
    db.collection("users").document(user_id).collection("notifications").add(alert)
    return "일정 충돌 알림 완료"

async def emergency_spell(user_id: str, emergency_message: str, apartment_id: str = None):
    """응급상황 알림"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Firebase 연결을 사용할 수 없습니다.")
    alert = {
        "id": int(datetime.now().timestamp() * 1000),
        "type": "emergency",
        "title": "🚨 긴급상황!",
        "message": emergency_message,
        "time": firestore.SERVER_TIMESTAMP,
        "isRead": False
    }
    db.collection("users").document(user_id).collection("notifications").add(alert)
    if apartment_id:
        community_alert = { "message": f"🆘 {apartment_id} 아파트 긴급상황 발생!" }
        db.collection("community_alerts").add(community_alert)

    return f"응급 알림 전송 완료"

async def ai_recommendation_spell(user_id: str, recommendation: str, category: str = "general"):
    """AI 추천 알림"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Firebase 연결을 사용할 수 없습니다.")
    alert = {
        "id": int(datetime.now().timestamp() * 1000),
        "type": "ai_recommendation",
        "title": f"💡 AI 추천 ({category})",
        "message": recommendation,
        "time": firestore.SERVER_TIMESTAMP,
        "isRead": False
    }
    db.collection("users").document(user_id).collection("notifications").add(alert)
    return f"AI 추천 알림 완료"


# --- 알림 관리 함수 ---
async def get_user_alerts(user_id: str, limit: int = 10) -> List[Dict]:
    """사용자의 알림 목록을 Firestore에서 조회합니다."""
    db = get_db()
    if not db:
        return []

    try:
        alerts_ref = db.collection("users").document(user_id).collection("notifications")
        # 최신순으로 정렬하여 limit만큼 가져옵니다.
        query = alerts_ref.order_by("time", direction=firestore.Query.DESCENDING).limit(limit)
        docs_stream = query.stream()
        alerts_list = [doc.to_dict() for doc in docs_stream]
        return alerts_list
    except Exception as e:
        print(f"알림 조회 중 오류 발생: {e}")
        return []

async def mark_alert_read(user_id: str, alert_id: str) -> bool:
    """특정 알림을 읽음 처리합니다."""
    db = get_db()
    if not db:
        return False
    try:
        alert_ref = db.collection("users").document(user_id).collection("notifications").document(alert_id)
        await alert_ref.update({"isRead": True})
        return True
    except Exception as e:
        print(f"알림 읽음 처리 중 오류 발생: {e}")
        return False

async def clear_user_alerts(user_id: str) -> str:
    """사용자의 모든 알림을 '삭제됨'으로 표시합니다 (Soft Delete)."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Firebase 연결을 사용할 수 없습니다.")
    try:
        alerts_ref = db.collection("users").document(user_id).collection("notifications")

        docs_stream = alerts_ref.where("isDeleted", "==", False).stream()

        batch = db.batch()
        count = 0
        for doc in docs_stream:
            batch.update(doc.reference, {"isDeleted": True})
            count += 1
            if count == 499:
                batch.commit()
                batch = db.batch() # 새 배치 시작
        
        # 남은 배치가 있다면 커밋합니다.
        if count > 0:
            batch.commit()
        
        print(f"{user_id}의 알림 {count}개를 '삭제됨'으로 처리했습니다.")
        return "알림 전체 삭제 요청이 처리되었습니다."
    except Exception as e:
        print(f"알림 전체 삭제 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="알림 삭제 중 오류가 발생했습니다.")

# --- 유틸리티 및 트리거 함수 ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """두 좌표 간의 거리를 계산 (m)"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # 지구 반지름 (km)
    return c * r * 1000
pass


async def check_geofence_exit(current_lat, current_lng, safe_zones):
    """지오펜스 이탈 체크"""
    for zone in safe_zones:
        distance = haversine_distance(current_lat, current_lng, zone['latitude'], zone['longitude'])
        if distance > zone['radius']:
            return {"is_outside": True, "zone_name": zone['name'], "distance": distance}
    return {"is_outside": False}
pass

async def check_schedule_conflict(user_id: str, new_schedule: Dict[str, Any]) -> bool:
    """일정 충돌 체크"""
    db = get_db()
    if not db:
        return False
    try:
        existing_schedules_ref = db.collection("users").document(user_id).collection("schedules")
        existing_raw = existing_schedules_ref.stream()
        
        existing_schedules = [doc.to_dict() for doc in existing_raw]
        new_start = datetime.fromisoformat(new_schedule['start_time'])
        new_end = datetime.fromisoformat(new_schedule['end_time'])
        
        for schedule in existing_schedules:
            exist_start = datetime.fromisoformat(schedule['start_time'])
            exist_end = datetime.fromisoformat(schedule['end_time'])
            if new_start < exist_end and new_end > exist_start:
                return True
    except Exception as e:
        print(f"일정 충돌 체크 중 오류 발생: {e}")
    
    return False

pass

async def auto_spell_trigger(trigger_type: str, data: Dict[str, Any]) -> str:
    """자동 스펠 트리거 - 조건 체크 후 알림 실행"""
    if trigger_type == "gps_safety":
        geofence_result = await check_geofence_exit(data['current_lat'], data['current_lng'], data['safe_zones'])
        if geofence_result['is_outside']:
            return await gps_safety_spell(data['user_id'], data['child_name'], data['current_location'])
    
    elif trigger_type == "schedule_conflict":
        if await check_schedule_conflict(data['user_id'], data['schedule']):
            return await schedule_conflict_spell(data['user_id'], f"{data['schedule']['title']} 일정이 기존 일정과 충돌합니다")
    
    elif trigger_type == "emergency":
        return await emergency_spell(data['user_id'], data['message'], data.get('apartment_id'))
    
    return "조건 미충족 또는 트리거 없음"
pass
