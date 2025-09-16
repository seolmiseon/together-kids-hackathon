from fastapi import APIRouter, HTTPException, Body
import httpx
import os
import firebase_admin
from firebase_admin import credentials, auth
import time
from typing import Dict

try:
    cred_path = os.path.join(os.path.dirname(__file__), '..', '..', 'serviceAccountKey.json')
    cred = credentials.Certificate(cred_path)
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"⚠️ Firebase Admin SDK 초기화 실패: {e}")

router = APIRouter(prefix="/auth", tags=["authentication"])

# 중복 요청 방지용 캐시 (간단한 메모리 캐시)
processed_codes: Dict[str, float] = {}

def is_code_already_processed(code: str) -> bool:
    """최근 5분 내에 처리된 코드인지 확인"""
    current_time = time.time()
    if code in processed_codes:
        # 5분(300초) 이내에 처리된 코드라면 중복으로 판단
        if current_time - processed_codes[code] < 300:
            return True
        else:
            # 오래된 코드는 캐시에서 제거
            del processed_codes[code]
    return False

def mark_code_as_processed(code: str):
    """코드를 처리됨으로 표시"""
    processed_codes[code] = time.time()


@router.options("/firebase/{provider}")
async def options_firebase_login(provider: str):
    """
    CORS preflight 요청을 처리합니다.
    """
    from fastapi import Response
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response


@router.post("/firebase/{provider}")
async def social_firebase_login(provider: str, body: dict = Body(...)):
    """
    소셜 로그인 Authorization Code를 사용하여 Firebase 커스텀 토큰을 생성합니다.
    """
    auth_code = body.get("code")
    if not auth_code:
        raise HTTPException(status_code=400, detail="인증 코드가 필요합니다.")

    # 중복 요청 확인
    if is_code_already_processed(auth_code):
        raise HTTPException(status_code=400, detail="이미 처리된 인증 코드입니다. 새로 로그인해주세요.")

    # 코드 처리됨으로 표시
    mark_code_as_processed(auth_code)

    # OAuth 토큰 교환 엔드포인트
    token_urls = {
        "kakao": "https://kauth.kakao.com/oauth/token",
        "naver": "https://nid.naver.com/oauth2.0/token",
        "google": "https://oauth2.googleapis.com/token"
    }
    
    client_configs = {
    "kakao": {
        "client_id": os.getenv("KAKAO_CLIENT_ID"),
        "client_secret": os.getenv("KAKAO_CLIENT_SECRET"),
        "redirect_uri": os.getenv("KAKAO_REDIRECT_URI", "https://togatherkids.web.app/auth/callback/kakao/")  # ✅ OAuth 표준에 따라 slash 포함
    },
    "naver": {
        "client_id": os.getenv("NAVER_CLIENT_ID"),
        "client_secret": os.getenv("NAVER_CLIENT_SECRET"),
        "redirect_uri": os.getenv("NAVER_REDIRECT_URI", "https://togatherkids.web.app/auth/callback/naver/")  # ✅ OAuth 표준에 따라 slash 포함
    },
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "https://togatherkids.web.app/auth/callback/google/")  # ✅ OAuth 표준에 따라 slash 포함
    }
}

    if provider not in token_urls:
        raise HTTPException(status_code=404, detail="지원하지 않는 소셜 로그인입니다.")

    # 사용자 정보 엔드포인트
    user_info_urls = {
        "kakao": "https://kapi.kakao.com/v2/user/me",
        "naver": "https://openapi.naver.com/v1/nid/me",
        "google": "https://www.googleapis.com/oauth2/v3/userinfo"
    }

    try:
        # 1. Authorization Code를 Access Token으로 교환
        async with httpx.AsyncClient() as client:
            token_data = {
                "grant_type": "authorization_code",
                "client_id": client_configs[provider]["client_id"],
                "client_secret": client_configs[provider]["client_secret"],
                "redirect_uri": client_configs[provider]["redirect_uri"],
                "code": auth_code
            }
            
            if provider == "naver":
                token_data["state"] = body.get("state", "")

           

            token_response = await client.post(
                token_urls[provider],
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
          
            
            token_response.raise_for_status()
            token_result = token_response.json()
            # Extract access token from response
            access_token = token_result.get("access_token")
            if not access_token:
                print(f"❌ access_token이 없습니다. 응답: {token_result}")
                raise HTTPException(status_code=401, detail=f"{provider} access token을 가져올 수 없습니다.")

        # 2. Access Token으로 사용자 정보 획득
        user_info_urls = {
            "kakao": "https://kapi.kakao.com/v2/user/me",
            "naver": "https://openapi.naver.com/v1/nid/me",
            "google": "https://www.googleapis.com/oauth2/v3/userinfo"
        }

        print(f"🔍 {provider} 사용자 정보 요청: {user_info_urls[provider]}")
        print(f"🔍 Access Token: {access_token[:30]}...")

        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                user_info_urls[provider],
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            print(f"🔍 사용자 정보 응답 상태: {user_response.status_code}")
            print(f"🔍 사용자 정보 응답: {user_response.text}")
            
            user_response.raise_for_status()
            user_data = user_response.json()
        
        print(f"🔍 파싱된 사용자 데이터: {user_data}")
       
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

        print(f"🔍 추출된 정보 - UID: {uid}, Name: {name}")
        
        custom_token = auth.create_custom_token(uid, {"displayName": name})
        print(f"✅ Firebase Custom Token 생성 성공!")
        
        # bytes를 문자열로 변환
        token_string = custom_token.decode('utf-8')
        print(f"🔍 토큰 문자열 길이: {len(token_string)}")
       
        return {"firebase_token": token_string}

    except httpx.HTTPStatusError as e:
        
        raise HTTPException(status_code=401, detail=f"{provider} 토큰이 유효하지 않습니다: {e.response.text}")
    except Exception as e:
        print(f"Firebase 인증 처리 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail="Firebase 인증 처리 중 서버 에러 발생")
