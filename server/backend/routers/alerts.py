from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import firebase_admin
from firebase_admin import firestore


from ..dependencies import get_current_user
from ..utils.spell_utils import (
    gps_safety_spell, schedule_conflict_spell, emergency_spell,
    auto_spell_trigger, get_user_alerts, clear_user_alerts,
    check_geofence_exit
)

if not firebase_admin._apps:
    from ..main import cred
    firebase_admin.initialize_app(cred)

db = firestore.client()

router = APIRouter(prefix="/alerts", tags=["simple-alerts"])

@router.post("/gps")
async def gps_alert_endpoint(
    body: dict, # child_name, location을 body로 받음
    current_user: dict = Depends(get_current_user)
):
    """GPS 안전구역 이탈 알림 생성"""
    uid = current_user.get("uid")
    child_name = body.get("child_name")
    location = body.get("location")
    result = await gps_safety_spell(uid, child_name, location)
    return {"status": "success", "message": result}

@router.post("/gps/check-safety")
async def check_gps_safety(
    body: dict, # child_id, current_lat, current_lng을 body로 받음
    current_user: dict = Depends(get_current_user)
):
    """실시간 GPS 안전구역 체크 (Firestore 연동)"""
    uid = current_user.get("uid")
    child_id = body.get("child_id")
    current_lat = body.get("current_lat")
    current_lng = body.get("current_lng")

    try:
        safe_zones_ref = db.collection("users").document(uid).collection("safe_zones")
        query = safe_zones_ref.where("child_id", "==", child_id).where("is_active", "==", True)
        safe_zones_docs = await query.get()
        
        zones_data = [zone.to_dict() for zone in safe_zones_docs]
        
        # 지오펜스 체크
        check_result = await check_geofence_exit(current_lat, current_lng, zones_data)
        
        if check_result.get("is_outside"):
            # Firestore에서 아이 정보 조회
            child_doc = await db.collection("users").document(uid).collection("children").document(child_id).get()
            child_name = child_doc.to_dict().get("name", "아이") if child_doc.exists else "아이"

            await gps_safety_spell(
                uid,
                child_name,
                f"안전구역({check_result['zone_name']})에서 {int(check_result['distance'])}m 이탈"
            )
            
            return {
                "status": "alert_sent",
                "message": f"{child_name}이(가) {check_result['zone_name']} 안전구역을 벗어났습니다",
                "distance": check_result['distance']
            }
        
        return {"status": "safe", "message": "안전구역 내에 있습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"안전구역 체크 중 오류 발생: {e}")


@router.post("/schedule")
async def schedule_alert_endpoint(
    body: dict, # conflict_details를 body로 받음
    current_user: dict = Depends(get_current_user)
):
    """일정 충돌 알림"""
    uid = current_user.get("uid")
    conflict_details = body.get("conflict_details")
    result = await schedule_conflict_spell(uid, conflict_details)
    return {"status": "success", "message": result}

@router.post("/emergency")
async def emergency_alert_endpoint(
    emergency_message: str,
    apartment_id: str = None,
    current_user: dict = Depends(get_current_user)
):
    """응급상황 알림"""
    result = await emergency_spell(str(current_user.get("uid")), emergency_message, apartment_id)
    return {"status": "success", "message": result}

@router.post("/trigger")
async def auto_trigger_endpoint(
    trigger_type: str,
    trigger_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """자동 트리거 실행 (백그라운드)"""
    background_tasks.add_task(auto_spell_trigger, trigger_type, trigger_data)
    return {"status": "trigger_started", "type": trigger_type}

@router.get("/")
async def get_alerts_endpoint(
    current_user: dict = Depends(get_current_user),
    limit: int = 10
):
    """사용자 알림 목록 조회"""
    uid = current_user.get("uid")
    alerts = await get_user_alerts(uid, limit)
    return {"alerts": alerts, "count": len(alerts)}

@router.delete("/clear")
async def clear_alerts_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """알림 전체 삭제"""
    uid = current_user.get("uid")
    result = await clear_user_alerts(uid)
    return {"status": "success", "message": result}
