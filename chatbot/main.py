# backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from models import ChatRequest, ChatResponse

from openai import OpenAI

# .env 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in .env file!")

client = OpenAI(api_key=OPENAI_API_KEY)  # 명시적으로 api_key 지정!

app = FastAPI()

# FAQ 리스트
FAQ_LIST = [
    {"question": "회원가입은 어떻게 하나요?", "answer": "홈페이지 우측 상단의 회원가입 버튼을 클릭해 정보를 입력하시면 가입이 완료됩니다."},
    {"question": "비밀번호를 잊어버렸어요.", "answer": "로그인 화면에서 '비밀번호 찾기'를 클릭하여 안내에 따라 재설정할 수 있습니다."},
    {"question": "회원탈퇴 하고 싶어요", "answer": "내 프로필 내 설정 제일 하단에 회원탈퇴 버튼이 있습니다."},
]

# FAQ 유사도 기준
def get_faq_answer(user_q: str):
    for faq in FAQ_LIST:
        if faq["question"] in user_q or user_q in faq["question"]:
            return faq["answer"]
    return None

# FastAPI 라우터
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    faq_answer = get_faq_answer(req.question)
    if faq_answer:
        return ChatResponse(answer=faq_answer)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": req.question}
            ],
            max_tokens=258,
        )
        answer = response.choices[0].message.content
        return ChatResponse(answer=answer.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {e}")

@app.get("/")
def root():
    return {"status": "AI Chatbot Backend Running"}
