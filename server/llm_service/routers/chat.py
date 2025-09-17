
from fastapi import APIRouter, HTTPException
from llm_service.models.chat_models import ChatRequest, ChatResponse, ConversationHistoryResponse
from llm_service.services.unified_chat_service import UnifiedChatService

router = APIRouter(prefix="/chat", tags=["chat"])

# 통합 서비스 인스턴스 (내부에 SessionManager 포함됨)
unified_chat_service = UnifiedChatService()



@router.post("/unified")
async def unified_chat_endpoint(request: ChatRequest):
    """통합 채팅 엔드포인트 - 백엔드에서 호출"""
    try:
        print(f"=== 통합 채팅 요청: {request.user_id} ===")
        print(f"메시지: {request.message}")
        
        # 실제 AI 처리
        result = await unified_chat_service.process_message(
            user_id=request.user_id,
            message=request.message,
            user_context=request.user_context or {}
        )
        
        return {
            "message": result["response"],
            "user_id": request.user_id,
            "timestamp": result["timestamp"]
        }
        
    except Exception as e:
        print(f"통합 채팅 처리 오류: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}")


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"=== 통합 채팅 요청: {request.user_id} ===")
        print(f"메시지: {request.message}")
        
        # 통합 서비스로 메시지 처리
        result = await unified_chat_service.process_message(
            user_id=request.user_id,
            message=request.message,
            user_context=request.user_context or {}
        )
        
        return ChatResponse(
            message=result["response"],
            user_id=request.user_id,
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        print(f"통합 채팅 처리 오류: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}")


@router.post("/ai-only", response_model=ChatResponse) 
async def ai_only_chat(request: ChatRequest):
    """AI 전용 채팅"""
    try:
        result = await unified_chat_service.process_message(
            user_id=request.user_id,
            message=request.message,
            user_context=request.user_context or {}
        )
        
        return ChatResponse(
            message=result["response"], 
            user_id=request.user_id, 
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 채팅 오류: {str(e)}")


@router.post("/community-only")
async def community_only_request(request: ChatRequest):
    try:
        result = await unified_chat_service.process_message(
            user_id=request.user_id,
            message=request.message,
            user_context=request.user_context or {}
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"커뮤니티 요청 오류: {str(e)}")


# Backend 호환을 위한 /history 엔드포인트 추가
@router.get("/history")
async def get_chat_history_for_backend(user_id: str, limit: int = 50):
    """Backend에서 호출하는 채팅 히스토리 조회"""
    try:
        history = unified_chat_service.session_manager.get_conversation_history(user_id)
        return {
            "user_id": user_id,
            "history": history[:limit],
            "total_count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 히스토리 조회 중 오류가 발생했습니다: {str(e)}")


@router.delete("/history")
async def clear_chat_history_for_backend(user_id: str):
    """Backend에서 호출하는 채팅 히스토리 삭제"""
    try:
        unified_chat_service.session_manager.clear_conversation_history(user_id)
        return {"message": f"{user_id}의 채팅 히스토리가 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 히스토리 삭제 중 오류가 발생했습니다: {str(e)}")


@router.get("/conversation/{user_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(user_id: str):
    """사용자의 대화 기록 조회"""
    try:
        history = unified_chat_service.session_manager.get_conversation_history(user_id)
        return ConversationHistoryResponse(
            user_id=user_id,
            conversation_history=history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 기록 조회 중 오류가 발생했습니다: {str(e)}")


@router.delete("/conversation/{user_id}")
async def clear_conversation_history(user_id: str):
    """사용자의 대화 기록 삭제"""
    try:
        unified_chat_service.session_manager.clear_conversation_history(user_id)
        return {"message": f"{user_id}의 대화 기록이 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 기록 삭제 중 오류가 발생했습니다: {str(e)}")
