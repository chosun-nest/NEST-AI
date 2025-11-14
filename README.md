# AI-ChatBot 실행 가이드

---

## [Nest-FE (프론트엔드)]

### 주요 수정 파일 목록

- `src/api/ai/ai.ts`
- `src/components/ai/Markdown.tsx`
- `src/components/chatbot/ChatBotUI.tsx`
- `src/components/chatbot/Markdown.tsx`  
  (※ `npm install react-markdown remark-gfm` 필요)
- `src/components/layout/ai.tsx`  
  (※ `npm install react-spinners` 필요)

---

### 설치 및 실행 방법

```bash
# 1. 패키지 설치 (최초 1회)
npm install react-markdown remark-gfm
npm install react-spinners

# 2. 개발 서버 실행
npm run dev
```

## Nest-AI (백엔드)

### 1. Chatbot 서버 실행법
```bash
cd Nest-AI/chatbot

# 1. 가상환경 생성 (최초 1회)
python -m venv venv

# 2. 가상환경 활성화
venv\Scripts\activate  # (Windows)

# 3. 라이브러리 설치 (최초 1회)
pip install -r requirements.txt

# 4. FastAPI 서버 실행
uvicorn main:app --reload
```

### ※ 2번 창에서 실행 시:
```bash
cd Nest-AI/chatbot
uvicorn main:app --reload
```

### 2. Crawler
- 경로: Nest-AI/crawler
- 실행 방법은 별도 안내

---

## Docker Compose로 실행 (권장)

### 1. 환경 설정
```bash
# 1. .env 파일 생성
cp .env.example .env

# 2. .env 파일 편집하여 API 키 입력
# OPENAI_API_KEY=your_actual_api_key_here
```

### 2. Docker Compose 실행
```bash
# 모든 서비스 빌드 및 실행
docker compose up --build

# 백그라운드 실행
docker compose up -d

# 로그 확인
docker compose logs -f

# 특정 서비스만 실행
docker compose up chatbot
docker compose up crawler
```

### 3. 서비스 접속
- **Chatbot API**: http://localhost:8000
- **Crawler API**: http://localhost:8001
- **Chatbot API 문서**: http://localhost:8000/docs
- **Crawler API 문서**: http://localhost:8001/docs

### 3-1. 자동 크롤링 스케줄러
Docker Compose 실행 시 자동으로 스케줄러가 함께 실행됩니다:
- **스케줄**: 평일(월~금) 오전 9시, 오후 1시, 오후 5시 (하루 3회)
- **대상**: 전체 9개 카테고리 (일반공지, 학사공지, 장학공지 등)
- **동작**: 크롤링 결과를 Spring API에 자동 저장

```bash
# 스케줄러 로그 확인
docker compose logs -f scheduler

# 특정 시간에 실행하도록 변경하려면
# crawler/scheduler.py 파일의 CronTrigger 수정
# 예: 매일 자정 -> CronTrigger(hour=0, minute=0)
# 예: 주말 오전 10시 -> CronTrigger(day_of_week='sat-sun', hour=10, minute=0)
```

### 4. 종료 및 정리
```bash
# 서비스 중지
docker compose down

# 볼륨까지 삭제
docker compose down -v

# 이미지까지 삭제
docker compose down --rmi all
```

---

## 프론트엔드 연동

### 공지사항 조회 (권장)
프론트엔드에서는 Spring API에 저장된 데이터를 조회합니다:

```javascript
// 특정 카테고리 공지사항 조회
const fetchNotices = async (category) => {
  const response = await fetch(
    `http://49.246.71.236:6030/api/v1/notices/${category}`
  );
  return await response.json();
};

// 사용 예시
const notices = await fetchNotices('일반공지');
```

**지원 카테고리**:
- 일반공지, 학사공지, 장학공지
- SW중심대학사업단
- IT융합대학, 컴퓨터공학전공, 정보통신공학전공, 인공지능공학전공, 모빌리티SW전공

### 수동 크롤링 (선택)
필요시 특정 카테고리만 즉시 크롤링:

```bash
curl http://localhost:8001/crawl/일반공지
```

---
### 참고
- 프론트엔드: Nest-FE 루트에서 작업
- 백엔드 챗봇: Nest-AI/chatbot 디렉토리에서 작업
- Docker 사용 시 의존성 설치 자동화
- 스케줄러가 평일 오전 9시, 오후 1시, 오후 5시에 자동으로 모든 공지를 크롤링
- 추가 패키지 설치나 환경변경시 이 문서를 업데이트