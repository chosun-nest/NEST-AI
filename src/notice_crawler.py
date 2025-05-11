# Nest-AI/src/notice_crawler.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests

app = FastAPI()

# CORS 설정 (React 통신 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Spring API URL
SPRING_API_URL = "http://localhost:6030/api/notices"

# 크롤링 대상 URL (카테고리별)
CATEGORIES = {
    "general": "https://www3.chosun.ac.kr/chosun/217/subview.do?enc=Zm5jdDF8QEB8JTJGYmJzJTJGY2hvc3VuJTJGMTE3JTJGYXJ0Y2xMaXN0LmRvJTNG",  # 교내 일반공지
    "academic": "https://www4.chosun.ac.kr/acguide/9326/subview.do?layout=unknown",  # 교내 학사공지
    "scholarship": "https://www3.chosun.ac.kr/scho/2138/subview.do",  # 교내 장학공지 (접수마감일 포함)
    "itcollege": "https://eie.chosun.ac.kr/eie/5563/subview.do?enc=Zm5jdDF8QEB8JTJGYmJzJTJGZWllJTJGMzIwJTJGYXJ0Y2xMaXN0LmRvJTNG",  # IT융합대학 공지
    "computer": "https://eie.chosun.ac.kr/ce/5670/subview.do?enc=Zm5jdDF8QEB8JTJGYmJzJTJGY2UlMkYzMjglMkZhcnRjbExpc3QuZG8lM0Y%3D"  # 컴퓨터공학과 공지
}

@app.get("/crawl/{category}")
def crawl_notices(category: str):
    # 카테고리 URL 가져오기
    url = CATEGORIES.get(category)
    if not url:
        return {"error": "Invalid category"}

    # Selenium 옵션 설정
    options = Options()
    options.add_argument("--headless")  # 창 없이 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0") # User-Agent 추가

    # ChromeDriver 자동 설치 및 로드
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # 페이지 열기
    driver.get(url)

    # BeautifulSoup 파싱
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # 크롬 드라이버 종료
    driver.quit()

    # 공지사항 크롤링
    notices = []
    # rows = soup.select("table tbody tr")
    rows = soup.select("table.board-table.horizon5 tbody tr:not(.notice)") # 필요한 데이터만 크롤링


    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue  # 데이터가 부족한 행은 무시

        # 공통 필드 (모든 카테고리 공통)
        number = cols[0].text.strip()
        title = cols[1].text.strip()
        writer = cols[2].text.strip()
        date = cols[3].text.strip()
        views = cols[4].text.strip().replace(",", "")
        link = cols[1].find("a")["href"] if cols[1].find("a") else ""

        # 2025년 작성일 필터링
        if not date.startswith("2025"):
            continue
        
        # 장학공지일 경우 "접수 마감일" 추가 처리
        if category == "scholarship":
            deadline = cols[5].text.strip()
            notice = {
                "category": category,
                "number": number,
                "title": title,
                "writer": writer,
                "date": date,
                "deadline": deadline,
                "views": int(views),
                "link": link
            }
        else:
            notice = {
                "category": category,
                "number": number,
                "title": title,
                "writer": writer,
                "date": date,
                "views": int(views),
                "link": link
            }

        notices.append(notice)

        # ✅ Spring 서버로 전송
        try:
            res = requests.post(SPRING_API_URL, json=notice)
            print(f"✅ 등록 완료: {notice['title']}")
        except Exception as e:
            print(f"❌ 실패: {e}")

    return {"message": f"{len(notices)} notices added", "notices": notices}
