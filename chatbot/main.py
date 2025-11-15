"""WantITNest 커뮤니티 RAG 챗봇 API"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Dict
import os
import logging

from models import (
    ChatRequest,
    ChatResponse,
    NoticeSearchRequest,
    NoticeSearchResponse,
    MatchingRequest,
    MatchingResponse,
    ContentSearchRequest,
    ContentSearchResponse
)

# RAG 컴포넌트
from rag.embedder import Embedder
from rag.vector_store import VectorStore
from rag.retriever import Retriever
from rag.generator import Generator

# 서비스
from services.user_service import UserService
from services.notice_service import NoticeService
from services.matching_service import MatchingService
from services.faq_service import FAQService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in .env file!")

# FastAPI 앱
app = FastAPI(
    title="WantITNest RAG Chatbot API",
    description="조선대학교 IT융합대학 WantITNest 커뮤니티 AI 챗봇",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수 (싱글톤)
embedder: Embedder = None
vector_store: VectorStore = None
retriever: Retriever = None
generator: Generator = None
user_service: UserService = None
notice_service: NoticeService = None
matching_service: MatchingService = None
faq_service: FAQService = None


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 RAG 컴포넌트 초기화"""
    global embedder, vector_store, retriever, generator
    global user_service, notice_service, matching_service, faq_service

    logger.info("=== WantITNest RAG 챗봇 초기화 시작 ===")

    try:
        # RAG 컴포넌트 초기화
        embedder = Embedder()
        vector_store = VectorStore()
        retriever = Retriever(embedder, vector_store)
        generator = Generator()

        # 서비스 초기화
        user_service = UserService()
        notice_service = NoticeService()
        matching_service = MatchingService(retriever, user_service)
        faq_service = FAQService()

        logger.info("=== WantITNest RAG 챗봇 초기화 완료 ===")

        # 벡터 DB 상태 확인
        collections = vector_store.list_collections()
        logger.info(f"활성 컬렉션: {collections}")

        for col_name in collections:
            count = vector_store.get_collection_count(col_name)
            logger.info(f"  - {col_name}: {count}개 문서")

    except Exception as e:
        logger.error(f"초기화 실패: {e}", exc_info=True)
        raise


# ==================== 헬퍼 함수 ====================

def _is_wantitnest_related(question: str) -> bool:
    """
    질문이 WantITNest 관련인지 판단

    Args:
        question: 사용자 질문

    Returns:
        WantITNest 관련 여부
    """
    # WantITNest 관련 키워드
    wantitnest_keywords = [
        "wantitnest", "원티네스트", "사이트", "웹사이트", "플랫폼",
        "회원가입", "로그인", "프로필", "팔로우", "게시글", "게시물",
        "프로젝트", "모집", "지원", "공지", "알림", "검색",
        "댓글", "좋아요", "신고", "차단", "설정", "탈퇴",
        "비밀번호", "이메일", "인증", "계정"
    ]

    question_lower = question.lower()

    # 키워드 포함 여부 확인
    for keyword in wantitnest_keywords:
        if keyword in question_lower:
            return True

    # "어떻게", "방법", "~는" 등의 패턴 + 사이트 기능 관련
    action_words = ["어떻게", "방법", "하는", "하나요", "할까요", "어디", "무엇"]
    for action in action_words:
        if action in question:
            return True

    return False


def _detect_query_intent(question: str) -> Dict[str, bool]:
    """
    질문의 의도를 파악하여 어떤 콘텐츠를 검색해야 하는지 판단

    Args:
        question: 사용자 질문

    Returns:
        검색할 콘텐츠 타입 딕셔너리
    """
    question_lower = question.lower()

    intent = {
        "search_notices": False,
        "search_posts": False,
        "search_projects": False,
        "search_community": False
    }

    # 공지사항 관련 키워드
    notice_keywords = ["공지", "알림", "안내", "notice"]
    for keyword in notice_keywords:
        if keyword in question_lower:
            intent["search_notices"] = True
            # 공지사항만 명시적으로 요청한 경우 다른 것은 검색하지 않음
            return intent

    # 프로젝트 관련 키워드
    project_keywords = ["프로젝트", "모집", "팀원", "project"]
    for keyword in project_keywords:
        if keyword in question_lower:
            intent["search_projects"] = True

    # 게시물 관련 키워드
    post_keywords = ["게시물", "게시글", "글", "포스트", "post"]
    for keyword in post_keywords:
        if keyword in question_lower:
            intent["search_posts"] = True

    # 커뮤니티 정보 관련
    community_keywords = ["커뮤니티", "사이트", "정보", "소개"]
    for keyword in community_keywords:
        if keyword in question_lower:
            intent["search_community"] = True

    # 아무것도 명시되지 않은 경우 전체 검색
    if not any(intent.values()):
        intent["search_notices"] = True
        intent["search_posts"] = True
        intent["search_projects"] = True
        intent["search_community"] = True

    return intent


# ==================== 엔드포인트 ====================

@app.get("/")
def root():
    """서버 상태 확인"""
    return {
        "status": "WantITNest RAG Chatbot Running",
        "version": "2.0.0",
        "features": ["RAG", "Post Search", "Project Search", "Notice Search", "User Matching", "Personalization"]
    }


@app.get("/health")
def health_check():
    """헬스 체크"""
    collections = vector_store.list_collections() if vector_store else []
    return {
        "status": "healthy",
        "collections": collections,
        "rag_initialized": embedder is not None
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    일반 채팅 (통합 RAG 기반)
    - 고정 FAQ 우선 체크
    - 게시물, 프로젝트, 공지사항, 커뮤니티 정보 통합 검색
    - 질의 의도 파악 후 관련성 높은 콘텐츠 추천
    - 사용자 개인화 지원
    - 미답변 질의 기록
    """
    try:
        # 1. 고정 FAQ 체크 (요구사항 #1)
        faq_answer = faq_service.get_faq_answer(req.question)
        if faq_answer:
            logger.info(f"FAQ 답변 반환: '{req.question}'")
            return ChatResponse(answer=faq_answer)

        # 사용자 정보 조회 (개인화)
        user_name = None
        if req.user_id:
            user_profile = await user_service.get_user_profile(req.user_id)
            if user_profile:
                user_name = user_profile.get("memberName")

        # 질문 의도 파악
        intent = _detect_query_intent(req.question)
        logger.info(f"질문 의도: {intent}")

        # 의도에 따라 검색할 콘텐츠 타입 결정
        content_types = []
        if intent["search_posts"]:
            content_types.append("post")
        if intent["search_projects"]:
            content_types.append("project")
        if intent["search_notices"]:
            content_types.append("notice")

        # 콘텐츠 타입이 없으면 전체 검색
        if not content_types:
            content_types = None

        # 통합 검색 (키워드 필터링 비활성화 - 벡터 검색만 사용하여 유연한 검색)
        all_results = retriever.search_all_content(
            query=req.question,
            content_types=content_types,
            tags=None,
            top_k=5,  # 최대 5개 (요구사항)
            keyword_filter=False  # 의미 기반 검색만 사용
        )

        # 커뮤니티 정보 검색 (의도에 따라)
        community_results = []
        if intent["search_community"]:
            community_results = retriever.retrieve_community_info(
                query=req.question,
                top_k=3
            )

        # 컨텍스트 구성
        context_parts = []
        references = []

        # 커뮤니티 정보
        if community_results:
            info_texts = [item["content"] for item in community_results]
            if info_texts:
                context_parts.append("**커뮤니티 정보:**\n" + "\n".join(info_texts))
                for item in community_results:
                    references.append({"type": "community_info", "title": item["metadata"].get("title", "")})

        # 게시물 (요구사항 형식 준수)
        if all_results.get("posts"):
            post_texts = []
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
            for post in all_results["posts"][:5]:  # 최대 5개 (요구사항)
                metadata = post["metadata"]
                post_id = metadata.get("id", "")
                title = metadata.get("title", "")
                author = metadata.get("author", "")
                created_at = metadata.get("created_at", "")

                # 게시물 상세 조회하여 전체 내용 가져오기
                from services.post_service import PostService
                post_service = PostService()
                post_detail = await post_service.get_post_detail(int(post_id)) if post_id else None

                # 게시물 링크 생성
                post_link = f"{frontend_url}/interests-detail/{post_id}"

                # 요구사항 형식으로 구성
                post_text = f"제목: {title}\n링크: {post_link}\n작성일: {created_at}, 작성자: {author}"

                # 본문 내용이 있으면 요약을 위해 추가
                if post_detail and post_detail.get("content"):
                    post_text += f"\n본문 내용: {post_detail.get('content')[:500]}"

                post_texts.append(post_text)
                references.append({"type": "post", "id": post_id, "title": title, "link": post_link})

            if post_texts:
                context_parts.append("**관련 게시물:**\n" + "\n\n".join(post_texts))

        # 프로젝트 (요구사항 형식 준수)
        if all_results.get("projects"):
            project_texts = []
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
            for project in all_results["projects"][:5]:  # 최대 5개 (요구사항)
                metadata = project["metadata"]
                project_id = metadata.get("id", "")
                title = metadata.get("title", "")
                author = metadata.get("author", "")
                created_at = metadata.get("created_at", "")
                current_members = metadata.get("current_members", "0")
                max_members = metadata.get("max_members", "0")

                # 프로젝트 상세 조회하여 전체 내용 가져오기
                from services.project_service import ProjectService
                project_service = ProjectService()
                project_detail = await project_service.get_project_detail(int(project_id)) if project_id else None

                # 프로젝트 링크 생성
                project_link = f"{frontend_url}/project/{project_id}"

                # 요구사항 형식으로 구성 (프로젝트 모집 게시물)
                project_text = f"제목: {title}\n링크: {project_link}\n작성일: {created_at}, 작성자: {author}\n모집 인원: {current_members}/{max_members}"

                # 모집 기간이 있으면 추가 (메타데이터에 있다면)
                if metadata.get("deadline"):
                    project_text += f", 모집 기간: ~{metadata.get('deadline')}"

                # 본문 내용이 있으면 요약을 위해 추가
                if project_detail and project_detail.get("content"):
                    project_text += f"\n본문 내용: {project_detail.get('content')[:500]}"

                project_texts.append(project_text)
                references.append({"type": "project", "id": project_id, "title": title, "link": project_link})

            if project_texts:
                context_parts.append("**관련 프로젝트:**\n" + "\n\n".join(project_texts))

        # 공지사항
        if all_results.get("notices"):
            notice_texts = []
            for notice in all_results["notices"][:3]:
                metadata = notice["metadata"]
                notice_text = f"[{metadata.get('category', '')}] {metadata.get('title', '')}\n작성일: {metadata.get('date', '')}"
                if metadata.get('link'):
                    notice_text += f"\n링크: {metadata.get('link', '')}"
                notice_texts.append(notice_text)
                references.append({"type": "notice", "title": metadata.get("title", ""), "link": metadata.get("link", "")})

            if notice_texts:
                context_parts.append("**관련 공지사항:**\n" + "\n\n".join(notice_texts))

        # 컨텍스트가 없으면 미답변 질의 처리 (요구사항 #3)
        if not context_parts:
            logger.warning(f"검색 결과 없음: '{req.question}'")

            # 벡터 DB 상태 확인
            collections = vector_store.list_collections() if vector_store else []
            if not collections or not any(vector_store.get_collection_count(c) > 0 for c in collections):
                return ChatResponse(answer="죄송합니다. 현재 데이터베이스가 초기화되지 않았습니다. 관리자에게 문의하여 벡터 DB를 초기화해주세요.")

            # WantITNest 관련 질문으로 판단되는 경우 미답변 질의 기록
            if _is_wantitnest_related(req.question):
                faq_service.save_unanswered_query(req.question, req.user_id)
                logger.info(f"미답변 질의 기록: '{req.question}'")
                return ChatResponse(answer="죄송합니다. 해당 질문에 대한 답변이 데이터베이스에 없습니다. 관리자에게 문의해주세요.")

            return ChatResponse(answer="죄송합니다. 관련 정보를 찾을 수 없습니다. 다른 키워드로 검색해보시겠어요?")

        context = "\n\n".join(context_parts)

        # 답변 생성
        answer = generator.generate_answer(
            question=req.question,
            context=context,
            user_name=user_name
        )

        logger.info(f"채팅 응답 생성 완료 (user: {req.user_id}, references: {len(references)})")
        return ChatResponse(answer=answer)

    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/chat/notices", response_model=NoticeSearchResponse)
async def search_notices(req: NoticeSearchRequest):
    """
    공지사항 검색 및 추천
    - 카테고리별 필터링 가능
    - 의미론적 검색
    - 관련도 기반 랭킹
    """
    try:
        # 사용자 정보 조회
        user_name = None
        if req.user_id:
            user_profile = await user_service.get_user_profile(req.user_id)
            if user_profile:
                user_name = user_profile.get("memberName")

        # 공지사항 검색
        notices = retriever.retrieve_notices(
            query=req.query,
            category=req.category,
            top_k=req.top_k
        )

        # 추천 답변 생성
        answer = generator.generate_notice_recommendation(
            notices=notices,
            user_query=req.query,
            user_name=user_name
        )

        # 공지사항 정보 포맷팅
        notice_list = []
        for notice in notices:
            notice_info = {
                "title": notice["metadata"].get("title", ""),
                "category": notice["metadata"].get("category", ""),
                "date": notice["metadata"].get("date", ""),
                "link": notice["metadata"].get("link", ""),
                "similarity": notice.get("similarity_score", 0.0)
            }
            notice_list.append(notice_info)

        logger.info(f"공지사항 검색 완료: {len(notices)}개")
        return NoticeSearchResponse(answer=answer, notices=notice_list)

    except Exception as e:
        logger.error(f"공지사항 검색 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/chat/matching", response_model=MatchingResponse)
async def match_users(req: MatchingRequest):
    """
    사용자 매칭 추천
    - 프로필 유사도 기반
    - 관심사, 전공, 기술스택 고려
    """
    try:
        # 유사 사용자 찾기
        similar_users = await matching_service.find_similar_users(
            user_id=req.user_id,
            top_k=req.top_k
        )

        # 현재 사용자 정보
        current_user = await user_service.get_user_profile(req.user_id)
        user_name = current_user.get("memberName") if current_user else None

        # 매칭 추천 답변 생성
        answer = generator.generate_user_matching_response(
            similar_users=similar_users,
            user_name=user_name
        )

        # 사용자 정보 포맷팅
        user_list = []
        for user in similar_users:
            user_info = {
                "user_id": user["metadata"].get("user_id", ""),
                "name": user["metadata"].get("name", ""),
                "major": user["metadata"].get("major", ""),
                "interests": user["metadata"].get("interests", []),
                "similarity": user.get("similarity_score", 0.0)
            }
            user_list.append(user_info)

        logger.info(f"사용자 매칭 완료: {len(similar_users)}명")
        return MatchingResponse(answer=answer, matched_users=user_list)

    except Exception as e:
        logger.error(f"사용자 매칭 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/chat/search", response_model=ContentSearchResponse)
async def search_content(req: ContentSearchRequest):
    """
    통합 콘텐츠 검색 (Post + Project + Notice)
    - 게시물, 프로젝트, 공지사항 통합 검색
    - 태그 필터링 지원
    - 콘텐츠 타입별 결과 제공
    """
    try:
        # 사용자 정보 조회
        user_name = None
        if req.user_id:
            user_profile = await user_service.get_user_profile(req.user_id)
            if user_profile:
                user_name = user_profile.get("memberName")

        # 통합 검색
        search_results = retriever.search_all_content(
            query=req.query,
            content_types=req.content_types,
            tags=req.tags,
            top_k=req.top_k
        )

        posts = search_results.get("posts", [])
        projects = search_results.get("projects", [])
        notices = search_results.get("notices", [])

        # 통합 응답 생성
        answer = generator.generate_content_search_response(
            posts=posts,
            projects=projects,
            notices=notices,
            user_query=req.query,
            user_name=user_name
        )

        # 결과 포맷팅
        post_list = []
        for post in posts:
            tags_str = post["metadata"].get("tags", "")
            tags_list = [t.strip() for t in tags_str.split(",")] if tags_str else []

            post_info = {
                "id": post["metadata"].get("id", ""),
                "title": post["metadata"].get("title", ""),
                "author": post["metadata"].get("author", ""),
                "tags": tags_list,  # 문자열을 다시 리스트로 변환
                "created_at": post["metadata"].get("created_at", ""),
                "view_count": post["metadata"].get("view_count", "0"),
                "like_count": post["metadata"].get("like_count", "0"),
                "similarity": post.get("similarity_score", 0.0)
            }
            post_list.append(post_info)

        project_list = []
        for project in projects:
            tags_str = project["metadata"].get("tags", "")
            tags_list = [t.strip() for t in tags_str.split(",")] if tags_str else []

            project_info = {
                "id": project["metadata"].get("id", ""),
                "title": project["metadata"].get("title", ""),
                "author": project["metadata"].get("author", ""),
                "tags": tags_list,  # 문자열을 다시 리스트로 변환
                "is_recruiting": project["metadata"].get("is_recruiting", "True") == "True",
                "current_members": project["metadata"].get("current_members", "0"),
                "max_members": project["metadata"].get("max_members", "0"),
                "created_at": project["metadata"].get("created_at", ""),
                "similarity": project.get("similarity_score", 0.0)
            }
            project_list.append(project_info)

        notice_list = []
        for notice in notices:
            notice_info = {
                "title": notice["metadata"].get("title", ""),
                "category": notice["metadata"].get("category", ""),
                "date": notice["metadata"].get("date", ""),
                "link": notice["metadata"].get("link", ""),
                "similarity": notice.get("similarity_score", 0.0)
            }
            notice_list.append(notice_info)

        logger.info(f"통합 검색 완료: posts={len(posts)}, projects={len(projects)}, notices={len(notices)}")
        return ContentSearchResponse(
            answer=answer,
            posts=post_list,
            projects=project_list,
            notices=notice_list
        )

    except Exception as e:
        logger.error(f"통합 검색 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/admin/initialize-vectors")
async def initialize_vectors(background_tasks: BackgroundTasks):
    """
    벡터 데이터베이스 초기화 (관리자용)
    - 백그라운드로 실행
    """
    def run_initialization():
        import asyncio
        from scripts.initialize_vectors import main as init_main
        asyncio.run(init_main())

    background_tasks.add_task(run_initialization)

    return {
        "status": "started",
        "message": "벡터 데이터베이스 초기화가 백그라운드에서 시작되었습니다."
    }


@app.get("/api/collections")
def get_collections():
    """컬렉션 상태 조회"""
    if not vector_store:
        raise HTTPException(status_code=500, detail="Vector store not initialized")

    collections = vector_store.list_collections()
    collection_info = {}

    for col_name in collections:
        count = vector_store.get_collection_count(col_name)
        collection_info[col_name] = {"count": count}

    return {
        "collections": collection_info,
        "total_collections": len(collections)
    }


@app.get("/api/admin/faq")
def get_faq_list():
    """
    FAQ 목록 조회 (관리자/사용자용)
    """
    try:
        faq_list = faq_service.get_faq_list()
        return {
            "status": "success",
            "count": len(faq_list),
            "faqs": faq_list
        }
    except Exception as e:
        logger.error(f"FAQ 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/admin/unanswered-queries")
def get_unanswered_queries(only_pending: bool = True):
    """
    미답변 질의 목록 조회 (관리자용)

    Args:
        only_pending: 미답변만 조회할지 여부 (기본값: True)
    """
    try:
        queries = faq_service.get_unanswered_queries(only_pending=only_pending)
        return {
            "status": "success",
            "count": len(queries),
            "queries": queries
        }
    except Exception as e:
        logger.error(f"미답변 질의 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
