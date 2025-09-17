from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import firebase_admin
from firebase_admin import firestore
from datetime import datetime
from pydantic import BaseModel


from ..schemas import User, UserUpdate
from ..dependencies import get_current_user

# 위치 데이터 스키마
class LocationUpdate(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None

if not firebase_admin._apps:
    from ..main import cred
    firebase_admin.initialize_app(cred)

db = firestore.client()

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    uid = current_user.get("uid")
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
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
            user_ref.set(user_data)
            return user_data
        
        user_data = user_doc.to_dict()
        # uid 필드 추가 (문서 ID와 동일)
        user_data["uid"] = uid
        return user_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 조회 중 오류 발생: {e}")

@router.put("/profile")
async def update_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """사용자 프로필을 Firestore에서 수정합니다."""
    uid = current_user.get("uid")
    update_data = user_update.dict(exclude_unset=True)
    
    try:
        user_ref = db.collection("users").document(uid)
        user_ref.update(update_data)
        
        # 업데이트된 문서를 다시 가져와서 반환합니다.
        updated_doc = user_ref.get()
        user_data = updated_doc.to_dict()
        # uid 필드 추가
        user_data["uid"] = uid
        return user_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 업데이트 중 오류 발생: {e}")


@router.get("/search")
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
        
        docs = query.get()
        
        # 검색 결과에서 자기 자신은 제외합니다.
        search_results = []
        for doc in docs:
            if doc.id != current_user_uid:
                user_data = doc.to_dict()
                user_data["uid"] = doc.id
                search_results.append(user_data)
        
        return search_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 검색 중 오류 발생: {e}")


@router.put("/location")
async def update_location(
    location: LocationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """사용자의 현재 위치를 업데이트합니다."""
    uid = current_user.get("uid")
    
    location_data = {
        "lat": location.lat,
        "lng": location.lng,
        "address": location.address,
        "last_updated": datetime.now().isoformat()
    }
    
    try:
        user_ref = db.collection("users").document(uid)
        user_ref.update({"location": location_data})
        
        return {"message": "위치가 업데이트되었습니다", "location": location_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"위치 업데이트 중 오류 발생: {e}")


@router.get("/location")
async def get_location(current_user: dict = Depends(get_current_user)):
    """사용자의 현재 위치를 조회합니다."""
    uid = current_user.get("uid")
    
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
            
        user_data = user_doc.to_dict()
        location = user_data.get("location")
        
        if not location:
            return {"message": "저장된 위치가 없습니다", "location": None}
            
        return {"location": location}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"위치 조회 중 오류 발생: {e}")


@router.get("/nearby-parents")
async def get_nearby_parents(
    current_user: dict = Depends(get_current_user),
    radius_km: float = Query(default=5.0, description="검색 반경 (km)")
):
    """근처에 있는 다른 부모들의 위치를 조회합니다."""
    current_uid = current_user.get("uid")
    
    try:
        # 모든 사용자의 위치 정보를 가져와서 거리 계산
        users_ref = db.collection("users")
        docs = users_ref.get()
        
        nearby_parents = []
        
        for doc in docs:
            if doc.id == current_uid:
                continue
                
            user_data = doc.to_dict()
            location = user_data.get("location")
            
            if location and location.get("lat") and location.get("lng"):
                # 실제 서비스에서는 GeoFire나 다른 위치 검색 라이브러리 사용 권장
                parent_info = {
                    "uid": doc.id,
                    "full_name": user_data.get("full_name", "알 수 없음"),
                    "location": location
                }
                nearby_parents.append(parent_info)
        
        return {"nearby_parents": nearby_parents}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"근처 부모 검색 중 오류 발생: {e}")


