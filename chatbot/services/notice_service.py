"""공지사항 조회 서비스 - Spring API 연동"""
import httpx
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class NoticeService:
    """Spring 백엔드와 연동하여 공지사항을 조회하는 서비스"""

    CATEGORIES = [
        "일반공지",
        "학사공지",
        "장학공지",
        "SW중심대학사업단",
        "IT융합대학",
        "컴퓨터공학전공",
        "정보통신공학전공",
        "인공지능공학전공",
        "모빌리티SW전공"
    ]

    def __init__(self):
        spring_host = os.getenv("SPRING_API_HOST", "host.docker.internal")
        self.base_url = f"http://{spring_host}:6030/api/v1"
        self.timeout = 30.0

    async def get_notices_by_category(
        self,
        category: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        카테고리별 공지사항 조회

        Args:
            category: 카테고리명
            limit: 최대 조회 개수 (옵션)

        Returns:
            공지사항 리스트
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/notices/{category}"
                if limit:
                    url += f"?limit={limit}"

                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    # Nest-BE는 {"notices": [...], "totalCount": ..., "pageInfo": {...}} 형식
                    notices = data.get("notices", [])
                    logger.info(f"공지사항 조회 성공: {category} - {len(notices)}개")
                    return notices
                else:
                    logger.warning(f"공지사항 조회 실패: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"공지사항 조회 오류: {e}")
            return []

    async def get_all_notices(self) -> List[Dict[str, Any]]:
        """
        모든 카테고리의 공지사항 조회 (벡터화용)

        Returns:
            전체 공지사항 리스트
        """
        all_notices = []

        for category in self.CATEGORIES:
            notices = await self.get_notices_by_category(category)
            all_notices.extend(notices)

        logger.info(f"전체 공지사항 조회 완료: {len(all_notices)}개")
        return all_notices

    async def get_recent_notices(
        self,
        category: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        최근 공지사항 조회

        Args:
            category: 카테고리 필터 (옵션)
            days: 최근 며칠 (기본 7일)

        Returns:
            최근 공지사항 리스트
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/notices/recent?days={days}"
                if category:
                    url += f"&category={category}"

                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    notices = data.get("notices", [])
                    logger.info(f"최근 공지사항 조회 성공: {len(notices)}개")
                    return notices
                else:
                    logger.warning(f"최근 공지사항 조회 실패: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"최근 공지사항 조회 오류: {e}")
            return []

    def format_notice_text(self, notice: Dict[str, Any]) -> str:
        """
        공지사항을 텍스트로 변환 (임베딩용)

        Args:
            notice: 공지사항 데이터 (Nest-BE NoticeResponseDto)

        Returns:
            공지사항 텍스트
        """
        parts = []

        # 공지 유형 (noticeType)
        if "noticeType" in notice:
            parts.append(f"[{notice['noticeType']}]")

        # 제목
        if "title" in notice:
            parts.append(notice["title"])

        # 작성자
        if "writer" in notice:
            parts.append(f"작성자: {notice['writer']}")

        # 게시일 (postDate)
        if "postDate" in notice:
            parts.append(f"게시일: {notice['postDate']}")

        # 조회수
        if "views" in notice:
            parts.append(f"조회수: {notice['views']}")

        return " | ".join(parts)

    def get_notice_metadata(self, notice: Dict[str, Any]) -> Dict[str, Any]:
        """
        공지사항 메타데이터 추출

        Args:
            notice: 공지사항 데이터 (Nest-BE NoticeResponseDto)

        Returns:
            메타데이터 딕셔너리
        """
        return {
            "id": notice.get("id", ""),
            "number": notice.get("number", ""),
            "category": notice.get("noticeType", ""),
            "title": notice.get("title", ""),
            "writer": notice.get("writer", ""),
            "date": notice.get("postDate", ""),
            "link": notice.get("link", ""),
            "views": str(notice.get("views", 0))
        }
