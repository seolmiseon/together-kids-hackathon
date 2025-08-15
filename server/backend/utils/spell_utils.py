import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import redis.asyncio as redis
from math import radians, cos, sin, asin, sqrt

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 캐시 저장 함수
async def set_cache(key: str, value: str, expire: Optional[int] = None) -> None:
    await redis_client.set(key, value)
    if expire:
        await redis_client.expire(key, expire)

# 캐시 조회 함수
async def get_cache(key: str) -> Optional[str]:
    return await redis_client.get(key)


async def gps_safety_spell(user_id: str, child_name: str, location: str, safe_zone: str = None):
    """GPS 안전구역 이탈 알림 - 3줄로 끝!"""
    alert = {
        "type": "gps_alert",
        "message": f"🚨 {child_name}이(가) 안전구역을 벗어났습니다!\n현재 위치: {location}",
        "timestamp": datetime.now().isoformat(),
        "urgency": "high"
    }
    redis_client.lpush(f"alerts:{user_id}", json.dumps(alert))
    redis_client.expire(f"alerts:{user_id}", 86400)  # 24시간 보관
    return f"GPS 알림 전송 완료: {child_name}"

async def schedule_conflict_spell(user_id: str, conflict_details: str, date: str = None):
    """일정 충돌 알림 - 3줄로 끝!"""
    alert = {
        "type": "schedule_conflict",
        "message": f"⏰ 일정 충돌 발생!\n{conflict_details}\n도움이 필요하시면 커뮤니티에 요청해보세요.",
        "timestamp": datetime.now().isoformat(),
        "urgency": "medium"
    }
    redis_client.lpush(f"alerts:{user_id}", json.dumps(alert))
    return f"일정 충돌 알림 완료"

async def emergency_spell(user_id: str, emergency_message: str, apartment_id: str = None):
    """응급상황 알림 - 3줄로 끝!"""
    alert = {
        "type": "emergency",
        "message": f"🚨 긴급상황!\n{emergency_message}\n즉시 대응이 필요합니다.",
        "timestamp": datetime.now().isoformat(),
        "urgency": "emergency"
    }
    redis_client.lpush(f"alerts:{user_id}", json.dumps(alert))
    
    # 응급상황이면 커뮤니티에도 알림
    if apartment_id:
        community_alert = {
            "type": "community_emergency",
            "message": f"🆘 {apartment_id} 아파트 긴급상황 발생!",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        redis_client.lpush(f"community_alerts:{apartment_id}", json.dumps(community_alert))
    
    return f"응급 알림 전송 완료"

async def ai_recommendation_spell(user_id: str, recommendation: str, category: str = "general"):
    """AI 추천 알림 - 3줄로 끝!"""
    alert = {
        "type": "ai_recommendation",
        "message": f"💡 AI 추천 사항\n{recommendation}",
        "category": category,
        "timestamp": datetime.now().isoformat(),
        "urgency": "low"
    }
    await set_cache(f"alerts:{user_id}", json.dumps(alert), expire=86400) 
    return f"AI 추천 알림 완료"



async def check_gps_trigger(data: Dict[str, Any]) -> bool:
    """GPS 트리거 조건 체크 - 간단한 거리 계산"""
    if not all(k in data for k in ['current_lat', 'current_lng', 'safe_lat', 'safe_lng', 'safe_radius']):
        return False
    
    # 간단한 거리 계산 (정확한 계산은 haversine 공식 사용)
    lat_diff = abs(data['current_lat'] - data['safe_lat'])
    lng_diff = abs(data['current_lng'] - data['safe_lng'])
    distance = (lat_diff + lng_diff) * 111  # 대략적인 km 변환
    
    return distance > data['safe_radius']

async def check_schedule_conflict(user_id: str, new_schedule: Dict[str, Any]) -> bool:
    """일정 충돌 체크 - Redis에서 기존 일정과 비교"""
    existing_schedules_key = f"schedules:{user_id}"
    existing = redis_client.get(existing_schedules_key)
    
    if not existing:
        return False
    
    # 간단한 시간 겹침 체크 (실제로는 더 정교한 로직 필요)
    existing_schedules = json.loads(existing)
    new_start = datetime.fromisoformat(new_schedule['start_time'])
    new_end = datetime.fromisoformat(new_schedule['end_time'])
    
    for schedule in existing_schedules:
        exist_start = datetime.fromisoformat(schedule['start_time'])
        exist_end = datetime.fromisoformat(schedule['end_time'])
        
        # 시간 겹침 체크
        if new_start < exist_end and new_end > exist_start:
            return True
    
    return False

async def auto_spell_trigger(trigger_type: str, data: Dict[str, Any]) -> str:
    """자동 스펠 트리거 - 조건 체크 후 알림 실행"""
    
    if trigger_type == "gps_safety":
        if await check_gps_trigger(data):
            return await gps_safety_spell(
                data['user_id'], 
                data['child_name'], 
                data['current_location']
            )
    
    elif trigger_type == "schedule_conflict":
        if await check_schedule_conflict(data['user_id'], data['schedule']):
            return await schedule_conflict_spell(
                data['user_id'],
                f"{data['schedule']['title']} 일정이 기존 일정과 충돌합니다"
            )
    
    elif trigger_type == "emergency":
        # 응급상황은 조건 없이 즉시 실행
        return await emergency_spell(
            data['user_id'],
            data['message'],
            data.get('apartment_id')
        )
    
    return "조건 미충족 또는 트리거 없음"

def haversine_distance(lat1, lon1, lat2, lon2):
    """두 좌표 간의 거리를 계산 (km)"""
    # 위도/경도를 라디안으로 변환
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # haversine 공식
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # 지구 반지름 (km)
    r = 6371
    return c * r * 1000  # 미터로 변환

async def check_geofence_exit(current_lat, current_lng, safe_zones):
    """지오펜스 이탈 체크"""
    for zone in safe_zones:
        distance = haversine_distance(
            current_lat, current_lng,
            zone['latitude'], zone['longitude']
        )
        
        if distance > zone['radius']:
            return {
                "is_outside": True,
                "zone_name": zone['name'],
                "distance": distance,
                "safe_radius": zone['radius']
            }
    
    return {"is_outside": False}


async def get_user_alerts(user_id: str, limit: int = 10) -> List[Dict]:
    """사용자 알림 목록 조회"""
    alerts_raw = redis_client.lrange(f"alerts:{user_id}", 0, limit-1)
    return [json.loads(alert) for alert in alerts_raw]

async def mark_alert_read(user_id: str, alert_index: int) -> bool:
    """알림 읽음 처리 (간단히 Redis에서 제거)"""
    try:
        redis_client.lrem(f"alerts:{user_id}", 0, alert_index)
        return True
    except:
        return False

async def clear_user_alerts(user_id: str) -> str:
    """사용자 알림 전체 삭제"""
    redis_client.delete(f"alerts:{user_id}")
    return "알림 전체 삭제 완료"



# 데모/테스트 함수
async def demo_spell_system() -> Dict[str, Any]:
    """스펠 시스템 데모 - 개발/테스트용"""
    demo_results = []
    
    # GPS 알림 데모
    gps_result = await gps_safety_spell("demo_user", "민수", "서울시 강남구 역삼동")
    demo_results.append({"type": "gps", "result": gps_result})
    
    # 일정 충돌 알림 데모  
    schedule_result = await schedule_conflict_spell("demo_user", "어린이집 하원 시간이 회사 회의와 겹칩니다")
    demo_results.append({"type": "schedule", "result": schedule_result})
    
    # AI 추천 알림 데모
    ai_result = await ai_recommendation_spell("demo_user", "오늘 비가 올 예정이니 실내 놀이를 준비해보세요", "weather")
    demo_results.append({"type": "ai", "result": ai_result})
    
    return {
        "message": "스펠 시스템 데모 완료",
        "results": demo_results,
        "timestamp": datetime.now().isoformat()
    }