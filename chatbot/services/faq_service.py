"""FAQ(자주 묻는 질문) 서비스"""
import json
import os
from typing import Optional, List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FAQService:
    """고정 FAQ 및 미답변 질의 관리"""

    # 고정 FAQ 리스트 (요구사항.md 기반)
    FIXED_FAQS = {
        "이 사이트에 대해서 설명해주세요": """**WantITNest**는 조선대학교 IT융합대학의 온라인 커뮤니티로 IT 학과 구성원이 진로, 협업, 정보 교류를 한곳에서 해결할 수 있는 통합 플랫폼입니다.

- 분산되어 있던 공지사항 정보를 통합 제공
- 졸업생과 재학생이 함께 활동하는 커뮤니티 기반의 정보 교류
- 프로젝트 모집 게시판을 통한 협업 기회 제공
- 매칭 시스템 기반 동일 관심 분야 사용자 매칭
- RAG 시스템 기반 AI 챗봇을 통한 편리한 정보 검색 등을 제공
- 다른 사용자의 프로필 조회를 통해 자신의 진로를 구체화 가능""",

        "프로젝트 모집/지원 방법이 궁금해요": """**모집 방법**
WantITNest에 로그인 >> 프로젝트 모집 게시판 이동 >> 좌측 하단의 글쓰기 버튼 클릭 >> 절차에 따른 모집글 작성

**지원 방법**
WantITNest에 로그인 >> 프로젝트 모집 게시판 이동 >> 관심 있는 프로젝트 모집 게시물 클릭 >> 우측 상단의 지원하기 버튼 클릭""",

        "게시글은 어떻게 작성하나요": """**게시글 작성 방법**
WantITNest에 로그인 >> 관심분야 게시판 이동 >> 좌측 하단의 글쓰기 버튼 클릭 >> 절차에 따른 게시글 작성""",

        "내 프로필은 어떻게 수정하나요": """**프로필 수정 방법**
WantITNest에 로그인 >> 좌측 상단의 자신의 프로필 이미지 클릭 >> 프로필 수정 버튼 클릭 >> 설정 클릭 >> 수정 후 저장 버튼 클릭""",

        "비밀번호를 잊어버렸어요": """**비밀번호 찾기**
우측 상단의 Login 버튼 클릭 >> 비밀번호 재설정 하기 클릭 >> 자신의 계정 이메일 입력 >> 메일로 발송된 재설정 링크 클릭 >> 비밀번호 재설정"""
    }

    def __init__(self, data_dir: str = "./chatbot/data"):
        """
        Args:
            data_dir: 데이터 저장 디렉토리
        """
        self.data_dir = data_dir
        self.unanswered_file = os.path.join(data_dir, "unanswered_queries.json")

        # 디렉토리 생성
        os.makedirs(data_dir, exist_ok=True)

    def get_faq_answer(self, question: str) -> Optional[str]:
        """
        고정 FAQ 답변 조회

        Args:
            question: 사용자 질문

        Returns:
            FAQ 답변 (없으면 None)
        """
        # 정확한 매칭
        for faq_question, answer in self.FIXED_FAQS.items():
            if self._is_similar_question(question, faq_question):
                logger.info(f"FAQ 매칭: '{question}' -> '{faq_question}'")
                return answer

        return None

    def _is_similar_question(self, user_question: str, faq_question: str) -> bool:
        """
        질문 유사도 판단

        Args:
            user_question: 사용자 질문
            faq_question: FAQ 질문

        Returns:
            유사 여부
        """
        # 소문자 변환 및 공백 제거
        user_q = user_question.lower().replace(" ", "").replace("?", "").replace(".", "")
        faq_q = faq_question.lower().replace(" ", "").replace("?", "").replace(".", "")

        # 핵심 키워드 기반 매칭
        if "사이트" in user_q and "설명" in user_q:
            return "사이트" in faq_q and "설명" in faq_q

        if "프로젝트" in user_q and ("모집" in user_q or "지원" in user_q):
            return "프로젝트" in faq_q and ("모집" in faq_q or "지원" in faq_q)

        if "게시글" in user_q and "작성" in user_q:
            return "게시글" in faq_q and "작성" in faq_q

        if "프로필" in user_q and "수정" in user_q:
            return "프로필" in faq_q and "수정" in faq_q

        if "비밀번호" in user_q and ("잊어버렸" in user_q or "찾기" in user_q or "분실" in user_q):
            return "비밀번호" in faq_q and "잊어버렸" in faq_q

        # 포함 관계 확인
        if faq_q in user_q or user_q in faq_q:
            return True

        return False

    def save_unanswered_query(self, question: str, user_id: Optional[str] = None) -> bool:
        """
        미답변 질의 기록

        Args:
            question: 사용자 질문
            user_id: 사용자 ID (옵션)

        Returns:
            저장 성공 여부
        """
        try:
            # 기존 데이터 로드
            unanswered = self._load_unanswered_queries()

            # 새 질의 추가
            new_query = {
                "question": question,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "answered": False
            }

            unanswered.append(new_query)

            # 파일에 저장
            with open(self.unanswered_file, 'w', encoding='utf-8') as f:
                json.dump(unanswered, f, ensure_ascii=False, indent=2)

            logger.info(f"미답변 질의 저장: '{question}' (user: {user_id})")
            return True

        except Exception as e:
            logger.error(f"미답변 질의 저장 실패: {e}")
            return False

    def _load_unanswered_queries(self) -> List[Dict]:
        """미답변 질의 목록 로드"""
        if not os.path.exists(self.unanswered_file):
            return []

        try:
            with open(self.unanswered_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"미답변 질의 로드 실패: {e}")
            return []

    def get_unanswered_queries(self, only_pending: bool = True) -> List[Dict]:
        """
        미답변 질의 목록 조회 (관리자용)

        Args:
            only_pending: 미답변만 조회할지 여부

        Returns:
            질의 목록
        """
        queries = self._load_unanswered_queries()

        if only_pending:
            return [q for q in queries if not q.get("answered", False)]

        return queries

    def get_faq_list(self) -> List[str]:
        """
        FAQ 질문 목록 반환

        Returns:
            FAQ 질문 리스트
        """
        return list(self.FIXED_FAQS.keys())
