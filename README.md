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
### 참고
- 프론트엔드: Nest-FE 루트에서 작업
- 백엔드 챗봇: Nest-AI/chatbot 디렉토리에서 작업
- 의존성 설치는 최초 1회만, 서버 실행은 매번 필요
- 추가 패키지 설치나 환경변경시 이 문서를 업데이트