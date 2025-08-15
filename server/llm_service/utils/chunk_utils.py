import re
from typing import List

def split_text_by_meaning(text: str) -> List[str]:
    # 문장 구분자 기준 분할 (마침표, 느낌표, 물음표 뒤 공백)
    chunks = re.split(r'(?<=[.!?])\s+', text.strip())
    # 빈 문자열 제거
    chunks = [chunk for chunk in chunks if chunk]
    return chunks
