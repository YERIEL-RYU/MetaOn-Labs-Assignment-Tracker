import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from db.handler import get_all_sites, add_crawl_log
import importlib

logger = logging.getLogger("Scheduler")

# 글로벌 스케줄러 인스턴스
_scheduler = None

def run_crawler_sync(site):
    """동기 환경(APScheduler 스레드)에서 비동기 크롤러 실행"""
    logger.info(f"'{site['name']}' 크롤링 시작...")
    start_time = datetime.now()
    
    # 동적 모듈 로드
    module_name = site['crawler_class'].lower().replace('crawler', '')
    try:
        module = importlib.import_module(f'crawler.{module_name}')
        crawler_class = getattr(module, site['crawler_class'])
    except Exception as e:
        error_msg = f"크롤러 클래스 로드 실패: {e}"
        logger.error(error_msg)
        add_crawl_log(site['id'], start_time, datetime.now(), False, error_msg)
        return

    crawler = crawler_class(site)
    
    # 비동기 실행을 위해 새 이벤트 루프 사용
    success, msg = asyncio.run(crawler.run())
    
    end_time = datetime.now()
    add_crawl_log(site['id'], start_time, end_time, success, msg)
    logger.info(f"'{site['name']}' 크롤링 완료. 성공: {success}")

def job_crawl_all_sites():
    """활성화된 모든 사이트 크롤링 작업"""
    sites = get_all_sites(active_only=True)
    if not sites:
        logger.info("활성화된 사이트가 없습니다.")
        return
        
    for site in sites:
        run_crawler_sync(site)

def start_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        # 기본 720시간 주기 (한달)
        _scheduler.add_job(
            job_crawl_all_sites, 
            IntervalTrigger(hours=720), 
            id='crawl_job', 
            replace_existing=True,
            next_run_time=datetime.now() # 시작 시 바로 1회 실행
        )
        _scheduler.start()
        logger.info("백그라운드 스케줄러가 시작되었습니다.")

def update_scheduler_interval(hours: int):
    """스케줄러 주기 업데이트"""
    if _scheduler is not None:
        _scheduler.reschedule_job('crawl_job', trigger=IntervalTrigger(hours=hours))
        logger.info(f"스케줄러 주기가 {hours}시간으로 변경되었습니다.")
