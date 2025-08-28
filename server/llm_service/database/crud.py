import firebase_admin
from firebase_admin import firestore
from typing import List, Dict


if not firebase_admin._apps:
    try:
        from ...backend.main import cred # main.py의 cred를 공유한다고 가정
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"crud.py에서 Firebase 초기화 중 오류 발생: {e}")

db = firestore.client()

async def get_all_schedules_from_firestore() -> List[Dict]:
    """
    Firestore의 모든 사용자로부터 모든 자녀의 모든 일정을 가져옵니다.
    """
    all_schedules = []
    users_ref = db.collection("users")
    users_stream = users_ref.stream()

    async for user in users_stream:
        user_data = user.to_dict()
        children_ref = user.reference.collection("children")
        children_stream = children_ref.stream()

        async for child in children_stream:
            child_data = child.to_dict()
            schedules_ref = child.reference.collection("schedules")
            schedules_stream = schedules_ref.stream()

            async for schedule in schedules_stream:
                schedule_data = schedule.to_dict()
                # RAG에 사용할 텍스트 형식으로 데이터를 가공합니다.
                text = (
                    f"사용자 {user_data.get('full_name', '알 수 없음')}의 자녀 {child_data.get('name', '알 수 없음')}의 일정입니다. "
                    f"일정 제목: {schedule_data.get('title', '')}. "
                    f"상세 내용: {schedule_data.get('description', '')}. "
                    f"시간: {schedule_data.get('start_time')}."
                )
                all_schedules.append({
                    "text": text,
                    "metadata": {
                        "source": "schedule",
                        "user_id": user.id,
                        "child_id": child.id,
                        "schedule_id": schedule.id
                    }
                })
    return all_schedules
