import asyncio
import os
from typing import List, Dict, Any
from playwright.async_api import Page, async_playwright
from crawler.base import BaseCrawler
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class HtdreamCrawler(BaseCrawler):
    """
    보건의료기술종합정보시스템 (htdream) 크롤러
    - Playwright 기반
    - .env 환경변수(HTDREAM_ID, HTDREAM_PW)를 이용한 로그인
    """

    async def login(self, page: Page) -> bool:
        env_id = os.getenv("HTDREAM_ID")
        env_pw = os.getenv("HTDREAM_PW")
        
        target_id = self.username if self.username else env_id
        target_pw = self.password if self.password else env_pw
        
        if not target_id or not target_pw:
            print("[Htdream] 로그인 정보가 없습니다. 공개된 공고 목록만 수집합니다.")
            return True # 공개 목록 수집을 위해 True 반환
            
        try:
            login_url = self.login_url if self.login_url else "https://www.htdream.kr/uat/uia/egovLoginUsr.do?userSe=PMS"
            await page.goto(login_url)
            
            # 실제 HTDream 로그인 폼 선택자 (추후 변경 필요 시 수정)
            try:
                await page.fill('input[name="mberId"]', target_id, timeout=3000)
                await page.fill('input[name="password"]', target_pw, timeout=3000)
                await page.click('button.btn_login', timeout=3000)
                await page.wait_for_load_state('networkidle')
            except Exception as e:
                print(f"[Htdream] 로그인 폼 요소 찾기 실패 (공개 목록만 수집): {e}")
                return True
                
            return True
        except Exception as e:
            print(f"[Htdream] Login error: {e}")
            return True # 에러가 나도 공개 목록 수집은 시도하도록 True 반환

    async def fetch_assignments(self, page: Page) -> List[Dict[str, Any]]:
        assignments = []
        try:
            # 보내주신 소스코드 기반 실제 과제 목록 URL
            await page.goto("https://www.htdream.kr/main/pubAmt/PubAmtList.do")
            await asyncio.sleep(self.sleep_time)
            
            # 테이블 구조: table.board tbody tr
            rows = await page.query_selector_all('table.board tbody tr')
            for row in rows:
                cols = await row.query_selector_all('td')
                if len(cols) < 5:
                    continue
                
                # HTML 구조 매핑
                # 0: 사업년도 (e.g. 2026)
                # 1: 공지 아이콘
                # 2: 공고명 (text-left)
                # 3: 공고기간 (e.g. 2026-06-10 ~ 2026-07-01)
                
                title_el = await cols[2].query_selector('a')
                if not title_el:
                    continue
                    
                title = await title_el.inner_text()
                # 불필요한 줄바꿈 제거
                title = title.replace('\n', ' ').strip()
                
                # onclick="fn_select2('8828', 'Y')" 에서 ID 추출
                onclick_attr = await title_el.get_attribute('onclick')
                detail_url = self.url
                if onclick_attr:
                    import re
                    match = re.search(r"fn_select2?\('([^']+)'", onclick_attr)
                    if match:
                        pbanId = match.group(1)
                        detail_url = f"https://www.htdream.kr/main/pubAmt/addPubAmtView2.do?pbanId={pbanId}"
                
                raw_period = await cols[3].inner_text()
                
                # 상태 확인: htdream은 기간 기반으로 판단 (현재 진행중인지 등)
                status = 'pending'
                
                # 공고기간 "2026-06-10 ~ 2026-07-01" 에서 종료일 추출
                deadline = raw_period.split('~')[-1].strip() if '~' in raw_period else raw_period
                
                assignments.append({
                    "course": "HTDream",
                    "title": title,
                    "deadline": self.normalize_deadline(deadline),
                    "status": status,
                    "url": detail_url,
                    "description": ""
                })
        except Exception as e:
            print(f"Htdream fetch error: {e}")
            
        return assignments

    async def run(self) -> tuple[bool, str]:
        """User-Agent 설정 등 봇 회피 로직 포함 가능"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # 세션 쿠키 저장을 위해 context를 유지하는 로직으로 발전시킬 수 있습니다.
                context = await browser.new_context()
                page = await context.new_page()
                page.set_default_timeout(self.timeout)

                print(f"[{self.site_name}] 로그인 시도...")
                is_logged_in = await self.login(page)
                if not is_logged_in:
                    await browser.close()
                    return False, "로그인 실패"

                await asyncio.sleep(self.sleep_time)

                print(f"[{self.site_name}] 공고 수집 중...")
                assignments = await self.fetch_assignments(page)
                
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
