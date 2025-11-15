"""임베딩 생성 모듈 - OpenAI Embeddings 사용"""
import os
from typing import List
from openai import OpenAI

class Embedder:
    """OpenAI API를 사용한 텍스트 임베딩 생성"""

    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Args:
            model: OpenAI 임베딩 모델 이름
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.dimension = 1536  # text-embedding-3-small의 기본 차원

    def embed_text(self, text: str) -> List[float]:
        """
        단일 텍스트를 벡터로 변환

        Args:
            text: 임베딩할 텍스트

        Returns:
            벡터 (List[float])
        """
        if not text or not text.strip():
            raise ValueError("텍스트가 비어있습니다")

        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        여러 텍스트를 배치로 벡터화

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            벡터 리스트
        """
        if not texts:
            return []

        # 빈 텍스트 필터링
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("모든 텍스트가 비어있습니다")

        response = self.client.embeddings.create(
            input=valid_texts,
            model=self.model
        )
        return [data.embedding for data in response.data]
