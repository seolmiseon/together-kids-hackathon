# init_embeddings.py
import asyncio
from services.vector_service import VectorService
from database import get_all_schedules, get_all_prompts  
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "mysql+pymysql://root:%60N2%28l%40-F-4z%3FV%5E%60r@104.197.64.41:3306/my-sql"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def main():
    vector_service = VectorService()
    db = SessionLocal()
    try:
        schedules = get_all_schedules(db) 
        for s in schedules:
            text = f"{s.title} {s.description or ''}"
            await vector_service.add_schedule_info(s['user_id'], s['text'], intent="schedule")
    
        prompts = get_all_prompts()  
        for p in prompts:
            await vector_service.add_schedule_info(p['user_id'], p['text'], intent="prompt")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
