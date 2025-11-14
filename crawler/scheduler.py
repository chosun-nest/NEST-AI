"""
크롤링 스케줄러
정기적으로 모든 카테고리의 공지사항을 크롤링합니다.
"""

import requests
import logging
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 크롤링 대상 카테고리
CATEGORIES = [
    "일반공지",
    "학사공지",
    "장학공지",
    "SW중심대학사업단",
    "IT융합대학",
    "컴퓨터공학전공",
    "정보통신공학전공",
    "인공지능공학전공",
    "모빌리티SW전공"
]

# Crawler API URL
CRAWLER_API_BASE = "http://crawler:8001"  # Docker 네트워크 내부 통신


def wait_for_crawler():
    """Crawler API가 준비될 때까지 대기"""
    max_retries = 30
    retry_interval = 2

    for attempt in range(max_retries):
        try:
            response = requests.get(f"{CRAWLER_API_BASE}/docs", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Crawler API 준비 완료")
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.info(f"⏳ Crawler API 대기 중... ({attempt + 1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                logger.error(f"❌ Crawler API 연결 실패: {e}")
                return False
    return False


def crawl_all_categories():
    """모든 카테고리 크롤링 실행"""
    logger.info("=" * 60)
    logger.info(f"크롤링 작업 시작: {datetime.now()}")
    logger.info("=" * 60)

    results = []
    for category in CATEGORIES:
        try:
            logger.info(f"📡 {category} 크롤링 시작...")
            response = requests.get(
                f"{CRAWLER_API_BASE}/crawl/{category}",
                timeout=300  # 5분 타임아웃
            )

            if response.status_code == 200:
                data = response.json()
                notice_count = len(data.get("notices", []))
                logger.info(f"✅ {category}: {notice_count}개 공지 등록 완료")
                results.append({"category": category, "count": notice_count, "status": "success"})
            else:
                logger.error(f"❌ {category}: HTTP {response.status_code}")
                results.append({"category": category, "status": "error", "code": response.status_code})

        except Exception as e:
            logger.error(f"❌ {category} 크롤링 실패: {str(e)}")
            results.append({"category": category, "status": "error", "error": str(e)})

    # 요약 출력
    success_count = sum(1 for r in results if r["status"] == "success")
    total_notices = sum(r.get("count", 0) for r in results if r["status"] == "success")

    logger.info("=" * 60)
    logger.info(f"크롤링 작업 완료: {datetime.now()}")
    logger.info(f"성공: {success_count}/{len(CATEGORIES)} 카테고리")
    logger.info(f"총 {total_notices}개 공지 등록")
    logger.info("=" * 60)


def main():
    """스케줄러 실행"""
    scheduler = BlockingScheduler()

    # 평일 오전 9시 크롤링
    scheduler.add_job(
        crawl_all_categories,
        CronTrigger(day_of_week='mon-fri', hour=9, minute=0),
        id='morning_crawl',
        name='평일 오전 9시 크롤링',
        replace_existing=True
    )

    # 평일 오후 1시 크롤링
    scheduler.add_job(
        crawl_all_categories,
        CronTrigger(day_of_week='mon-fri', hour=13, minute=0),
        id='afternoon_crawl',
        name='평일 오후 1시 크롤링',
        replace_existing=True
    )

    # 평일 오후 5시 크롤링
    scheduler.add_job(
        crawl_all_categories,
        CronTrigger(day_of_week='mon-fri', hour=17, minute=0),
        id='evening_crawl',
        name='평일 오후 5시 크롤링',
        replace_existing=True
    )

    # 시작 정보 출력
    logger.info("🚀 크롤링 스케줄러 시작")
    logger.info("📅 스케줄: 평일 오전 9시, 오후 1시, 오후 5시 (총 3회)")

    # Crawler API 준비 대기
    logger.info("⏳ Crawler API 연결 대기 중...")
    if wait_for_crawler():
        logger.info("⏰ 시작 시 즉시 크롤링 실행...")
        crawl_all_categories()
    else:
        logger.warning("⚠️  시작 시 크롤링 건너뜀 (다음 스케줄에 실행 예정)")

    # 스케줄러 시작
    logger.info("⏰ 다음 실행 대기 중...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("스케줄러 종료")


if __name__ == "__main__":
    main()
