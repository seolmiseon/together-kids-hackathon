
from fastapi import APIRouter, HTTPException
from llm_service.models.chat_models import ChatRequest, ChatResponse, ConversationHistoryResponse
from llm_service.services.unified_chat_service import UnifiedChatService

router = APIRouter(prefix="/chat", tags=["chat"])

# 통합 서비스 인스턴스 (내부에 SessionManager 포함됨)
unified_chat_service = UnifiedChatService()



@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"=== 통합 채팅 요청: {request.user_id} ===")
        print(f"메시지: {request.message}")
        
        # 통합 서비스로 메시지 처리
        result = await unified_chat_service.process_message(
            user_id=request.user_id,
            message=request.message,
            chat_mode="auto"  # 자동 모드 선택
        )
        
        print(f"처리 결과: {result['mode']}, 응답 {len(result['responses'])}개")
        
        # AI 응답이 있는 경우 그것을 주 응답으로 사용
        main_response = ""
        community_status = ""
        
        for response in result["responses"]:
            if response["type"] == "ai":
                main_response = response["content"]["response"]
                if response["content"].get("suggestion"):
                    main_response += f"\n\n {response['content']['suggestion']}"
            elif response["type"] == "community":
                community_status = response["content"]["message"]
                if response["content"]["status"] == "emergency_alert_sent":
                    main_response = f"{response['content']['ai_assessment']}\n\n{community_status}"
        
        # 커뮤니티 상태가 있으면 추가
        if community_status and not main_response:
            main_response = community_status
        elif community_status and result["urgency"] != "high":
            main_response += f"\n\n{community_status}"
        
        return ChatResponse(
            message=main_response,
            user_id=request.user_id,
            timestamp=None
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
            chat_mode="ai_only"
        )
        
        ai_response = result["responses"][0]["content"]["response"]
        return ChatResponse(message=ai_response, user_id=request.user_id, timestamp=None)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 채팅 오류: {str(e)}")


@router.post("/community-only")
async def community_only_request(request: ChatRequest):
    try:
        result = await unified_chat_service.process_message(
            user_id=request.user_id,
            message=request.message,
            chat_mode="community_only"
        )
        
        return result["responses"][0]["content"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"커뮤니티 요청 오류: {str(e)}")


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
