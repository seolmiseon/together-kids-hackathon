from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

# from ..database import get_db
from ..database_sqlite import get_db
from ..models import User as UserModel, UserApartment, Apartment
from ..schemas import User, UserUpdate, UserApartment as UserApartmentSchema, MessageResponse
from ..dependencies import get_current_active_user
from ..redis_client import set_cache, get_cache, redis_client

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile", response_model=User)
async def get_profile(current_user: UserModel = Depends(get_current_active_user)):
    """현재 사용자 프로필 조회"""
    return current_user

@router.put("/profile", response_model=User)
async def update_profile(
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """사용자 프로필 수정"""
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    # 프로필 캐시 갱신
    cache_key = f"user_profile:{current_user.id}"
    set_cache(cache_key, current_user.json(), expire_seconds=3600)
    return current_user

@router.get("/apartments", response_model=List[UserApartmentSchema])
async def get_user_apartments(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cache_key = f"user_apartments:{current_user.id}"
    cached = get_cache(cache_key)
    if cached:
        return json.loads(cached)
    user_apartments = db.query(UserApartment).filter(UserApartment.user_id == current_user.id).all()
    set_cache(cache_key, json.dumps([ua.__dict__ for ua in user_apartments]), expire_seconds=300)
    return user_apartments

@router.post("/apartments/{apartment_id}/join", response_model=MessageResponse)
async def join_apartment(
    apartment_id: int,
    unit_number: Optional[str] = None,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """아파트 커뮤니티 가입"""
    # 아파트 존재 확인
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="존재하지 않는 아파트입니다")
    
    # 이미 가입한 아파트인지 확인
    existing = db.query(UserApartment).filter(
        UserApartment.user_id == current_user.id,
        UserApartment.apartment_id == apartment_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="이미 가입한 아파트입니다")
    
    # 새 관계 생성
    user_apartment = UserApartment(
        user_id=current_user.id,
        apartment_id=apartment_id,
        unit_number=unit_number
    )
    
    db.add(user_apartment)
    db.commit()
    # 캐시 무효화
    cache_key = f"user_apartments:{current_user.id}"
    redis_client.delete(cache_key)
    return {"message": f"{apartment.name} 커뮤니티에 가입되었습니다"}

@router.delete("/apartments/{apartment_id}/leave", response_model=MessageResponse)
async def leave_apartment(
    apartment_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """아파트 커뮤니티 탈퇴"""
    user_apartment = db.query(UserApartment).filter(
        UserApartment.user_id == current_user.id,
        UserApartment.apartment_id == apartment_id
    ).first()
    
    if not user_apartment:
        raise HTTPException(status_code=404, detail="가입하지 않은 아파트입니다")
    
    db.delete(user_apartment)
    db.commit()
    cache_key = f"user_apartments:{current_user.id}"
    redis_client.delete(cache_key)
    return {"message": "아파트 커뮤니티에서 탈퇴되었습니다"}

@router.get("/search", response_model=List[User])
async def search_users(
    q: str = Query(..., min_length=2, description="검색어"),
    apartment_id: Optional[int] = Query(None, description="아파트 ID로 필터링"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """사용자 검색"""
    query = db.query(UserModel).filter(
        UserModel.is_active == True,
        UserModel.id != current_user.id  # 자신 제외
    )
    
    # 이름 또는 사용자명으로 검색
    query = query.filter(
        (UserModel.full_name.ilike(f"%{q}%")) |
        (UserModel.username.ilike(f"%{q}%"))
    )
    
    # 특정 아파트 사용자만 검색
    if apartment_id:
        query = query.join(UserApartment).filter(
            UserApartment.apartment_id == apartment_id
        )
    
    users = query.limit(20).all()
    return users
