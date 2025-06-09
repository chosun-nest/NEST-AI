from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
import requests
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 크롤링 대상 카테고리 및 URL
CATEGORIES = {
    "일반공지": "https://www3.chosun.ac.kr/chosun/217/subview.do",
    "학사공지": "https://www4.chosun.ac.kr/acguide/9326/subview.do?layout=unknown",
    "장학공지": "https://www3.chosun.ac.kr/scho/2138/subview.do",
    "IT융합대학 공지": "https://eie.chosun.ac.kr/eie/5563/subview.do",
    "컴퓨터공학과 공지": "https://eie.chosun.ac.kr/ce/5670/subview.do"
}

def get_base_url(full_url: str):
    parts = full_url.split("/", 3)
    return f"{parts[0]}//{parts[2]}"

@app.get("/crawl/{category}")
def crawl_notices(category: str):
    url = CATEGORIES.get(category)
    if not url:
        return {"error": f"Invalid category '{category}'"}

    BASE_URL = get_base_url(url)

    # 셀레니움 옵션 설정
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    notices = []
    MAX_PAGE = 30  # 공지 300개 이상이면 30~50 설정

    for page in range(1, MAX_PAGE + 1):
        try:
            # 페이지 전환 JS 실행
            driver.execute_script(f"page_link('{page}')")
            time.sleep(1.2)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            # ⚠️ 고정공지 제외한 행만 선택
            rows = soup.select("table tbody tr")

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue

                # ✅ 고정 공지 제외
                number_text = cols[0].text.strip()
                if number_text in ["", "일반공지"]:
                    continue

                number = number_text
                title = cols[1].text.strip()
                writer = cols[2].text.strip()

                if category == "장학공지":
                    date_divs = cols[3].find_all("div", class_="date_fl")
                    date = date_divs[0].text.strip() if date_divs else cols[3].text.strip()
                else:
                    date = cols[3].text.strip()

                views = cols[4].text.strip().replace(",", "")

                link_tag = cols[1].select_one("a")
                href = link_tag["href"] if link_tag else ""
                link = urljoin(BASE_URL, href)

                # 작성일 2025년만 필터링
                if not date.startswith("2025"):
                    continue

                notice = {
                    "category": category,
                    "number": number,
                    "title": title,
                    "writer": writer,
                    "date": date,
                    "views": views,
                    "link": link
                }

                # 장학공지 마감일 필드 추가
                if category == "장학공지" and len(date_divs) > 1:
                    deadline = date_divs[1].text.strip()
                    notice["deadline"] = deadline

                notices.append(notice)

        except Exception as e:
            print(f"❌ 페이지 {page} 처리 실패: {e}")
            continue

    driver.quit()

    # Spring API로 전송
    try:
        api_url = f"http://localhost:6030/api/v1/notices/{category}"
        res = requests.post(api_url, json={"notices": notices})
        print(f"✅ 등록 성공: {res.status_code}, 응답: {res.json()}")
    except Exception as e:
        print(f"❌ 등록 실패: {e}")

    return {"message": f"{len(notices)}개 {category} 등록 완료", "notices": notices}
