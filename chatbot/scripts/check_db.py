"""벡터 DB 상태 확인 스크립트"""
import sys
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.append(str(Path(__file__).parent.parent))

from rag.vector_store import VectorStore

def main():
    """벡터 DB 상태 확인"""
    print("=== 벡터 DB 상태 확인 ===\n")

    vector_store = VectorStore()
    collections = vector_store.list_collections()

    if not collections:
        print("❌ 컬렉션이 없습니다. 벡터 DB를 초기화해야 합니다.")
        print("\n초기화 방법:")
        print("  python scripts/initialize_vectors.py")
        return

    print(f"✅ 총 {len(collections)}개의 컬렉션이 있습니다.\n")

    total_docs = 0
    for col_name in collections:
        count = vector_store.get_collection_count(col_name)
        total_docs += count
        status = "✅" if count > 0 else "⚠️"
        print(f"{status} {col_name}: {count}개 문서")

    print(f"\n총 {total_docs}개의 문서가 저장되어 있습니다.")

    if total_docs == 0:
        print("\n❌ 문서가 없습니다. 벡터 DB를 초기화해야 합니다.")
        print("\n초기화 방법:")
        print("  python scripts/initialize_vectors.py")

if __name__ == "__main__":
    main()
