"""사용자 매칭 서비스"""
from typing import List, Dict, Any, Optional
from rag.retriever import Retriever
from services.user_service import UserService
import logging

logger = logging.getLogger(__name__)


class MatchingService:
    """사용자 프로필 기반 매칭 서비스"""

    def __init__(
        self,
        retriever: Retriever,
        user_service: UserService
    ):
        """
        Args:
            retriever: RAG Retriever
            user_service: 사용자 서비스
        """
        self.retriever = retriever
        self.user_service = user_service

    async def find_similar_users(
        self,
        user_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        유사한 사용자 찾기

        Args:
            user_id: 현재 사용자 ID
            top_k: 추천할 사용자 수

        Returns:
            유사 사용자 리스트
        """
        try:
            # 현재 사용자 프로필 조회
            user_profile = await self.user_service.get_user_profile(user_id)

            if not user_profile:
                logger.warning(f"사용자 프로필을 찾을 수 없음: {user_id}")
                return []

            # 프로필을 텍스트로 변환
            profile_text = self.user_service.format_user_profile_text(user_profile)

            # 유사 사용자 검색
            similar_users = self.retriever.retrieve_similar_users(
                user_profile=profile_text,
                top_k=top_k,
                exclude_user_id=user_id
            )

            logger.info(f"사용자 매칭 완료: {user_id} -> {len(similar_users)}명")
            return similar_users

        except Exception as e:
            logger.error(f"사용자 매칭 오류: {e}")
            return []

    async def find_users_by_interest(
        self,
        interest: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        특정 관심사를 가진 사용자 찾기

        Args:
            interest: 관심사 키워드
            top_k: 반환할 사용자 수

        Returns:
            관련 사용자 리스트
        """
        try:
            # 관심사를 쿼리로 사용
            query = f"관심분야: {interest}"

            # 벡터 검색
            similar_users = self.retriever.retrieve_similar_users(
                user_profile=query,
                top_k=top_k
            )

            logger.info(f"관심사별 사용자 검색 완료: {interest} -> {len(similar_users)}명")
            return similar_users

        except Exception as e:
            logger.error(f"관심사별 검색 오류: {e}")
            return []

    async def find_project_partners(
        self,
        user_id: str,
        project_description: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        프로젝트 파트너 추천

        Args:
            user_id: 현재 사용자 ID
            project_description: 프로젝트 설명
            top_k: 추천할 사용자 수

        Returns:
            추천 파트너 리스트
        """
        try:
            # 프로젝트 설명을 쿼리로 사용
            similar_users = self.retriever.retrieve_similar_users(
                user_profile=project_description,
                top_k=top_k,
                exclude_user_id=user_id
            )

            logger.info(f"프로젝트 파트너 추천 완료: {len(similar_users)}명")
            return similar_users

        except Exception as e:
            logger.error(f"프로젝트 파트너 추천 오류: {e}")
            return []

    def calculate_match_score(
        self,
        user1: Dict[str, Any],
        user2: Dict[str, Any]
    ) -> float:
        """
        두 사용자 간의 매칭 점수 계산 (규칙 기반)

        Args:
            user1: 사용자 1 프로필
            user2: 사용자 2 프로필

        Returns:
            매칭 점수 (0.0 ~ 1.0)
        """
        score = 0.0
        max_score = 0.0

        # 전공 일치 (30점)
        max_score += 30
        if user1.get("major") == user2.get("major"):
            score += 30

        # 관심사 중복 (40점)
        max_score += 40
        interests1 = set(user1.get("interests", []))
        interests2 = set(user2.get("interests", []))
        common_interests = interests1 & interests2
        if interests1 and interests2:
            score += (len(common_interests) / len(interests1 | interests2)) * 40

        # 기술스택 중복 (30점)
        max_score += 30
        tech1 = set(user1.get("tech_stack", []))
        tech2 = set(user2.get("tech_stack", []))
        common_tech = tech1 & tech2
        if tech1 and tech2:
            score += (len(common_tech) / len(tech1 | tech2)) * 30

        return score / max_score if max_score > 0 else 0.0
