import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import logging

logger = logging.getLogger(__name__)

# Firebase 인스턴스 저장용 전역 변수
_firebase_app = None
_firestore_db = None

def initialize_firebase():
    """Firebase Admin SDK 초기화"""
    global _firebase_app, _firestore_db
    
    if firebase_admin._apps:
        logger.info("Firebase가 이미 초기화되어 있습니다.")
        return
    
    try:
        # serviceAccountKey.json 파일 경로를 서버 루트에서 찾도록 수정
        service_account_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'serviceAccountKey.json')
        
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            _firestore_db = firestore.client()
            logger.info("✅ Firebase Admin SDK 초기화 성공")
        else:
            logger.warning(f"⚠️ Firebase Service Account 키 파일을 찾을 수 없습니다: {service_account_path}")
            logger.warning("Firebase 기능이 비활성화됩니다.")
    except Exception as e:
        logger.error(f"⚠️ Firebase Admin SDK 초기화 실패: {e}")

def get_firebase_auth():
    """Firebase Auth 인스턴스 반환"""
    if not firebase_admin._apps:
        raise Exception("Firebase가 초기화되지 않았습니다.")
    return auth

def get_firestore_db():
    """Firestore DB 인스턴스 반환"""
    global _firestore_db
    if _firestore_db is None:
        if not firebase_admin._apps:
            raise Exception("Firebase가 초기화되지 않았습니다.")
        _firestore_db = firestore.client()
    return _firestore_db

# 모듈 로드 시 Firebase 초기화
initialize_firebase()