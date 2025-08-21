# import redis  # Redis 사용 시 주석 해제
import json
from datetime import datetime
from typing import Dict, List


class SessionManager:
    def __init__(self):
        # === Redis 버전 (주석 처리) ===
        # self.redis_client = redis.Redis(
        #     host=host, 
        #     port=port, 
        #     db=db, 
        #     decode_responses=True
        # )
        
        # === 메모리 기반 버전 (해커톤용) ===
        self.conversations = {}
        self.user_contexts = {}
    
    def save_message(self, user_id: str, role: str, content: str):
        """사용자 대화 메시지 저장"""
        # === Redis 버전 (주석 처리) ===
        # key = f"chat:{user_id}"
        # message = {
        #     "role": role,
        #     "content": content,
        #     "timestamp": datetime.now().isoformat()
        # }
        # self.redis_client.lpush(key, json.dumps(message))
        # self.redis_client.ltrim(key, 0, 49)
        # self.redis_client.expire(key, 86400)
        
        # === 메모리 기반 버전 (해커톤용) ===
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.conversations[user_id].append(message)
        
        # 최근 50개 메시지만 유지
        if len(self.conversations[user_id]) > 50:
            self.conversations[user_id] = self.conversations[user_id][-50:]
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """사용자의 최근 대화 히스토리 가져오기"""
        # === Redis 버전 (주석 처리) ===
        # key = f"chat:{user_id}"
        # messages = self.redis_client.lrange(key, 0, limit-1)
        # return [json.loads(msg) for msg in reversed(messages)]
        
        # === 메모리 기반 버전 (해커톤용) ===
        if user_id not in self.conversations:
            return []
        
        # 최근 limit개 메시지 반환
        messages = self.conversations[user_id][-limit:]
        return messages
    
    def save_conversation_history(self, user_id: str, conversation_history: List[Dict]):
        """전체 대화 기록을 저장"""
        # 시스템 메시지는 제외하고 사용자/어시스턴트 메시지만 저장
        for message in conversation_history:
            if message.get("role") in ["user", "assistant"]:
                self.save_message(user_id, message["role"], message["content"])
    
    def clear_conversation_history(self, user_id: str):
        """사용자 대화 기록 삭제"""
        # === Redis 버전 (주석 처리) ===
        # key = f"chat:{user_id}"
        # self.redis_client.delete(key)
        
        # === 메모리 기반 버전 (해커톤용) ===
        if user_id in self.conversations:
            del self.conversations[user_id]
    
    def save_user_context(self, user_id: str, context: Dict):
        """사용자 컨텍스트 정보 저장"""
        # === Redis 버전 (주석 처리) ===
        # key = f"context:{user_id}"
        # self.redis_client.hset(key, mapping=context)
        # self.redis_client.expire(key, 604800)  # 7일 후 만료
        
        # === 메모리 기반 버전 (해커톤용) ===
        self.user_contexts[user_id] = context
    
    def get_user_context(self, user_id: str) -> Dict:
        """사용자 컨텍스트 정보 가져오기"""
        # === Redis 버전 (주석 처리) ===
        # key = f"context:{user_id}"
        # return self.redis_client.hgetall(key)
        
        # === 메모리 기반 버전 (해커톤용) ===
        return self.user_contexts.get(user_id, {})
    
    def clear_conversation(self, user_id: str):
        """사용자 대화 기록 삭제"""
        self.clear_conversation_history(user_id)
        key = f"chat:{user_id}"
        self.redis_client.delete(key)
