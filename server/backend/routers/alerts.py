from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

# from ..database import get_db
from ..database_sqlite import get_db
from ..models import User as UserModel, Child  as ChildModel,SafeZone
from ..dependencies import get_current_active_user
from ..utils.spell_utils import (
    gps_safety_spell, schedule_conflict_spell, emergency_spell,
    auto_spell_trigger, get_user_alerts, clear_user_alerts, demo_spell_system,
    check_geofence_exit
)


router = APIRouter(prefix="/alerts", tags=["simple-alerts"])

@router.post("/gps")
async def gps_alert_endpoint(
    child_name: str,
    location: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    """GPS 안전구역 이탈 알림"""
    result = await gps_safety_spell(str(current_user.id), child_name, location)
    return {"status": "success", "message": result}

@router.post("/gps/check-safety")
async def check_gps_safety(
    child_id: int,
    current_lat: float,
    current_lng: float,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """실시간 GPS 안전구역 체크"""
    
    # 해당 아이의 안전구역 조회
    safe_zones = db.query(SafeZone).filter(
        SafeZone.user_id == current_user.id,
        SafeZone.child_id == child_id,
        SafeZone.is_active == True
    ).all()
    
    zones_data = [
        {
            "name": zone.name,
            "latitude": zone.latitude,
            "longitude": zone.longitude,
            "radius": zone.radius
        }
        for zone in safe_zones
    ]
    
    # 지오펜스 체크
    check_result = await check_geofence_exit(current_lat, current_lng, zones_data)
    
    if check_result["is_outside"]:
        # 자동 알림 트리거
        child = db.query(ChildModel).filter(ChildModel.id == child_id).first()
        await gps_safety_spell(
            str(current_user.id),
            child.name,
            f"안전구역({check_result['zone_name']})에서 {int(check_result['distance'])}m 이탈"
        )
        
        return {
            "status": "alert_sent",
            "message": f"{child.name}이(가) {check_result['zone_name']} 안전구역을 벗어났습니다",
            "distance": check_result['distance']
        }
    
    return {"status": "safe", "message": "안전구역 내에 있습니다"}
@router.post("/schedule")
async def schedule_alert_endpoint(
    conflict_details: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    """일정 충돌 알림"""
    result = await schedule_conflict_spell(str(current_user.id), conflict_details)
    return {"status": "success", "message": result}

@router.post("/emergency")
async def emergency_alert_endpoint(
    emergency_message: str,
    apartment_id: str = None,
    current_user: UserModel = Depends(get_current_active_user)
):
    """응급상황 알림"""
    result = await emergency_spell(str(current_user.id), emergency_message, apartment_id)
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
    current_user: UserModel = Depends(get_current_active_user),
    limit: int = 10
):
    """사용자 알림 목록 조회"""
    alerts = await get_user_alerts(str(current_user.id), limit)
    return {"alerts": alerts, "count": len(alerts)}

@router.delete("/clear")
async def clear_alerts_endpoint(
    current_user: UserModel = Depends(get_current_active_user)
):
    """알림 전체 삭제"""
    result = await clear_user_alerts(str(current_user.id))
    return {"status": "success", "message": result}

@router.get("/demo")
async def demo_endpoint():
    """스펠 시스템 데모 (개발용)"""
    result = await demo_spell_system()
    return result
