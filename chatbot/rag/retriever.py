"""문서 검색(Retriever) 모듈"""
from typing import List, Dict, Any, Optional
from .embedder import Embedder
from .vector_store import VectorStore
import logging

logger = logging.getLogger(__name__)


class Retriever:
    """RAG 시스템의 검색 컴포넌트"""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore
    ):
        """
        Args:
            embedder: 임베딩 생성기
            vector_store: 벡터 스토어
        """
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve_notices(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
        keyword_filter: bool = True
    ) -> List[Dict[str, Any]]:
        """
        공지사항 검색 (하이브리드: 키워드 필터링 + 벡터 검색)

        Args:
            query: 사용자 질문
            category: 카테고리 필터 (옵션)
            top_k: 반환할 결과 수
            keyword_filter: 키워드 필터링 적용 여부 (기본 True)

        Returns:
            검색된 공지사항 리스트
        """
        try:
            # 쿼리 임베딩
            query_embedding = self.embedder.embed_text(query)

            # 필터 조건 설정
            where = {"category": category} if category else None

            # 벡터 검색 (더 많이 가져온 후 필터링)
            n_results = top_k * 10 if keyword_filter else top_k
            results = self.vector_store.search(
                collection_name="notices",
                query_embedding=query_embedding,
                n_results=n_results,
                where=where
            )

            # 결과 포맷팅
            notices = []
            query_keywords = query.lower().split()  # 쿼리를 키워드로 분리

            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i]
                title = metadata.get("title", "").lower()
                content = doc.lower()

                # 키워드 필터링: 제목 또는 내용에 쿼리 키워드 포함 여부 확인
                if keyword_filter:
                    # 쿼리의 모든 키워드 중 하나라도 제목이나 내용에 포함되어 있는지 확인
                    keyword_match = any(keyword in title or keyword in content for keyword in query_keywords)
                    if not keyword_match:
                        continue  # 키워드 매칭 안되면 스킵

                notice = {
                    "content": doc,
                    "metadata": metadata,
                    "similarity_score": 1 - results["distances"][i],  # 거리를 유사도로 변환
                    "id": results["ids"][i]
                }
                notices.append(notice)

                # top_k개 찾으면 종료
                if len(notices) >= top_k:
                    break

            # 키워드 필터링 결과가 없으면 벡터 검색 결과 상위 항목 사용 (폴백)
            if len(notices) == 0 and keyword_filter:
                logger.warning(f"키워드 필터링 결과 없음, 벡터 검색 결과 사용")
                for i, doc in enumerate(results["documents"][:top_k]):
                    notice = {
                        "content": doc,
                        "metadata": results["metadatas"][i],
                        "similarity_score": 1 - results["distances"][i],
                        "id": results["ids"][i]
                    }
                    notices.append(notice)

            # 날짜 기준 내림차순 정렬 (최신순)
            notices.sort(key=lambda x: x["metadata"].get("date", ""), reverse=True)

            logger.info(f"공지사항 검색 완료: {len(notices)}개 (키워드 필터: {keyword_filter})")
            return notices

        except Exception as e:
            logger.error(f"공지사항 검색 실패: {e}")
            return []

    def retrieve_community_info(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        커뮤니티 정보 검색

        Args:
            query: 사용자 질문
            top_k: 반환할 결과 수

        Returns:
            검색된 커뮤니티 정보 리스트
        """
        try:
            query_embedding = self.embedder.embed_text(query)

            results = self.vector_store.search(
                collection_name="community_info",
                query_embedding=query_embedding,
                n_results=top_k
            )

            info_list = []
            for i, doc in enumerate(results["documents"]):
                info = {
                    "content": doc,
                    "metadata": results["metadatas"][i],
                    "similarity_score": 1 - results["distances"][i],
                    "id": results["ids"][i]
                }
                info_list.append(info)

            logger.info(f"커뮤니티 정보 검색 완료: {len(info_list)}개")
            return info_list

        except Exception as e:
            logger.error(f"커뮤니티 정보 검색 실패: {e}")
            return []

    def retrieve_similar_users(
        self,
        user_profile: str,
        top_k: int = 5,
        exclude_user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        유사한 사용자 프로필 검색 (매칭용)

        Args:
            user_profile: 사용자 프로필 텍스트
            top_k: 반환할 결과 수
            exclude_user_id: 제외할 사용자 ID (본인)

        Returns:
            유사한 사용자 리스트
        """
        try:
            profile_embedding = self.embedder.embed_text(user_profile)

            results = self.vector_store.search(
                collection_name="user_profiles",
                query_embedding=profile_embedding,
                n_results=top_k + 1  # 본인 제외를 위해 +1
            )

            similar_users = []
            for i, doc in enumerate(results["documents"]):
                user_id = results["metadatas"][i].get("user_id")

                # 본인 제외
                if exclude_user_id and user_id == exclude_user_id:
                    continue

                user = {
                    "profile": doc,
                    "metadata": results["metadatas"][i],
                    "similarity_score": 1 - results["distances"][i],
                    "user_id": user_id
                }
                similar_users.append(user)

            # top_k개만 반환
            similar_users = similar_users[:top_k]

            logger.info(f"유사 사용자 검색 완료: {len(similar_users)}개")
            return similar_users

        except Exception as e:
            logger.error(f"유사 사용자 검색 실패: {e}")
            return []

    def hybrid_search(
        self,
        query: str,
        search_notices: bool = True,
        search_community: bool = True,
        category: Optional[str] = None,
        top_k_per_source: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        하이브리드 검색 (공지사항 + 커뮤니티 정보)

        Args:
            query: 사용자 질문
            search_notices: 공지사항 검색 여부
            search_community: 커뮤니티 정보 검색 여부
            category: 공지사항 카테고리 필터
            top_k_per_source: 소스별 결과 수

        Returns:
            검색 결과 딕셔너리
        """
        results = {}

        if search_notices:
            results["notices"] = self.retrieve_notices(
                query=query,
                category=category,
                top_k=top_k_per_source
            )

        if search_community:
            results["community_info"] = self.retrieve_community_info(
                query=query,
                top_k=top_k_per_source
            )

        return results

    def retrieve_posts(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        top_k: int = 5,
        keyword_filter: bool = True
    ) -> List[Dict[str, Any]]:
        """
        게시물 검색 (하이브리드: 키워드 필터링 + 벡터 검색)

        Args:
            query: 사용자 질문
            tags: 태그 필터 (옵션)
            top_k: 반환할 결과 수
            keyword_filter: 키워드 필터링 적용 여부 (기본 True)

        Returns:
            검색된 게시물 리스트
        """
        try:
            query_embedding = self.embedder.embed_text(query)

            # 태그 필터 설정
            where = None
            if tags:
                # ChromaDB에서는 리스트 필터링이 복잡하므로, 단순화
                where = {"tags": {"$in": tags}}

            # 벡터 검색 (더 많이 가져온 후 필터링)
            n_results = top_k * 10 if keyword_filter else top_k
            results = self.vector_store.search(
                collection_name="posts",
                query_embedding=query_embedding,
                n_results=n_results,
                where=where
            )

            posts = []
            query_keywords = query.lower().split()

            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i]
                title = metadata.get("title", "").lower()
                content = doc.lower()
                tags_str = metadata.get("tags", "").lower()

                # 키워드 필터링
                if keyword_filter:
                    keyword_match = any(
                        keyword in title or keyword in content or keyword in tags_str
                        for keyword in query_keywords
                    )
                    if not keyword_match:
                        continue

                post = {
                    "content": doc,
                    "metadata": metadata,
                    "similarity_score": 1 - results["distances"][i],
                    "id": results["ids"][i]
                }
                posts.append(post)

                if len(posts) >= top_k:
                    break

            # 키워드 필터링 결과가 없으면 벡터 검색 결과 상위 항목 사용 (폴백)
            if len(posts) == 0 and keyword_filter:
                logger.warning(f"키워드 필터링 결과 없음, 벡터 검색 결과 사용")
                for i, doc in enumerate(results["documents"][:top_k]):
                    post = {
                        "content": doc,
                        "metadata": results["metadatas"][i],
                        "similarity_score": 1 - results["distances"][i],
                        "id": results["ids"][i]
                    }
                    posts.append(post)

            # 날짜 기준 내림차순 정렬 (최신순)
            posts.sort(key=lambda x: x["metadata"].get("created_at", ""), reverse=True)

            logger.info(f"게시물 검색 완료: {len(posts)}개 (키워드 필터: {keyword_filter})")
            return posts

        except Exception as e:
            logger.error(f"게시물 검색 실패: {e}")
            return []

    def retrieve_projects(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        recruiting_only: bool = False,
        top_k: int = 5,
        keyword_filter: bool = True
    ) -> List[Dict[str, Any]]:
        """
        프로젝트 검색 (하이브리드: 키워드 필터링 + 벡터 검색)

        Args:
            query: 사용자 질문
            tags: 태그 필터 (옵션)
            recruiting_only: 모집중인 프로젝트만 검색 여부
            top_k: 반환할 결과 수
            keyword_filter: 키워드 필터링 적용 여부 (기본 True)

        Returns:
            검색된 프로젝트 리스트
        """
        try:
            query_embedding = self.embedder.embed_text(query)

            # 필터 조건 설정
            where = {}
            if recruiting_only:
                where["is_recruiting"] = "True"
            if tags:
                where["tags"] = {"$in": tags}

            where = where if where else None

            # 벡터 검색 (더 많이 가져온 후 필터링)
            n_results = top_k * 10 if keyword_filter else top_k
            results = self.vector_store.search(
                collection_name="projects",
                query_embedding=query_embedding,
                n_results=n_results,
                where=where
            )

            projects = []
            query_keywords = query.lower().split()

            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i]
                title = metadata.get("title", "").lower()
                content = doc.lower()
                tags_str = metadata.get("tags", "").lower()

                # 키워드 필터링
                if keyword_filter:
                    keyword_match = any(
                        keyword in title or keyword in content or keyword in tags_str
                        for keyword in query_keywords
                    )
                    if not keyword_match:
                        continue

                project = {
                    "content": doc,
                    "metadata": metadata,
                    "similarity_score": 1 - results["distances"][i],
                    "id": results["ids"][i]
                }
                projects.append(project)

                if len(projects) >= top_k:
                    break

            # 키워드 필터링 결과가 없으면 벡터 검색 결과 상위 항목 사용 (폴백)
            if len(projects) == 0 and keyword_filter:
                logger.warning(f"키워드 필터링 결과 없음, 벡터 검색 결과 사용")
                for i, doc in enumerate(results["documents"][:top_k]):
                    project = {
                        "content": doc,
                        "metadata": results["metadatas"][i],
                        "similarity_score": 1 - results["distances"][i],
                        "id": results["ids"][i]
                    }
                    projects.append(project)

            # 날짜 기준 내림차순 정렬 (최신순)
            projects.sort(key=lambda x: x["metadata"].get("created_at", ""), reverse=True)

            logger.info(f"프로젝트 검색 완료: {len(projects)}개 (키워드 필터: {keyword_filter})")
            return projects

        except Exception as e:
            logger.error(f"프로젝트 검색 실패: {e}")
            return []

    def search_all_content(
        self,
        query: str,
        content_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        top_k: int = 5,
        keyword_filter: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        통합 콘텐츠 검색 (Post + Project + Notice)

        Args:
            query: 사용자 질문
            content_types: 검색할 콘텐츠 타입 리스트 ["post", "project", "notice"] - None이면 전체
            tags: 태그 필터 (옵션)
            top_k: 콘텐츠 타입별 결과 수
            keyword_filter: 키워드 필터링 적용 여부 (기본 False - 벡터 검색만 사용)

        Returns:
            검색 결과 딕셔너리
        """
        results = {}

        # content_types가 None이면 전체 검색
        if content_types is None:
            content_types = ["post", "project", "notice"]

        if "post" in content_types:
            results["posts"] = self.retrieve_posts(
                query=query,
                tags=tags,
                top_k=top_k,
                keyword_filter=keyword_filter
            )

        if "project" in content_types:
            results["projects"] = self.retrieve_projects(
                query=query,
                tags=tags,
                top_k=top_k,
                keyword_filter=keyword_filter
            )

        if "notice" in content_types:
            results["notices"] = self.retrieve_notices(
                query=query,
                top_k=top_k,
                keyword_filter=keyword_filter
            )

        return results
