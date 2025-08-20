from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import os

# SQLite 전용 imports
from .database_sqlite import get_db, create_tables, User, Child, Schedule, ChatMessage

app = FastAPI(title="함께 키즈 API (SQLite)", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 시작 시 테이블 생성
@app.on_event("startup")
async def startup_event():
    create_tables()
    print("🚀 함께 키즈 SQLite 서버 시작!")

# 기본 엔드포인트
@app.get("/")
async def root():
    return {"message": "함께 키즈 API (SQLite 버전)", "status": "running"}

# 헬스체크
@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "sqlite"}

# 사용자 관련 API
@app.post("/users/")
async def create_user(user_data: dict, db: Session = Depends(get_db)):
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user

# 채팅 API (OpenAI 연동)
@app.post("/chat")
async def chat_with_ai(message_data: dict, db: Session = Depends(get_db)):
    user_message = message_data.get("message", "")
    user_id = message_data.get("user_id", 1)
    
    # 간단한 응답 (실제로는 OpenAI API 호출)
    ai_response = f"안녕하세요! '{user_message}'에 대한 일정 조율을 도와드리겠습니다."
    
    # 채팅 기록 저장
    chat_record = ChatMessage(
        user_id=user_id,
        message=user_message,
        response=ai_response
    )
    db.add(chat_record)
    db.commit()
    
    return {"response": ai_response, "timestamp": chat_record.created_at}

# 일정 관련 API
@app.get("/schedules/{user_id}")
async def get_user_schedules(user_id: int, db: Session = Depends(get_db)):
    schedules = db.query(Schedule).filter(Schedule.user_id == user_id).all()
    return schedules

if __name__ == "__main__":
    uvicorn.run("main_sqlite:app", host="0.0.0.0", port=8000, reload=True)