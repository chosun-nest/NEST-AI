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
# import os
# from dotenv import load_dotenv

# load_dotenv()
# SPRING_SERVER_BASE_URL = os.getenv("SPRING_SERVER_BASE_URL", "http://localhost:6030")


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
# SW중심대학사업단 구조: 별도 독립적
# 일반공지, 장학공지 구조: 같음
# 장학공지: 마감일 추가
# 나머지 구조: 같음
CATEGORIES = {
    "일반공지": "https://www3.chosun.ac.kr/chosun/217/subview.do",
    "학사공지": "https://www4.chosun.ac.kr/acguide/9326/subview.do?layout=unknown",
    "장학공지": "https://www3.chosun.ac.kr/scho/2138/subview.do",
    "SW중심대학사업단": "https://sw.chosun.ac.kr/main/menu?gc=605XOAS",
    "IT융합대학": "https://eie.chosun.ac.kr/eie/5563/subview.do",
    "컴퓨터공학전공": "https://eie.chosun.ac.kr/ce/5670/subview.do",
    "정보통신공학전공": "https://eie.chosun.ac.kr/ice/7953/subview.do",
    "인공지능공학전공": "https://eie.chosun.ac.kr/aie/7977/subview.do",
    "모빌리티SW전공": "https://mobility.chosun.ac.kr/mobility/12563/subview.do"

}

# 기본 URL 추출 함수
def get_base_url(full_url: str):
    parts = full_url.split("/", 3)
    return f"{parts[0]}//{parts[2]}"

@app.get("/crawl/{category}")
def crawl_notices(category: str):
    url = CATEGORIES.get(category)
    if not url:
        return {"error": f"Invalid category '{category}'"}

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
    driver.get(url)

    notices = []
    MAX_PAGE = 30  # 공지 300개 이상이면 30~50 설정

    # 공지사항 행 선택
    for page in range(1, MAX_PAGE + 1):
        try:
            if category == "SW중심대학사업단":
                driver.get(f"{url}&do=list&page={page}")
            else:
                driver.get(url)
                time.sleep(0.5)
                driver.execute_script(f"page_link('{page}')")

            time.sleep(1.2)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            if category == "SW중심대학사업단":
                rows = soup.select("table.board_list tbody tr")
                print(f"🔥 SW중심 rows: {len(rows)}")

                for row in rows:
                    try:
                        if "notice" in row.get("class", []):
                            continue

                        cols = row.find_all("td")
                        if len(cols) < 5:
                            continue

                        number = cols[0].text.strip()
                        title_tag = cols[1].select_one("a > p")
                        title = title_tag.get_text(strip=True) if title_tag else "제목 없음"

                        a_tag = cols[1].select_one("a")
                        link = a_tag["href"] if a_tag and a_tag.has_attr("href") else ""
                        if not link.startswith("http"):
                            link = urljoin(BASE_URL, link)

                        writer = cols[2].text.strip()
                        date = cols[3].text.strip()
                        views = cols[4].text.replace("조회 :", "").strip()

                        if not date.startswith("2025"):
                            continue

                        notices.append({
                            "category": category,
                            "number": number,
                            "title": title,
                            "writer": writer,
                            "date": date,
                            "views": views,
                            "link": link
                        })

                    except Exception as e:
                        print(f"❌ SW공지 row 파싱 실패: {e}")

                continue

            # 그 외 일반/장학/학과 공지
            rows = soup.select("table tbody tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue

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

                if category == "장학공지" and len(date_divs) > 1:
                    deadline = date_divs[1].text.strip()
                    notice["deadline"] = deadline

                notices.append(notice)
        except Exception as e:
            print(f"❌ page {page} error: {e}")
            continue
        
    driver.quit()

     #  크롤링 결과 확인
    print(f"📦 전송할 공지 개수: {len(notices)}")
    if not notices:
        print("🚨 크롤링된 공지가 없습니다.")


    # Spring API로 전송
    try:
        api_url = f"http://49.246.71.236:6030/api/v1/notices/{category}"
        res = requests.post(api_url, json={"notices": notices})
        print(f"✅ 등록 시도 상태 코드: {res.status_code}")
        print(f"✅ 응답 본문: {res.text}")  # 여기서 JSON이 안 나오면 문제!
        print(f"✅ 응답 Content-Type: {res.headers.get('Content-Type')}")
    
        # 이 줄은 try 밖으로 빼는 게 좋음
        res_json = res.json()  # 여기서 JSON 아니라서 예외 발생 중
        print(f"✅ 등록 성공 응답: {res_json}")
    except Exception as e:
        print(f"❌ 등록 실패: {e}")


    return {"message": f"{len(notices)}개 {category} 등록 완료", "notices": notices}

# FastAPI 서버 실행을 위한 메인 함수
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)