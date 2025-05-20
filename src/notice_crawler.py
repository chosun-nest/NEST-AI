from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
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

# 크롤링 대상 URL (카테고리별)
CATEGORIES = {
    "일반공지": "https://www3.chosun.ac.kr/chosun/217/subview.do",
    "학사공지": "https://www4.chosun.ac.kr/acguide/9326/subview.do?layout=unknown",
    "장학공지": "https://www3.chosun.ac.kr/scho/2138/subview.do",
    "IT융합대학 공지": "https://eie.chosun.ac.kr/eie/5563/subview.do",
    "컴퓨터공학과 공지": "https://eie.chosun.ac.kr/ce/5670/subview.do"
}

# 기본 URL 추출 함수
def get_base_url(full_url):
    parts = full_url.split("/", 3)
    return f"{parts[0]}//{parts[2]}"

@app.get("/crawl/{category}")
def crawl_notices(category: str):
    url = CATEGORIES.get(category)
    if not url:
        return {"error": "Invalid category"}
    
    # BASE_URL 추출
    BASE_URL = get_base_url(url)

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

        # 마감일 처리 (장학공지)
        if category == "장학공지":
            # 마감일은 두 개의 <div> 중 첫 번째
            date_divs = cols[3].find_all("div", class_="date_fl")
            if len(date_divs) > 0:
                date = date_divs[0].text.strip()
            else:
                date = cols[3].text.strip()
        else:
            date = cols[3].text.strip()

        views = cols[4].text.strip().replace(",", "")

        #  제목과 링크 처리
        subject_cell = cols[1]
        link_tag = subject_cell.select_one("a")
        title = link_tag.text.strip() if link_tag else subject_cell.text.strip()
        href = link_tag["href"] if link_tag else ""
        link = urljoin(BASE_URL, href)
        
        # 2025년 작성일 필터링
        if not date.startswith("2025"):
            continue
        
        # 장학공지의 "접수 마감일" 처리
        deadline = ""
        if category == "장학공지":
            deadline = date_divs[1].text.strip()
            notice = {
                "category": category,
                "number": number,
                "title": title,
                "writer": writer,
                "date": date,
                "deadline": deadline,
                "views": views,
                "link": link
            }
        else:
            notice = {
                "category": category,
                "number": number,
                "title": title,
                "writer": writer,
                "date": date,
                "views": views,
                "link": link
            }
        
        # # 장학공지의 접수 마감일 추가
        # if deadline:
        #     notice["deadline"] = deadline
        
        notices.append(notice)

    # 모든 notice를 한 번에 Spring 서버로 전송
    try:
        api_url = f"http://localhost:6030/api/v1/notices/{category}" # TODO: 추후 배포 중인 스프링 서버 주소로 변경 필요
        res = requests.post(api_url, json={"notices": notices})
        print(f"✅ 전체 등록 완료: {res.status_code}, 스프링 응답: {res.json()}")
    except Exception as e:
        print(f"❌ 전체 등록 실패: {e}")

    return {"message": f"{len(notices)} notices added", "notices": notices}
