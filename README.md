## 📁 프로젝트 파일 구조

📁 crawler/
    ├── 🐳 Dockerfile
    ├── 🐍 notice_crawler.py
    ├── 📄 requirements.txt
    └── 🐳 docker-compose.yml

# 📌 아이콘 설명:
🐳 → Docker 관련 파일
🐍 → Python 파일
📄 → 일반 텍스트/설정 파일

---

# 📌 2025-04-13 수정 내용
## ✅ 1. `crawler/notice_crawler.py`
- **Selenium + BeautifulSoup 혼합 사용**
- **조선대 IT융합대학 공지사항 1~10페이지 크롤링**
  - 각 페이지는 `?page=` 파라미터를 붙여 반복
  - 상단 고정 공지 제외: `tr.notice` 제외한 `tr`만 선택

```python
MAX_PAGE = 10  # 페이지 수 조정 가능

rows = soup.select("table.board-table.horizon5 tbody tr:not(.notice)")
```

- Spring API로 POST 전송 (requests.post())
- 에러 로그와 성공 로그 구분

```python
for notice in all_notices:
    try:
        res = requests.post(API_URL, json=notice, headers=headers)
        if res.status_code == 200:
            print(f"✅ 등록 완료: {notice['title']}")
        else:
            print(f"❌ 실패: {res.status_code}, {res.text}")
    except Exception as e:
        print(f"🚨 예외 발생: {e}")
```

## ✅ 2. docker-compose.yml`
- mysql-container
