"""ChromaDB 벡터 스토어 관리 모듈"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB를 사용한 벡터 스토어 관리"""

    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """
        Args:
            persist_directory: ChromaDB 저장 경로
        """
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        logger.info(f"ChromaDB 초기화 완료: {persist_directory}")

    def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        컬렉션 가져오기 또는 생성

        Args:
            name: 컬렉션 이름
            metadata: 컬렉션 메타데이터

        Returns:
            ChromaDB Collection
        """
        # ChromaDB는 빈 메타데이터를 허용하지 않으므로 None 전달
        collection_metadata = metadata if metadata else None

        if collection_metadata:
            return self.client.get_or_create_collection(
                name=name,
                metadata=collection_metadata
            )
        else:
            return self.client.get_or_create_collection(name=name)

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """
        문서를 컬렉션에 추가

        Args:
            collection_name: 컬렉션 이름
            documents: 문서 텍스트 리스트
            embeddings: 임베딩 벡터 리스트
            metadatas: 메타데이터 리스트
            ids: 문서 ID 리스트
        """
        collection = self.get_or_create_collection(collection_name)

        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"{collection_name}에 {len(documents)}개 문서 추가 완료")

    def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        유사한 문서 검색

        Args:
            collection_name: 컬렉션 이름
            query_embedding: 쿼리 임베딩 벡터
            n_results: 반환할 결과 수
            where: 필터 조건 (메타데이터 기반)

        Returns:
            검색 결과 (documents, metadatas, distances, ids)
        """
        collection = self.get_or_create_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else []
        }

    def delete_collection(self, collection_name: str):
        """
        컬렉션 삭제

        Args:
            collection_name: 삭제할 컬렉션 이름
        """
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"컬렉션 삭제 완료: {collection_name}")
        except Exception as e:
            logger.error(f"컬렉션 삭제 실패: {e}")

    def list_collections(self) -> List[str]:
        """
        모든 컬렉션 목록 반환

        Returns:
            컬렉션 이름 리스트
        """
        collections = self.client.list_collections()
        return [col.name for col in collections]

    def get_collection_count(self, collection_name: str) -> int:
        """
        컬렉션의 문서 개수 반환

        Args:
            collection_name: 컬렉션 이름

        Returns:
            문서 개수
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            return collection.count()
        except Exception as e:
            logger.error(f"컬렉션 카운트 실패: {e}")
            return 0
