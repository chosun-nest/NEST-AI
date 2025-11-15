# 변경 사항 (Changelog)

## 2025-11-15 (v2) - 공지사항 검색 문제 해결

### 주요 변경 사항

#### 1. 질문 의도 파악 시스템 추가
- **파일**: `main.py`
- **함수**: `_detect_query_intent()`
- **기능**:
  - 사용자 질문에서 키워드 추출하여 검색 대상 결정
  - "공지", "알림", "안내" → 공지사항만 검색
  - "프로젝트", "모집" → 프로젝트만 검색
  - "게시물", "글" → 게시물만 검색
  - 명시되지 않은 경우 → 전체 검색

#### 2. 키워드 필터링 완화
- **파일**: `rag/retriever.py`, `main.py`
- **변경 내용**:
  - `search_all_content()`에 `keyword_filter` 파라미터 추가
  - 기본값 `False`로 설정하여 의미 기반 벡터 검색만 사용
  - 키워드가 정확히 매칭되지 않아도 의미상 유사한 콘텐츠 검색 가능
- **효과**:
  - "마일리지 관련 공지사항" → "포인트", "적립" 등 유사 키워드 포함 공지도 검색 가능

#### 3. 검색 정확도 개선
- 질문 의도에 따라 불필요한 콘텐츠 타입은 검색하지 않음
- 검색 속도 향상 및 관련성 높은 결과만 반환

### 예시

**이전**:
```
질문: "마일리지 관련 공지사항 검색해줘"
결과: 죄송합니다. 관련 정보를 찾을 수 없습니다.
```

**개선 후**:
```
질문: "마일리지 관련 공지사항 검색해줘"
- 질문 의도 파악: {"search_notices": True, "search_posts": False, ...}
- 공지사항만 검색 수행
- 벡터 검색으로 "포인트", "적립" 등 유사 의미의 공지사항도 검색
결과: 관련 공지사항 5개 반환
```

### 기술적 개선 사항

1. **의도 기반 검색**:
   - 질문에서 "공지" 키워드 감지 시 다른 콘텐츠는 검색하지 않음
   - 불필요한 벡터 검색 제거로 성능 향상

2. **하이브리드 검색 옵션**:
   - `keyword_filter=True`: 키워드 + 벡터 검색 (정확한 매칭)
   - `keyword_filter=False`: 벡터 검색만 (유연한 검색) ← 기본값

3. **로깅 개선**:
   - 질문 의도 로그 추가: `logger.info(f"질문 의도: {intent}")`
   - 검색 결과 추적 용이

---

## 2025-11-15 (v1) - 요구사항 기반 RAG 시스템 개선

### 주요 변경 사항

#### 1. 고정 FAQ 시스템 구현 (요구사항 #1)
- **파일**: `services/faq_service.py` (신규)
- **기능**:
  - 5개의 고정 FAQ 답변 자동 매칭
  - 사용자 질문과 FAQ 키워드 기반 유사도 판단
  - FAQ 질문 목록 조회 API 제공
- **FAQ 목록**:
  1. 이 사이트에 대해서 설명해주세요
  2. 프로젝트 모집/지원 방법이 궁금해요
  3. 게시글은 어떻게 작성하나요?
  4. 내 프로필은 어떻게 수정하나요?
  5. 비밀번호를 잊어버렸어요

#### 2. 게시물 추천 포맷 수정 (요구사항 #2)
- **파일**: `main.py`, `rag/generator.py`
- **변경 내용**:
  - 요구사항 명세의 마크다운 형식 적용
  - 게시물 형식:
    ```markdown
    ### [게시물 제목](게시물링크)
    작성일, 작성자
    요약 : [요약본]
    ```
  - 프로젝트 모집 게시물 형식:
    ```markdown
    ### [게시물 제목](게시물링크)
    작성일, 작성자
    모집 기간, 모집 인원
    요약 : [요약본]
    ```
  - 최대 5개까지 최신순으로 추천
  - 제목, 내용, 태그, 작성자 등 모든 필드에서 키워드 검색

#### 3. 미답변 질의 기록 기능 (요구사항 #3)
- **파일**: `services/faq_service.py`, `main.py`
- **기능**:
  - WantITNest 관련 질문이지만 데이터베이스에 답변이 없는 경우 자동 기록
  - 질의 내용, 사용자 ID, 타임스탬프 저장
  - JSON 파일로 저장 (`chatbot/data/unanswered_queries.json`)
  - 관리자용 조회 API 제공 (`/api/admin/unanswered-queries`)
- **판단 로직**:
  - WantITNest 관련 키워드 포함 여부 확인
  - "어떻게", "방법" 등 질문 패턴 감지

#### 4. Generator 프롬프트 개선
- **파일**: `rag/generator.py`
- **개선 사항**:
  - 요구사항 문서의 답변 원칙 반영
  - 간결하고 정확한 답변 생성
  - 추측성 답변 금지
  - 불필요한 빈 줄 제거
  - 마크다운 형식 준수

### 새로운 API 엔드포인트

#### FAQ 관련
- `GET /api/admin/faq` - FAQ 목록 조회
  - Response: `{"status": "success", "count": 5, "faqs": [...]}`

#### 미답변 질의 관련
- `GET /api/admin/unanswered-queries?only_pending=true` - 미답변 질의 목록 조회
  - Query Parameters:
    - `only_pending` (boolean): 미답변만 조회 (기본값: true)
  - Response: `{"status": "success", "count": N, "queries": [...]}`

### 파일 구조 변경

```
chatbot/
├── services/
│   ├── faq_service.py         # 신규: FAQ 및 미답변 질의 관리
│   ├── user_service.py
│   ├── notice_service.py
│   ├── matching_service.py
│   ├── post_service.py
│   └── project_service.py
├── data/
│   ├── unanswered_queries.json # 신규: 미답변 질의 저장
│   └── community_info.json
├── main.py                     # 수정: FAQ 통합, 미답변 질의 처리
├── rag/
│   └── generator.py            # 수정: 프롬프트 개선
└── 요구사항.md                 # 참조 문서
```

### 작동 흐름

1. **사용자 질문 입력**
   ```
   POST /api/chat
   {"question": "이 사이트에 대해 설명해주세요", "user_id": "user123"}
   ```

2. **FAQ 우선 체크**
   - 고정 FAQ와 매칭되면 즉시 답변 반환

3. **RAG 검색**
   - FAQ 매칭 실패 시 벡터 DB 검색
   - 게시물, 프로젝트, 공지사항, 커뮤니티 정보 통합 검색

4. **미답변 질의 처리**
   - 검색 결과 없고 WantITNest 관련 질문인 경우
   - 자동으로 미답변 질의 기록
   - 관리자 확인용 메시지 반환

### 테스트 방법

#### 1. FAQ 테스트
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "비밀번호를 잊어버렸어요"}'
```

#### 2. 게시물 추천 테스트
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "프론트엔드 관련 게시물 추천해줘"}'
```

#### 3. 미답변 질의 조회
```bash
curl http://localhost:8000/api/admin/unanswered-queries
```

### 주의사항

1. **환경변수 설정 필요**
   - `FRONTEND_URL`: 프론트엔드 URL (기본값: http://localhost:5173)
   - `OPENAI_API_KEY`: OpenAI API 키

2. **데이터 디렉토리**
   - `chatbot/data/` 디렉토리는 자동 생성됨
   - `unanswered_queries.json`은 최초 실행 시 생성

3. **벡터 DB 초기화**
   - 서비스 최초 실행 전 벡터 DB 초기화 필요
   - `POST /api/admin/initialize-vectors` 호출

### 향후 개선 사항

- [ ] 미답변 질의에 대한 관리자 답변 등록 기능
- [ ] FAQ 동적 추가/수정 API
- [ ] 게시물 추천 시 조회수/좋아요 수 가중치 적용
- [ ] 사용자 피드백 수집 및 학습 기능
