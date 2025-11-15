# 클라이언트와 주고받을 데이터 모델 정의

from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    question: str
    user_id: Optional[str] = None  # 사용자 ID (개인화용)

class ChatResponse(BaseModel):
    answer: str

class NoticeSearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    category: Optional[str] = None  # 카테고리 필터
    top_k: int = 5

class NoticeSearchResponse(BaseModel):
    answer: str
    notices: List[dict]

class MatchingRequest(BaseModel):
    user_id: str
    top_k: int = 5

class MatchingResponse(BaseModel):
    answer: str
    matched_users: List[dict]

class ContentSearchRequest(BaseModel):
    query: str  # 검색 키워드
    user_id: Optional[str] = None
    content_types: Optional[List[str]] = None  # ["post", "project", "notice"] - None이면 전체 검색
    tags: Optional[List[str]] = None  # 태그 필터
    top_k: int = 5

class ContentSearchResponse(BaseModel):
    answer: str
    posts: List[dict] = []
    projects: List[dict] = []
    notices: List[dict] = []
