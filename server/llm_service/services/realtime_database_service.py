import firebase_admin
from firebase_admin import db, credentials
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
import os

from .unified_chat_service import UnifiedChatService
from .emotion_service import emotion_service

logger = logging.getLogger(__name__)

class RealtimeStatusService:
    def __init__(self):
        # Firebase Admin SDK 초기화
        try:
            cred_path = os.path.join(os.path.dirname(__file__), '..', '..', 'serviceAccountKey.json')
            cred = credentials.Certificate(cred_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://togatherkids-default-rtdb.firebaseio.com'
                })
            print("✅ Firebase Admin SDK 초기화 성공!")
        except Exception as e:
            print(f"⚠️ Firebase Admin SDK 초기화 실패: {e}")
        
        # Firebase Realtime Database 참조
        self.db = db
        self.unified_chat = UnifiedChatService()
        
    async def update_user_status(self, user_id: str, message: str, user_context: Dict = None) -> Dict:
        """사용자 실시간 상태 업데이트"""
        try:
            if not user_context:
                user_context = {"children": []}
            
            # 1. 기존 unified_chat_service 로직 활용
            classification = self.unified_chat.classify_intent_and_urgency(message)
            
            # 2. 감정 분석 수행
            emotion_result = await emotion_service.analyze_emotion_quick(message)
            
            # 3. 위치 정보 추출
            user_lat, user_lng = self.unified_chat.extract_user_location(user_context)
            
            # 4. 사용자 상태 데이터 구성
            status_data = {
                'user_id': user_id,
                'status': 'active',
                'last_seen': datetime.now().isoformat(),
                'current_activity': {
                    'intent': classification['intent'],
                    'urgency': classification['urgency'],
                    'message_preview': message[:50] + "..." if len(message) > 50 else message
                },
                'emotion_state': {
                    'emotion': emotion_result.get('emotion', '중립'),
                    'stress_level': emotion_result.get('stress_level', 3),
                    'confidence': emotion_result.get('confidence', 0.5)
                },
                'location': {
                    'lat': user_lat,
                    'lng': user_lng
                } if user_lat and user_lng else None,
                'user_info': {
                    'children_count': len(user_context.get('children', [])),
                    'area': user_context.get('area', '미설정')
                },
                'timestamp': datetime.now().timestamp()
            }
            
            # 4. Firebase Realtime Database에 저장
            ref = self.db.reference(f'user_status/{user_id}')
            ref.set(status_data)
            
            # 5. 고스트레스 사용자는 도움 요청 등록
            if emotion_result.get('stress_level', 0) >= 4:
                await self._register_help_request(user_id, status_data)
            
            logger.info(f"✅ 사용자 상태 업데이트 완료: {user_id}")
            return status_data
            
        except Exception as e:
            logger.error(f" 사용자 상태 업데이트 실패: {e}")
            return {}
    
    async def _register_help_request(self, user_id: str, status_data: Dict):
        """도움 요청 등록"""
        try:
            request_data = {
                'user_id': user_id,
                'emotion': status_data['emotion_state']['emotion'],
                'stress_level': status_data['emotion_state']['stress_level'],
                'intent': status_data['current_activity']['intent'],
                'urgency': status_data['current_activity']['urgency'],
                'message_preview': status_data['current_activity']['message_preview'],
                'location': status_data['location'],
                'timestamp': datetime.now().isoformat(),
                'status': 'waiting_help'
            }
            
            # 통합 도움 요청 등록
            ref = self.db.reference('help_requests').push()
            ref.set(request_data)
            
            logger.info(f"🆘 도움 요청 등록: {user_id}")
            
        except Exception as e:
            logger.error(f" 도움 요청 등록 실패: {e}")
    
    async def get_user_status(self, user_id: str) -> Optional[Dict]:
        """사용자 상태 조회"""
        try:
            ref = self.db.reference(f'user_status/{user_id}')
            data = ref.get()
            return data
        except Exception as e:
            logger.error(f" 사용자 상태 조회 실패: {e}")
            return None
    
    async def get_online_users_in_area(self, area: str, minutes: int = 30) -> List[Dict]:
        """지역 내 온라인 사용자 조회"""
        try:
            cutoff_time = (datetime.now() - timedelta(minutes=minutes)).timestamp()
            
            ref = self.db.reference('user_status')
            all_users = ref.get() or {}
            
            online_users = []
            for user_id, user_data in all_users.items():
                if (user_data.get('user_info', {}).get('location_area') == area and
                    user_data.get('timestamp', 0) > cutoff_time):
                    online_users.append(user_data)
            
            return online_users
            
        except Exception as e:
            logger.error(f"❌ 온라인 사용자 조회 실패: {e}")
            return []
    
    async def monitor_area_users(self, area: str) -> Dict:
        """지역별 사용자 실시간 모니터링"""
        try:
            online_users = await self.get_online_users_in_area(area)
            
            # 통계 계산
            total_users = len(online_users)
            yukAmanrab_users = [u for u in online_users if u.get('emotion_state', {}).get('stress_level', 0) >= 4]
            available_helpers = [u for u in online_users if u.get('emotion_state', {}).get('stress_level', 5) <= 2]
            
            monitoring_result = {
                'area': area,
                'timestamp': datetime.now().isoformat(),
                'stats': {
                    'total_online': total_users,
                    'yukAmanrab_count': len(yukAmanrab_users),
                    'available_helpers': len(available_helpers)
                },
                'yukAmanrab_users': yukAmanrab_users,
                'helper_candidates': available_helpers[:5]  # 최대 5명
            }
            
            # yukAmanrab 사용자가 있으면 알림
            if yukAmanrab_users:
                await self._notify_yukAmanrab_detected(area, yukAmanrab_users)
            
            logger.info(f"✅ {area} 지역 모니터링 완료: 온라인 {total_users}명, yukAmanrab {len(yukAmanrab_users)}명")
            return monitoring_result
            
        except Exception as e:
            logger.error(f"❌ 지역 모니터링 실패: {e}")
            return {}
    
    async def _notify_yukAmanrab_detected(self, area: str, yukAmanrab_users: List[Dict]):
        """yukAmanrab 사용자 감지 시 알림"""
        try:
            for user in yukAmanrab_users:
                user_id = user['user_id']
                stress_level = user.get('emotion_state', {}).get('stress_level', 0)
                
                # Firebase에 알림 데이터 저장
                notification_ref = self.db.reference(f'notifications/{user_id}')
                await notification_ref.push_async({
                    'type': 'helper_available',
                    'message': f'{area} 지역에 도움 줄 수 있는 부모님들이 계세요!',
                    'stress_level': stress_level,
                    'area': area,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"📢 yukAmanrab 사용자 {user_id}에게 알림 전송")
                
        except Exception as e:
            logger.error(f"❌ yukAmanrab 알림 실패: {e}")
    
    async def find_potential_helpers(self, area: str, requester_stress: int = 4) -> List[Dict]:
        """도움 줄 수 있는 사용자 찾기"""
        try:
            online_users = await self.get_online_users_in_area(area)
            
            helpers = []
            for user in online_users:
                user_stress = user.get('emotion_state', {}).get('stress_level', 5)
                # 스트레스 낮고, 최근 활동한 사용자
                if user_stress <= 3 and user.get('status') == 'active':
                    helpers.append({
                        'user_id': user['user_id'],
                        'stress_level': user_stress,
                        'last_seen': user['last_seen'],
                        'current_activity': user.get('current_activity', {})
                    })
            
            # 스트레스 낮은 순으로 정렬
            helpers.sort(key=lambda x: x['stress_level'])
            return helpers[:5]  # 최대 5명
            
        except Exception as e:
            logger.error(f" 도우미 찾기 실패: {e}")
            return []
    
    async def get_help_requests_in_area(self, area: str) -> List[Dict]:
        """지역 내 도움 요청 조회"""
        try:
            ref = self.db.reference('help_requests')
            requests = ref.get() or {}
            
            # 1시간 이내 요청만
            cutoff_time = datetime.now() - timedelta(hours=1)
            recent_requests = []
            
            for request_id, request_data in requests.items():
                request_time = datetime.fromisoformat(request_data['timestamp'])
                if request_time > cutoff_time and request_data.get('status') == 'waiting_help':
                    request_data['request_id'] = request_id
                    recent_requests.append(request_data)
            
            # 최신순 정렬
            recent_requests.sort(key=lambda x: x['timestamp'], reverse=True)
            return recent_requests
            
        except Exception as e:
            logger.error(f" 도움 요청 조회 실패: {e}")
            return []
    
    async def match_helper_with_requester(self, request_id: str, helper_user_id: str) -> bool:
        """도우미와 요청자 매칭"""
        try:
            # 요청 상태 업데이트
            ref = self.db.reference(f'help_requests/{request_id}')
            ref.update({
                'status': 'matched',
                'helper_user_id': helper_user_id,
                'matched_at': datetime.now().isoformat()
            })
            
            logger.info(f"🤝 매칭 완료: {helper_user_id} → {request_id}")
            return True
            
        except Exception as e:
            logger.error(f" 매칭 실패: {e}")
            return False
    
    async def set_user_offline(self, user_id: str):
        """사용자 오프라인 상태로 변경"""
        try:
            ref = self.db.reference(f'user_status/{user_id}')
            ref.update({
                'status': 'offline',
                'last_seen': datetime.now().isoformat()
            })
            logger.info(f"👋 사용자 오프라인: {user_id}")
            
        except Exception as e:
            logger.error(f" 오프라인 설정 실패: {e}")

# 전역 인스턴스
realtime_status_service = RealtimeStatusService()