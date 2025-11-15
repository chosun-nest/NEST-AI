"""벡터 데이터베이스 초기화 스크립트"""
import sys
import os
import json
import asyncio
import logging
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.append(str(Path(__file__).parent.parent))

from rag.embedder import Embedder
from rag.vector_store import VectorStore
from services.notice_service import NoticeService
from services.user_service import UserService
from services.post_service import PostService
from services.project_service import ProjectService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def initialize_community_info(embedder: Embedder, vector_store: VectorStore):
    """커뮤니티 정보 임베딩"""
    logger.info("커뮤니티 정보 임베딩 시작...")

    # JSON 파일 로드
    data_path = Path(__file__).parent.parent / "data" / "community_info.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    info_list = data.get("info", [])

    if not info_list:
        logger.warning("커뮤니티 정보가 없습니다.")
        return

    # 텍스트 준비
    documents = []
    metadatas = []
    ids = []

    for item in info_list:
        # 텍스트 생성
        text = f"[{item['category']}] {item['title']}: {item['content']}"
        documents.append(text)

        # 메타데이터
        metadatas.append({
            "category": item["category"],
            "title": item["title"],
            "id": item["id"]
        })

        # ID
        ids.append(f"community_info_{item['id']}")

    # 임베딩 생성
    logger.info(f"임베딩 생성 중... ({len(documents)}개)")
    embeddings = embedder.embed_texts(documents)

    # 벡터 스토어에 저장
    vector_store.add_documents(
        collection_name="community_info",
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    logger.info(f"커뮤니티 정보 임베딩 완료: {len(documents)}개")


async def initialize_notices(embedder: Embedder, vector_store: VectorStore):
    """공지사항 임베딩"""
    logger.info("공지사항 임베딩 시작...")

    notice_service = NoticeService()

    # 모든 공지사항 조회
    all_notices = await notice_service.get_all_notices()

    if not all_notices:
        logger.warning("공지사항이 없습니다.")
        return

    # 텍스트 준비
    documents = []
    metadatas = []
    ids = []

    for i, notice in enumerate(all_notices):
        # 텍스트 생성
        text = notice_service.format_notice_text(notice)
        documents.append(text)

        # 메타데이터
        metadata = notice_service.get_notice_metadata(notice)
        metadatas.append(metadata)

        # ID
        ids.append(f"notice_{i}")

    # 배치 처리 (한 번에 너무 많으면 에러날 수 있음)
    batch_size = 100
    total_batches = (len(documents) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, len(documents))

        batch_docs = documents[start_idx:end_idx]
        batch_metas = metadatas[start_idx:end_idx]
        batch_ids = ids[start_idx:end_idx]

        logger.info(f"배치 {batch_idx + 1}/{total_batches} 임베딩 생성 중...")

        # 임베딩 생성
        embeddings = embedder.embed_texts(batch_docs)

        # 벡터 스토어에 저장
        vector_store.add_documents(
            collection_name="notices",
            documents=batch_docs,
            embeddings=embeddings,
            metadatas=batch_metas,
            ids=batch_ids
        )

    logger.info(f"공지사항 임베딩 완료: {len(documents)}개")


async def initialize_user_profiles(embedder: Embedder, vector_store: VectorStore):
    """사용자 프로필 임베딩"""
    logger.info("사용자 프로필 임베딩 시작...")

    user_service = UserService()

    # 모든 사용자 조회
    all_users = await user_service.get_all_users()

    if not all_users:
        logger.warning("사용자가 없습니다.")
        return

    # 텍스트 준비
    documents = []
    metadatas = []
    ids = []

    for user in all_users:
        # 프로필을 텍스트로 변환
        profile_text = user_service.format_user_profile_text(user)
        documents.append(profile_text)

        # 학과명 추출
        departments = []
        if "memberDepartmentResponseDtoList" in user:
            departments = [d.get("departmentName", "") for d in user["memberDepartmentResponseDtoList"] if d.get("departmentName")]

        # 관심사 추출
        interests = []
        if "memberInterestResponseDtoList" in user:
            interests = [i.get("interestName", "") for i in user["memberInterestResponseDtoList"] if i.get("interestName")]

        # 메타데이터
        metadatas.append({
            "user_id": str(user.get("memberId", "")),
            "name": user.get("memberName", ""),
            "major": ", ".join(departments) if departments else "",
            "interests": interests
        })

        # ID
        ids.append(f"user_{user.get('memberId', '')}")

    # 임베딩 생성
    logger.info(f"임베딩 생성 중... ({len(documents)}개)")
    embeddings = embedder.embed_texts(documents)

    # 벡터 스토어에 저장
    vector_store.add_documents(
        collection_name="user_profiles",
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    logger.info(f"사용자 프로필 임베딩 완료: {len(documents)}개")


async def initialize_posts(embedder: Embedder, vector_store: VectorStore):
    """게시물 임베딩"""
    logger.info("게시물 임베딩 시작...")

    post_service = PostService()

    # 모든 게시물 조회
    all_posts = await post_service.get_all_posts(size=200)  # 최대 200개

    if not all_posts:
        logger.warning("게시물이 없습니다.")
        return

    # 텍스트 준비
    documents = []
    metadatas = []
    ids = []

    for post in all_posts:
        # 텍스트 생성
        text = post_service.format_post_text(post)
        documents.append(text)

        # 메타데이터
        metadata = post_service.get_post_metadata(post)
        metadatas.append(metadata)

        # ID
        post_id = post.get("id", "")
        ids.append(f"post_{post_id}")

    # 배치 처리
    batch_size = 100
    total_batches = (len(documents) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, len(documents))

        batch_docs = documents[start_idx:end_idx]
        batch_metas = metadatas[start_idx:end_idx]
        batch_ids = ids[start_idx:end_idx]

        logger.info(f"배치 {batch_idx + 1}/{total_batches} 임베딩 생성 중...")

        # 임베딩 생성
        embeddings = embedder.embed_texts(batch_docs)

        # 벡터 스토어에 저장
        vector_store.add_documents(
            collection_name="posts",
            documents=batch_docs,
            embeddings=embeddings,
            metadatas=batch_metas,
            ids=batch_ids
        )

    logger.info(f"게시물 임베딩 완료: {len(documents)}개")


async def initialize_projects(embedder: Embedder, vector_store: VectorStore):
    """프로젝트 임베딩"""
    logger.info("프로젝트 임베딩 시작...")

    project_service = ProjectService()

    # 모든 프로젝트 조회
    all_projects = await project_service.get_all_projects(size=200)  # 최대 200개

    if not all_projects:
        logger.warning("프로젝트가 없습니다.")
        return

    # 텍스트 준비
    documents = []
    metadatas = []
    ids = []

    for project in all_projects:
        # 텍스트 생성
        text = project_service.format_project_text(project)
        documents.append(text)

        # 메타데이터
        metadata = project_service.get_project_metadata(project)
        metadatas.append(metadata)

        # ID
        project_id = project.get("projectId", "")
        ids.append(f"project_{project_id}")

    # 배치 처리
    batch_size = 100
    total_batches = (len(documents) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, len(documents))

        batch_docs = documents[start_idx:end_idx]
        batch_metas = metadatas[start_idx:end_idx]
        batch_ids = ids[start_idx:end_idx]

        logger.info(f"배치 {batch_idx + 1}/{total_batches} 임베딩 생성 중...")

        # 임베딩 생성
        embeddings = embedder.embed_texts(batch_docs)

        # 벡터 스토어에 저장
        vector_store.add_documents(
            collection_name="projects",
            documents=batch_docs,
            embeddings=embeddings,
            metadatas=batch_metas,
            ids=batch_ids
        )

    logger.info(f"프로젝트 임베딩 완료: {len(documents)}개")


async def main():
    """메인 함수"""
    logger.info("=== 벡터 데이터베이스 초기화 시작 ===")

    # 초기화
    embedder = Embedder()
    vector_store = VectorStore()

    # 기존 컬렉션 삭제 (선택사항)
    # vector_store.delete_collection("community_info")
    # vector_store.delete_collection("notices")
    # vector_store.delete_collection("user_profiles")

    try:
        # 1. 커뮤니티 정보 임베딩
        await initialize_community_info(embedder, vector_store)

        # 2. 공지사항 임베딩
        await initialize_notices(embedder, vector_store)

        # 3. 게시물 임베딩
        await initialize_posts(embedder, vector_store)

        # 4. 프로젝트 임베딩
        await initialize_projects(embedder, vector_store)

        # 5. 사용자 프로필 임베딩
        await initialize_user_profiles(embedder, vector_store)

        # 결과 확인
        logger.info("\n=== 벡터 데이터베이스 초기화 완료 ===")
        logger.info(f"컬렉션 목록: {vector_store.list_collections()}")

        for collection_name in vector_store.list_collections():
            count = vector_store.get_collection_count(collection_name)
            logger.info(f"- {collection_name}: {count}개 문서")

    except Exception as e:
        logger.error(f"초기화 실패: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
