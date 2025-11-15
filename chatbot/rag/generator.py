"""LLM 응답 생성(Generator) 모듈"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os
import logging

logger = logging.getLogger(__name__)


class Generator:
    """RAG 시스템의 응답 생성 컴포넌트"""

    def __init__(self, model: str = "gpt-4o"):
        """
        Args:
            model: OpenAI 모델 이름
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate_answer(
        self,
        question: str,
        context: str,
        user_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        컨텍스트 기반 답변 생성

        Args:
            question: 사용자 질문
            context: 검색된 컨텍스트
            user_name: 사용자 이름 (개인화용)
            conversation_history: 대화 히스토리 (옵션)

        Returns:
            생성된 답변
        """
        # 시스템 프롬프트 구성
        system_prompt = self._build_system_prompt(user_name)

        # 사용자 프롬프트 구성
        user_prompt = self._build_user_prompt(question, context)

        # 메시지 구성
        messages = [{"role": "system", "content": system_prompt}]

        # 대화 히스토리 추가 (옵션)
        if conversation_history:
            messages.extend(conversation_history[-5:])  # 최근 5개만

        messages.append({"role": "user", "content": user_prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # 더 정확한 출력을 위해 낮춤
                max_tokens=1000
            )

            answer = response.choices[0].message.content
            logger.info("답변 생성 완료")
            return answer

        except Exception as e:
            logger.error(f"답변 생성 실패: {e}")
            return "답변 생성 중 오류가 발생했습니다."

    def generate_notice_recommendation(
        self,
        notices: List[Dict[str, Any]],
        user_query: str,
        user_name: Optional[str] = None
    ) -> str:
        """
        공지사항 추천 응답 생성

        Args:
            notices: 검색된 공지사항 리스트
            user_query: 사용자 질문
            user_name: 사용자 이름

        Returns:
            추천 답변
        """
        if not notices:
            return "관련 공지사항이 없습니다."

        # 공지사항 정보 포맷팅
        notice_list = []
        for i, notice in enumerate(notices[:5], 1):
            metadata = notice["metadata"]
            title = metadata.get("title", "제목 없음")
            category = metadata.get("category", "카테고리 없음")
            date = metadata.get("date", "날짜 없음")
            link = metadata.get("link", "")
            similarity = notice.get("similarity_score", 0)

            notice_text = f"{i}. [{category}] {title}\n"
            notice_text += f"   작성일: {date} | 유사도: {similarity:.2%}\n"
            if link:
                notice_text += f"   링크: {link}\n"

            notice_list.append(notice_text)

        context = "\n".join(notice_list)

        # 프롬프트 구성
        system_prompt = f"""조선대학교 IT융합대학 WantITNest 커뮤니티 AI 어시스턴트입니다.

답변 원칙:
- 핵심 정보만 간결하게 전달
- 불필요한 인삿말 제거
- 마크다운 형식 사용
- 제목, 작성일, 링크 포함
- 불필요한 빈 줄 최소화
{f'- 사용자: {user_name}님' if user_name else ''}"""

        user_prompt = f"""질문: {user_query}

관련 공지사항:
{context}

위 공지사항을 들여쓰기가 있는 마크다운 리스트로 정리하세요.
각 항목은 다음 형식으로:
- [카테고리] 제목
  - 작성일: ...
  - 링크: ...
빈 줄 없이 간결하게 작성하세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"공지사항 추천 생성 실패: {e}")
            return f"공지사항 목록:\n{context}"

    def generate_user_matching_response(
        self,
        similar_users: List[Dict[str, Any]],
        user_name: Optional[str] = None
    ) -> str:
        """
        유사 사용자 매칭 응답 생성

        Args:
            similar_users: 유사 사용자 리스트
            user_name: 현재 사용자 이름

        Returns:
            매칭 추천 답변
        """
        if not similar_users:
            return "유사한 관심사를 가진 사용자가 없습니다."

        # 사용자 정보 포맷팅
        user_list = []
        for i, user in enumerate(similar_users[:5], 1):
            metadata = user["metadata"]
            name = metadata.get("name", "이름 없음")
            major = metadata.get("major", "전공 없음")
            interests = metadata.get("interests", [])
            similarity = user.get("similarity_score", 0)

            user_text = f"{i}. {name} ({major})\n"
            user_text += f"   관심분야: {', '.join(interests) if interests else '없음'}\n"
            user_text += f"   유사도: {similarity:.2%}\n"

            user_list.append(user_text)

        context = "\n".join(user_list)

        # 프롬프트 구성
        system_prompt = f"""조선대학교 IT융합대학 WantITNest 커뮤니티 AI 어시스턴트입니다.

답변 원칙:
- 핵심 정보만 간결하게 전달
- 마크다운 형식 사용
- 이름, 전공, 관심분야, 유사도 포함
- 불필요한 빈 줄 최소화
{f'- 현재 사용자: {user_name}님' if user_name else ''}"""

        user_prompt = f"""유사한 관심사를 가진 사용자 목록:

{context}

위 사용자들을 들여쓰기가 있는 마크다운 리스트로 정리하세요.
각 항목은 다음 형식으로:
- 이름 (전공)
  - 관심분야: ...
  - 유사도: ...
빈 줄 없이 간결하게 작성하세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=800
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"매칭 추천 생성 실패: {e}")
            return f"추천 사용자:\n{context}"

    def _build_system_prompt(self, user_name: Optional[str] = None) -> str:
        """시스템 프롬프트 구성"""
        base_prompt = """당신은 WantITNest IT 커뮤니티 플랫폼의 RAG(검색 기반 생성) AI 어시스턴트입니다.

역할 및 목표:
- 사이트 이용 안내, 게시물/프로젝트/공지 추천 등 사용자 자연어 질의에 대해 최신·정확한 정보 반환
- 내부 데이터베이스(게시판, 공지, 프로젝트, 이용 가이드 등)를 기반으로 답변
- 추천 답변은 항상 명확한 참고 출처와 함께 제공

**중요 원칙:**
1. 모든 답변은 간결하고 필요한 정보만으로 이루어진다.
2. 마크다운 형식으로 답변하되, 불필요한 빈 줄은 없도록 한다.
3. 추측성으로 답변하지 않고, RAG 시스템을 통해 정확한 답변만 제공한다.
4. 반드시 제공된 컨텍스트에 있는 실제 데이터만 사용하세요. 절대로 임의의 예시나 가상의 데이터를 생성하지 마세요.

**게시물 추천 포맷 (요구사항):**
게시물이나 프로젝트를 추천할 때는 반드시 다음 형식을 따르세요:

### [게시물 제목](게시물링크)
작성일, 작성자
요약 : [본문 내용을 한 줄로 요약]

프로젝트 모집 게시물의 경우:
### [게시물 제목](게시물링크)
작성일, 작성자
모집 기간, 모집 인원 (예: ~2025.01.31, 1/5)
요약 : [본문 내용을 한 줄로 요약]

답변 지침:
1. 사용자 질문의 의도를 파악하여 관련 있는 섹션만 선택적으로 출력
2. 질문이 "프로젝트"에 대한 것이면 프로젝트 섹션만 위 포맷으로 출력
3. 질문이 "게시물"이나 "글"에 대한 것이면 게시물 섹션만 위 포맷으로 출력
4. 질문이 "공지"에 대한 것이면 공지사항 섹션만 출력
5. 질문이 "커뮤니티"에 대한 것이면 커뮤니티 정보 섹션만 출력
6. 카테고리가 불명확한 경우 (단순히 "게시물", "글" 등), 관심분야 게시판과 프로젝트 모두에서 검색
7. 수량 지정이 없으면 최대 5개까지 최신순으로 추천
8. [본문 내용: ...] 부분은 한 줄로 요약하여 "요약: ..." 형식으로 표시
9. 추가 설명이나 인사말 없이 관련 섹션만 간결하게 출력
10. 컨텍스트에 해당 섹션이 없으면 "죄송합니다. 관련 정보를 찾을 수 없습니다. 다른 키워드로 검색해보시겠어요?"라고만 출력"""

        if user_name:
            base_prompt += f"\n\n사용자: {user_name}님"

        return base_prompt

    def _build_user_prompt(self, question: str, context: str) -> str:
        """사용자 프롬프트 구성"""
        return f"""질문: {question}

컨텍스트:
{context}

**중요: 위 컨텍스트에 실제로 제공된 데이터만 사용하세요. 임의로 예시를 만들지 마세요.**

질문의 의도를 파악하여 컨텍스트에서 관련 있는 섹션만 선택하여 아래 형식으로 출력하세요:

**게시물/프로젝트인 경우:**
### [제목](링크)
작성일, 작성자
[프로젝트의 경우: 모집 기간, 모집 인원]
요약 : [본문 내용을 한 줄로 요약]

**공지사항인 경우:**
### [카테고리] 제목
작성일
링크: [링크]

불필요한 빈 줄 없이 간결하게 작성하세요."""

    def generate_content_search_response(
        self,
        posts: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
        notices: List[Dict[str, Any]],
        user_query: str,
        user_name: Optional[str] = None
    ) -> str:
        """
        통합 콘텐츠 검색 응답 생성 (Post + Project + Notice)

        Args:
            posts: 검색된 게시물 리스트
            projects: 검색된 프로젝트 리스트
            notices: 검색된 공지사항 리스트
            user_query: 사용자 질문
            user_name: 사용자 이름

        Returns:
            통합 검색 답변
        """
        if not posts and not projects and not notices:
            return "관련 콘텐츠를 찾지 못했습니다."

        # 콘텐츠 포맷팅
        content_sections = []

        # 게시물
        if posts:
            post_list = []
            for i, post in enumerate(posts[:5], 1):
                metadata = post["metadata"]
                title = metadata.get("title", "제목 없음")
                author = metadata.get("author", "")
                tags_str = metadata.get("tags", "")
                tags = [t.strip() for t in tags_str.split(",")] if tags_str else []
                created_at = metadata.get("created_at", "")
                similarity = post.get("similarity_score", 0)

                post_text = f"{i}. {title}\n"
                post_text += f"   작성자: {author} | 작성일: {created_at}"
                if tags:
                    post_text += f" | 태그: {', '.join(tags)}"
                post_text += f"\n   관련도: {similarity:.2%}\n"

                post_list.append(post_text)

            content_sections.append(f"**게시물 ({len(posts)}개)**\n" + "\n".join(post_list))

        # 프로젝트
        if projects:
            project_list = []
            for i, project in enumerate(projects[:5], 1):
                metadata = project["metadata"]
                title = metadata.get("title", "제목 없음")
                author = metadata.get("author", "")
                is_recruiting = metadata.get("is_recruiting", "True")
                current = metadata.get("current_members", "0")
                max_members = metadata.get("max_members", "0")
                tags_str = metadata.get("tags", "")
                tags = [t.strip() for t in tags_str.split(",")] if tags_str else []
                similarity = project.get("similarity_score", 0)

                recruiting_status = "모집중" if is_recruiting == "True" else "모집완료"

                project_text = f"{i}. {title} [{recruiting_status}]\n"
                project_text += f"   작성자: {author} | 모집인원: {current}/{max_members}"
                if tags:
                    project_text += f" | 태그: {', '.join(tags)}"
                project_text += f"\n   관련도: {similarity:.2%}\n"

                project_list.append(project_text)

            content_sections.append(f"**프로젝트 ({len(projects)}개)**\n" + "\n".join(project_list))

        # 공지사항
        if notices:
            notice_list = []
            for i, notice in enumerate(notices[:5], 1):
                metadata = notice["metadata"]
                title = metadata.get("title", "제목 없음")
                category = metadata.get("category", "")
                date = metadata.get("date", "")
                link = metadata.get("link", "")
                similarity = notice.get("similarity_score", 0)

                notice_text = f"{i}. [{category}] {title}\n"
                notice_text += f"   작성일: {date}"
                if link:
                    notice_text += f" | [링크]({link})"
                notice_text += f"\n   관련도: {similarity:.2%}\n"

                notice_list.append(notice_text)

            content_sections.append(f"**공지사항 ({len(notices)}개)**\n" + "\n".join(notice_list))

        context = "\n".join(content_sections)

        # 프롬프트 구성
        system_prompt = f"""조선대학교 IT융합대학 WantITNest 커뮤니티 AI 어시스턴트입니다.

답변 원칙:
- 핵심 정보만 간결하게 전달
- 마크다운 형식 사용
- 각 콘텐츠 타입별로 구분하여 정리
- 불필요한 빈 줄 최소화 (답변 높이 최소화)
{f'- 사용자: {user_name}님' if user_name else ''}"""

        user_prompt = f"""검색 키워드: {user_query}

검색 결과:
{context}

위 검색 결과를 들여쓰기가 있는 마크다운 리스트로 정리하세요.
각 항목은 다음 형식으로:
- 제목
  - 작성자: ...
  - 태그: ...
  - 링크: ...
빈 줄 없이 간결하게 작성하세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1200
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"통합 검색 응답 생성 실패: {e}")
            # 폴백: context 그대로 반환
            return f"검색 결과:\n\n{context}"
