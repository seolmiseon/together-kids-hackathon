from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from google.cloud import firestore
from ..firebase_config import get_firestore_db

from ..schemas import User, UserUpdate
from ..dependencies import get_current_user

# 위치 데이터 스키마
class LocationUpdate(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None

# FCM 토큰 스키마
class FCMTokenRequest(BaseModel):
    fcm_token: str
    device_id: Optional[str] = None  # 기기 식별자 (선택사항)

# Firestore DB 인스턴스 가져오기
def get_db():
    try:
        return get_firestore_db()
    except Exception:
        # Firebase가 초기화되지 않은 경우 None 반환
        return None

db = get_db()

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
           # 문서를 다시 읽어와서 실제 타임스탬프 값을 가져옴
            created_doc = user_ref.get()
            return sanitize_firestore_data(created_doc.to_dict(), uid)
        
        user_data = user_doc.to_dict()
        return sanitize_firestore_data(user_data, uid)
        
    except Exception as e:
                raise HTTPException(status_code=500, detail=f"프로필 조회 중 오류 발생: {e}")
    
    def sanitize_firestore_data(data: dict, uid: str) -> dict:
        """Firestore 데이터를 JSON 직렬화 가능한 형태로 변환"""
        sanitized = {"uid": uid}
    
        for key, value in data.items():
            if hasattr(value, "isoformat"):  # Timestamp 객체
                sanitized[key] = value.isoformat()
            elif hasattr(value, "to_dict"):  # 다른 Firestore 객체
                sanitized[key] = value.to_dict()
            else:
                sanitized[key] = value
    
        return sanitized

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


@router.post("/fcm-token")
async def register_fcm_token(
    token_request: FCMTokenRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    FCM 토큰 등록/업데이트
    
    - fcm_token: Firebase Cloud Messaging 토큰
    - device_id: 기기 식별자 (선택사항, 여러 기기 지원용)
    """
    uid = current_user.get("uid")
    
    if not token_request.fcm_token:
        raise HTTPException(status_code=400, detail="FCM 토큰이 필요합니다.")
    
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        user_data = user_doc.to_dict()
        fcm_tokens = user_data.get("fcm_tokens", [])
        
        # 기존 토큰 목록에 새 토큰 추가 (중복 제거)
        if token_request.fcm_token not in fcm_tokens:
            fcm_tokens.append(token_request.fcm_token)
            # 최대 10개 기기까지만 저장 (너무 많으면 오래된 것 제거)
            if len(fcm_tokens) > 10:
                fcm_tokens = fcm_tokens[-10:]
        
        # Firestore 업데이트
        update_data = {
            "fcm_tokens": fcm_tokens,
            "fcm_token_updated_at": datetime.now().isoformat()
        }
        
        # device_id가 있으면 기기 정보도 저장
        if token_request.device_id:
            device_info = user_data.get("devices", {})
            device_info[token_request.device_id] = {
                "fcm_token": token_request.fcm_token,
                "updated_at": datetime.now().isoformat()
            }
            update_data["devices"] = device_info
        
        user_ref.update(update_data)
        
        return {
            "success": True,
            "message": "FCM 토큰이 등록되었습니다.",
            "token_count": len(fcm_tokens)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FCM 토큰 등록 중 오류 발생: {e}")


@router.get("/fcm-token")
async def get_fcm_tokens(
    current_user: dict = Depends(get_current_user)
):
    """
    사용자의 FCM 토큰 목록 조회
    """
    uid = current_user.get("uid")
    
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        user_data = user_doc.to_dict()
        fcm_tokens = user_data.get("fcm_tokens", [])
        
        return {
            "fcm_tokens": fcm_tokens,
            "token_count": len(fcm_tokens),
            "updated_at": user_data.get("fcm_token_updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FCM 토큰 조회 중 오류 발생: {e}")


@router.delete("/fcm-token")
async def delete_fcm_token(
    fcm_token: str = Query(..., description="삭제할 FCM 토큰"),
    current_user: dict = Depends(get_current_user)
):
    """
    특정 FCM 토큰 삭제 (기기 로그아웃 등)
    """
    uid = current_user.get("uid")
    
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        user_data = user_doc.to_dict()
        fcm_tokens = user_data.get("fcm_tokens", [])
        
        # 토큰 제거
        if fcm_token in fcm_tokens:
            fcm_tokens.remove(fcm_token)
            user_ref.update({
                "fcm_tokens": fcm_tokens,
                "fcm_token_updated_at": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": "FCM 토큰이 삭제되었습니다.",
                "remaining_token_count": len(fcm_tokens)
            }
        else:
            return {
                "success": False,
                "message": "해당 FCM 토큰을 찾을 수 없습니다."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FCM 토큰 삭제 중 오류 발생: {e}")


@router.delete("/fcm-token/all")
async def delete_all_fcm_tokens(
    current_user: dict = Depends(get_current_user)
):
    """
    사용자의 모든 FCM 토큰 삭제 (전체 기기 로그아웃)
    """
    uid = current_user.get("uid")
    
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        user_ref.update({
            "fcm_tokens": [],
            "devices": {},
            "fcm_token_updated_at": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "모든 FCM 토큰이 삭제되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FCM 토큰 삭제 중 오류 발생: {e}")


