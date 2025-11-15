# WantITNest RAG Chatbot

조선대학교 IT융합대학 WantITNest 커뮤니티를 위한 RAG(Retrieval-Augmented Generation) 기반 AI 챗봇입니다.

## 주요 기능

### 1. 커뮤니티 정보 Q&A
- 커뮤니티, 학과, 학사 정보에 대한 질문 답변
- 벡터 검색 기반 정확한 정보 제공
- 사용자 이름을 활용한 개인화된 답변

### 2. 통합 콘텐츠 검색 (Post + Project + Notice)
- 게시물, 프로젝트, 공지사항 통합 의미론적 검색
- 카테고리/태그별 필터링 지원
- 유사도 기반 관련 콘텐츠 추천 (2-3개)
- 상세 페이지 링크 제공

### 3. 사용자 매칭 시스템
- 프로필 유사도 기반 사용자 추천
- 관심사, 전공, 기술스택 고려
- 프로젝트 파트너 매칭

## 기술 스택

- **프레임워크**: FastAPI
- **LLM**: OpenAI GPT-4o
- **임베딩**: OpenAI text-embedding-3-small
- **벡터 DB**: ChromaDB (로컬 영속성)
- **Spring API 연동**: httpx (비동기)

## 프로젝트 구조

```
chatbot/
├── main.py                     # FastAPI 메인 애플리케이션
├── models.py                   # Pydantic 데이터 모델
├── requirements.txt            # 의존성 목록
├── rag/                        # RAG 시스템 컴포넌트
│   ├── embedder.py            # OpenAI 임베딩 생성
│   ├── vector_store.py        # ChromaDB 관리
│   ├── retriever.py           # 문서 검색
│   └── generator.py           # LLM 응답 생성
├── services/                   # 비즈니스 로직 서비스
│   ├── user_service.py        # 사용자 정보 조회
│   ├── notice_service.py      # 공지사항 조회
│   └── matching_service.py    # 사용자 매칭
├── scripts/                    # 유틸리티 스크립트
│   └── initialize_vectors.py  # 벡터 DB 초기화
└── data/                       # 데이터 저장소
    ├── community_info.json    # 커뮤니티 정보
    └── chroma_db/             # ChromaDB 저장소
```

## 설치 및 실행

### 1. 의존성 설치

```bash
cd chatbot
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 입력:

```env
OPENAI_API_KEY=your_openai_api_key_here
SPRING_API_HOST=host.docker.internal
FRONTEND_URL=http://localhost:5173
```

- `OPENAI_API_KEY`: OpenAI API 키
- `SPRING_API_HOST`: Spring API 호스트 (Docker: host.docker.internal, 로컬: localhost)
- `FRONTEND_URL`: 프론트엔드 URL (게시물/프로젝트 링크 생성용)
  - Posts: `{FRONTEND_URL}/interests-detail/{id}`
  - Projects: `{FRONTEND_URL}/project/{id}`

### 3. 벡터 데이터베이스 초기화

최초 실행 시 벡터 데이터베이스를 초기화해야 합니다:

```bash
cd chatbot
python scripts/initialize_vectors.py
```

이 스크립트는 다음 작업을 수행합니다:
- 커뮤니티 정보 임베딩
- Spring API에서 공지사항 가져와서 임베딩
- Spring API에서 사용자 프로필 가져와서 임베딩

### 4. 서버 실행

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

또는 Docker Compose 사용:

```bash
cd ..
docker-compose up chatbot
```

## API 엔드포인트

### 1. 일반 채팅 (RAG)

**Endpoint**: `POST /api/chat`

**Request**:
```json
{
  "question": "IT융합대학에는 어떤 전공이 있나요?",
  "user_id": "user123"  // optional
}
```

**Response**:
```json
{
  "answer": "홍길동님, IT융합대학은 4개의 전공으로 구성되어 있습니다..."
}
```

### 2. 공지사항 검색

**Endpoint**: `POST /api/chat/notices`

**Request**:
```json
{
  "query": "장학금 신청",
  "user_id": "user123",  // optional
  "category": "장학공지",  // optional
  "top_k": 5
}
```

**Response**:
```json
{
  "answer": "장학금 관련 공지사항을 찾았습니다...",
  "notices": [
    {
      "title": "2025학년도 1학기 장학금 신청 안내",
      "category": "장학공지",
      "date": "2025-01-15",
      "link": "https://...",
      "similarity": 0.89
    }
  ]
}
```

### 3. 사용자 매칭

**Endpoint**: `POST /api/chat/matching`

**Request**:
```json
{
  "user_id": "user123",
  "top_k": 5
}
```

**Response**:
```json
{
  "answer": "홍길동님과 비슷한 관심사를 가진 동료를 추천합니다...",
  "matched_users": [
    {
      "user_id": "user456",
      "name": "김철수",
      "major": "인공지능공학",
      "interests": ["AI", "웹개발"],
      "similarity": 0.85
    }
  ]
}
```

### 4. 벡터 DB 초기화 (관리자)

**Endpoint**: `POST /api/admin/initialize-vectors`

백그라운드에서 벡터 데이터베이스를 재초기화합니다.

### 5. 컬렉션 상태 확인

**Endpoint**: `GET /api/collections`

**Response**:
```json
{
  "collections": {
    "community_info": {"count": 15},
    "notices": {"count": 523},
    "user_profiles": {"count": 120}
  },
  "total_collections": 3
}
```

### 6. 헬스 체크

**Endpoint**: `GET /health`

서버 및 RAG 시스템 상태 확인

## 데이터 관리

### 커뮤니티 정보 추가

`data/community_info.json` 파일을 수정하여 커뮤니티 정보를 추가할 수 있습니다:

```json
{
  "info": [
    {
      "id": "16",
      "category": "새 카테고리",
      "title": "제목",
      "content": "내용"
    }
  ]
}
```

변경 후 벡터 DB를 재초기화하세요:

```bash
python scripts/initialize_vectors.py
```

### 공지사항 업데이트

공지사항은 Spring API에서 자동으로 가져옵니다. 크롤러가 새 공지를 수집한 후 벡터 DB를 재초기화하면 반영됩니다.

### 사용자 프로필 업데이트

사용자 프로필도 Spring API에서 가져옵니다. 정기적으로 벡터 DB를 재초기화하여 최신 상태를 유지하세요.

## Spring API 연동

### 필요한 Spring API 엔드포인트

1. **사용자 프로필**: `GET /api/v1/users/{user_id}`
2. **전체 사용자**: `GET /api/v1/users`
3. **카테고리별 공지**: `GET /api/v1/notices/{category}`
4. **최근 공지**: `GET /api/v1/notices/recent?days=7`

### API 응답 예시

**사용자 프로필**:
```json
{
  "id": "user123",
  "name": "홍길동",
  "major": "인공지능공학",
  "grade": "3",
  "interests": ["AI", "웹개발"],
  "tech_stack": ["Python", "React"],
  "projects": ["프로젝트1", "프로젝트2"],
  "bio": "AI와 웹 개발에 관심이 많습니다."
}
```

**공지사항**:
```json
{
  "category": "학사공지",
  "number": "123",
  "title": "2025학년도 1학기 수강신청 안내",
  "writer": "학사지원팀",
  "date": "2025-01-10",
  "views": "1234",
  "link": "https://...",
  "content": "수강신청 일정은..."
}
```

## 성능 최적화

- **배치 임베딩**: 여러 문서를 한 번에 임베딩하여 API 호출 최소화
- **캐싱**: ChromaDB의 영속성을 활용한 빠른 검색
- **비동기 처리**: httpx를 사용한 비동기 Spring API 호출
- **Top-K 제한**: 검색 결과 수를 제한하여 LLM 토큰 사용 최적화

## 문제 해결

### ChromaDB 오류

ChromaDB 데이터가 손상된 경우:

```bash
rm -rf data/chroma_db
python scripts/initialize_vectors.py
```

### Spring API 연결 실패

`.env` 파일의 `SPRING_API_HOST` 확인:
- 로컬 테스트: `localhost`
- Docker 환경: `host.docker.internal`
- 프로덕션: 실제 IP 주소

### OpenAI API 오류

- API 키가 올바른지 확인
- API 사용량 한도 확인
- 네트워크 연결 확인

## 개발 로드맵

- [ ] 대화 히스토리 관리 (세션별)
- [ ] 다국어 지원 (영어)
- [ ] 프로젝트 파트너 매칭 개선
- [ ] 실시간 공지사항 업데이트 웹훅
- [ ] 챗봇 성능 모니터링 대시보드
- [ ] A/B 테스트 프레임워크

## 라이선스

MIT License

## 기여

버그 리포트 및 기능 제안은 이슈로 등록해주세요.
