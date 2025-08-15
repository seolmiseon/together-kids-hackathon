from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_context: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    message: str
    user_id: str
    timestamp: Optional[str] = None


class UserContextUpdate(BaseModel):
    user_id: str
    child_name: Optional[str] = None
    child_age: Optional[str] = None
    preferred_time: Optional[str] = None
    apartment_complex: Optional[str] = None


class ConversationHistoryResponse(BaseModel):
    user_id: str
    conversation_history: List[ChatMessage]
    total_messages: int
