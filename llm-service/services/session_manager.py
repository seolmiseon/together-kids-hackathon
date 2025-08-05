import redis
import json
from datetime import datetime
from typing import Dict, List


class SessionManager:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.Redis(
            host=host, 
            port=port, 
            db=db, 
            decode_responses=True
        )
    
    def save_message(self, user_id: str, role: str, content: str):
        """사용자 대화 메시지를 Redis에 저장"""
        key = f"chat:{user_id}"
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.lpush(key, json.dumps(message))
        # 최근 50개 메시지만 유지
        self.redis_client.ltrim(key, 0, 49)
        # 24시간 후 자동 만료
        self.redis_client.expire(key, 86400)
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """사용자의 최근 대화 히스토리 가져오기"""
        key = f"chat:{user_id}"
        messages = self.redis_client.lrange(key, 0, limit-1)
        return [json.loads(msg) for msg in reversed(messages)]
    
    def save_conversation_history(self, user_id: str, conversation_history: List[Dict]):
        """전체 대화 기록을 저장"""
        # 시스템 메시지는 제외하고 사용자/어시스턴트 메시지만 저장
        for message in conversation_history:
            if message.get("role") in ["user", "assistant"]:
                self.save_message(user_id, message["role"], message["content"])
    
    def clear_conversation_history(self, user_id: str):
        """사용자 대화 기록 삭제"""
        key = f"chat:{user_id}"
        self.redis_client.delete(key)
    
    def save_user_context(self, user_id: str, context: Dict):
        """사용자 컨텍스트 정보 저장"""
        key = f"context:{user_id}"
        self.redis_client.hset(key, mapping=context)
        self.redis_client.expire(key, 604800)  # 7일 후 만료
    
    def get_user_context(self, user_id: str) -> Dict:
        """사용자 컨텍스트 정보 가져오기"""
        key = f"context:{user_id}"
        return self.redis_client.hgetall(key)
    
    def clear_conversation(self, user_id: str):
        """사용자 대화 기록 삭제"""
        key = f"chat:{user_id}"
        self.redis_client.delete(key)
