from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Spring API URL
SPRING_API_URL = "http://localhost:6030/api/notices"

# 크롤링 대상 URL (카테고리별)
CATEGORIES = {
    "일반공지": "https://www3.chosun.ac.kr/chosun/217/subview.do",
    "학사공지": "https://www4.chosun.ac.kr/acguide/9326/subview.do?layout=unknown",
    "장학공지": "https://www3.chosun.ac.kr/scho/2138/subview.do",
    "IT융합대학 공지": "https://eie.chosun.ac.kr/eie/5563/subview.do",
    "컴퓨터공학과 공지": "https://eie.chosun.ac.kr/ce/5670/subview.do"
}

@app.get("/crawl/{category}")
def crawl_notices(category: str):
    url = CATEGORIES.get(category)
    if not url:
        return {"error": "Invalid category"}

    # Selenium 옵션 설정
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")

    # ChromeDriver 설치 및 로드
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # 페이지 열기
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    notices = []

    # 공지사항 행 선택
    rows = soup.select("table tbody tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue
        
        # 공통 필드 처리
        number = cols[0].text.strip()
        title = cols[1].text.strip()
        writer = cols[2].text.strip()
        date = cols[3].text.strip()
        views = cols[4].text.strip().replace(",", "")
        link = cols[1].find("a")["href"] if cols[1].find("a") else ""

        # 2025년 작성일 필터링
        if not date.startswith("2025"):
            continue
        
        # 장학공지의 "접수 마감일" 처리
        deadline = ""
        if category == "장학공지" and len(cols) > 5:
            deadline = cols[5].text.strip()

        # 공지사항 데이터 구조
        notice = {
            "category": category,
            "number": number,
            "title": title,
            "writer": writer,
            "date": date,
            "views": int(views),
            "link": link
        }
        
        # 장학공지의 접수 마감일 추가
        if deadline:
            notice["deadline"] = deadline
        
        notices.append(notice)

        # Spring 서버로 데이터 전송
        try:
            res = requests.post(SPRING_API_URL, json=notice)
            print(f"✅ 등록 완료: {notice['title']}")
        except Exception as e:
            print(f"❌ 전송 실패: {e}")

    return {"message": f"{len(notices)} notices added", "notices": notices}
