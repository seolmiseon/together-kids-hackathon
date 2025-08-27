from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import firebase_admin
from firebase_admin import firestore


from ..schemas import User, UserUpdate
from ..dependencies import get_current_user

if not firebase_admin._apps:
    from ..main import cred
    firebase_admin.initialize_app(cred)

db = firestore.client()

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile", response_model=User)
async def get_profile(   current_user: dict = Depends(get_current_user)):
    uid = current_user.get("uid")
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = await user_ref.get()
        if not user_doc.exists:
            user_data = {
                "uid": uid,
                "email": current_user.get("email"),
                "user_name": current_user.get("email"), # 초기값
                "full_name": current_user.get("displayName", "사용자"),
                "is_active": True,
                "is_verified": current_user.get("email_verified", False),
                "created_at": firestore.SERVER_TIMESTAMP,
            }
            await user_ref.set(user_data)
            return user_data
        
        return user_doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 조회 중 오류 발생: {e}")

@router.put("/profile", response_model=User)
async def update_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """사용자 프로필을 Firestore에서 수정합니다."""
    uid = current_user.get("uid")
    update_data = user_update.dict(exclude_unset=True)
    
    try:
        user_ref = db.collection("users").document(uid)
        await user_ref.update(update_data)
        
        # 업데이트된 문서를 다시 가져와서 반환합니다.
        updated_doc = await user_ref.get()
        return updated_doc.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 업데이트 중 오류 발생: {e}")


@router.get("/search", response_model=List[User])
async def search_users(
    q: str = Query(..., min_length=2, description="검색어"),
    current_user: dict = Depends(get_current_user)
):
    """사용자 이름으로 다른 사용자를 검색합니다."""
    current_user_uid = current_user.get("uid")
    try:
        # Firestore는 ILIKE를 직접 지원하지 않으므로, 범위 쿼리로 유사 검색을 구현합니다.
        # full_name 필드를 기준으로 검색합니다.
        users_ref = db.collection("users")
        query = users_ref.where("full_name", ">=", q).where("full_name", "<=", q + '\uf8ff').limit(20)
        
        docs = await query.get()
        
        # 검색 결과에서 자기 자신은 제외합니다.
        search_results = [doc.to_dict() for doc in docs if doc.id != current_user_uid]
        
        return search_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 검색 중 오류 발생: {e}")


# @router.get("/apartments", response_model=List[UserApartmentSchema])
# async def get_user_apartments(
#     current_user: UserModel = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     cache_key = f"user_apartments:{current_user.id}"
#     cached = get_cache(cache_key)
#     if cached:
#         return json.loads(cached)
#     user_apartments = db.query(UserApartment).filter(UserApartment.user_id == current_user.id).all()
#     set_cache(cache_key, json.dumps([ua.__dict__ for ua in user_apartments]), expire_seconds=300)
#     return user_apartments

# @router.post("/apartments/{apartment_id}/join", response_model=MessageResponse)
# async def join_apartment(
#     apartment_id: int,
#     unit_number: Optional[str] = None,
#     current_user: UserModel = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """아파트 커뮤니티 가입"""
#     # 아파트 존재 확인
#     apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
#     if not apartment:
#         raise HTTPException(status_code=404, detail="존재하지 않는 아파트입니다")
    
#     # 이미 가입한 아파트인지 확인
#     existing = db.query(UserApartment).filter(
#         UserApartment.user_id == current_user.id,
#         UserApartment.apartment_id == apartment_id
#     ).first()
    
#     if existing:
#         raise HTTPException(status_code=400, detail="이미 가입한 아파트입니다")
    
#     # 새 관계 생성
#     user_apartment = UserApartment(
#         user_id=current_user.id,
#         apartment_id=apartment_id,
#         unit_number=unit_number
#     )
    
#     db.add(user_apartment)
#     db.commit()
#     # 캐시 무효화
#     cache_key = f"user_apartments:{current_user.id}"
#     redis_client.delete(cache_key)
#     return {"message": f"{apartment.name} 커뮤니티에 가입되었습니다"}

# @router.delete("/apartments/{apartment_id}/leave", response_model=MessageResponse)
# async def leave_apartment(
#     apartment_id: int,
#     current_user: UserModel = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """아파트 커뮤니티 탈퇴"""
#     user_apartment = db.query(UserApartment).filter(
#         UserApartment.user_id == current_user.id,
#         UserApartment.apartment_id == apartment_id
#     ).first()
    
#     if not user_apartment:
#         raise HTTPException(status_code=404, detail="가입하지 않은 아파트입니다")
    
#     db.delete(user_apartment)
#     db.commit()
#     cache_key = f"user_apartments:{current_user.id}"
#     redis_client.delete(cache_key)
#     return {"message": "아파트 커뮤니티에서 탈퇴되었습니다"}