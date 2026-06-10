import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from crawler.base import BaseCrawler
import time

class SromeCrawler(BaseCrawler):
    """
    S-ROME (KEIT 산업기술R&D) 크롤러
    - requests + BeautifulSoup 사용 (정적 HTML)
    - 로그인 불필요
    """

    async def login(self, page: Any = None) -> bool:
        # 로그인 불필요
        return True

    async def fetch_assignments(self, page: Any = None) -> List[Dict[str, Any]]:
        # SromeCrawler는 run()을 통째로 오버라이드하여 이 메서드는 사용하지 않습니다.
        return []

    async def run(self) -> tuple[bool, str]:
        """Playwright를 사용하지 않고 requests로 동기적 실행을 담당합니다."""
        print(f"[{self.site_name}] requests 수집 시작...")
        assignments = []
        try:
            # 예시 URL 순회 로직 (pageIndex 1 ~ 3까지만 순회한다고 가정)
            max_pages = 3 
            base_url = "https://srome.keit.re.kr/srome/biz/perform/opnnPrpsl/retrieveTaskAnncmListView.do"
            
            for page_idx in range(1, max_pages + 1):
                url = f"{base_url}?prgmId=XPG201040000&pageIndex={page_idx}"
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    print(f"[{self.site_name}] 페이지 {page_idx} 요청 실패: HTTP {response.status_code}")
                    break
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 보내주신 SROME HTML 구조 (div 기반)
                rows = soup.select('.table_list .table_box')
                if not rows:
                    break
                    
                for row in rows:
                    title_el = row.select_one('p.subject span.title')
                    if not title_el:
                        continue
                        
                    title = title_el.text.strip()
                    
                    detail_url = url
                    a_el = row.select_one('p.subject a')
                    if a_el and a_el.has_attr('onclick'):
                        import re
                        match = re.search(r"f_detail\('([^']+)',\s*'([^']+)'", a_el['onclick'])
                        if match:
                            ancmId = match.group(1)
                            bsnsYy = match.group(2)
                            detail_url = f"https://srome.keit.re.kr/srome/biz/perform/opnnPrpsl/retrieveTaskAnncmInfoView.do?pageIndex=&ancmId={ancmId}&bsnsYy={bsnsYy}&prgmId=XPG201040000&srchGubun=&srchKwd=&startDate=&endDate=&rcveStatus=all"
                    
                    status_text = ""
                    badges = row.select('p.banner span.badge')
                    for badge in badges:
                        if badge.text.strip() in ['접수중', '접수예정', '접수마감']:
                            status_text = badge.text.strip()
                            break
                    
                    status = 'pending'
                    if '마감' in status_text:
                        status = 'missing'
                    
                    period = ""
                    info_ps = row.select('.info p')
                    for p in info_ps:
                        label = p.select_one('.label')
                        if label and '접수기간' in label.text:
                            val_el = p.select_one('.value')
                            if val_el:
                                period = val_el.text.strip() # 예: "2026-05-29 09:00 ~ 2026-06-30 18:00"
                            break
                    
                    # 마감일 추출 (기간의 뒷부분)
                    deadline = period.split('~')[-1].strip() if '~' in period else period
                    
                    assignments.append({
                        "course": "KEIT R&D 공고",
                        "title": title,
                        "deadline": self.normalize_deadline(deadline),
                        "status": status,
                        "url": detail_url,
                        "description": ""
                    })
                    
                time.sleep(self.sleep_time) # 서버 부하 방지를 위한 간격
                
            if assignments:
                self.save(assignments)
                print(f"[{self.site_name}] {len(assignments)}개 과제 저장 완료.")
            else:
                print(f"[{self.site_name}] 수집된 과제가 없습니다.")
                
            return True, ""
            
        except Exception as e:
            error_msg = f"크롤링 중 오류 발생: {str(e)}"
            print(f"[{self.site_name}] {error_msg}")
            return False, error_msg

    # normalize_deadline은 BaseCrawler의 기본 구현 사용
