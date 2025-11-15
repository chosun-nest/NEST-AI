"""검색 테스트 스크립트"""
import sys
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.append(str(Path(__file__).parent.parent))

from rag.embedder import Embedder
from rag.vector_store import VectorStore
from rag.retriever import Retriever

def main():
    """검색 테스트"""
    print("=== 검색 테스트 ===\n")

    embedder = Embedder()
    vector_store = VectorStore()
    retriever = Retriever(embedder, vector_store)

    # Python 관련 게시물 검색
    query = "Python"
    print(f"검색어: {query}\n")

    posts = retriever.retrieve_posts(query=query, top_k=2, keyword_filter=False)

    print(f"검색 결과: {len(posts)}개\n")

    for i, post in enumerate(posts, 1):
        print(f"--- 게시물 {i} ---")
        print(f"ID: {post['id']}")
        print(f"Content: {post['content'][:100]}...")
        print(f"Metadata: {post['metadata']}")
        print(f"Similarity: {post['similarity_score']:.4f}")
        print()

if __name__ == "__main__":
    main()
