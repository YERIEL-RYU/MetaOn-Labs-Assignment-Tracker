import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import datetime
from playwright.async_api import async_playwright, Page
import sys
import os

# db 모듈 임포트를 위해 시스템 패스 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.handler import save_assignments

class BaseCrawler(ABC):
    def __init__(self, site_data: dict):
        self.site_id = site_data['id']
        self.site_name = site_data['name']
        self.url = site_data['url']
        self.login_url = site_data['login_url']
        self.username = site_data['username']
        self.password = site_data['password']
        self.timeout = 60000  # 60초 타임아웃 (로딩이 느린 사이트 대비)
        self.sleep_time = 1.5 # 요청 간격 1.5초

    @abstractmethod
    async def login(self, page: Any = None) -> bool:
        """
        주어진 객체(Playwright Page 등)에서 로그인 수행.
        성공 시 True, 실패 시 False 반환
        """
        pass

    @abstractmethod
    async def fetch_assignments(self, page: Any = None) -> List[Dict[str, Any]]:
        """
        로그인된 상태의 Page 객체에서 과제 정보를 수집하여 반환.
        반환 형태:
        [
            {
                "course": "과목명",
                "title": "과제명",
                "deadline": "ISO 8601 문자열 (YYYY-MM-DD HH:MM:SS)",
                "status": "pending" | "submitted" | "missing",
                "url": "해당 과제 URL (옵션)",
                "description": "설명 (옵션)"
            }, ...
        ]
        """
        pass

    def normalize_deadline(self, raw_deadline: str) -> str:
        """
        다양한 포맷의 마감일 문자열을 ISO 8601 포맷으로 정규화
        서브클래스에서 오버라이드하여 사이트별 포맷에 맞게 조정 가능.
        """
        import re
        # 날짜 형식 (YYYY-MM-DD, YYYY.MM.DD, YYYY/MM/DD 등) 뒤에 시간이 올 수도 안올 수도 있음
        match = re.search(r'(\d{4})[./-](\d{2})[./-](\d{2})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?', raw_deadline)
        if match:
            y, m, d = match.group(1), match.group(2), match.group(3)
            hh = match.group(4) or "23"
            mm = match.group(5) or "59"
            ss = match.group(6) or "59"
            return f"{y}-{m}-{d} {hh.zfill(2)}:{mm.zfill(2)}:{ss.zfill(2)}"
        return raw_deadline

    def save(self, assignments: List[Dict[str, Any]]):
        """
        수집된 과제 목록을 DB에 저장
        """
        save_assignments(self.site_id, assignments)

    async def run(self) -> tuple[bool, str]:
        """
        크롤링 전체 프로세스 실행
        반환값: (성공 여부: bool, 에러 메시지: str)
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                page.set_default_timeout(self.timeout)

                # 로그인
                print(f"[{self.site_name}] 로그인 시도...")
                is_logged_in = await self.login(page)
                if not is_logged_in:
                    await browser.close()
                    return False, "로그인 실패"

                await asyncio.sleep(self.sleep_time)

                # 과제 수집
                print(f"[{self.site_name}] 과제 수집 중...")
                assignments = await self.fetch_assignments(page)
                
                # 저장
                if assignments:
                    self.save(assignments)
                    print(f"[{self.site_name}] {len(assignments)}개 과제 저장 완료.")
                else:
                    print(f"[{self.site_name}] 수집된 과제가 없습니다.")

                await browser.close()
                return True, ""
        except Exception as e:
            error_msg = f"크롤링 중 오류 발생: {str(e)}"
            print(f"[{self.site_name}] {error_msg}")
            return False, error_msg
