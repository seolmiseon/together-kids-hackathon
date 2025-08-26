from fastapi import APIRouter, HTTPException, Body
import httpx
import os
import firebase_admin
from firebase_admin import credentials, auth

try:
    cred_path = os.path.join(os.path.dirname(__file__), '..', '..', 'serviceAccountKey.json')
    cred = credentials.Certificate(cred_path)
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"⚠️ Firebase Admin SDK 초기화 실패: {e}")

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/firebase/{provider}")
async def social_firebase_login(provider: str, body: dict = Body(...)):
    """
    소셜 로그인 Access Token을 사용하여 Firebase 커스텀 토큰을 생성합니다.
    """
    social_access_token = body.get("accessToken")
    if not social_access_token:
        raise HTTPException(status_code=400, detail="소셜 액세스 토큰이 필요합니다.")

    
    user_info_urls = {
        "kakao": "https://kapi.kakao.com/v2/user/me",
        "naver": "https://openapi.naver.com/v1/nid/me",
        # Google은 ID Token을 사용하는 것이 더 안전하지만, Access Token 방식도 가능합니다.
        "google": "https://www.googleapis.com/oauth2/v2/userinfo"
    }

    if provider not in user_info_urls:
        raise HTTPException(status_code=404, detail="지원하지 않는 소셜 로그인입니다.")

    try:
        
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                user_info_urls[provider],
                headers={"Authorization": f"Bearer {social_access_token}"},
            )
            user_response.raise_for_status()
            user_data = user_response.json()
        
       
        if provider == 'kakao':
            uid = f"kakao:{user_data.get('id')}"
            name = user_data.get("properties", {}).get("nickname")
        elif provider == 'naver':
            response_data = user_data.get("response", {})
            uid = f"naver:{response_data.get('id')}"
            name = response_data.get("name")
        elif provider == 'google':
            uid = f"google:{user_data.get('id')}"
            name = user_data.get("name")
        else:
            raise HTTPException(status_code=500, detail="소셜 정보 처리 중 오류 발생")

        
        custom_token = auth.create_custom_token(uid, {"displayName": name})
        
       
        return {"firebase_token": custom_token}

    except httpx.HTTPStatusError as e:
        
        raise HTTPException(status_code=401, detail=f"{provider} 토큰이 유효하지 않습니다: {e.response.text}")
    except Exception as e:
        print(f"Firebase 인증 처리 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail="Firebase 인증 처리 중 서버 에러 발생")
