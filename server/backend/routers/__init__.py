from .auth import router as auth_router
from .users import router as users_router  
from .children import router as children_router
from .ai import router as ai_router
from llm_service.routers.chat import router as chat_router
from llm_service.routers.schedule import router as schedule_router  

__all__ = ["auth_router", "users_router", "children_router", "ai_router", "chat_router", "schedule_router"]
