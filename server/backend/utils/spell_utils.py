import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from math import radians, cos, sin, asin, sqrt


from ..redis_client import redis_client, set_cache, get_cache


async def gps_safety_spell(user_id: str, child_name: str, location: str, safe_zone: str = None):
    """GPS 안전구역 이탈 알림"""
    alert = {
        "id": int(datetime.now().timestamp() * 1000),
        "type": "safety",
        "title": f"🚨 {child_name} 안전구역 이탈",
        "message": f"현재 위치: {location}",
        "time": datetime.now().isoformat(),
        "isRead": False
    }

    await redis_client.lpush(f"notifications:{user_id}", json.dumps(alert))
    await redis_client.expire(f"notifications:{user_id}", 86400)
    return f"GPS 알림 전송 완료: {child_name}"

async def schedule_conflict_spell(user_id: str, conflict_details: str, date: str = None):
    """일정 충돌 알림"""
    alert = {
        "id": int(datetime.now().timestamp() * 1000),
        "type": "schedule",
        "title": "⏰ 일정 충돌 발생!",
        "message": conflict_details,
        "time": datetime.now().isoformat(),
        "isRead": False
    }
    await redis_client.lpush(f"notifications:{user_id}", json.dumps(alert))
    return "일정 충돌 알림 완료"

async def emergency_spell(user_id: str, emergency_message: str, apartment_id: str = None):
    """응급상황 알림"""
    alert = {
        "id": int(datetime.now().timestamp() * 1000),
        "type": "emergency",
        "title": "🚨 긴급상황!",
        "message": emergency_message,
        "time": datetime.now().isoformat(),
        "isRead": False
    }
    await redis_client.lpush(f"notifications:{user_id}", json.dumps(alert))
    
    if apartment_id:
        community_alert = { "message": f"🆘 {apartment_id} 아파트 긴급상황 발생!" }
        await redis_client.lpush(f"community_alerts:{apartment_id}", json.dumps(community_alert))
    
    return f"응급 알림 전송 완료"

async def ai_recommendation_spell(user_id: str, recommendation: str, category: str = "general"):
    """AI 추천 알림"""
    alert = {
        "id": int(datetime.now().timestamp() * 1000),
        "type": "ai_recommendation",
        "title": f"💡 AI 추천 ({category})",
        "message": recommendation,
        "time": datetime.now().isoformat(),
        "isRead": False
    }
    await redis_client.lpush(f"notifications:{user_id}", json.dumps(alert))
    return f"AI 추천 알림 완료"


# --- 알림 관리 함수 ---
async def get_user_alerts(user_id: str, limit: int = 10) -> List[Dict]:
    """사용자의 알림 목록을 Redis에서 조회합니다."""
    notification_key = f"notifications:{user_id}"
    try:
       
        alerts_raw = await redis_client.lrange(notification_key, 0, limit - 1)
        if not alerts_raw:
            return []
        return [json.loads(alert) for alert in alerts_raw]
    except Exception as e:
        print(f"알림 조회 중 오류 발생: {e}")
        return []

async def mark_alert_read(user_id: str, alert_id: str) -> bool:
    """특정 알림을 읽음 처리합니다."""
    notification_key = f"notifications:{user_id}"
    try:
        all_alerts_raw = await redis_client.lrange(notification_key, 0, -1)
        for i, alert_str in enumerate(all_alerts_raw):
            alert = json.loads(alert_str)
            if str(alert.get("id")) == alert_id:
                alert["isRead"] = True
                await redis_client.lset(notification_key, i, json.dumps(alert))
                return True
        return False
    except Exception as e:
        print(f"알림 읽음 처리 중 오류 발생: {e}")
        return False

async def clear_user_alerts(user_id: str) -> str:
    """사용자 알림 전체 삭제"""
    await redis_client.delete(f"notifications:{user_id}")
    return "알림 전체 삭제 완료"


# --- 유틸리티 및 트리거 함수 ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """두 좌표 간의 거리를 계산 (m)"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # 지구 반지름 (km)
    return c * r * 1000

async def check_geofence_exit(current_lat, current_lng, safe_zones):
    """지오펜스 이탈 체크"""
    for zone in safe_zones:
        distance = haversine_distance(current_lat, current_lng, zone['latitude'], zone['longitude'])
        if distance > zone['radius']:
            return {"is_outside": True, "zone_name": zone['name'], "distance": distance}
    return {"is_outside": False}

async def check_schedule_conflict(user_id: str, new_schedule: Dict[str, Any]) -> bool:
    """일정 충돌 체크"""
    existing_schedules_key = f"schedules:{user_id}"
    existing_raw = await get_cache(existing_schedules_key)
    if not existing_raw: return False
    
    existing_schedules = json.loads(existing_raw)
    new_start = datetime.fromisoformat(new_schedule['start_time'])
    new_end = datetime.fromisoformat(new_schedule['end_time'])
    
    for schedule in existing_schedules:
        exist_start = datetime.fromisoformat(schedule['start_time'])
        exist_end = datetime.fromisoformat(schedule['end_time'])
        if new_start < exist_end and new_end > exist_start:
            return True
    return False

async def auto_spell_trigger(trigger_type: str, data: Dict[str, Any]) -> str:
    """자동 스펠 트리거 - 조건 체크 후 알림 실행"""
    if trigger_type == "gps_safety":
        if await check_geofence_exit(data['current_lat'], data['current_lng'], data['safe_zones']):
            return await gps_safety_spell(data['user_id'], data['child_name'], data['current_location'])
    
    elif trigger_type == "schedule_conflict":
        if await check_schedule_conflict(data['user_id'], data['schedule']):
            return await schedule_conflict_spell(data['user_id'], f"{data['schedule']['title']} 일정이 기존 일정과 충돌합니다")
    
    elif trigger_type == "emergency":
        return await emergency_spell(data['user_id'], data['message'], data.get('apartment_id'))
    
    return "조건 미충족 또는 트리거 없음"
