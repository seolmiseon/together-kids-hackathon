from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional
from datetime import datetime, date, timedelta
from firebase_admin import firestore
import firebase_admin

from ..schemas import Child, ChildCreate, ChildUpdate, Schedule, ScheduleCreate, ScheduleUpdate, MessageResponse
from ..dependencies import get_current_user

if not firebase_admin._apps:
    from ..main import cred
    firebase_admin.initialize_app(cred)

db = firestore.client()

router = APIRouter(prefix="/children", tags=["children"])

@router.get("/", response_model=List[Child])
async def get_children(
    current_user: dict = Depends(get_current_user)
):
    """현재 로그인한 사용자의 자녀 목록을 Firestore에서 조회합니다."""
    uid = current_user.get("uid")
    try:
        children_ref = db.collection("users").document(uid).collection("children")
        docs = await children_ref.stream() # 비동기적으로 문서를 가져옵니다.
        children_list = [doc.to_dict() for doc in docs]
        return children_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자녀 목록 조회 중 오류 발생: {e}")


@router.post("/", response_model=Child)
async def create_child(
    child_data: ChildCreate,
    current_user: dict = Depends(get_current_user)
):
    """새 아이 프로필을 Firestore에 생성합니다."""
    uid = current_user.get("uid")
    try:
        new_child_ref = db.collection("users").document(uid).collection("children").document()
        
        child_dict = child_data.dict()
        child_dict["id"] = new_child_ref.id # 생성된 문서 ID를 데이터에 포함
        child_dict["parent_id"] = uid
        child_dict["created_at"] = firestore.SERVER_TIMESTAMP
        child_dict["updated_at"] = firestore.SERVER_TIMESTAMP
        await new_child_ref.set(child_dict)
        return child_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자녀 프로필 생성 중 오류 발생: {e}")

@router.get("/{child_id}", response_model=Child)
async def get_child(
    child_id: str,
    current_user: dict = Depends(get_current_user)
):
    """특정 아이 프로필을 Firestore에서 조회합니다."""
    uid = current_user.get("uid")
    try:
        child_ref = db.collection("users").document(uid).collection("children").document(child_id)
        child_doc = await child_ref.get()
        
        if not child_doc.exists:
            raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다")
        
        return child_doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자녀 프로필 조회 중 오류 발생: {e}")


@router.put("/{child_id}", response_model=Child)
async def update_child(
    child_id: str,
    child_update: ChildUpdate,
    current_user: dict = Depends(get_current_user)
):
    """아이 프로필을 Firestore에서 수정합니다."""
    uid = current_user.get("uid")
    update_data = child_update.dict(exclude_unset=True)
    update_data["updated_at"] = firestore.SERVER_TIMESTAMP
    
    try:
        child_ref = db.collection("users").document(uid).collection("children").document(child_id)
        await child_ref.update(update_data)
        
        updated_doc = await child_ref.get()
        if not updated_doc.exists:
            raise HTTPException(status_code=404, detail="업데이트 후 아이를 찾을 수 없습니다")
            
        return updated_doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자녀 프로필 수정 중 오류 발생: {e}")


@router.delete("/{child_id}", response_model=MessageResponse)
async def delete_child(
    child_id: str,
    current_user: dict = Depends(get_current_user)
):
    """아이 프로필을 Firestore에서 삭제합니다."""
    uid = current_user.get("uid")
    try:
        child_ref = db.collection("users").document(uid).collection("children").document(child_id)
        await child_ref.delete()
        
        # (추가 기능) 관련 스케줄도 함께 삭제하는 로직이 필요하다면 여기에 추가합니다.
        # 예: schedules 컬렉션에서 child_id가 일치하는 문서를 쿼리하여 삭제
        
        return {"message": "아이 프로필이 삭제되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자녀 프로필 삭제 중 오류 발생: {e}")
    

@router.get("/{child_id}/schedules", response_model=List[Schedule])
async def get_child_schedules(
    child_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    schedule_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """특정 아이의 모든 일정을 Firestore에서 조회합니다."""
    uid = current_user.get("uid")
    try:
        child_doc = await db.collection("users").document(uid).collection("children").document(child_id).get()
        if not child_doc.exists:
            raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다")
        
        query = child_doc.reference.collection("schedules")
        if start_date:
            query = query.where("start_time", ">=", datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.where("start_time", "<=", datetime.combine(end_date, datetime.max.time()))
        if schedule_type:
            query = query.where("schedule_type", "==", schedule_type)
            
        docs = await query.order_by("start_time").stream()
        schedules_list = [doc.to_dict() for doc in docs]
        return schedules_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일정 조회 중 오류 발생: {e}")

@router.post("/{child_id}/schedules", response_model=Schedule)
async def create_schedule(
    child_id: str,
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(get_current_user)
):
    """특정 아이의 새 일정을 Firestore에 생성합니다."""
    uid = current_user.get("uid")
    try:
        child_doc = await db.collection("users").document(uid).collection("children").document(child_id).get()
        if not child_doc.exists:
            raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다")

        new_schedule_ref = child_doc.reference.collection("schedules").document()
        schedule_dict = schedule_data.dict()
        schedule_dict["id"] = new_schedule_ref.id
        schedule_dict["created_at"] = firestore.SERVER_TIMESTAMP
        schedule_dict["updated_at"] = firestore.SERVER_TIMESTAMP
        
        await new_schedule_ref.set(schedule_dict)
        return schedule_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일정 생성 중 오류 발생: {e}")

@router.get("/schedules/today", response_model=List[Schedule])
async def get_today_schedules(current_user: dict = Depends(get_current_user)):
    """오늘의 모든 아이 일정 조회"""
    uid = current_user.get("uid")
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())

        schedules_ref = db.collection_group("schedules")
        query = schedules_ref.where("parent_id", "==", uid) \
                             .where("start_time", ">=", today_start) \
                             .where("start_time", "<=", today_end)
        
        docs_stream = query.order_by("start_time").stream()
        schedules_list = [doc.to_dict() for doc in docs_stream]
        return schedules_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오늘 일정 조회 중 오류 발생: {e}")


@router.get("/schedules/upcoming", response_model=List[Schedule])
async def get_upcoming_schedules(
    days: int = Query(7, description="앞으로 며칠간의 일정"),
    current_user: dict = Depends(get_current_user)
):
    """다가오는 일정 조회"""
    uid = current_user.get("uid")
    try:
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        schedules_ref = db.collection_group("schedules")
        query = schedules_ref.where("parent_id", "==", uid) \
                             .where("start_time", ">=", start_date) \
                             .where("start_time", "<=", end_date) \
                             .where("is_completed", "==", False)
        
        docs_stream = query.order_by("start_time").stream()
        schedules_list = [doc.to_dict() for doc in docs_stream]
        return schedules_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다가오는 일정 조회 중 오류 발생: {e}")
