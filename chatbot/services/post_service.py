"""게시물 서비스"""
import httpx
import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class PostService:
    """게시물 조회 서비스"""

    def __init__(self, base_url: str = None, timeout: float = 10.0):
        """
        Args:
            base_url: Spring API 기본 URL
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url or os.getenv("SPRING_API_URL", "http://host.docker.internal:6030/api/v1")
        self.timeout = timeout

    async def search_posts(
        self,
        keyword: str,
        search_type: str = "ALL",
        tags: Optional[List[str]] = None,
        page: int = 0,
        size: int = 10,
        sort: str = "createdAt,desc"
    ) -> List[Dict[str, Any]]:
        """
        게시물 검색

        Args:
            keyword: 검색 키워드
            search_type: 검색 타입 (ALL, TITLE, CONTENT)
            tags: 태그 필터링 리스트
            page: 페이지 번호 (0부터 시작)
            size: 페이지 크기
            sort: 정렬 (createdAt,desc / viewCount,desc 등)

        Returns:
            게시물 리스트 (PostSummaryDto)
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 파라미터 구성
                params = {
                    "keyword": keyword,
                    "searchType": search_type,
                    "page": page,
                    "size": size,
                    "sort": sort
                }

                # 태그 필터링 추가
                if tags:
                    params["tags"] = tags

                response = await client.get(f"{self.base_url}/posts/search", params=params)

                if response.status_code == 200:
                    data = response.json()
                    # PostListResponseDto 형식: {"posts": [...], "totalCount": ..., "pageInfo": {...}}
                    posts = data.get("posts", [])
                    logger.info(f"게시물 검색 성공: keyword={keyword}, {len(posts)}개")
                    return posts
                else:
                    logger.warning(f"게시물 검색 실패: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"게시물 검색 오류: {e}")
            return []

    async def get_post_detail(self, post_id: int) -> Optional[Dict[str, Any]]:
        """
        게시물 상세 조회

        Args:
            post_id: 게시물 ID

        Returns:
            게시물 상세 정보 (PostDetailResponseDto) 또는 None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/posts/{post_id}")

                if response.status_code == 200:
                    post_data = response.json()
                    logger.info(f"게시물 상세 조회 성공: {post_id}")
                    return post_data
                else:
                    logger.warning(f"게시물 상세 조회 실패: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"게시물 상세 조회 오류: {e}")
            return None

    async def get_all_posts(
        self,
        tags: Optional[List[str]] = None,
        page: int = 0,
        size: int = 100,
        sort: str = "createdAt,desc"
    ) -> List[Dict[str, Any]]:
        """
        전체 게시물 조회 (벡터화용)

        Args:
            tags: 태그 필터링 리스트
            page: 페이지 번호
            size: 페이지 크기
            sort: 정렬

        Returns:
            게시물 리스트 (PostSummaryDto)
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "page": page,
                    "size": size,
                    "sort": sort
                }

                if tags:
                    params["tags"] = tags

                response = await client.get(f"{self.base_url}/posts", params=params)

                if response.status_code == 200:
                    data = response.json()
                    posts = data.get("posts", [])
                    logger.info(f"전체 게시물 조회 성공: {len(posts)}개")
                    return posts
                else:
                    logger.warning(f"전체 게시물 조회 실패: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"전체 게시물 조회 오류: {e}")
            return []

    def format_post_text(self, post: Dict[str, Any]) -> str:
        """
        게시물을 텍스트로 변환 (임베딩용)

        Args:
            post: 게시물 데이터 (PostSummaryDto)

        Returns:
            게시물 텍스트
        """
        parts = []

        # 제목
        if "title" in post:
            parts.append(f"제목: {post['title']}")

        # 미리보기 내용
        if "previewContent" in post:
            parts.append(f"내용: {post['previewContent']}")

        # 작성자
        if "author" in post and post["author"]:
            author = post["author"]
            author_name = author.get("name", "알 수 없음")
            parts.append(f"작성자: {author_name}")

        # 태그
        if "tags" in post and post["tags"]:
            tags = ", ".join(post["tags"])
            parts.append(f"태그: {tags}")

        # 작성일
        if "createdAt" in post:
            parts.append(f"작성일: {post['createdAt']}")

        # 조회수, 좋아요
        if "viewCount" in post:
            parts.append(f"조회수: {post['viewCount']}")
        if "likeCount" in post:
            parts.append(f"좋아요: {post['likeCount']}")

        return " | ".join(parts) if parts else "게시물 정보 없음"

    def get_post_metadata(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        게시물 메타데이터 추출

        Args:
            post: 게시물 데이터 (PostSummaryDto)

        Returns:
            메타데이터 딕셔너리
        """
        author_name = ""
        if "author" in post and post["author"]:
            author_name = post["author"].get("name", "")

        tags = post.get("tags", [])
        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

        return {
            "id": str(post.get("id", "") or ""),
            "title": str(post.get("title", "") or ""),
            "author": str(author_name or ""),
            "tags": str(tags_str or ""),  # 리스트를 문자열로 변환
            "created_at": str(post.get("createdAt", "") or ""),
            "view_count": str(post.get("viewCount", 0) or 0),
            "like_count": str(post.get("likeCount", 0) or 0),
            "comment_count": str(post.get("commentCount", 0) or 0),
            "image_url": str(post.get("imageUrl", "") or ""),
            "preview_content": str(post.get("previewContent", "") or "")
        }
