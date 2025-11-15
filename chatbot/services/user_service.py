"""사용자 정보 조회 서비스 - Spring API 연동"""
import httpx
import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class UserService:
    """Spring 백엔드와 연동하여 사용자 정보를 조회하는 서비스"""

    def __init__(self):
        spring_host = os.getenv("SPRING_API_HOST", "host.docker.internal")
        self.base_url = f"http://{spring_host}:6030/api/v1"
        self.timeout = 10.0

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        사용자 프로필 조회

        Args:
            user_id: 사용자 ID (memberId)

        Returns:
            사용자 프로필 딕셔너리 (MemberResponseDto) 또는 None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/members/{user_id}")

                if response.status_code == 200:
                    user_data = response.json()
                    logger.info(f"사용자 프로필 조회 성공: {user_id}")
                    return user_data
                else:
                    logger.warning(f"사용자 프로필 조회 실패: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"사용자 프로필 조회 오류: {e}")
            return None

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """
        모든 사용자 프로필 조회 (벡터화용)

        Returns:
            사용자 리스트 (MemberResponseDto 리스트)
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 실제 엔드포인트는 /api/v1/members 또는 페이징 처리 필요
                response = await client.get(f"{self.base_url}/members")

                if response.status_code == 200:
                    data = response.json()
                    # 페이징 처리된 경우 대비
                    if isinstance(data, dict):
                        users = data.get("members", data.get("content", []))
                    else:
                        users = data

                    logger.info(f"전체 사용자 조회 성공: {len(users)}명")
                    return users
                else:
                    logger.warning(f"전체 사용자 조회 실패: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"전체 사용자 조회 오류: {e}")
            return []

    def format_user_profile_text(self, user_data: Dict[str, Any]) -> str:
        """
        사용자 프로필을 텍스트로 변환 (임베딩용)

        Args:
            user_data: 사용자 데이터 (Nest-BE MemberResponseDto)

        Returns:
            프로필 텍스트
        """
        parts = []

        # 기본 정보
        if "memberName" in user_data:
            parts.append(f"이름: {user_data['memberName']}")

        # 학과 정보 (memberDepartmentResponseDtoList)
        if "memberDepartmentResponseDtoList" in user_data:
            dept_list = user_data["memberDepartmentResponseDtoList"]
            if dept_list:
                departments = [d.get("departmentName", "") for d in dept_list if d.get("departmentName")]
                if departments:
                    parts.append(f"학과: {', '.join(departments)}")

        # 학생 여부
        if "memberIsStudent" in user_data:
            parts.append(f"학생: {'예' if user_data['memberIsStudent'] else '아니오'}")

        # 자기소개
        if "memberIntroduce" in user_data and user_data["memberIntroduce"]:
            parts.append(f"소개: {user_data['memberIntroduce']}")

        # 관심사 (memberInterestResponseDtoList)
        if "memberInterestResponseDtoList" in user_data:
            interest_list = user_data["memberInterestResponseDtoList"]
            if interest_list:
                interests = [i.get("interestName", "") for i in interest_list if i.get("interestName")]
                if interests:
                    parts.append(f"관심분야: {', '.join(interests)}")

        # 기술스택 (memberTechStackResponseDtoList)
        if "memberTechStackResponseDtoList" in user_data:
            tech_list = user_data["memberTechStackResponseDtoList"]
            if tech_list:
                tech_stacks = [t.get("techStackName", "") for t in tech_list if t.get("techStackName")]
                if tech_stacks:
                    parts.append(f"기술스택: {', '.join(tech_stacks)}")

        return " | ".join(parts) if parts else "프로필 정보 없음"
