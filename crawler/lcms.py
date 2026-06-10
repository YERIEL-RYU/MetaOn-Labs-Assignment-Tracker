import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import Page
from typing import List, Dict, Any
from crawler.base import BaseCrawler

class LcmsCrawler(BaseCrawler):
    """일반적인 LCMS 기반 시스템 크롤러 예시"""
    
    SELECTOR_ID = 'input[name="uid"]'
    SELECTOR_PW = 'input[name="pswd"]'
    SELECTOR_LOGIN_BTN = '#btn_login'

    async def login(self, page: Page) -> bool:
        """LCMS 시스템 로그인 구현"""
        try:
            await page.goto(self.login_url)
            await page.fill(self.SELECTOR_ID, self.username)
            await page.fill(self.SELECTOR_PW, self.password)
            await page.click(self.SELECTOR_LOGIN_BTN)
            
            await page.wait_for_load_state('networkidle')
            
            # 로그인 성공 여부 검사 (예: 로그아웃 버튼 존재 여부)
            logout_btn = await page.query_selector('a.logout')
            if logout_btn:
                return True
            return False
        except Exception as e:
            print(f"LCMS login error: {e}")
            return False

    async def fetch_assignments(self, page: Page) -> List[Dict[str, Any]]:
        """LCMS 과제 수집 로직 (가상의 구조)"""
        assignments = []
        try:
            report_url = f"{self.url}/report/list.jsp"
            await page.goto(report_url)
            await asyncio.sleep(self.sleep_time)
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            rows = soup.select('table.board_list tbody tr')
            for row in rows:
                cols = row.select('td')
                if len(cols) < 5:
                    continue
                    
                course_name = cols[0].text.strip()
                title = cols[1].text.strip()
                raw_deadline = cols[2].text.strip()
                status_text = cols[4].text.strip()
                
                status = 'pending'
                if '완료' in status_text or '제출' in status_text:
                    status = 'submitted'
                elif '미제출' in status_text:
                    status = 'missing'
                    
                assignments.append({
                    "course": course_name,
                    "title": title,
                    "deadline": self.normalize_deadline(raw_deadline),
                    "status": status,
                    "url": "",
                    "description": ""
                })
                    
        except Exception as e:
            print(f"LCMS fetch error: {e}")
            
        return assignments

    # normalize_deadline은 BaseCrawler의 기본 구현 사용
