"""프로젝트 서비스"""
import httpx
import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class ProjectService:
    """프로젝트 조회 서비스"""

    def __init__(self, base_url: str = None, timeout: float = 10.0):
        """
        Args:
            base_url: Spring API 기본 URL
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url or os.getenv("SPRING_API_URL", "http://host.docker.internal:6030/api/v1")
        self.timeout = timeout

    async def search_projects(
        self,
        keyword: str,
        search_type: str = "ALL",
        tags: Optional[List[str]] = None,
        page: int = 0,
        size: int = 10,
        sort: str = "createdAt,desc"
    ) -> List[Dict[str, Any]]:
        """
        프로젝트 검색

        Args:
            keyword: 검색 키워드
            search_type: 검색 타입 (ALL, TITLE, CONTENT)
            tags: 태그 필터링 리스트
            page: 페이지 번호 (0부터 시작)
            size: 페이지 크기
            sort: 정렬 (createdAt,desc / viewCount,desc 등)

        Returns:
            프로젝트 리스트 (ProjectSummaryDto)
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

                response = await client.get(f"{self.base_url}/projects/search", params=params)

                if response.status_code == 200:
                    data = response.json()
                    # ProjectListResponseDto 형식: {"projects": [...], "totalCount": ..., "pageInfo": {...}}
                    projects = data.get("projects", [])
                    logger.info(f"프로젝트 검색 성공: keyword={keyword}, {len(projects)}개")
                    return projects
                else:
                    logger.warning(f"프로젝트 검색 실패: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"프로젝트 검색 오류: {e}")
            return []

    async def get_project_detail(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        프로젝트 상세 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            프로젝트 상세 정보 (ProjectDetailResponseDto) 또는 None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/projects/{project_id}")

                if response.status_code == 200:
                    project_data = response.json()
                    logger.info(f"프로젝트 상세 조회 성공: {project_id}")
                    return project_data
                else:
                    logger.warning(f"프로젝트 상세 조회 실패: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"프로젝트 상세 조회 오류: {e}")
            return None

    async def get_all_projects(
        self,
        tags: Optional[List[str]] = None,
        page: int = 0,
        size: int = 100,
        sort: str = "createdAt,desc"
    ) -> List[Dict[str, Any]]:
        """
        전체 프로젝트 조회 (벡터화용)

        Args:
            tags: 태그 필터링 리스트
            page: 페이지 번호
            size: 페이지 크기
            sort: 정렬

        Returns:
            프로젝트 리스트 (ProjectSummaryDto)
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

                response = await client.get(f"{self.base_url}/projects", params=params)

                if response.status_code == 200:
                    data = response.json()
                    projects = data.get("projects", [])
                    logger.info(f"전체 프로젝트 조회 성공: {len(projects)}개")
                    return projects
                else:
                    logger.warning(f"전체 프로젝트 조회 실패: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"전체 프로젝트 조회 오류: {e}")
            return []

    def format_project_text(self, project: Dict[str, Any]) -> str:
        """
        프로젝트를 텍스트로 변환 (임베딩용)

        Args:
            project: 프로젝트 데이터 (ProjectSummaryDto)

        Returns:
            프로젝트 텍스트
        """
        parts = []

        # 제목
        if "projectTitle" in project:
            parts.append(f"제목: {project['projectTitle']}")

        # 미리보기 내용
        if "previewContent" in project:
            parts.append(f"설명: {project['previewContent']}")

        # 작성자
        if "author" in project and project["author"]:
            author = project["author"]
            author_name = author.get("name", "알 수 없음")
            parts.append(f"작성자: {author_name}")

        # 모집 정보
        if "currentNumberOfMembers" in project and "maximumNumberOfMembers" in project:
            current = project["currentNumberOfMembers"]
            maximum = project["maximumNumberOfMembers"]
            parts.append(f"모집인원: {current}/{maximum}")

        # 모집 상태
        if "isRecruiting" in project:
            status = "모집중" if project["isRecruiting"] else "모집완료"
            parts.append(f"상태: {status}")

        # 태그
        if "tags" in project and project["tags"]:
            tags = ", ".join(project["tags"])
            parts.append(f"태그: {tags}")

        # 작성일
        if "createdAt" in project:
            parts.append(f"작성일: {project['createdAt']}")

        # 조회수
        if "viewCount" in project:
            parts.append(f"조회수: {project['viewCount']}")

        return " | ".join(parts) if parts else "프로젝트 정보 없음"

    def get_project_metadata(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        프로젝트 메타데이터 추출

        Args:
            project: 프로젝트 데이터 (ProjectSummaryDto)

        Returns:
            메타데이터 딕셔너리
        """
        author_name = ""
        if "author" in project and project["author"]:
            author_name = project["author"].get("name", "")

        tags = project.get("tags", [])
        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

        return {
            "id": str(project.get("projectId", "") or ""),
            "title": str(project.get("projectTitle", "") or ""),
            "author": str(author_name or ""),
            "tags": str(tags_str or ""),  # 리스트를 문자열로 변환
            "created_at": str(project.get("createdAt", "") or ""),
            "view_count": str(project.get("viewCount", 0) or 0),
            "comment_count": str(project.get("commentCount", 0) or 0),
            "is_recruiting": str(project.get("isRecruiting", True)),
            "current_members": str(project.get("currentNumberOfMembers", 0) or 0),
            "max_members": str(project.get("maximumNumberOfMembers", 0) or 0),
            "image_url": str(project.get("imageUrl", "") or ""),
            "preview_content": str(project.get("previewContent", "") or "")
        }
