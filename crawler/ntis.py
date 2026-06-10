import asyncio
from typing import List, Dict, Any
from playwright.async_api import Page, async_playwright
from crawler.base import BaseCrawler

class NtisCrawler(BaseCrawler):
    """
    NTIS (국가R&D통합공고) 크롤러
    - Playwright headless 사용
    - User-Agent 우회 필요 (robots.txt 차단 회피용)
    """

    async def login(self, page: Page) -> bool:
        # 공고 목록은 대개 로그인 불필요이거나, 필요하다면 여기에 구현
        return True

    async def fetch_assignments(self, page: Page) -> List[Dict[str, Any]]:
        assignments = []
        try:
            # NTIS 공고 목록 페이지
            await page.goto("https://www.ntis.go.kr/rndgate/eg/un/ra/mng.do")
            await asyncio.sleep(self.sleep_time)
            
            rows = await page.query_selector_all('table.basic_list tbody tr')
            for row in rows:
                title_el = await row.query_selector('td[data-title="공고명"] a')
                if not title_el:
                    continue
                    
                title = await title_el.inner_text()
                
                href_attr = await title_el.get_attribute('href')
                detail_url = self.url
                if href_attr:
                    detail_url = "https://www.ntis.go.kr" + href_attr
                
                deadline_el = await row.query_selector('td[data-title="마감일"]') 
                raw_deadline = await deadline_el.inner_text() if deadline_el else ""
                
                status_el = await row.query_selector('td[data-title="현황"] span')
                status_text = await status_el.inner_text() if status_el else ""
                
                status = 'pending'
                if '마감' in status_text:
                    status = 'missing'
                
                assignments.append({
                    "course": "NTIS 공고",
                    "title": title.strip(),
                    "deadline": self.normalize_deadline(raw_deadline.strip()),
                    "status": status,
                    "url": detail_url,
                    "description": ""
                })
        except Exception as e:
            print(f"NTIS fetch error: {e}")
            
        return assignments

    async def run(self) -> tuple[bool, str]:
        """User-Agent 설정을 위해 run() 오버라이드"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                page.set_default_timeout(self.timeout)

                # 봇 감지 우회를 위한 User-Agent 헤더 셋팅
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })

                print(f"[{self.site_name}] 크롤링 시작...")
                await self.login(page)
                await asyncio.sleep(self.sleep_time)
                
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
