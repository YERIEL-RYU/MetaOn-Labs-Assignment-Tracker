import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import Page
from typing import List, Dict, Any
from datetime import datetime
from crawler.base import BaseCrawler

class CoursemosCrawler(BaseCrawler):
    """코스모스 (Coursemos) 기반 LMS 크롤러 예시"""
    
    # CSS 셀렉터 상수 분리
    SELECTOR_ID = 'input#username'
    SELECTOR_PW = 'input#password'
    SELECTOR_LOGIN_BTN = 'button#loginbtn'
    SELECTOR_COURSE_LIST = 'ul.course-list > li > a'
    SELECTOR_ASSIGNMENT_LIST = 'ul.assignment-list > li'

    async def login(self, page: Page) -> bool:
        """코스모스 시스템 로그인 구현"""
        try:
            await page.goto(self.login_url)
            await page.fill(self.SELECTOR_ID, self.username)
            await page.fill(self.SELECTOR_PW, self.password)
            await page.click(self.SELECTOR_LOGIN_BTN)
            
            # 로그인 성공 후 메인 페이지 또는 대시보드로 이동할 때까지 대기
            await page.wait_for_load_state('networkidle')
            
            # 로그인 실패 체크 (예: 에러 메시지가 있는지)
            error_msg = await page.query_selector('.loginerrors')
            if error_msg:
                return False
                
            return True
        except Exception as e:
            print(f"Coursemos login error: {e}")
            return False

    async def fetch_assignments(self, page: Page) -> List[Dict[str, Any]]:
        """코스모스 과제 수집 로직 (가상의 구조)"""
        assignments = []
        try:
            # 대시보드나 전체 과제 모아보기 페이지로 이동 (가정)
            dashboard_url = f"{self.url}/my/"
            await page.goto(dashboard_url)
            await asyncio.sleep(self.sleep_time)
            
            # BeautifulSoup를 사용한 파싱
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # 가상의 파싱 로직 (실제 사이트 구조에 맞게 수정 필요)
            course_items = soup.select('.course-item')
            for course in course_items:
                course_name = course.select_one('.course-title').text.strip() if course.select_one('.course-title') else "Unknown Course"
                
                tasks = course.select('.task-item')
                for task in tasks:
                    title = task.select_one('.task-title').text.strip()
                    raw_deadline = task.select_one('.deadline').text.strip()
                    status_text = task.select_one('.status').text.strip().lower()
                    
                    status = 'pending'
                    if '제출' in status_text and '미제출' not in status_text:
                        status = 'submitted'
                    
                    assignments.append({
                        "course": course_name,
                        "title": title,
                        "deadline": self.normalize_deadline(raw_deadline),
                        "status": status,
                        "url": self.url + task.select_one('a')['href'] if task.select_one('a') else "",
                        "description": ""
                    })
                    
        except Exception as e:
            print(f"Coursemos fetch error: {e}")
            
        return assignments

    # normalize_deadline은 BaseCrawler의 기본 구현 사용
