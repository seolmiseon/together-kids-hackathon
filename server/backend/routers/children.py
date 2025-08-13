from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import json

from database import get_db
from models import Child as ChildModel, User as UserModel, Schedule as ScheduleModel
from schemas import Child, ChildCreate, ChildUpdate, Schedule, ScheduleCreate, ScheduleUpdate, MessageResponse
from routers.auth import get_current_active_user
from backend.redis_client import set_cache, get_cache, redis_client


router = APIRouter(prefix="/children", tags=["children"])

@router.get("/", response_model=List[Child])
async def get_children(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cache_key = f"children_list:{current_user.id}"
    cached = get_cache(cache_key)
    if cached:
        return json.loads(cached)
    children = db.query(ChildModel).filter(
        ChildModel.parent_id == current_user.id
    ).all()
    set_cache(cache_key, json.dumps(children), expire_seconds=300)
    return children

@router.post("/", response_model=Child)
async def create_child(
    child_data: ChildCreate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """새 아이 프로필 생성"""
    child = ChildModel(
        parent_id=current_user.id,
        **child_data.dict()
    )
    
    db.add(child)
    db.commit()
    db.refresh(child)
    # 캐시 무효화
    cache_key = f"children_list:{current_user.id}"
    redis_client.delete(cache_key)
    return child

@router.get("/{child_id}", response_model=Child)
async def get_child(
    child_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """특정 아이 프로필 조회"""
    child = db.query(ChildModel).filter(
        ChildModel.id == child_id,
        ChildModel.parent_id == current_user.id
    ).first()
    
    if not child:
        raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다")
    
    return child

@router.put("/{child_id}", response_model=Child)
async def update_child(
    child_id: int,
    child_update: ChildUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """아이 프로필 수정"""
    child = db.query(ChildModel).filter(
        ChildModel.id == child_id,
        ChildModel.parent_id == current_user.id
    ).first()
    
    if not child:
        raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다")
    
    update_data = child_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(child, field, value)
    
    db.commit()
    db.refresh(child)
    # 캐시 무효화
    cache_key = f"children_list:{current_user.id}"
    redis_client.delete(cache_key)
    return child

@router.delete("/{child_id}", response_model=MessageResponse)
async def delete_child(
    child_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """아이 프로필 삭제"""
    child = db.query(ChildModel).filter(
        ChildModel.id == child_id,
        ChildModel.parent_id == current_user.id
    ).first()
    
    if not child:
        raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다")
    
    # 관련 스케줄도 함께 삭제
    db.query(ScheduleModel).filter(ScheduleModel.child_id == child_id).delete()
    db.delete(child)
    db.commit()
    # 캐시 무효화
    cache_key = f"children_list:{current_user.id}"
    redis_client.delete(cache_key)
    return {"message": "아이 프로필이 삭제되었습니다"}

# ===== 일정 관리 =====

@router.get("/{child_id}/schedules", response_model=List[Schedule])
async def get_child_schedules(
    child_id: int,
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    schedule_type: Optional[str] = Query(None, description="일정 유형"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """아이의 일정 목록 조회"""
    # 아이 소유권 확인
    child = db.query(ChildModel).filter(
        ChildModel.id == child_id,
        ChildModel.parent_id == current_user.id
    ).first()
    
    if not child:
        raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다")
    
    query = db.query(ScheduleModel).filter(ScheduleModel.child_id == child_id)
    
    # 날짜 필터
    if start_date:
        query = query.filter(ScheduleModel.start_time >= start_date)
    if end_date:
        query = query.filter(ScheduleModel.start_time <= end_date)
    
    # 일정 유형 필터
    if schedule_type:
        query = query.filter(ScheduleModel.schedule_type == schedule_type)
    
    schedules = query.order_by(ScheduleModel.start_time).all()
    return schedules

@router.post("/{child_id}/schedules", response_model=Schedule)
async def create_schedule(
    child_id: int,
    schedule_data: ScheduleCreate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """새 일정 생성"""
    # 아이 소유권 확인
    child = db.query(ChildModel).filter(
        ChildModel.id == child_id,
        ChildModel.parent_id == current_user.id
    ).first()
    
    if not child:
        raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다")
    
    # child_id 설정
    schedule_data.child_id = child_id
    
    schedule = ScheduleModel(**schedule_data.dict())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    return schedule

@router.put("/{child_id}/schedules/{schedule_id}", response_model=Schedule)
async def update_schedule(
    child_id: int,
    schedule_id: int,
    schedule_update: ScheduleUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """일정 수정"""
    # 일정 조회 및 소유권 확인
    schedule = db.query(ScheduleModel).join(ChildModel).filter(
        ScheduleModel.id == schedule_id,
        ScheduleModel.child_id == child_id,
        ChildModel.parent_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
    
    update_data = schedule_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    
    return schedule

@router.delete("/{child_id}/schedules/{schedule_id}", response_model=MessageResponse)
async def delete_schedule(
    child_id: int,
    schedule_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """일정 삭제"""
    # 일정 조회 및 소유권 확인
    schedule = db.query(ScheduleModel).join(ChildModel).filter(
        ScheduleModel.id == schedule_id,
        ScheduleModel.child_id == child_id,
        ChildModel.parent_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
    
    db.delete(schedule)
    db.commit()
    
    return {"message": "일정이 삭제되었습니다"}

@router.get("/schedules/today", response_model=List[Schedule])
async def get_today_schedules(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """오늘의 모든 아이 일정 조회"""
    today = datetime.now().date()
    
    schedules = db.query(ScheduleModel).join(ChildModel).filter(
        ChildModel.parent_id == current_user.id,
        ScheduleModel.start_time >= today,
        ScheduleModel.start_time < today.replace(day=today.day + 1)
    ).order_by(ScheduleModel.start_time).all()
    
    return schedules

@router.get("/schedules/upcoming", response_model=List[Schedule])
async def get_upcoming_schedules(
    days: int = Query(7, description="앞으로 며칠간의 일정"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """다가오는 일정 조회"""
    from datetime import timedelta
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)
    
    schedules = db.query(ScheduleModel).join(ChildModel).filter(
        ChildModel.parent_id == current_user.id,
        ScheduleModel.start_time >= start_date,
        ScheduleModel.start_time <= end_date,
        ScheduleModel.is_completed == False
    ).order_by(ScheduleModel.start_time).all()
    
    return schedules
